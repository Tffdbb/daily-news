#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""垂直领域采集器 - 只留高质量源"""
import json, subprocess, urllib.request, urllib.error, ssl, re

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','8','--max-time','9','-o','-','-w',''], capture_output=True, timeout=12, text=True)
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

def f_json(url):
    h = f(url)
    if len(h) > 10:
        try: return json.loads(h)
        except: pass
    return None

def collect():
    all_news = []

    # 1. 少数派 (效率工具/深度文章)
    print('  Fetching 少数派...')
    h = f('https://sspai.com/')
    for m in re.finditer(r'<a[^>]*href="(https?://sspai\.com[^"]+)"[^>]*>([^<]{8,50})</a>', h):
        if len(all_news) >= 8: break
        t = m.group(2).strip()
        if len(t) >= 6 and '会员' not in t and '广告' not in t:
            all_news.append({'t':t[:50], 'u':m.group(1), 'src':'少数派'})

    # 2. QbitAI (AI/科技)
    print('  Fetching QbitAI...')
    h = f('https://www.qbitai.com/')
    for m in re.finditer(r'<a[^>]*href="(https?://www\.qbitai\.com/\d+[^"]*)"[^>]*>([^<]{8,50})</a>', h):
        if len(all_news) >= 12: break
        t = m.group(2).strip()
        if len(t) >= 6:
            all_news.append({'t':t[:50], 'u':m.group(1), 'src':'QbitAI'})

    # 3. GitHub Trending (科技趋势)
    print('  Fetching GitHub Trending...')
    h = f('https://github.com/trending')
    for m in re.finditer(r'<h2[^>]*class="[^"]*h3[^"]*"[^>]*>\s*<a[^>]*href="/([^/]+/[^/"]+)"[^>]*>([^<]+)</a>', h):
        if len(all_news) >= 6: break
        repo = m.group(1).strip()
        all_news.append({'t':repo + ' ⭐', 'u':'https://github.com/'+repo, 'src':'GitHub'})

    return all_news

if __name__ == '__main__':
    news = collect()
    with open('more_news.json', 'w', encoding='utf-8') as f:
        json.dump({'more': news}, f, ensure_ascii=False)
    print(f'Vertical collector done: {len(news)} items')
