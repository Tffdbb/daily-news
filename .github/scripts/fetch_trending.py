#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub Trending 每日热榜 + 知乎热榜"""
import json, subprocess, re, urllib.request, ssl

_CTX = ssl.create_default_context()
_CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36','--connect-timeout','8','--max-time','10','-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

def fallback(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=10, context=_CTX)
        return r.read().decode('utf-8','replace')
    except: return ''

def get(url):
    h = curl(url)
    return h if len(h) >= 100 else (fallback(url) or h)

def fetch_github_trending():
    """GitHub 今日热门项目"""
    items = []
    # 先试试官方API
    gh_url = 'https://api.github.com/search/repositories?q=created:>=%s&sort=stars&order=desc&per_page=15' % __import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%d')
    h = get(gh_url)
    j = None
    try: j = json.loads(h)
    except: pass
    
    if j and 'items' in j:
        for r in j['items'][:15]:
            name = r.get('full_name','')
            desc = (r.get('description','') or '')[:60]
            stars = r.get('stargazers_count',0)
            lang = r.get('language','') or ''
            url = r.get('html_url','')
            items.append({'t': name, 'desc': desc, 'stars': stars, 'lang': lang, 'u': url, 'src': 'GitHub', 'cat': 'trending'})
        return items
    
    # API失败则爬网页
    h = get('https://github.com/trending')
    # 尝试提取仓库信息
    blocks = re.findall(r'<h2[^>]*>\s*<a[^>]*href="/([^"]+)"[^>]*>([^<]+)</a>', h)
    descs = re.findall(r'<p[^>]*class="col-9[^"]*"[^>]*>\s*(.+?)\s*</p>', h, re.DOTALL)
    langs = re.findall(r'<span[^>]*itemprop="programmingLanguage"[^>]*>([^<]+)', h)
    stars = [int(s.replace(',','')) for s in re.findall(r'class="d-inline-block float-sm-right">\s*<svg[^>]*>.*?</svg>\s*([\d,]+)', h, re.DOTALL)]
    
    for i, (href, name) in enumerate(blocks):
        if i >= 15: break
        name = name.strip()
        full = href.strip()
        desc = ''
        if i < len(descs): desc = re.sub(r'<[^>]+>', '', descs[i]).strip()[:50]
        lang = langs[i] if i < len(langs) else ''
        star = stars[i] if i < len(stars) else 0
        items.append({'t': name or full, 'desc': desc, 'stars': star, 'lang': lang, 'u': 'https://github.com/'+full, 'src': 'GitHub', 'cat': 'trending'})
    
    return items

def fetch_zhihu_hot():
    """知乎热榜"""
    items = []
    h = get('https://www.zhihu.com/hot')
    # 提取热榜条目
    for m in re.finditer(r'<a[^>]*href="(//www\.zhihu\.com/question/\d+)"[^>]*>([^<]{8,60})</a>', h):
        href = m.group(1).strip()
        t = m.group(2).strip()
        u = 'https:' + href if href.startswith('//') else 'https://www.zhihu.com' + href
        items.append({'t': t[:45], 'u': u, 'src': '知乎', 'cat': 'topic'})
        if len(items) >= 8:
            break
    
    # fallback: 取知乎热榜JSON API
    if not items:
        h = get('https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10')
        try:
            j = json.loads(h)
            for item in j.get('data',[]):
                target = item.get('target', {})
                t = target.get('title', '') or target.get('question', {}).get('title', '')
                u = target.get('url','')
                if not u: u = item.get('url','')
                items.append({'t': t[:45], 'u': u, 'src': '知乎', 'cat': 'topic'})
        except: pass
    
    return items

def main():
    data = {}
    
    print('  GitHub Trending...')
    data['trending'] = fetch_github_trending()
    print(f'    -> {len(data["trending"])} repos')
    
    print('  知乎热榜...')
    data['zhihu'] = fetch_zhihu_hot()
    print(f'    -> {len(data["zhihu"])} items')
    
    with open('trending.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f'Trending done')

if __name__ == '__main__':
    main()
