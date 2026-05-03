#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RSS采集器 - 纯中文源，兼容多种格式"""
import json, subprocess, urllib.request, urllib.error, ssl, xml.etree.ElementTree as ET, re

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
        raw = r.read()
        # 自动检测编码
        try:
            return raw.decode('utf-8')
        except:
            import chardet
            enc = chardet.detect(raw)['encoding'] or 'utf-8'
            return raw.decode(enc, 'replace')
    except Exception as e:
        return ''

def f(url):
    h = curl(url)
    if len(h) < 100:
        h2 = fallback(url)
        if len(h2) > len(h): return h2
    return h

def parse_rss(text, src, max_items=6):
    items = []
    if not text or len(text) < 50: return items
    if '<html' in text[:200].lower() and 'rss' not in text[:500].lower() and 'feed' not in text[:500].lower():
        return items

    # 清理编码问题
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    text = text.replace('encoding="gb2312"', 'encoding="utf-8"')
    text = text.replace('encoding="GBK"', 'encoding="utf-8"')
    text = text.replace('encoding="gbk"', 'encoding="utf-8"')
    # 修复常见XML错误
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)

    try:
        root = ET.fromstring(text)
    except:
        # 用正则强行提取
        titles = re.findall(r'<title[^>]*>([^<]+)</title>', text)
        links = re.findall(r'<link[^>]*>([^<]+)</link>', text)
        for i, t in enumerate(titles):
            if i >= max_items: break
            if len(t) < 6: continue
            u = links[i] if i < len(links) else ''
            eng_ratio = sum(1 for c in t if c.isascii() and c.isalpha()) / max(len(t), 1)
            if eng_ratio > 0.4: continue
            items.append({'t':t[:50], 'u':u, 'src':src})
        return items

    # XML解析成功
    entries = list(root.iter('item')) or list(root.iter('entry'))
    for entry in entries:
        if len(items) >= max_items: break
        titles = entry.find('title')
        links = entry.find('link')
        t = (titles.text or '').strip() if titles is not None else ''
        u = ''
        if links is not None:
            u = (links.text or links.get('href','') or '').strip()
        t = re.sub(r'<[^>]+>', '', t)
        if not t or len(t) < 6: continue
        eng_ratio = sum(1 for c in t if c.isascii() and c.isalpha()) / max(len(t), 1)
        if eng_ratio > 0.4: continue
        items.append({'t':t[:50], 'u':u, 'src':src})
    return items

def collect():
    all_news = []
    sources = {
        '央视新闻': 'http://news.cctv.com/rss/1.xml',
        '新华网': 'http://www.xinhuanet.com/rss/news.xml',
        '人民网': 'http://www.people.com.cn/rss/important.xml',
        '环球网': 'https://www.huanqiu.com/rss.xml',
        '参考消息': 'https://www.cankaoxiaoxi.com/rss.xml',
        '观察者网': 'https://www.guancha.cn/rss.xml',
        '中国经济网': 'https://www.ce.cn/rss/main.xml',
        '澎湃新闻': 'https://www.thepaper.cn/rss/newspaper.xml',
        # 备用：用HTTP代替HTTPS
        '新华网2': 'https://www.xinhuanet.com/rss/news.xml',
        '央视新闻2': 'https://news.cctv.com/rss/1.xml',
    }
    for name, url in sources.items():
        html = f(url)
        items = parse_rss(html, name.replace('2',''), max_items=5)
        print(f'  {name}: {len(items)} items')
        all_news.extend(items)
    return all_news

if __name__ == '__main__':
    news = collect()
    news = news[:30]  # 总量限制
    with open('rss_news.json', 'w', encoding='utf-8') as f:
        json.dump({'rss': news}, f, ensure_ascii=False)
    print(f'RSS collector done: {len(news)} items')
