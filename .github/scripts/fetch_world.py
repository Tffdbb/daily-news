#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全球动态 - 多个国际源聚合，扩展daily-news全球化视野"""
import json, re, datetime, os, subprocess, concurrent.futures, urllib.request, urllib.error, ssl, xml.etree.ElementTree as ET

_CTX = ssl.create_default_context()
_CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE

def curl_fetch(url, timeout_sec=8):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','6','--max-time',str(timeout_sec),'-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

def urlopen_fetch(url, timeout=8):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=timeout, context=_CTX)
        return r.read().decode('utf-8','replace')
    except: return ''

def f(url, timeout=10):
    h = curl_fetch(url, timeout)
    if len(h) < 100:
        h2 = urlopen_fetch(url, timeout+1)
        if len(h2) > len(h): return h2
    return h

# ────── 工具函数 ──────

def ban(t):
    """过滤广告/低质标题"""
    ban_words = ['下载','注册','登录','会员','广告','推广','免费领取','签到','抽奖','红包','更多>>','READ MORE','Subscribe']
    if len(t) < 6 or len(t) > 120: return True
    for b in ban_words:
        if b.lower() in t.lower(): return True
    return False

def keep(seen, t):
    k = t[:12]
    if k and k not in seen:
        seen.add(k)
        return True
    return False

def guess_cat(t):
    """英文标题的粗略分类"""
    t_lower = t.lower()
    if any(k in t_lower for k in ['china','trade','tariff','economy','inflation','fed','interest rate','gdp','debt','bank','fiscal','treasury','yuan','dollar','market','stock','ipo','crypto','bitcoin','bond']):
        return 'finance'
    if any(k in t_lower for k in ['war','conflict','military','sanction','defense','nato','ukraine','russia','israel','iran','palestine','taiwan','election','vote','diplomacy','treaty','united nations','foreign']):
        return 'macro'
    if any(k in t_lower for k in ['ai','artificial intelligence','tech','chip','semiconductor','google','apple','microsoft','meta','amazon','nvidia','tesla','robot','quantum','software','data','cyber','startup','satellite','space']):
        return 'tech'
    if any(k in t_lower for k in ['climate','weather','flood','earthquake','pandemic','health','covid','vaccine','energy','renewable','solar','wind','nuclear','pollution']):
        return 'oppo'
    return 'macro'  # 默认归入宏观

# ────── 采集源 ──────

def wsj_news():
    """WSJ 头条 (RSS)"""
    h = urlopen_fetch('https://feeds.a.dj.com/rss/RSSWorldNews.xml', 8)
    items = []
    seen = set()
    for m in re.finditer(r'<title>([^<]+)</title>', h):
        t = m.group(1).strip()
        if ban(t) or not keep(seen, t): continue
        items.append({'t':t[:60],'u':'https://www.wsj.com/','src':'WSJ','cat':'macro'})
        if len(items) >= 5: break
    return items

def reuters_news():
    """Reuters 全球新闻 (RSS)"""
    h = urlopen_fetch('https://www.reutersagency.com/feed/', 8)
    items = []
    seen = set()
    for m in re.finditer(r'<title>([^<]+)</title>', h):
        t = m.group(1).strip()
        if 'Reuters' in t or ban(t) or not keep(seen, t): continue
        items.append({'t':t[:60],'u':'https://www.reuters.com/','src':'Reuters','cat':guess_cat(t)})
        if len(items) >= 5: break
    return items

def bbc_news():
    """BBC 全球新闻"""
    urls = [
        'https://feeds.bbci.co.uk/news/world/rss.xml',
        'https://feeds.bbci.co.uk/news/technology/rss.xml',
        'https://feeds.bbci.co.uk/news/business/rss.xml',
    ]
    items = []
    seen = set()
    cat_map = {'world':'macro', 'technology':'tech', 'business':'finance'}
    for url in urls:
        h = urlopen_fetch(url, 8)
        cat = 'macro'
        for k,v in cat_map.items():
            if k in url: cat = v
        for m in re.finditer(r'<title>([^<]+)</title>', h):
            t = m.group(1).strip()
            if 'BBC' in t or ban(t) or not keep(seen, t): continue
            items.append({'t':t[:60],'u':'https://www.bbc.com/news','src':'BBC','cat':cat})
            if len(items) >= 12: break
        if len(items) >= 12: break
    return items[:12]

def guardian_news():
    """The Guardian 国际版"""
    h = urlopen_fetch('https://www.theguardian.com/world/rss', 8)
    items = []
    seen = set()
    for m in re.finditer(r'<title>([^<]+)</title>', h):
        t = m.group(1).strip()
        if 'Guardian' in t or ban(t) or not keep(seen, t): continue
        items.append({'t':t[:60],'u':'https://www.theguardian.com/international','src':'Guardian','cat':guess_cat(t)})
        if len(items) >= 5: break
    return items

def bloomberg_news():
    """Bloomberg 全球 (RSS替代)"""
    h = urlopen_fetch('https://www.bloomberg.com/feed/podcast/etf-report.xml', 8)
    items = []
    seen = set()
    for m in re.finditer(r'<title>([^<]+)</title>', h):
        t = m.group(1).strip()
        if 'Bloomberg' in t or ban(t) or not keep(seen, t): continue
        items.append({'t':t[:60],'u':'https://www.bloomberg.com/','src':'Bloomberg','cat':'finance'})
        if len(items) >= 3: break
    return items

