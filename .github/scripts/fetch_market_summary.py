#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A股大盘日报 + 周趋势 + 月趋势 数据采集"""

import json, sys, urllib.request, ssl, datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read().decode('utf-8')
    except Exception as e:
        return None

def fetch_json(url, timeout=8):
    raw = api(url, timeout)
    if raw:
        try:
            if raw.startswith('(') or raw.startswith('{'):
                return json.loads(raw)
            if '({' in raw:
                raw = raw[raw.index('(')+1:raw.rindex(')')]
                return json.loads(raw)
        except:
            pass
    return None

def get_kline(secid, scale, datalen):
    """获取K线数据, scale=240日K, 周K不用(默认240日线), 取足够天数"""
    url = (f'https://push2.eastmoney.com/api/qt/stock/kline/get?secid={secid}'
           f'&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'
           f'&klt=101&fqt=1&end=20500101&lmt={datalen}')
    data = fetch_json(url)
    if data and data.get('data') and data['data'].get('klines'):
        return [x.split(',') for x in data['data']['klines']]
    return []

def analyze_trend(klines, label):
    """
    分析K线趋势，返回：
    {
        'label': '本周'/'本月',
        'start_date': '', 'end_date': '',
        'range': '',         # 涨跌幅
        'direction': '',      # 上涨/下跌/震荡
        'vol_trend': '',      # 放量/缩量
        'summary': ''         # 一句话结论
    }
    """
    if not klines or len(klines) < 2:
        return None
    
    first = klines[0]
    last = klines[-1]
    # 格式: f51=日期, f52=开盘, f53=收盘, f54=最高, f55=最低, f56=成交量(手), f57=成交额
    open_p = float(first[1])
    close_p = float(last[2])
    high_p = max(float(k[3]) for k in klines)
    low_p = min(float(k[4]) for k in klines)
    
    start_date = first[0]
    end_date = last[0]
    
    # 涨跌幅
    pct = (close_p - open_p) / open_p * 100 if open_p else 0
    
    # 方向判断
    if pct > 2:
        direction = '📈 显著上涨'
    elif pct > 0.5:
        direction = '📈 小幅上涨'
    elif pct > -0.5:
        direction = '➡️ 区间震荡'
    elif pct > -2:
        direction = '📉 小幅下跌'
    else:
        direction = '📉 显著下跌'
    
    # 波动率（最高最低差距）
    swing = (high_p - low_p) / low_p * 100 if low_p else 0
    
    # 量能趋势：前半段 vs 后半段
    half = len(klines) // 2
    vol_first = sum(float(k[5]) for k in klines[:half]) / half
    vol_second = sum(float(k[5]) for k in klines[half:]) / (len(klines) - half)
    vol_diff = (vol_second - vol_first) / vol_first * 100 if vol_first else 0
    if vol_diff > 20:
        vol_trend = '后段放量'
    elif vol_diff < -20:
        vol_trend = '后段缩量'
    else:
        vol_trend = '量能平稳'
    
    # 连续涨跌天数
    up_days = 0
    down_days = 0
    max_up = 0
    max_down = 0
    for i in range(1, len(klines)):
        if float(klines[i][2]) > float(klines[i-1][2]):
            up_days += 1
            down_days = 0
            max_up = max(max_up, up_days)
        else:
            down_days += 1
            up_days = 0
            max_down = max(max_down, down_days)
    
    # 总结
    swing_desc = '' if swing > 10 else '波动较小' if swing < 3 else ''
    vol_desc = vol_trend
    parts = [direction, f'{pct:+.2f}%']
    if swing > 5: parts.append(f'振幅{swing:.1f}%')
    parts.append(vol_desc)
    if max_up >= 4: parts.append(f'连涨{max_up}天')
    if max_down >= 3: parts.append(f'连跌{max_down}天')
    
    return {
        'label': label,
        'start_date': start_date,
        'end_date': end_date,
        'range': f'{pct:+.2f}%',
        'direction': direction,
        'open': f'{open_p:.0f}' if open_p > 10 else f'{open_p:.1f}',
        'close': f'{close_p:.0f}' if close_p > 10 else f'{close_p:.1f}',
        'high': f'{high_p:.0f}' if high_p > 10 else f'{high_p:.1f}',
        'low': f'{low_p:.0f}' if low_p > 10 else f'{low_p:.1f}',
        'swing': f'{swing:.1f}%',
        'vol_trend': vol_trend,
        'max_up_days': max_up,
        'max_down_days': max_down,
        'summary': ' '.join(parts)
    }

