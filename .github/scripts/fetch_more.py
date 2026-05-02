#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""垂直领域采集器 - 知乎日报/豆瓣热门/GitHub Trending/少数派"""
import urllib.request, urllib.error, json, ssl, re, socket

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
socket.setdefaulttimeout(15)
HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
TIMEOUT = 15

def f(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=TIMEOUT, context=CTX)
        return r.read().decode('utf-8','replace')
    except: return ''

def f_json(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'curl/8'}), timeout=TIMEOUT, context=CTX)
        return json.loads(r.read().decode('utf-8','replace'))
    except: return None

def collect():
    all_news = []

    # 1. 知乎日报 - API
    print('  Fetching 知乎日报...')
    data = f_json('https://daily.zhihu.com/api/4/news/latest')
    if data and 'stories' in data:
        for s in data['stories'][:6]:
            t = s.get('title','').strip()
            if t and len(t) >= 6:
                u = f"https://daily.zhihu.com/story/{s['id']}" if 'id' in s else ''
                all_news.append({'t':t, 'u':u, 'src':'知乎日报'})
        print(f'    got {len(data["stories"][:6])} items')

    # 2. 豆瓣电影热门
    print('  Fetching 豆瓣电影...')
    html = f('https://movie.douban.com/')
    if html:
        titles = re.findall(r'<a[^>]*class="title"[^>]*>([^<]+)', html)
        for t in titles[:5]:
            t = t.strip()
            if t and len(t) >= 4:
                all_news.append({'t':t, 'u':'https://movie.douban.com', 'src':'豆瓣电影'})
        print(f'    got {len(titles[:5])} items')

    # 3. 豆瓣读书新书速递
    print('  Fetching 豆瓣读书...')
    html = f('https://book.douban.com/')
    if html:
        titles = re.findall(r'title="([^"]{4,50})"', html)
        seen = set()
        for t in titles:
            t = t.strip()
            if t and t[:6] not in seen and len(t) >= 4:
                seen.add(t[:6])
                all_news.append({'t':f'📚 {t}', 'u':'https://book.douban.com', 'src':'豆瓣读书'})
            if len([x for x in all_news if x['src']=='豆瓣读书']) >= 4: break
        print(f'    got {len([x for x in all_news if x["src"]=="豆瓣读书"])} items')

    # 4. GitHub Trending
    print('  Fetching GitHub Trending...')
    html = f('https://github.com/trending')
    if html:
        repos = re.findall(r'<h2[^>]*class="h3[^"]*">\s*<a[^>]*>([^<]+)</a>\s*</h2>', html)
        if not repos:
            repos = re.findall(r'<h2[^>]*>.*?href="/([^"]+)"[^>]*>', html)
        for r in repos[:5]:
            r = r.strip()
            if r and '/' in r:
                all_news.append({'t':f'⭐ {r}', 'u':f'https://github.com/{r}', 'src':'GitHub Trending'})
        print(f'    got {len([x for x in all_news if x["src"]=="GitHub Trending"])} items')

    # 5. 少数派
    print('  Fetching 少数派...')
    html = f('https://sspai.com/')
    if html:
        titles = re.findall(r'<a[^>]*class="[^"]*article-title[^"]*"[^>]*>([^<]+)', html)
        if not titles:
            titles = re.findall(r'<a[^>]*href="/post/[^"]*"[^>]*>([^<]{6,})', html)
        seen = set()
        for t in titles:
            t = t.strip()
            if t and t[:6] not in seen:
                seen.add(t[:6])
                all_news.append({'t':t, 'u':'https://sspai.com', 'src':'少数派'})
            if len([x for x in all_news if x['src']=='少数派']) >= 4: break
        print(f'    got {len([x for x in all_news if x["src"]=="少数派"])} items')

    # 6. 量子位
    print('  Fetching 量子位...')
    html = f('https://www.qbitai.com/')
    if html:
        titles = re.findall(r'<h2[^>]*>.*?<a[^>]*>([^<]+)', html, re.DOTALL)
        if not titles:
            titles = re.findall(r'entry-title[^>]*>.*?<a[^>]*>([^<]+)', html)
        if not titles:
            titles = re.findall(r'<a[^>]*href="https://www\.qbitai\.com/\d+[^"]*"[^>]*>([^<]{6,})', html)
        for t in titles[:4]:
            t = t.strip()
            if t and len(t) >= 6:
                all_news.append({'t':t, 'u':'https://www.qbitai.com', 'src':'量子位'})

    # 7. 虎嗅 (用RSS)
    print('  Fetching 虎嗅RSS...')
    html = f('https://www.huxiu.com/rss/0.xml')
    if html:
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(html)
            for item in list(root.iter('item'))[:4]:
                title = item.find('title')
                t = (title.text or '').strip() if title is not None else ''
                if t and len(t) >= 6:
                    all_news.append({'t':t, 'u':'https://www.huxiu.com', 'src':'虎嗅'})
        except: pass
    
    print(f'  total: {len(all_news)} items')
    return all_news

if __name__ == '__main__':
    news = collect()
    with open('more_news.json', 'w', encoding='utf-8') as f:
        json.dump({'more': news}, f, ensure_ascii=False)
    print(f'Done: {len(news)} items')
