#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""贵金属（黄金元/克，白银元/克）+ A股当日成交额排行"""
import json, subprocess, urllib.request, urllib.error, ssl

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

def get(url):
    h = curl(url)
    if not h or len(h) < 50:
        h = fallback(url)
    return h

def fetch():
    result = {'metals': [], 'volume': []}

    # 1. 贵金属
    # 黄金ETF(159934) = 1份≈0.01克 → 金价元/克 = price × 100
    # 白银LOF(161226) = 跟踪LBMA银价, 1份≈0.00032盎司≈0.01克 → 银价元/克 = price × 100
    # 简化：都按×100近似
    h = get('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f2,f3,f4,f12,f14&secids=0.159934,0.161226')
    try:
        for it in json.loads(h).get('data',{}).get('diff',[]):
            name = it.get('f14','')
            price = it.get('f2',0)
            change = it.get('f3',0)
            chg_s = f'{change:+.2f}%' if change else '0%'
            if '黄金' in name:
                g = round(price * 100, 1)
                result['metals'].append({'name':'黄金','price':f'{g}元/克','change':chg_s})
            elif '白银' in name:
                g = round(price * 100, 2)
                result['metals'].append({'name':'白银','price':f'{g}元/克','change':chg_s})
    except: pass

    # 2. A股当日成交额排行
    h2 = get('https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=8&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3,f4,f12,f14,f62')
    try:
        for it in json.loads(h2).get('data',{}).get('diff',[]):
            name = it.get('f14','')
            code = it.get('f12','')
            price = it.get('f2',0)
            change = it.get('f3',0)
            amt = it.get('f62',0) / 1e8
            p = f'{price:.2f}'
            if price >= 100: p = f'{price:.1f}'
            result['volume'].append({'name':name,'code':code,'price':p,'change':f'{change:+.2f}%' if change else '','vol':f'{amt:.1f}亿'})
    except: pass

    return result

if __name__ == '__main__':
    data = fetch()
    with open('metal_volume.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f'Metals: {len(data["metals"])}, Volume: {len(data["volume"])}')
