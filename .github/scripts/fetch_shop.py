#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""热议话题采集器 - 百度热搜+社区热议+网站流量排名"""
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
    return h if len(h) >= 100 else (fallback(url) or h)

# 主要平台流量排名
PLATFORMS = [
    ('淘宝', 'taobao.com'),
    ('京东', 'jd.com'),
    ('拼多多', 'pinduoduo.com'),
    ('抖音', 'douyin.com'),
    ('哔哩哔哩', 'bilibili.com'),
    ('微博', 'weibo.com'),
    ('知乎', 'zhihu.com'),
    ('小红书', 'xiaohongshu.com'),
    ('百度', 'baidu.com'),
    ('快手', 'kuaishou.com'),
    ('美团', 'meituan.com'),
    ('闲鱼', '2.taobao.com'),
    ('得物', 'dewu.com'),
]

def fetch_ranks():
    """从Tranco获取全球网站排名"""
    results = []
    for name, domain in PLATFORMS:
        url = f'https://tranco-list.eu/api/ranks/domain/{domain}'
        try:
            h = fallback(url) if url.startswith('https') else curl(url)
            j = json.loads(h)
            rank = j.get('ranks', [{}])[0].get('rank', 0)
            results.append({'name': name, 'domain': domain, 'rank': rank})
            print(f'  {name}: #{rank}')
        except:
            results.append({'name': name, 'domain': domain, 'rank': 0})
            print(f'  {name}: error')
    results.sort(key=lambda x: (x['rank'] or 99999))
    return results

def collect():
    all_items = []

    # 1. 网站流量排名（热议的基础背景）
    print('  Fetching Tranco ranks...')
    ranks = fetch_ranks()
    # 排名数据只返回，不加入话题列表（在generate_site里单独渲染）
    for r in ranks:
        pass  # ranks will be rendered as a separate section

    # 2. 百度实时热搜
    print('  Fetching 百度热搜...')
    h = f('https://top.baidu.com/board?tab=realtime')
    for m in re.finditer(r'"word":"([^"]{4,40})"', h):
        t = m.group(1).strip()
        if any(x in t for x in ['广告','推广']): continue
        hot_raw = ''
        hm = re.search(r'"rawHot":"(\d+)"', h[m.end():m.end()+200])
        if hm: hot_raw = hm.group(1)
        if t[:8] not in [x.get('t','')[:8] for x in all_items]:
            tag = '🔥' if hot_raw and int(hot_raw) > 500000 else ''
            all_items.append({'t':tag + t[:40], 'src':'百度热搜', 'cat':'topic'})
            if len([x for x in all_items if x['src']=='百度热搜']) >= 6:
                break

    # 3. V2EX 热门
    print('  Fetching V2EX...')
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
    return deduped[:20], ranks

if __name__ == '__main__':
    items, ranks = collect()
    data = {'shop': items, 'ranks': ranks}
    with open('shop_news.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f'Topic collector done: {len(items)} items + {len(ranks)} ranks')
