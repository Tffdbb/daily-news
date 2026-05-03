#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A股量化选股 - 多因子策略"""
import json, subprocess, urllib.request, urllib.error, ssl, sys

_CTX = ssl.create_default_context()
_CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','8','--max-time','10','-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

def fallback(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=10, context=_CTX)
        b = r.read()
        try: return b.decode('utf-8')
        except: return b.decode('gbk','replace')
    except: return ''

def get(url):
    h = curl(url)
    if not h or len(h) < 50:
        h = fallback(url)
    return h

def pick(stocks):
    c = []
    for s in stocks:
        name = s.get('f14','')
        code = s.get('f12','')
        if 'ST' in name or '退' in name: continue
        chg = s.get('f3',0) or 0
        if chg < 1.0 or chg > 18.0: continue
        vr = s.get('f23',0) or 0
        if vr < 0.8: continue
        to = s.get('f38',0) or 0
        if to < 0.5: continue
        pe = s.get('f115',0) or 0
        if pe > 500: continue
        amt = (s.get('f62',0) or 0) / 1e8
        cc = (s.get('f21',1) or 1) / 1e10
        rt = to/1e8 if to > 100 else to
        score = 0
        score += min(chg/5, 1.5)*20
        score += min(vr/3, 1.5)*20
        score += min(rt/5, 1.0)*15
        score += min(amt/5, 1.0)*15
        score += min(cc/30, 1.0)*15
        if 10 < pe < 50: score += 15
        c.append({'name':name,'code':code,'chg':chg,'volRatio':vr,'turnover':'%.1f'%rt,'pe':int(pe),'amt':round(amt,1),'score':round(score,1)})
    c.sort(key=lambda x:-x['score'])
    return c[:10]

def main():
    all_ = []
    for page in [1,2,3,4,5]:
        url = 'https://push2.eastmoney.com/api/qt/clist/get?pn=%d&pz=100&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23,f25,f37,f38,f62,f115,f152,f168,f169,f170,f171' % page
        h = get(url)
        try:
            items = json.loads(h).get('data',{}).get('diff',[])
            all_.extend(items)
        except: pass
        if len(items) < 100: break
    picks = pick(all_)
    with open('quant_picks.json','w',encoding='utf-8') as f:
        json.dump({'picks':picks}, f, ensure_ascii=False)
    print('scan %d picked %d' % (len(all_), len(picks)))

if __name__ == '__main__':
    main()
