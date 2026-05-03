#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""热卖榜采集器 - 京东/淘宝/什么值得买热销商品"""
import json, subprocess, re

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','8','--max-time','10','-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

def collect():
    all_items = []

    # 1. 什么值得买 - 热销榜
    print('  Fetching 什么值得买...')
    h = curl('https://www.smzdm.com/')
    # 找商品标题
    for m in re.finditer(r'"title":"([^"]{4,60})"', h):
        t = m.group(1).strip()
        if any(x in t for x in ['优惠','优惠券','促销','满减','好价']):
            continue
        if len(t) >= 6 and t[:8] not in [x.get('t','')[:8] for x in all_items]:
            all_items.append({'t':t[:50], 'src':'什么值得买', 'cat':'shop'})

    # 2. 京东排行榜 - 实时热卖
    print('  Fetching 京东排行榜...')
    h = curl('https://www.jd.com/')
    for m in re.finditer(r'<a[^>]*href="(//item\.jd\.com/[^"]+)"[^>]*>([^<]{6,50})</a>', h):
        t = m.group(2).strip()
        # 去重
        if t[:8] in [x.get('t','')[:8] for x in all_items]:
            continue
        t = re.sub(r'<[^>]+>', '', t)
        t = re.sub(r'\s+', ' ', t).strip()
        if len(t) >= 6 and len(t) <= 50:
            all_items.append({'t':t[:50], 'u':'https:' + m.group(1), 'src':'京东热卖', 'cat':'shop'})
        if len(all_items) >= 20:
            break

    # 3. 淘宝热销
    print('  Fetching 淘宝热销...')
    h = curl('https://www.taobao.com/')
    for m in re.finditer(r'"title":"([^"]{6,50})"', h):
        t = m.group(1).strip()
        t = re.sub(r'<[^>]+>', '', t)
        t = re.sub(r'\s+', ' ', t).strip()
        if t[:8] in [x.get('t','')[:8] for x in all_items]:
            continue
        if len(t) >= 6 and '广告' not in t:
            all_items.append({'t':t[:50], 'src':'淘宝热销', 'cat':'shop'})
        if len(all_items) >= 25:
            break

    # 4. 抖音电商热卖（通过什么值得买补充）
    # 已经通过 smzdm 获取了

    # 去重
    seen=set();deduped=[]
    for item in all_items:
        k = item['t'][:10]
        if k not in seen:
            seen.add(k)
            deduped.append(item)
    return deduped[:20]

if __name__ == '__main__':
    items = collect()
    with open('shop_news.json', 'w', encoding='utf-8') as f:
        json.dump({'shop': items}, f, ensure_ascii=False)
    print(f'Shop collector done: {len(items)} items')