def google_news_world():
    """Google News 世界版"""
    h = urlopen_fetch('https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en', 8)
    items = []
    seen = set()
    for m in re.finditer(r'<title>([^<]+)</title>', h):
        t = m.group(1).strip()
        if ban(t) or not keep(seen, t): continue
        items.append({'t':t[:60],'u':'https://news.google.com/','src':'Google News','cat':guess_cat(t)})
        if len(items) >= 8: break
    return items

def ap_news():
    """美联社 AP News"""
    h = urlopen_fetch('https://rsshub.app/apnews/rss', 6)
    if len(h) < 100:
        h = urlopen_fetch('https://apnews.com/', 8)
        items = []
        seen = set()
        for m in re.finditer(r'"headline":"([^"]{10,80})"', h):
            t = m.group(1).strip()
            if ban(t) or not keep(seen, t): continue
            items.append({'t':t[:60],'u':'https://apnews.com/','src':'AP News','cat':guess_cat(t)})
            if len(items) >= 4: break
        return items
    items = []
    seen = set()
    for m in re.finditer(r'<title>([^<]+)</title>', h):
        t = m.group(1).strip()
        if 'AP' in t or ban(t) or not keep(seen, t): continue
        items.append({'t':t[:60],'u':'https://apnews.com/','src':'AP News','cat':guess_cat(t)})
        if len(items) >= 4: break
    return items

def frd_data():
    """FRED 美联储 - 主要经济指标"""
    # 使用 fred.stlouisfed.org 公开概况页面
    h = urlopen_fetch('https://fred.stlouisfed.org/', 8)
    items = []
    seen = set()
    # 找最新指标
    for m in re.finditer(r'<h3[^>]*>([^<]+)</h3>', h):
        t = m.group(1).strip()
        if ban(t) or not keep(seen, t): continue
        items.append({'t':t[:60],'u':'https://fred.stlouisfed.org/','src':'FRED','cat':'finance'})
        if len(items) >= 3: break
    # 找趋势话题
    if len(items) < 3:
        for m in re.finditer(r'<a[^>]*fred[^>]*>([^<]{10,60})</a>', h):
            t = m.group(1).strip()
            if ban(t) or not keep(seen, t): continue
            items.append({'t':t[:60],'u':'https://fred.stlouisfed.org/','src':'FRED','cat':'finance'})
            if len(items) >= 3: break
    return items

def polymarket_news():
    """Polymarket 预测市场 - 热门事件"""
    h = f('https://gamma-api.polymarket.com/events?limit=10&closed=false&tag=all')
    items = []
    try:
        events = json.loads(h)[:12]
        for ev in events:
            t = ev.get('title','').strip()
            if not t or len(t) < 8: continue
            volumes = [m.get('volume', '0') for m in ev.get('markets', []) if m.get('volume')]
            vol_str = ''
            if volumes:
                try:
                    vol = sum(float(v) for v in volumes)
                    if vol > 1000000:
                        vol_str = f' (${vol/1000000:.1f}M vol)'
                    elif vol > 1000:
                        vol_str = f' (${vol/1000:.0f}K vol)'
                except: pass
            items.append({'t':f'{t[:55]}{vol_str}','u':'https://polymarket.com/','src':'Polymarket','cat':'macro'})
            if len(items) >= 6: break
    except: pass
    return items

def coin_gecko():
    """CoinGecko 加密货币 Top 10"""
    h = f('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false')
    items = []
    try:
        coins = json.loads(h)
        for c in coins:
            sym = c.get('symbol','').upper()
            price = c.get('current_price', 0)
            chg = c.get('price_change_percentage_24h', 0)
            emoji = '🟢' if chg >= 0 else '🔴'
            items.append({
                't':f'{emoji} {sym} ${price:,.2f} ({chg:+.2f}%)',
                'u':'https://www.coingecko.com/',
                'src':'CoinGecko',
                'cat':'finance'
            })
    except:
        pass
    return items

# ────── 主入口 ──────

def _safe(fn):
    try: return fn() or []
    except: return []

def main():
    sources = [
        ('BBC', bbc_news),
        ('WSJ', wsj_news),
        ('Reuters', reuters_news),
        ('Guardian', guardian_news),
        ('Bloomberg', bloomberg_news),
        ('Google News', google_news_world),
        ('AP News', ap_news),
        ('FRED', frd_data),
        ('Polymarket', polymarket_news),
        ('CoinGecko', coin_gecko),
    ]

    all_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_safe, fn): name for name, fn in sources}
        for f in concurrent.futures.as_completed(futs):
            name = futs[f]
            try:
                items = f.result(timeout=20)
                if items:
                    all_items.extend(items)
                    print(f'  {name}: {len(items)} items')
                else:
                    print(f'  {name}: empty')
            except Exception as e:
                print(f'  {name}: error {e}')

    # 去重 + 排序
    seen = set()
    deduped = []
    for n in all_items:
        k = n.get('t','')[:15]
        if k and k not in seen:
            seen.add(k)
            deduped.append(n)

    out = {'world': deduped}
    with open('world_news.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)

    print(f'\n🌍 全球动态采集完成: {len(deduped)} 条 (来自 {len(sources)} 个源)')
    for n in deduped:
        print(f'  [{n["src"]}] {n["t"][:60]}')

if __name__ == '__main__':
    main()
