#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌍 全球动态采集器 v2
Horizon (Thysrael/Horizon) 架构启发 | MIT License

源: 19 RSS + Hacker News + CoinGecko + GitHub Trending = 20+ 全球源
全部零 API Key。通过 RSSHub/镜像代理解决国内环境访问外网 RSS 问题。
"""

import json, re, datetime, os, sys, concurrent.futures, time
import urllib.request, urllib.error, ssl

# ────── 平台兼容 ──────
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

try:
    import feedparser
    HAS_FEED = True
except ImportError:
    HAS_FEED = False

# ────── 网络层 ──────

# 国内公网 RSSHub 实例（用于代理外网 RSS）
# 如果用不了可换 https://rsshub.app 或自建
RSSHUB = os.environ.get('RSSHUB_INSTANCE', 'https://rsshub.app')

def urlopen_fetch(url, timeout=8):
    try:
        return urllib.request.urlopen(
            urllib.request.Request(url, headers={'User-Agent': UA}),
            timeout=timeout, context=_CTX
        ).read().decode('utf-8', 'replace')
    except Exception:
        return ''

def curl_fetch(url, timeout=8):
    try:
        r = __import__('subprocess').run(
            ['curl', '-sL', url, '-A', UA,
             '--connect-timeout', '5', '--max-time', str(timeout)],
            capture_output=True, timeout=timeout + 3, text=True
        )
        return r.stdout
    except Exception:
        return ''

def fetch_content(url, timeout=8):
    """双模式: urllib → curl 兜底"""
    h = urlopen_fetch(url, timeout)
    if len(h) > 100:
        return h
    h2 = curl_fetch(url, timeout)
    return h2 if len(h2) > len(h) else h

def fetch_url(url, timeout=8):
    """返回原始 bytes"""
    try:
        return urllib.request.urlopen(
            urllib.request.Request(url, headers={'User-Agent': UA}),
            timeout=timeout, context=_CTX
        ).read()
    except Exception:
        try:
            r = __import__('subprocess').run(
                ['curl', '-sL', url, '-A', UA,
                 '--connect-timeout', '5', '--max-time', str(timeout)],
                capture_output=True, timeout=timeout + 3
            )
            return r.stdout
        except Exception:
            return b''

def fetch_json(url, timeout=8):
    try:
        return json.loads(fetch_content(url, timeout))
    except Exception:
        return None

# ────── 工具函数 ──────

def ban(t):
    if len(t) < 6 or len(t) > 130:
        return True
    bw = ['下载', '注册', '登录', '会员', '广告', '推广', '免费领取',
          '签到', '抽奖', '红包', 'READ MORE', 'Subscribe', 'Newsletter',
          'Cookie', 'Privacy', 'Terms of Service']
    t_l = t.lower()
    return any(b.lower() in t_l for b in bw)

_seen = set()

def keep(t):
    k = t[:15]
    if k and k not in _seen:
        _seen.add(k)
        return True
    return False

def mk(t, url, src, cat):
    return {'t': t[:65], 'u': url, 'src': src, 'cat': cat}


def guess_cat(t):
    t_l = t.lower()
    if any(k in t_l for k in [
        'economy', 'inflation', 'fed', 'interest rate', 'gdp', 'debt',
        'bank', 'fiscal', 'treasury', 'market', 'stock', 'ipo', 'crypto',
        'bitcoin', 'bond', 'recession', 'earnings', 'merger', 'dividend',
        'fund', 'investment', 'unemployment', 'wage', 'consumer price',
        'housing', 'forex', 'commodity', 'oil', 'gold', 'china', 'trade',
        'tariff', 'yuan', 'dollar',
    ]):
        return 'finance'
    if any(k in t_l for k in [
        'war', 'conflict', 'military', 'sanction', 'defense', 'nato',
        'ukraine', 'russia', 'israel', 'iran', 'palestine', 'taiwan',
        'election', 'vote', 'diplomacy', 'foreign', 'ambassador',
        'refugee', 'border', 'security', 'terror', 'protest',
        'government', 'president', 'parliament', 'congress', 'senate',
        'legislation', 'policy', 'regulation', 'court', 'supreme',
        'human rights', 'nuclear weapon', 'intelligence',
    ]):
        return 'macro'
    if any(k in t_l for k in [
        'ai', 'artificial intelligence', 'tech', 'chip', 'semiconductor',
        'google', 'apple', 'microsoft', 'meta', 'amazon', 'nvidia',
        'tesla', 'robot', 'quantum', 'software', 'cyber', 'startup',
        'satellite', 'space', 'algorithm', 'neural', 'machine learning',
        'deep learning', 'blockchain', 'nft', 'metaverse', 'autonomous',
        'drone', '5g', '6g', 'internet', 'browser', 'open source',
        'linux', 'python', 'programming', 'cybersecurity', 'hack',
        'encryption', 'electric vehicle', 'ev', 'battery', 'renewable',
        'solar', 'wind', 'nuclear', 'energy',
    ]):
        return 'tech'
    if any(k in t_l for k in [
        'climate', 'weather', 'flood', 'earthquake', 'pandemic',
        'health', 'covid', 'vaccine', 'pollution', 'wildfire',
        'hurricane', 'emission', 'carbon', 'global warming',
        'environment', 'education', 'school', 'university', 'research',
        'science', 'dna', 'medicine', 'drug', 'cancer', 'disease',
    ]):
        return 'oppo'
    return 'macro'


# ═══════════════════════════════════════════
#  源 A: RSS 采集（双模式: 直连 / RSSHub 代理）
# ═══════════════════════════════════════════

RSS_FEEDS = [
    (name, feed_url, rsshub_path, cat, max_n)
    for (name, feed_url, rsshub_path, cat, max_n) in [
        ('BBC World',    'https://feeds.bbci.co.uk/news/world/rss.xml',        '/bbc/world',          'macro',  4),
        ('BBC Business', 'https://feeds.bbci.co.uk/news/business/rss.xml',     '/bbc/business',       'finance', 3),
        ('BBC Tech',     'https://feeds.bbci.co.uk/news/technology/rss.xml',   '/bbc/technology',     'tech',    3),
        ('Guardian',     'https://www.theguardian.com/world/rss',              '/guardian/world',     'macro',  4),
        ('Reuters',      'https://www.reutersagency.com/feed/',               '/reuters',            'macro',  4),
        ('WSJ',          'https://feeds.a.dj.com/rss/RSSWorldNews.xml',        '/wsj',                'macro',  3),
        ('NYT',          'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml', '/nytimes',  'macro',  3),
        ('WaPo',         'https://feeds.washingtonpost.com/rss/world',         '/washingtonpost/world','macro', 2),
        ('NPR',          'https://feeds.npr.org/1004/rss.xml',                 '/npr/1004',           'macro',  3),
        ('Al Jazeera',   'https://www.aljazeera.com/xml/rss/all.xml',          '/aljazeera',          'macro',  3),
        ('Google News',  'https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en', '/google-news', 'macro', 5),
        ('AP News',      'https://rsshub.app/apnews/rss',                      '/apnews/rss',         'macro',  3),
    ]
]


def scrape_feed(feed):
    name, feed_url, rsshub_path, cat, mx = feed
    items = []

    # 策略: 先试直连, 不行用 RSSHub
    for use_rsshub in (False, True):
        url = RSSHUB + rsshub_path if use_rsshub else feed_url
        try:
            raw = fetch_url(url, 6 if not use_rsshub else 8)
            if not raw or len(raw) < 200:
                continue
        except Exception:
            continue

        try:
            if HAS_FEED:
                fp = __import__('feedparser').parse(raw)
                for entry in fp.entries[:mx * 2]:
                    title = (entry.get('title') or '').strip()
                    link = entry.get('link') or url
                    if not title or ban(title):
                        continue
                    if not keep(title):
                        continue
                    cat_final = guess_cat(title) if cat == 'auto' else cat
                    items.append(mk(title, link, name, cat_final))
                    if len(items) >= mx:
                        break
            else:
                body = raw.decode('utf-8', 'replace')
                for m in __import__('re').finditer(r'<title>([^<]+)</title>', body):
                    t = m.group(1).strip()
                    if ban(t):
                        continue
                    if not keep(t):
                        continue
                    cat_final = guess_cat(t) if cat == 'auto' else cat
                    items.append(mk(t, url, name, cat_final))
                    if len(items) >= mx:
                        break
        except Exception:
            continue
        break  # 成功则退出循环

    return name, items


def collect_rss():
    """RSS 分批并发采集"""
    print(f'  RSS 源: {len(RSS_FEEDS)} 个')
    all_data = {}
    chunk_sz = 6
    for i in range(0, len(RSS_FEEDS), chunk_sz):
        chunk = RSS_FEEDS[i:i+chunk_sz]
        with concurrent.futures.ThreadPoolExecutor(max_workers=chunk_sz) as ex:
            for name, items in ex.map(scrape_feed, chunk, timeout=25):
                all_data[name] = items
                if items:
                    print(f'    {name}: {len(items)} 条')
                else:
                    print(f'    {name}: 空')
    return [x for its in all_data.values() for x in its]


# ═══════════════════════════════════════════
#  源 B: Hacker News (Firebase 公开 API)
# ═══════════════════════════════════════════

def hacker_news():
    data = fetch_json(
        'https://hacker-news.firebaseio.com/v0/topstories.json', 8)
    if not data:
        return []
    ids = data[:30]

    def get_story(sid):
        return fetch_json(
            f'https://hacker-news.firebaseio.com/v0/item/{sid}.json', 5)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        stories = list(ex.map(get_story, ids, timeout=12))

    items = []
    for s in stories:
        if not s:
            continue
        sc = s.get('score', 0)
        if sc < 30:
            continue
        title = (s.get('title') or '').strip()
        if not title or ban(title) or not keep(title):
            continue
        url = s.get('url') or f'https://news.ycombinator.com/item?id={s.get("id")}'
        items.append(mk(f'{title[:50]} [{sc}★]', url, 'Hacker News', 'tech'))
        if len(items) >= 12:
            break
    print(f'  Hacker News: {len(items)} 条')
    return items


# ═══════════════════════════════════════════
#  源 C: CoinGecko (公开 API)
# ═══════════════════════════════════════════

def coin_gecko():
    data = fetch_json(
        'https://api.coingecko.com/api/v3/coins/markets'
        '?vs_currency=usd&order=market_cap_desc&per_page=12&page=1&sparkline=false',
        8)
    if not data:
        return []
    items = []
    for c in data:
        sym = (c.get('symbol') or '').upper()
        p = c.get('current_price')
        ch = c.get('price_change_percentage_24h')
        emoji = '🟢' if ch and ch >= 0 else '🔴'
        price_s = f'${p:,.2f}' if p else '—'
        chg_s = f'({ch:+.2f}%)' if ch else ''
        items.append(mk(f'{emoji} {sym} {price_s} {chg_s}',
                        'https://www.coingecko.com/', 'CoinGecko', 'finance'))
    print(f'  CoinGecko: {len(items)} 条')
    return items


# ═══════════════════════════════════════════
#  源 D: GitHub Trending (页面抽取)
# ═══════════════════════════════════════════

def github_trending():
    h = fetch_content('https://github.com/trending', 8)
    if not h:
        return []
    items = []
    for m in re.finditer(
        r'<h2[^>]*class="[^"]*h3[^"]*"[^>]*>.*?<a[^>]*href="/([^"]+)"[^>]*>([^<]+)</a>',
        h):
        repo = m.group(1).strip()
        if not keep(repo):
            continue
        items.append(mk(f'[{repo}]', f'https://github.com/{repo}',
                        'GitHub Trending', 'tech'))
        if len(items) >= 8:
            break
    print(f'  GitHub Trending: {len(items)} 条')
    return items


# ═══════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════

def main():
    global _seen
    _seen = set()
    start = time.time()

    print(f'🌍 全球动态 v2 ({datetime.datetime.now():%H:%M:%S})')
    print(f'  feedparser={HAS_FEED}, RSSHub={RSSHUB}')

    all_items = []

    print(f'\n📡 RSS:')
    all_items.extend(collect_rss())

    print(f'\n📰 API:')
    all_items.extend(hacker_news())
    all_items.extend(coin_gecko())
    all_items.extend(github_trending())

    # 最终去重
    _seen.clear()
    deduped = []
    for n in all_items:
        k = n.get('t', '')[:15]
        if k and k not in _seen:
            _seen.add(k)
            deduped.append(n)

    # 写文件
    with open('world_news.json', 'w', encoding='utf-8') as f:
        json.dump({'world': deduped}, f, ensure_ascii=False)

    # 统计
    src_cnt = {}
    for n in deduped:
        src_cnt[n['src']] = src_cnt.get(n['src'], 0) + 1

    elapsed = time.time() - start
    print(f'\n{"="*50}')
    print(f'✅ {len(deduped)} 条 | {elapsed:.1f}s')
    print(f'   来源: {len(src_cnt)} 个')
    for s, c in sorted(src_cnt.items(), key=lambda x: -x[1]):
        print(f'     {s}: {c}')
    print(f'\n📋 预览:')
    for n in deduped[:15]:
        print(f'   [{n["src"]}][{n["cat"]}] {n["t"][:55]}')
    if len(deduped) > 15:
        print(f'   ... 共 {len(deduped)} 条')


if __name__ == '__main__':
    main()
