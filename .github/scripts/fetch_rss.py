#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RSS采集器 - 纯中文源（替换英文RSS）"""
import json, subprocess, urllib.request, urllib.error, ssl, xml.etree.ElementTree as ET, re

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

def parse_rss(xml_text, src, max_items=8):
    items = []
    if not xml_text.strip(): return items
    try:
        root = ET.fromstring(xml_text)
        for entry in root.iter('item'):
            titles = entry.find('title')
            links = entry.find('link')
            desc = entry.find('description')
            t = (titles.text or '').strip() if titles is not None else ''
            u = (links.text or '').strip() if links is not None else ''
            if not links.text:
                u = links.get('href','') if links is not None else ''
            # 清理 HTML 标签
            t = re.sub(r'<[^>]+>', '', t)
            if not t or len(t) < 6: continue
            # 过滤英文（英文标题不要）
            eng_ratio = sum(1 for c in t if c.isascii() and c.isalpha()) / max(len(t), 1)
            if eng_ratio > 0.4: continue
            items.append({'t':t[:50], 'u':u, 'src':src})
        if not items:
            for entry in root.iter('entry'):
                titles = entry.find('title')
                links = entry.find('link')
                t = (titles.text or '').strip() if titles is not None else ''
                u = (links.get('href') or '') if links is not None else ''
                t = re.sub(r'<[^>]+>', '', t)
                if not t or len(t) < 6: continue
                eng_ratio = sum(1 for c in t if c.isascii() and c.isalpha()) / max(len(t), 1)
                if eng_ratio > 0.4: continue
                items.append({'t':t[:50], 'u':u, 'src':src})
    except: pass
    # 去重
    seen=set();deduped=[]
    for item in items:
        k=item['t'][:8]
        if k not in seen: seen.add(k);deduped.append(item)
    return deduped[:max_items]

def collect():
    all_news = []
    # 纯中文RSS源
    sources = {
        '澎湃新闻': 'https://www.thepaper.cn/rss/newspaper.xml',
        '观察者网': 'https://www.guancha.cn/rss.xml',
        '环球网': 'https://www.huanqiu.com/rss.xml',
        '央视新闻': 'https://news.cctv.com/rss/1.xml',
        '新华网': 'https://www.xinhuanet.com/rss/news.xml',
        '人民网': 'https://www.people.com.cn/rss/important.xml',
        '中国经济网': 'https://www.ce.cn/rss/main.xml',
        '参考消息': 'https://www.cankaoxiaoxi.com/rss.xml',
    }
    for name, url in sources.items():
        html = f(url)
        items = parse_rss(html, name, 6)
        print(f'  {name}: {len(items)} items')
        all_news.extend(items)
    return all_news

if __name__ == '__main__':
    news = collect()
    with open('rss_news.json', 'w', encoding='utf-8') as f:
        json.dump({'rss': news}, f, ensure_ascii=False)
    print(f'RSS collector done: {len(news)} items')
