#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""热议话题采集器 - 知乎热榜+豆瓣热门+微博热议"""
import json, subprocess, re, urllib.request, urllib.error, ssl

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','8','--max-time','10','-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

_CTX = ssl.create_default_context()
_CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
def fallback(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=10, context=_CTX)
        return r.read().decode('utf-8','replace')
    except: return ''

def f(url):
    h = curl(url)
    if len(h) < 100:
        h2 = fallback(url)
        if len(h2) > len(h): return h2
    return h

def collect():
    all_items = []

    # 1. 知乎热榜（JSON API，无反爬）
    print('  Fetching 知乎热榜...')
    h = f('https://www.zhihu.com/billboard')
    # 或者用热榜API
    h2 = f('https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20')
    for m in re.finditer(r'"title":"([^"]{6,60})"', h2):
        t = m.group(1).strip()
        t = t.replace('\\u0026','&').replace('\\quot;','"')
        if t[:8] not in [x.get('t','')[:8] for x in all_items]:
            all_items.append({'t':t[:50], 'src':'知乎热榜', 'cat':'topic'})
            if len([x for x in all_items if x['src']=='知乎热榜']) >= 8:
                break

    # 备用：从页面HTML提取
    if len([x for x in all_items if x['src']=='知乎热榜']) < 3:
        h3 = f('https://www.zhihu.com/hot')
        for m in re.finditer(r'"titleText":"([^"]{6,60})"', h3):
            t = m.group(1).strip()
            if t[:8] not in [x.get('t','')[:8] for x in all_items]:
                all_items.append({'t':t[:50], 'src':'知乎热榜', 'cat':'topic'})

    # 2. 豆瓣热门（豆瓣小组精选/书影音热门）
    print('  Fetching 豆瓣热门...')
    h = f('https://www.douban.com/group/explore')
    for m in re.finditer(r'title="([^"]{6,60})"', h):
        t = m.group(1).strip()
        if len(t) < 6: continue
        if any(x in t for x in ['加入','退出','论坛']): continue
        if t[:10] not in [x.get('t','')[:10] for x in all_items]:
            all_items.append({'t':t[:50], 'src':'豆瓣热门', 'cat':'topic'})
            if len([x for x in all_items if x['src']=='豆瓣热门']) >= 6:
                break

    # 3. 微博热搜（JSON嵌入）
    print('  Fetching 微博热搜...')
    h = f('https://weibo.com/ajax/side/hotSearch')
    for m in re.finditer(r'"word":"([^"]{4,40})"', h):
        t = m.group(1).strip()
        # 过滤广告
        if '广告' in t or '推荐' in t: continue
        if t[:8] not in [x.get('t','')[:8] for x in all_items]:
            all_items.append({'t':t[:40], 'src':'微博热搜', 'cat':'topic'})
            if len([x for x in all_items if x['src']=='微博热搜']) >= 6:
                break

    # 去重
    seen=set();deduped=[]
    for item in all_items:
        k = item['t'][:10]
        if k not in seen:
            seen.add(k)
            deduped.append(item)
    return deduped[:15]

if __name__ == '__main__':
    items = collect()
    with open('shop_news.json', 'w', encoding='utf-8') as f:
        json.dump({'shop': items}, f, ensure_ascii=False)
    print(f'Topic collector done: {len(items)} items')
