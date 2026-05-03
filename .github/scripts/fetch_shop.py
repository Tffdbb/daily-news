#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""热卖榜采集器 - 什么值得买好价/热门"""
import json, subprocess, re

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','8','--max-time','10','-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

def collect():
    all_items = []

    # 1. 什么值得买 - 好价
    print('  Fetching 什么值得买好价...')
    h = curl('https://www.smzdm.com/')
    # JSON 嵌入的数据
    for m in re.finditer(r'"title":"([^"]{4,60})"', h):
        t = m.group(1).strip()
        if not t or len(t) < 6: continue
        if any(x in t for x in ['优惠券','促销','满减','签到','抽奖']): continue
        if t[:8] in [x.get('t','')[:8] for x in all_items]: continue
        all_items.append({'t':t[:50], 'src':'什么值得买', 'cat':'shop'})

    # 2. 什么值得买 - 排行榜
    print('  Fetching 值得买排行榜...')
    h = curl('https://www.smzdm.com/top/')
    for m in re.finditer(r'"title":"([^"]{6,60})"', h):
        t = m.group(1).strip()
        if not t or len(t) < 6: continue
        if t[:8] in [x.get('t','')[:8] for x in all_items]: continue
        all_items.append({'t':t[:50], 'src':'值得买热榜', 'cat':'shop'})

    # 3. 淘宝/天猫热销API
    print('  Fetching 淘宝热销...')
    h = curl('https://www.taobao.com/')
    # 淘宝首页搜索框的热搜词
    for m in re.finditer(r'"text":"([^"]{4,30})"', h):
        t = m.group(1).strip()
        if '广告' in t or '推广' in t: continue
        if t[:6] in [x.get('t','')[:6] for x in all_items]: continue
        if len(t) >= 4:
            all_items.append({'t':'🔥 ' + t, 'src':'淘宝热搜', 'cat':'shop'})

    # 4. 抖音热卖（通过抖音开放数据）
    print('  Fetching 抖音热卖...')
    h = curl('https://www.douyin.com/')
    for m in re.finditer(r'"word":"([^"]{4,30})"', h):
        t = m.group(1).strip()
        if t[:6] in [x.get('t','')[:6] for x in all_items]: continue
        if len(t) >= 4:
            all_items.append({'t':'🎬 ' + t, 'src':'抖音热榜', 'cat':'shop'})

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
