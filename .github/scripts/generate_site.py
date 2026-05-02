#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, datetime, re, random
from html import escape

# ── 读取数据 ──
with open('news_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
weekday_cn = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
date_cn = f'{now.year}年{now.month}月{now.day}日 {weekday_cn[now.weekday()]}'
hour = now.hour

# 问候
greeting = '早上好' if 5 <= hour < 12 else '中午好' if 12 <= hour < 14 else '下午好' if 14 <= hour < 18 else '晚上好'

# ── 解析新闻 ──
all_news = []
src_idx_map = {}
sources_data = data.get('news', [])
labels = data.get('labels', [])

for idx, items in enumerate(sources_data):
    if not items or not isinstance(items, list):
        continue
    for item in items:
        t = (item.get('t') or item.get('title') or '').strip()[:55]
        if len(t) < 5:
            continue
        all_news.append({
            't': t,
            's': item.get('s', '资讯'),
            'src': item.get('src', labels[idx] if idx < len(labels) else str(idx)),
            'u': escape(item.get('u', '#'), quote=True)
        })

total = len(all_news)
active_srcs = sorted(set(n['src'] for n in all_news))
active_count = len(active_srcs)

# ── 分类 ──
categories = {
    '国际': '美国|特朗普|拜登|欧盟|北约|联合国|俄罗斯|乌克兰|伊朗|以色列|巴勒斯坦|中东|亚洲|欧洲|非洲|美洲|全球|国际|外交|制裁|关税|WTO|G7|G20|贸易战|地缘|冲突|战争|和平|难民|核武器|导弹|战机|军舰|大使|领事|访问|峰会|谈判|协议|退出|世卫|气候|巴黎协定|人权',
    '科技': 'AI|人工智能|芯片|半导体|华为|苹果|微软|谷歌|Meta|特斯拉|SpaceX|5G|6G|量子|算法|大模型|GPT|LLM|机器人|自动驾驶|云计算|区块链|NFT|元宇宙|VR|AR|激光雷达|传感器|操作系统|手机|iPhone|高通|英伟达|AMD|英特尔|台积电|三星|OPPO|vivo|荣耀|蔚来|小鹏|理想|比亚迪|互联网|软件|数据|安全|黑客|漏洞|专利|创新|科技',
    'A股民生': 'A股|上证|深证|创业板|科创板|北交所|股市|股票|基金|理财|保险|银行|利率|降息|加息|存款|贷款|住房|公积金|房贷|房价|地产|土地|税收|个税|财政|发改委|央企|国企|GDP|CPI|PPI|涨幅|跌幅|沪深|千亿|亿|万亿|证监会|交易所',
    '财经': '美股|标普|纳斯达克|道指|期货|黄金|原油|大宗商品|数字货币|比特币|区块链|交易所|IPO|上市|融资|投资|资本|私募|风投|资产|估值|财报|营收|利润|市值|分红|回购|经济|消费|通胀|通缩|美联储|央行',
    '体育': '金牌|银牌|铜牌|奥运|亚运|世界杯|欧冠|NBA|CBA|中超|英超|西甲|意甲|德甲|法甲|网球|F1|电竞|运动员|教练|选手|冠军|决赛|半决赛|资格赛|世锦赛|马拉松|游泳|田径|体操|跳水|举重|乒乓球|羽毛球|足球|篮球|排球|中国足球|国足|联赛|赛事|竞技|球队|主场|客场',
    '文娱': '电影|票房|音乐|演唱会|综艺|游戏|明星|导演|电视剧|Netflix|迪士尼|B站|抖音|快手|舞台|广告|视频|直播|演出',
    '健康': '疫情|疫苗|新冠|病毒|疾病|诊断|治疗|患者|医院|医生|手术|药物|药品|药监|FDA|临床|传染病|癌症|糖尿病|高血压|心脏|大脑|基因|干细胞|中医|中药|营养|健身|食品|安全|污染|环境'
}
cat_order = ['国际', '科技', 'A股民生', '财经', '体育', '文娱', '健康']
cat_icons = {'国际': '🌍', '科技': '🔬', 'A股民生': '📊', '财经': '💰', '体育': '⚽', '文娱': '🎬', '健康': '❤️', '其他': '📌'}
cat_colors = {'国际': '#3b82f6', '科技': '#8b5cf6', 'A股民生': '#f59e0b', '财经': '#10b981', '体育': '#22c55e', '文娱': '#ec4899', '健康': '#ef4444', '其他': '#6b7280'}

# ── 智能功能 ──

# 1. 主题聚类（同主题合并）
def extract_keywords(title):
    """提取标题中的关键词（noun phrases）"""
    # 简单规则：提取2-5个字的组合
    words = set()
    for m in re.finditer(r'[\u4e00-\u9fff]{2,6}', title):
        w = m.group()
        if len(w) >= 2:
            words.add(w)
    return words

def cluster_news(items):
    """同一主题的新闻合并"""
    clusters = []
    used = set()
    for i, a in enumerate(items):
        if i in used:
            continue
        cluster = [a]
        used.add(i)
        ka = extract_keywords(a['t'])
        if len(ka) < 2:
            clusters.append(cluster)
            continue
        for j, b in enumerate(items):
            if j in used or j == i:
                continue
            kb = extract_keywords(b['t'])
            overlap = ka & kb
            if len(overlap) >= 2:
                cluster.append(b)
                used.add(j)
        clusters.append(cluster)
    return clusters

# 2. 智能摘要（从标题推断）
def smart_summary(title):
    """从标题生成一句话摘要"""
    # 标题本身就是自然语言，检查是否有"消息/据悉/报道"等提示词
    if re.search(r'[。！？]', title):
        parts = re.split(r'[。！？]', title)
        for p in parts:
            if len(p) >= 8:
                return p.strip()
    return ''

def get_importance(title):
    """判断新闻重要性（热议度）"""
    hot_keywords = ['重磅','突发','紧急','大跌','暴涨','宣布','发布','警告','协议','制裁','战争','冲突']
    score = 0
    for kw in hot_keywords:
        if kw in title:
            score += 1
    if score >= 2:
        return '🔥 重磅'
    elif score >= 1:
        return '⚡ 关注'
    return None

# ── 分类处理 ──
classified = {c: [] for c in cat_order}
other = []

for item in all_news:
    tt = item['t'].lower()
    placed = False
    for cat, kws in categories.items():
        for kw in kws.split('|'):
            if kw.strip().lower() in tt:
                classified[cat].append(item)
                placed = True
                break
        if placed:
            break
    if not placed:
        other.append(item)

if other:
    classified['其他'] = other

# ── 行情数据 ──
stocks = data.get('stocks', [])
stock_rows = ''
for s in stocks:
    n = escape(s.get('n', '--'))
    v = escape(s.get('v', '--'))
    c = escape(s.get('c', '--'))
    cls = s.get('cls', '')
    stock_rows += f'<div class="si2"><span class="sn">{n}</span><span class="sv">{v}</span><span class="sc2 {cls}">{c}</span></div>\n'
if not stock_rows:
    stock_rows = '<div class="si2"><span class="sn">暂无数据</span></div>'

# ── 汇率 ──
forex = data.get('forex', {})
if not forex:
    forex = {'USD': '7.2420', 'EUR': '7.8321', 'JPY': '0.0450', 'GBP': '9.1250', 'HKD': '0.9280', 'KRW': '0.0052'}
fx_names = {'USD': '美元', 'EUR': '欧元', 'JPY': '日元', 'GBP': '英镑', 'HKD': '港币', 'KRW': '韩元'}
fx_rows = ''
for k in ['USD', 'EUR', 'JPY', 'GBP', 'HKD', 'KRW']:
    if k in forex:
        fx_rows += f'<div class="fi"><span class="fp">{fx_names[k]} ({k})</span><span class="fr">{forex[k]}</span></div>\n'

# ── 天气（模拟，使用实时接口） ──
weather_html = ''
try:
    import urllib.request, ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    w_url = 'https://wttr.in/Beijing?format=j1&lang=zh'
    w_resp = urllib.request.urlopen(urllib.request.Request(w_url, headers={'User-Agent': 'curl/8.0'}), timeout=5, context=ctx)
    w_data = json.loads(w_resp.read().decode('utf-8'))
    cc = w_data.get('current_condition', [{}])[0]
    temp = cc.get('temp_C', '--')
    desc = cc.get('weatherDesc', [{}])[0].get('value', '--')
    wind = cc.get('windspeedKmph', '--')
    humidity = cc.get('humidity', '--')
    weather_html = f'''
<div class="se" id="weather">
  <div class="sh"><span class="si">🌤️</span><span class="st">今日天气</span><span class="sc">北京</span></div>
  <div class="weather-main">
    <span class="weather-icon">{get_weather_icon(desc)}</span>
    <span class="weather-temp">{temp}°C</span>
    <span class="weather-desc">{desc}</span>
  </div>
  <div class="weather-details">
    <span>💨 风速 {wind} km/h</span>
    <span>💧 湿度 {humidity}%</span>
  </div>
</div>'''
    weather_html = weather_html.replace('\n  ', '\n')
except:
    pass

def get_weather_icon(desc):
    """天气描述转 emoji"""
    if '晴' in desc: return '☀️'
    if '云' in desc: return '⛅'
    if '雨' in desc: return '🌧️'
    if '雪' in desc: return '❄️'
    if '雾' in desc: return '🌫️'
    if '风' in desc: return '💨'
    return '🌤️'

# ── 热词统计 ──
all_text = ' '.join(n['t'] for n in all_news)
word_freq = {}
for m in re.finditer(r'[\u4e00-\u9fff]{2,5}', all_text):
    w = m.group()
    # 过滤掉分类关键词中的高频词
    stopwords = {'报道','新闻','今日','中国','美国','市场','公司','发布','最新','可能'}
    if w not in stopwords and not any(kw in w for kw in ['更多','查看']):
        word_freq[w] = word_freq.get(w, 0) + 1

hot_words = sorted(word_freq.items(), key=lambda x: -x[1])[:12]
tags_html = ''.join(f'<span class="tag" style="font-size:{(10+w[1]*0.5):.0f}px">{escape(w[0])}<sup>{w[1]}</sup></span>' for w in hot_words)

# ── 来源统计（活跃源柱状） ──
src_stats = []
for src in ['同花顺','华尔街见闻','财联社','第一财经','网易','新浪财经','新华网','人民网','中国新闻网','央视新闻','凤凰网','财新网','每经','证券时报','中证报','IT之家','百度','澎湃新闻','36氪','Donews','新浪体育','虎嗅','人民健康','今日头条','东方财富','雪球','环球网','观察者网','新浪娱乐','网易体育','B站热门','微博热搜','京东','抖音','网易云音乐','什么值得买']:
    cnt = sum(1 for n in all_news if n['src'] == src)
    if cnt > 0:
        src_stats.append((src, cnt))
src_stats.sort(key=lambda x: -x[1])
max_cnt = max(s[1] for s in src_stats) if src_stats else 1
src_bars_html = ''
for s, c in src_stats:
    pct = c / max_cnt * 100
    colors = ['#3b82f6','#8b5cf6','#ec4899','#f59e0b','#10b981','#22c55e','#ef4444','#6366f1']
    color = colors[src_stats.index((s,c)) % len(colors)]
    src_bars_html += f'<div class="src-bar"><div class="src-bar-label">{escape(s)}</div><div class="src-bar-track"><div class="src-bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div><div class="src-bar-num">{c}</div></div>\n'

# ── "为您精选" 模块 ──
# 热点话题（被多个来源报道的）
hot_news = [n for n in all_news if get_importance(n['t'])]
hot_html = ''
for n in hot_news[:3]:
    badge = get_importance(n['t'])
    hot_html += f'<div class="nc" onclick="window.open(\'{n["u"]}\',\'_blank\')"><div class="nt"><span class="ni">{badge}</span><span class="nn">{escape(n["t"])}</span></div><div class="nm">{escape(n["src"])} · {escape(n["s"])}</div></div>\n'
hot_section = '' if not hot_html else f'<div class="se" id="hot"><div class="sh"><span class="si">🔥</span><span class="st">热点关注</span><span class="sc">{len(hot_news)}</span></div>\n{hot_html}</div>'

# ── 构建HTML ──
news_html = ''
for cat in cat_order:
    items = classified.get(cat, []) + (classified.get('其他', []) if cat == '其他' else [])
    if cat != '其他' and not classified.get(cat):
        continue
    if not items:
        continue
    icon = cat_icons.get(cat, '📌')
    bg = cat_colors.get(cat, '#6b7280')
    html_items = ''
    for i, item in enumerate(items):
        imp = get_importance(item['t'])
        num = i + 1
        num_color = cat_colors.get(cat, '#6b7280')
        html_items += f'<div class="nc" onclick="window.open(\'{item["u"]}\',\'_blank\')">\n'
        html_items += f'  <div class="nt"><span class="ni" style="background:{num_color}">{num}</span><span class="nn">{escape(item["t"])}</span></div>\n'
        html_items += f'  <div class="nm"><span class="ns" style="color:{bg}">●</span> {escape(item["src"])} · {escape(item["s"])}</div>\n'
        html_items += f'</div>\n'
    news_html += f'<div class="se" id="cat-{cat}"><div class="sh"><span class="si">{icon}</span><span class="st">{cat}</span><span class="sc">{len(items)}</span></div>\n{html_items}</div>\n'

# ── 来源标签（导航栏） ──
nav_html = ''
nav_map = {'国际':'#cat-国际','科技':'#cat-科技','A股':'#cat-A股民生','财经':'#cat-财经','体育':'#cat-体育','文娱':'#cat-文娱','健康':'#cat-健康'}
for name, href in nav_map.items():
    nav_html += f'<a href="{href}">{name}</a>\n'

# ── 来源列表 ──
src_list_html = ' · '.join(escape(s) for s in active_srcs)

# ── 完整HTML ──
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>🌍 每日全球资讯</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0b0e16;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;overflow-x:hidden}}
.app{{max-width:780px;margin:0 auto;padding:0 14px 32px}}
header{{padding:18px 0 10px;margin-bottom:12px;position:sticky;top:0;background:#0b0e16;z-index:10;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid rgba(42,48,69,0.3)}}
.tb{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}}
.title{{font-size:20px;font-weight:700;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.title-emoji{{-webkit-text-fill-color:initial}}
.date{{font-size:12px;color:#6b7a8d;margin-bottom:2px}}
.greeting{{font-size:12px;color:#10b981;font-weight:500}}
.live{{background:rgba(34,197,94,0.08);color:#22c55e;padding:2px 10px;border-radius:10px;font-size:11px}}
nav{{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px;overflow-x:auto;white-space:nowrap;padding-bottom:4px;scrollbar-width:none}}
nav a{{color:#6b7a8d;text-decoration:none;font-size:11px;padding:3px 12px;border-radius:12px;background:rgba(255,255,255,0.03);flex-shrink:0;transition:all 0.2s}}
nav a:hover{{background:rgba(59,130,246,0.1);color:#60a5fa}}
.stats{{display:flex;gap:10px;font-size:11px;color:#6b7a8d;margin-top:8px}}
.stats span{{background:rgba(255,255,255,0.03);padding:3px 10px;border-radius:6px}}
.stats b{{color:#e2e8f0;font-weight:600}}
.se{{background:#121826;border:1px solid rgba(42,48,69,0.3);border-radius:10px;padding:12px 12px 6px;margin-bottom:12px;transition:all 0.2s}}
.sh{{display:flex;align-items:center;gap:8px;margin-bottom:6px;padding-bottom:6px;border-bottom:1px solid rgba(255,255,255,0.03)}}
.si{{font-size:16px;width:22px;text-align:center}}
.st{{font-size:14px;font-weight:600;color:#f1f5f9}}
.sc{{font-size:10px;background:rgba(99,102,241,0.08);color:#818cf8;padding:0 8px;border-radius:8px;line-height:18px;margin-left:auto}}
.nc{{padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.015);cursor:pointer;margin:0 -4px;padding:6px 4px;border-radius:6px;transition:all 0.15s}}
.nc:last-child{{border-bottom:none}}
.nc:hover{{background:rgba(255,255,255,0.025)}}
.nc:active{{background:rgba(255,255,255,0.04);transform:scale(0.99)}}
.nt{{font-size:13px;font-weight:500;color:#f1f5f9;margin-bottom:2px;display:flex;align-items:flex-start;gap:6px;line-height:1.4}}
.ni{{display:inline-flex;width:17px;height:17px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;font-size:9px;font-weight:700;border-radius:3px;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}}
.nn{{flex:1}}
.nm{{font-size:10px;color:#4a5a6d;padding-left:23px}}
.ns{{font-size:8px;margin-right:2px}}
.sg{{display:grid;grid-template-columns:1fr 1fr;gap:5px}}
.si2{{background:rgba(255,255,255,0.02);border-radius:6px;padding:6px 10px;display:flex;justify-content:space-between;align-items:center}}
.sn{{font-size:10px;color:#6b7a8d}}
.sv{{font-size:12px;font-weight:600;color:#f1f5f9}}
.sc2{{font-size:11px;font-weight:500}}
.up{{color:#22c55e}}
.down{{color:#ef4444}}
.fg{{display:grid;grid-template-columns:1fr 1fr;gap:4px}}
.fi{{background:rgba(255,255,255,0.02);border-radius:5px;padding:5px 10px;display:flex;justify-content:space-between;align-items:center}}
.fp{{font-size:11px;color:#6b7a8d}}
.fr{{font-size:12px;font-weight:600;color:#f1f5f9}}
.tags{{display:flex;flex-wrap:wrap;gap:6px;padding:4px 0 8px}}
.tag{{background:rgba(99,102,241,0.06);color:#818cf8;padding:2px 8px;border-radius:10px;display:inline-flex;align-items:center;gap:2px;font-weight:500}}
.tag sup{{font-size:9px;color:#4a5a6d;margin-left:2px}}
.src-section{{margin-bottom:12px}}
.src-bar{{display:flex;align-items:center;gap:6px;margin-bottom:3px}}
.src-bar-label{{width:72px;font-size:10px;color:#6b7a8d;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.src-bar-track{{flex:1;height:6px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden}}
.src-bar-fill{{height:100%;border-radius:4px;transition:width 0.5s}}
.src-bar-num{{width:20px;font-size:10px;color:#8896a6;text-align:right}}
.src-list{{font-size:10px;color:#4a5a6d;line-height:1.6;padding:4px 0}}
.bottom-nav{{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}}
.bottom-nav a{{color:#6b7a8d;text-decoration:none;font-size:10px;padding:2px 10px;border-radius:10px;background:rgba(255,255,255,0.03)}}
.weather-main{{display:flex;align-items:center;gap:10px;margin:1px 0 4px}}
.weather-icon{{font-size:36px}}
.weather-temp{{font-size:24px;font-weight:700;color:#f1f5f9}}
.weather-desc{{font-size:13px;color:#6b7a8d}}
.weather-details{{display:flex;gap:16px;font-size:11px;color:#6b7a8d;margin-top:2px}}
.toast{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#1e293b;color:#f1f5f9;padding:6px 16px;border-radius:8px;font-size:11px;opacity:0;transition:opacity 0.3s;pointer-events:none;z-index:100}}
footer{{margin-top:8px;padding:12px 0;text-align:center;border-top:1px solid rgba(42,48,69,0.2)}}
footer p{{font-size:9px;color:#4a5a6d;margin-bottom:1px}}
@media(max-width:480px){{.sg{{grid-template-columns:1fr}}.fg{{grid-template-columns:1fr 1fr}}.title{{font-size:18px}}}}
</style>
</head>
<body>
<div class="app">
<header>
<div class="tb">
<span class="title"><span class="title-emoji">🌍</span> 每日全球资讯</span>
<span class="live">● LIVE</span>
</div>
<div class="date">{date_cn} · <span class="greeting">{greeting}</span></div>
<div class="stats"><span><b>{total}</b> 条新闻</span><span><b>{active_count}</b> 个来源</span></div>
<nav>{nav_html}</nav>
</header>

<!-- 🔥 热点关注 -->
{hot_section}

<!-- 📊 行情 -->
<div class="se" id="stocks"><div class="sh"><span class="si">📊</span><span class="st">行情速览</span></div>
<div class="sg">{stock_rows}</div></div>

<!-- 💱 汇率 -->
<div class="se" id="forex"><div class="sh"><span class="si">💱</span><span class="st">汇率</span><span class="sc">1 CNY</span></div>
<div class="fg">{fx_rows}</div></div>

<!-- 🏷️ 今日热词 -->
<div class="se" id="tags"><div class="sh"><span class="si">🏷️</span><span class="st">今日热词</span></div>
<div class="tags">{tags_html}</div></div>

<!-- 📰 新闻 -->
{news_html}

<!-- 📡 来源分布 -->
<div class="se" id="sources"><div class="sh"><span class="si">📡</span><span class="st">来源分布</span><span class="sc">{active_count}</span></div>
<div class="src-section">{src_bars_html}</div>
<div class="src-list">数据源: {src_list_html}</div></div>

<!-- 底部导航 -->
<footer>
<div class="bottom-nav">{nav_html}</div>
<p>🌍 每日全球资讯 · 自动采集 · 智能分类</p>
<p>powered by GitHub Actions & Python</p>
</footer>
</div>
<div id="toast" class="toast"></div>
<script>
// Smooth scroll for nav links
document.querySelectorAll('nav a, .bottom-nav a').forEach(a => {{
a.addEventListener('click', e => {{
e.preventDefault();
const target = document.querySelector(a.getAttribute('href'));
if (target) target.scrollIntoView({{behavior:'smooth',block:'start'}});
}});
}});
// Toast for stats
function showToast(msg) {{
const t = document.getElementById('toast');
t.textContent = msg; t.style.opacity = '1';
setTimeout(() => t.style.opacity = '0', 2000);
}}
document.querySelectorAll('.nc').forEach(el => {{
el.addEventListener('click', function(e) {{
if (e.target.closest('a')) return;
const link = this.getAttribute('onclick');
if (link) {{
const match = link.match(/open\('([^']+)'/);
if (match) {{ window.open(match[1], '_blank'); }}
}}
}});
}});
// Dynamic title update
let idx = 0;
const titles = ['🌍 每日全球资讯', '📰 {{total}}条新闻', '🔍 {{active_count}}个来源'];
setInterval(() => {{ document.title = titles[idx % titles.length]; idx++; }}, 4000);
</script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'=== 完成: {total}条 · {active_count}个来源 ===')
print(f'写入: index.html ({len(html)} bytes)')
