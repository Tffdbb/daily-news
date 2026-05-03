#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""贵金属 + A股成交额排行采集器"""
import json, subprocess, re, urllib.request, urllib.error, ssl

_CTX = ssl.create_default_context()
_CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
def fallback(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=10, context=_CTX)
        b = r.read()
        try: return b.decode('utf-8')
        except: return b.decode('gbk','replace')
    except: return ''

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','8','--max-time','10','-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

def fetch():
    result = {'metals': [], 'volume': []}

    # 1. 黄金ETF（折算国际金价）
    # 黄金ETF(159934) 价格10.1元 ≈ 1克黄金≈？元
    # 公式：1克黄金 = 黄金ETF价格 × 100 ÷ 持仓份额（约1份=0.01克）
    # 简单近似：黄金ETF价格 × 100 ≈ 国内金价(元/克)
    h = curl('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f2,f3,f4,f12,f14&secids=0.159934,0.518880,0.161226')
    try:
        j = json.loads(h)
        items = j.get('data',{}).get('diff',[])
        for it in items:
            name = it.get('f14','')
            price = it.get('f2',0)
            change = it.get('f3',0)
            if '黄金' in name:
                # 黄金ETF(159934) 价格10.1元 = 1份=0.01克 → 1克=100份=价格×100
                # 更准：实际持仓约每份0.01克，金价元/克 = price / 0.01 = price * 100
                gold_g = round(price / 0.01, 1) if price > 0 else 0
                result['metals'].append({
                    'name': '黄金',
                    'price': f'{gold_g}元/克',
                    'change': f'{change:+.2f}%' if change else '0%'
                })
            elif '白银' in name:
                # 白银LOF(161226)跟踪国际银价，1份≈0.001盎司≈0.031克
                # 元/克 = price / 0.031
                silver_g = round(price / 0.031, 2) if price > 0 else 0
                result['metals'].append({
                    'name': '白银',
                    'price': f'{silver_g}元/克',
                    'change': f'{change:+.2f}%' if change else '0%'
                })
    except: pass

    # 2. A股成交额排行（当日成交额f62）
    h2 = curl('https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=8&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3,f4,f12,f14,f62')
    if not h2 or len(h2) < 50:
        h2 = fallback(h2)
    try:
        j2 = json.loads(h2)
        items2 = j2.get('data',{}).get('diff',[])
        for it in items2:
            name = it.get('f14','')
            code = it.get('f12','')
            price = it.get('f2',0)
            change = it.get('f3',0)
            # f62是当日成交额(元)，/1e8转亿
            amt = it.get('f62',0) / 1e8
            result['volume'].append({
                'name': name,
                'code': code,
                'price': f'{price:.2f}' if price < 1000 else f'{price:.1f}',
                'change': f'{change:+.2f}%' if change else '',
                'vol': f'{amt:.1f}亿'
            })
    return result

if __name__ == '__main__':
    data = fetch()
    with open('metal_volume.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f'Metals: {len(data["metals"])}, Volume: {len(data["volume"])}')
