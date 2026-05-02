#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日全球资讯 - Python 数据采集器"""

import json, re, urllib.request, urllib.error, ssl, socket, sys, datetime

TIMEOUT = 10
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx)
        return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return ''


def extract(html, pattern, min_len=6, max_count=5):
    seen = set(); items = []
    for m in re.finditer(pattern, html):
        if len(items) >= max_count: break
        t = m.group(1).strip()
        if len(t) >= min_len and len(t) < 55 and t[:8] not in seen and '更多' not in t and '广告' not in t:
            seen.add(t[:8]); items.append(t)
    return items


def extract_links(html, pattern, min_len=8, max_count=5):
    seen = set(); items = []
    for m in re.finditer(pattern, html):
        if len(items) >= max_count: break
        t = m.group(2).strip(); u = m.group(1).strip()
        if len(t) >= min_len and t[:8] not in seen:
            seen.add(t[:8]); items.append({'t': t[:50], 'u': u})
    return items


def s1():
    html = fetch('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    if not html: return []
    try:
        j = json.loads(html)
        return [{'t': i['title'].strip()[:55], 's': '同花顺快讯', 'src': '同花顺', 'u': 'https://www.10jqka.com.cn/'}
                for i in j.get('data', {}).get('list', []) if i.get('title') and len(i['title']) > 4][:15]
    except: return []


def s2():
    html = fetch('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=10')
    if not html: return []
    try:
        j = json.loads(html)
        return [{'t': (i.get('title') or i.get('content_text', '')).replace('<em>', '').replace('</em>', '').strip()[:55],
                 's': '见闻快讯', 'src': '华尔街见闻', 'u': 'https://wallstreetcn.com' + i.get('uri', '') if i.get('uri') else 'https://wallstreetcn.com/'}
                for i in j.get('data', {}).get('items', []) if i.get('title') or i.get('content_text')][:10]
    except: return []


def s3():
    html = fetch('https://www.cls.cn/')
    items = extract(html, r'"title"\s*:\s*"([^"]+)"', 6, 6)
    if len(items) < 3: items = extract(html, r'"content":"([^"]{8,60})"', 6, 6)
    return [{'t': t, 's': '电报快讯', 'src': '财联社', 'u': 'https://www.cls.cn/'} for t in items]


def s4():
    html = fetch('https://www.yicai.com/')
    links = extract_links(html, r'<a[^>]*href="(https://www\.yicai\.com/news/[^"]+)"[^>]*>([^<]{8,55})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '一财', 'src': '第一财经', 'u': i['u']} for i in links]


def s5():
    html = fetch('https://news.163.com/')
    links = extract_links(html, r'<a[^>]*href="(https://news\.163\.com/[^"]+)"[^>]*>([^<]{8,45})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '网易精选', 'src': '网易新闻', 'u': i['u']} for i in links]


def s6():
    html = fetch('https://finance.sina.com.cn/')
    links = extract_links(html, r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '财经资讯', 'src': '新浪财经', 'u': i['u']} for i in links if '更多' not in i['t'] and '客户端' not in i['t']]


def s7():
    html = fetch('https://www.xinhuanet.com/')
    links = extract_links(html, r'<a[^>]*href="([^"]+\.htm)"[^>]*>([^<]{8,45})</a>', 8, 3)
    return [{'t': i['t'][:50], 's': '官方发布', 'src': '新华网',
             'u': i['u'] if i['u'].startswith('http') else 'https://www.xinhuanet.com' + i['u']}
            for i in links if 'English' not in i['t'] and '更多' not in i['t']]


def s8():
    html = fetch('https://www.people.com.cn/')
    links = extract_links(html, r'<a[^>]*href="(https?://[^"]*people\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>', 8, 3)
    return [{'t': i['t'][:50], 's': '人民网', 'src': '人民网', 'u': i['u']}
            for i in links if '许可证' not in i['t'] and '广告' not in i['t'] and '更多' not in i['t']]


def s9():
    html = fetch('https://www.chinanews.com.cn/')
    links = extract_links(html, r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '即时新闻', 'src': '中国新闻网', 'u': i['u']} for i in links]


def s10():
    html = fetch('https://news.cctv.com/')
    links = extract_links(html, r'<a[^>]*href="(https?://news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 3)
    return [{'t': i['t'][:50], 's': '央视报道', 'src': '央视新闻', 'u': i['u']} for i in links]


def s11():
    html = fetch('https://www.ifeng.com/')
    links = extract_links(html, r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '凤凰网评', 'src': '凤凰网', 'u': i['u']}
            for i in links if '查看' not in i['t'] and '更多' not in i['t'] and 'PHOENIX' not in i['t']]


def s12():
    html = fetch('https://www.caixin.com/')
    links = extract_links(html, r'<a[^>]*href="(https?://www\.caixin\.com[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 3)
    return [{'t': i['t'][:50], 's': '财新独家', 'src': '财新网', 'u': i['u']} for i in links]


def s13():
    html = fetch('https://www.nbd.com.cn/')
    links = extract_links(html, r'<a[^>]*href="(https?://www\.nbd\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '每经资讯', 'src': '每日经济新闻', 'u': i['u']} for i in links]


def s14():
    html = fetch('https://www.stcn.com/')
    links = extract_links(html, r'<a[^>]*href="(https?://www\.stcn\.com[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '券商中国', 'src': '证券时报', 'u': i['u']} for i in links]


def s15():
    html = fetch('https://www.cs.com.cn/')
    links = extract_links(html, r'<a[^>]*href="(https?://www\.cs\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 3)
    return [{'t': i['t'][:50], 's': '中证报', 'src': '中国证券报', 'u': i['u']} for i in links]


def s16():
    html = fetch('https://www.ithome.com/rss/')
    items = []; seen = set()
    for m in re.finditer(r'<title><!\[CDATA\[([^\]]+)\]\]></title>', html):
        if len(items) >= 4: break
        t = m.group(1).strip()
        if len(t) > 4 and t != 'IT之家' and t[:8] not in seen: seen.add(t[:8]); items.append(t)
    if len(items) < 2:
        first = True
        for m in re.finditer(r'<title>([^<]+)</title>', html):
            if len(items) >= 4: break
            if first: first = False; continue
            t = m.group(1).strip()
            if len(t) > 4 and t[:8] not in seen: seen.add(t[:8]); items.append(t)
    return [{'t': t[:50], 's': '科技资讯', 'src': 'IT之家', 'u': 'https://www.ithome.com/'} for t in items]


def s17():
    html = fetch('https://top.baidu.com/board?tab=realtime')
    items = []; seen = set()
    for pat in [r'data-title="([^"]+)"', r'"word":"([^"]+)"']:
        for m in re.finditer(pat, html):
            if len(items) >= 6: break
            t = m.group(1).strip()
            if len(t) > 3 and t[:6] not in seen: seen.add(t[:6]); items.append(t)
        if len(items) >= 4: break
    return [{'t': t[:40], 's': '热搜话题', 'src': '百度热搜', 'u': 'https://www.baidu.com/s?wd=' + urllib.request.quote(t)} for t in items]


def s18():
    html = fetch('https://www.thepaper.cn/')
    links = extract_links(html, r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '深度报道', 'src': '澎湃新闻', 'u': i['u']} for i in links]


def s19():
    html = fetch('https://36kr.com/')
    items = extract(html, r'"title":"([^"]{6,50})"', 6, 4)
    if len(items) < 2: items = extract(html, r'"widgetTitle":"([^"]{6,50})"', 6, 4)
    return [{'t': t[:45], 's': '科技商业', 'src': '36氪', 'u': 'https://36kr.com/'} for t in items]


def s20():
    html = fetch('https://www.donews.com/')
    links = extract_links(html, r'<a[^>]*href="(https?://www\.donews\.com[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 3)
    return [{'t': i['t'][:50], 's': '互联网资讯', 'src': 'Donews', 'u': i['u']} for i in links]


def s21():
    html = fetch('https://sports.sina.com.cn/')
    links = extract_links(html, r'<a[^>]*href="(https?://sports\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '体育资讯', 'src': '新浪体育', 'u': i['u']} for i in links if '更多' not in i['t'] and '频道' not in i['t']]


def s22():
    html = fetch('https://www.huxiu.com/')
    seen = set(); items = []
    for m in re.finditer(r'<h2[^>]*>([^<]+)</h2>', html):
        if len(items) >= 3: break
        t = m.group(1).strip()
        if len(t) > 6 and t[:8] not in seen: seen.add(t[:8]); items.append(t)
    return [{'t': t[:45], 's': '深度商业', 'src': '虎嗅', 'u': 'https://www.huxiu.com/'} for t in items]


def s23():
    html = fetch('https://health.people.com.cn/')
    links = extract_links(html, r'<a[^>]*href="(https?://health\.people\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 3)
    return [{'t': i['t'][:50], 's': '健康资讯', 'src': '人民健康', 'u': i['u']} for i in links if '人民' not in i['t'] and '健康' not in i['t']]


def s24():
    """今日头条"""
    html = fetch('https://www.toutiao.com/')
    items = []; seen = set()
    for pat in [r'"title":"([^"]{6,50})"', r'"abstract":"([^"]{6,50})"', r'"word":"([^"]{6,50})"']:
        for m in re.finditer(pat, html):
            if len(items) >= 5: break
            t = m.group(1).strip()
            if len(t) > 5 and t[:6] not in seen and '{{' not in t and 'var' not in t:
                seen.add(t[:6]); items.append(t)
        if len(items) >= 3: break
    return [{'t': t[:40], 's': '热点话题', 'src': '今日头条', 'u': 'https://www.toutiao.com/'} for t in items]


def s25():
    """东方财富"""
    html = fetch('https://www.eastmoney.com/')
    links = extract_links(html, r'<a[^>]*href="(https?://[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{6,50})</a>', 6, 5)
    return [{'t': i['t'][:50], 's': '财经资讯', 'src': '东方财富', 'u': i['u']} for i in links
            if any(k in i['t'] for k in ['股','涨','跌','亿','元','A股','市场','投资','基金','行情','板块'])]


def s26():
    """雪球"""
    html = fetch('https://xueqiu.com/')
    links = extract_links(html, r'<a[^>]*href="(https?://xueqiu\.com/\d+/\d+[^"]*)"[^>]*>([^<]{6,50})</a>', 6, 4)
    return [{'t': i['t'][:50], 's': '投资者社区', 'src': '雪球', 'u': i['u']} for i in links]


def s27():
    """环球网"""
    html = fetch('https://www.huanqiu.com/')
    links = extract_links(html, r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '国际视野', 'src': '环球网', 'u': i['u']} for i in links]


def s28():
    """观察者网"""
    html = fetch('https://www.guancha.cn/')
    links = extract_links(html, r'<a[^>]*href="(https?://www\.guancha\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '深度观察', 'src': '观察者网', 'u': i['u']} for i in links]


def s29():
    """新浪娱乐"""
    html = fetch('https://ent.sina.com.cn/')
    links = extract_links(html, r'<a[^>]*href="(https?://ent\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '文娱资讯', 'src': '新浪娱乐', 'u': i['u']} for i in links if '更多' not in i['t'] and '频道' not in i['t']]


def s30():
    """网易体育"""
    html = fetch('https://sports.163.com/')
    links = extract_links(html, r'<a[^>]*href="(https?://sports\.163\.com[^"]+)"[^>]*>([^<]{8,50})</a>', 8, 4)
    return [{'t': i['t'][:50], 's': '体育赛事', 'src': '网易体育', 'u': i['u']} for i in links if '更多' not in i['t'] and '直播' not in i['t']]


def get_stocks():
    html = fetch('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001,0.399006,1.000688,1.000300,1.000016,1.000905,0.399001')
    if not html: return []
    try:
        j = json.loads(html)
        return [{'n': s.get('f14', '--'), 'v': f"{s.get('f2', 0):.2f}",
                 'c': f"{'+' if s.get('f3', 0) >= 0 else ''}{s.get('f3', 0):.2f}%",
                 'cls': 'up' if s.get('f3', 0) >= 0 else 'down'}
                for s in j.get('data', {}).get('diff', [])[:8]]
    except: return []


def get_forex():
    html = fetch('https://api.exchangerate-api.com/v4/latest/CNY')
    if not html: return {}
    try:
        j = json.loads(html)
        r = j.get('rates', {})
        fx = {}
        for sym in ['USD', 'EUR', 'JPY', 'GBP', 'HKD', 'KRW']:
            if sym in r and r[sym] > 0: fx[sym] = f"{1 / r[sym]:.4f}"
        return fx
    except: return {}


if __name__ == '__main__':
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    print(f'=== Python采集器 ({now.month}月{now.day}日) ===')

    sources = [
        ('同花顺', s1), ('华尔街见闻', s2), ('财联社', s3), ('第一财经', s4),
        ('网易', s5), ('新浪财经', s6), ('新华网', s7), ('人民网', s8),
        ('中国新闻网', s9), ('央视新闻', s10), ('凤凰网', s11), ('财新网', s12),
        ('每经', s13), ('证券时报', s14), ('中证报', s15), ('IT之家', s16),
        ('百度', s17), ('澎湃新闻', s18), ('36氪', s19), ('Donews', s20),
        ('新浪体育', s21), ('虎嗅', s22), ('人民健康', s23),
        ('今日头条', s24), ('东方财富', s25), ('雪球', s26),
        ('环球网', s27), ('观察者网', s28), ('新浪娱乐', s29), ('网易体育', s30),
        ('B站热门', s31), ('微博热搜', s32), ('京东', s33),
        ('抖音', s34), ('网易云音乐', s35), ('什么值得买', s36),
    ]

    all_news = []
    cnt = {}

    for name, func in sources:
        try:
            items = func()
        except Exception:
            items = []
        all_news.append(items)
        if items:
            cnt[name] = len(items)

    print(f'来源({len(cnt)}): {sum(cnt.values())} 条')
    for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
        print(f'  {k}:{v}')

    stocks = get_stocks()
    forex = get_forex()
    print(f'  股票: {"live" if stocks else "fallback"} | 汇率: {"live" if forex else "fallback"}')

    labels = ['同花顺','华尔街见闻','财联社','第一财经','网易','新浪财经','新华网','人民网','中国新闻网','央视新闻','凤凰网','财新网','每经','证券时报','中证报','IT之家','百度','澎湃新闻','36氪','Donews','新浪体育','虎嗅','人民健康','今日头条','东方财富','雪球','环球网','观察者网','新浪娱乐','网易体育','B站热门','微博热搜','京东','抖音','网易云音乐','什么值得买']

    output = {
        'date': now.strftime('%Y年%m月%d日 %A'),
        'sources': {k: v for k, v in sorted(cnt.items(), key=lambda x: -x[1])},
        'news': all_news,
        'labels': labels,
        'stocks': stocks,
        'forex': forex,
        'timestamp': now.isoformat(),
    }

    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    print(f'\n写入: news_data.json')
    print('=== Python采集完成 ===')