def main():
    result = {
        'indices': [],
        'sectors_up': [],
        'sectors_down': [],
        'zt_count': 0,
        'dt_count': 0,
        'summary': '',
        'weekly': None,
        'monthly': None
    }

    # 1. 三大指数
    idx_url = ('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f2,f3,f4,f12,f14'
               '&secids=1.000001,0.399001,0.399006')
    idx_data = fetch_json(idx_url)
    name_map = {'000001':'上证指数', '399001':'深证成指', '399006':'创业板指'}
    if idx_data and idx_data.get('data',{}).get('diff'):
        for item in idx_data['data']['diff']:
            code = item.get('f12','')
            price = item.get('f2',0)
            change = item.get('f3',0) or 0
            result['indices'].append({
                'name': name_map.get(code, item.get('f14',code)),
                'price': f'{price:.0f}' if price > 10 else f'{price:.1f}',
                'change': f'{change:+.2f}%'
            })

    # 2. 行业板块涨跌
    sector_url = ('https://push2.eastmoney.com/api/qt/clist/get?cb=&fid=f3&po=0&pz=20&pn=1&np=1'
                  '&fltt=2&invt=2&fs=m:90+t:3&fields=f12,f14,f3,f62')
    sec_data = fetch_json(sector_url)
    if sec_data and sec_data.get('data',{}).get('diff'):
        items = sec_data['data']['diff']
        real_sectors = [x for x in items if x.get('f14','') not in ('融资融券','深股通','富时罗素','标准普尔','沪深300','上证50')]
        real_sectors.sort(key=lambda x: (x.get('f3') or 0), reverse=True)
        for s in real_sectors[:3]:
            pct = s.get('f3',0)
            result['sectors_up'].append({'name': s['f14'], 'pct': f'{pct:+.2f}'})
        real_sectors.sort(key=lambda x: (x.get('f3') or 0))
        for s in real_sectors[:3]:
            pct = s.get('f3',0)
            result['sectors_down'].append({'name': s['f14'], 'pct': f'{pct:+.2f}'})

    # 3. 涨停跌停
    all_url = ('https://push2.eastmoney.com/api/qt/clist/get?cb=&fid=f3&po=0&pz=500&pn=1&np=1'
               '&fltt=2&invt=2&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f3')
    all_data = fetch_json(all_url)
    zt = dt = 0
    if all_data and all_data.get('data',{}).get('diff'):
        for item in all_data['data']['diff']:
            chg = item.get('f3',0)
            if chg >= 9.95: zt += 1
            elif chg <= -9.95: dt += 1
    result['zt_count'] = zt
    result['dt_count'] = dt

    # 4. 一句话总结
    if result['indices']:
        idx = result['indices'][0]
        chg_val = idx.get('change','0%').replace('%','')
        chg_float = float(chg_val.replace('+',''))
        if chg_float > 1:
            feeling = '市场全面走强'
        elif chg_float > 0.3:
            feeling = '市场温和上涨'
        elif chg_float > -0.3:
            feeling = '市场窄幅震荡'
        elif chg_float > -1:
            feeling = '市场小幅回调'
        else:
            feeling = '市场明显走弱'
        parts = []
        if zt > 20: parts.append(f'涨停{zt}家')
        if dt > 5: parts.append(f'跌停{dt}家')
        s_up = '-'.join(s['name'] for s in result['sectors_up'])
        if s_up: parts.append('领涨:'+s_up)
        if parts:
            result['summary'] = feeling + ' | ' + ' '.join(parts)
        else:
            result['summary'] = feeling

    # === 5. 周趋势分析 ===
    # 取最近5个交易日 = 1周
    klines = get_kline('1.000001', 240, 5)
    if klines and len(klines) >= 2:
        result['weekly'] = analyze_trend(klines, '本周')

    # === 6. 月趋势分析 ===
    # 取最近22个交易日 ≈ 1个月
    klines_month = get_kline('1.000001', 240, 22)
    if klines_month and len(klines_month) >= 5:
        result['monthly'] = analyze_trend(klines_month, '本月')

    # 写入
    try:
        with open('news_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {}
    data['market_summary'] = result
    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    print(f'MARKET_SUMMARY: 指数{len(result["indices"])}个, 涨停{zt}, 跌停{dt}')
    if result['weekly']: print(f'  周: {result["weekly"]["summary"]}')
    if result['monthly']: print(f'  月: {result["monthly"]["summary"]}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
