#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""热议话题采集器 - 来自新闻中高频讨论的话题 + 百度热搜"""
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

def f(url, fallback_first=False):
    if fallback_first:
        h2 = fallback(url)
        if len(h2) > 100: return h2
    h = curl(url)
    return h if len(h) >= 100 else (fallback(url) or h)

def collect():
    all_items = []

    # 1. 百度实时热搜（无反爬，直接 JSON）
    print('  Fetching 百度热搜...')
    h = f('https://top.baidu.com/board?tab=realtime')
    for m in re.finditer(r'"word":"([^"]{4,40})"', h):
        t = m.group(1).strip()
        if any(x in t for x in ['广告','推广']): continue
        # 放热度指数
        hot_raw = ''
        hm = re.search(r'"rawHot":"(\d+)"', h[m.end():m.end()+200])
        if hm: hot_raw = hm.group(1)
        if t[:8] not in [x.get('t','')[:8] for x in all_items]:
            tag = '🔥' if hot_raw and int(hot_raw) > 500000 else ''
            all_items.append({'t':tag + t[:40], 'src':'百度热搜', 'cat':'topic'})
            if len([x for x in all_items if x['src']=='百度热搜']) >= 8:
                break

    # 2. 脉脉热榜（职场热议，常出社会话题）
    print('  Fetching 脉脉热榜...')
    h = f('https://maimai.cn/web/topic_center')
    for m in re.finditer(r'"title":"([^"]{4,40})"', h):
        t = m.group(1).strip()
        if t[:8] not in [x.get('t','')[:8] for x in all_items]:
            all_items.append({'t':t[:40], 'src':'脉脉热榜', 'cat':'topic'})
            if len([x for x in all_items if x['src']=='脉脉热榜']) >= 4:
                break

    # 3. 虎嗅推荐（科技+商业热议）
    print('  Fetching 虎嗅热议...')
    h = f('https://www.huxiu.com/')
    for m in re.finditer(r'<h2[^>]*>([^<]{6,50})</h2>', h):
        t = m.group(1).strip()
        t = re.sub(r'<[^>]+>', '', t).strip()
        if not t: continue
        if t[:10] not in [x.get('t','')[:10] for x in all_items]:
            all_items.append({'t':t[:45], 'src':'虎嗅热议', 'cat':'topic'})
            if len([x for x in all_items if x['src']=='虎嗅热议']) >= 6:
                break

    # 4. V2EX 热门（程序员社区热议）
    print('  Fetching V2EX 热门...')
    h = f('https://www.v2ex.com/')
    for m in re.finditer(r'class="topic-link"[^>]*>([^<]{6,60})</a>', h):
        t = m.group(1).strip()
        if t[:10] not in [x.get('t','')[:10] for x in all_items]:
            all_items.append({'t':t[:45], 'src':'V2EX', 'cat':'topic'})
            if len([x for x in all_items if x['src']=='V2EX']) >= 4:
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
