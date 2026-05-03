#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""贵金属 + A股成交额排行采集器"""
import json, subprocess, re

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
                gold_g = round(price * 100, 1)  # 折算元/克
                result['metals'].append({
                    'name': '黄金',
                    'price': f'{gold_g}元/克',
                    'change': f'{change:+.2f}%' if change else '0%'
                })
            elif '白银' in name:
                silver_g = round(price * 100, 2)  # 白银LOF类似折算
                result['metals'].append({
                    'name': '白银',
                    'price': f'{silver_g}元/克',
                    'change': f'{change:+.2f}%' if change else '0%'
                })
    except: pass

    # 2. A股成交额排行
    h2 = curl('https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=8&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f20&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3,f4,f12,f14,f20')
    try:
        j2 = json.loads(h2)
        items2 = j2.get('data',{}).get('diff',[])
        for it in items2:
            name = it.get('f14','')
            code = it.get('f12','')
            price = it.get('f2',0)
            change = it.get('f3',0)
            vol_yuan = it.get('f20',0) / 1e8  # 转亿
            result['volume'].append({
                'name': name,
                'code': code,
                'price': f'{price:.2f}' if price < 1000 else f'{price:.1f}',
                'change': f'{change:+.2f}%' if change else '',
                'vol': f'{vol_yuan:.0f}亿'
            })
    except: pass

    return result

if __name__ == '__main__':
    data = fetch()
    with open('metal_volume.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f'Metals: {len(data["metals"])}, Volume: {len(data["volume"])}')
