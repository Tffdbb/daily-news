#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RSS采集器 - 国际新闻源, 使用xml.etree.ElementTree解析RSS"""
import urllib.request, urllib.error, json, ssl, xml.etree.ElementTree as ET, re, socket

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

def parse_rss(xml_text, src, max_items=6):
    """通用RSS解析"""
    items = []
    if not xml_text.strip(): return items
    try:
        root = ET.fromstring(xml_text)
        # RSS 2.0
        for entry in root.iter('item'):
            titles = entry.find('title')
            links = entry.find('link')
            descs = entry.find('description')
            t = (titles.text or '').strip() if titles is not None else ''
            u = (links.text or '').strip() if links is not None else ''
            if not t or len(t) < 8: continue
            # clean HTML from title
            t = re.sub(r'<[^>]+>', '', t)
            if t[:6] not in [x[:6] for x in [y['t'] for y in items]]:
                items.append({'t':t, 'u':u, 'src':src})
        # Atom format (fallback)
        if not items:
            for entry in root.iter('entry'):
                titles = entry.find('title')
                links = entry.find('link')
                t = (titles.text or '').strip() if titles is not None else ''
                u = (links.get('href') or '') if links is not None else ''
                if not t or len(t) < 8: continue
                t = re.sub(r'<[^>]+>', '', t)
                if t[:6] not in [x[:6] for x in [y['t'] for y in items]]:
                    items.append({'t':t, 'u':u, 'src':src})
    except: pass
    return items[:max_items]

def collect():
    all_news = []
    sources = {
        # RSS 源
        'BBC': 'https://feeds.bbci.co.uk/news/rss.xml',
        'Reuters': 'https://www.reutersagency.com/feed/',
        'Guardian': 'https://www.theguardian.com/world/rss',
        'AP News': 'https://rsshub.app/apnews',
        'NYT': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
        'TechCrunch': 'https://techcrunch.com/feed/',
        'Hacker News': 'https://hnrss.org/frontpage',
        'The Verge': 'https://www.theverge.com/rss/index.xml',
        'CNN': 'http://rss.cnn.com/rss/cnn_topstories.rss',
    }
    for name, url in sources.items():
        html = f(url)
        items = parse_rss(html, name, 5)
        print(f'  {name}: {len(items)} items')
        all_news.extend(items)
    return all_news

if __name__ == '__main__':
    news = collect()
    with open('rss_news.json', 'w', encoding='utf-8') as f:
        json.dump({'rss': news}, f, ensure_ascii=False)
    print(f'RSS collector done: {len(news)} items')
