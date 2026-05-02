#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日生活资讯 - 按吃住行玩钱五大维度生成页面"""
import json, os, datetime, re, random
from html import escape

with open('news_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
weekday_cn = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
date_cn = f'{now.year}年{now.month}月{now.day}日 {weekday_cn[now.weekday()]}'
hour = now.hour
greeting = '早上好' if 5 <= hour < 12 else '中午好' if 12 <= hour < 14 else '下午好' if 14 <= hour < 18 else '晚上好'

# ── 解析新闻 ──
all_news = []
sources_data = data.get('news', [])
groups = data.get('groups', {})

if isinstance(sources_data, list) and sources_data:
    if isinstance(sources_data[0], list):
        for idx, items in enumerate(sources_data):
            if not items or not isinstance(items, list): continue
            for item in items:
                t = (item.get('t') or item.get('title') or '').strip()[:60]
                if len(t) < 5: continue
                all_news.append({
                    't': t, 'src': item.get('src', '资讯'),
                    'cat': item.get('cat', 'life'),
                    'u': escape(item.get('u', '#'), quote=True)
                })
    else:
        for item in sources_data:
            t = (item.get('t') or item.get('title') or '').strip()[:60]
            if len(t) < 5: continue
            all_news.append({
                't': t, 'src': item.get('src', '资讯'),
                'cat': item.get('cat', 'life'),
                'u': escape(item.get('u', '#'), quote=True)
            })

total = len(all_news)
active_srcs = sorted(set(n['src'] for n in all_news))
print(f'Loaded {total} news from {len(active_srcs)} sources')

# 如果 groups 有值直接用
if not any(groups.values()) and all_news:
    # 重新分类
    cats = {
        'money': ['财经','股市','基金','消费','涨价','降价','工资','收入','补贴','社保','医保','利率',
                  '银行','贷款','理财','保险','汇','税','房价','地价','证监会','A股','股票','涨停'],
        'home': ['房价','房地产','租房','住房','物业','小区','城市','规划','市政','水电','燃气',
                 '供暖','物业','学区','落户','户籍','拆迁','棚改','基建'],
        'food': ['餐饮','食品','外卖','餐厅','菜价','外卖','饮食','喝酒','饮料','奶茶','零食',
                 '营养','食材','超市','盒马','美团','饿了么','价格','连锁','预制菜'],
        'travel': ['出行','交通','地铁','公交','高铁','飞机','机票','火车','自驾','油价',
                   '电动车','充电','停车','限行','车牌','共享','单车','红灯','拥堵','路况'],
        'play': ['电影','综艺','游戏','体育','赛事','旅游','景点','演出','音乐','演唱会',
                 'B站','视频','直播','电竞','比赛','球星','球队','演唱会','上映','票房'],
    }
    cat_order = ['money','home','food','travel','play']
    cat_names = {'money':'💰 钱袋子','home':'🏠 住得安','food':'🍜 吃得香','travel':'🚗 行得畅','play':'🎮 玩得嗨'}
    
    grouped = {}
    for item in all_news:
        tt = item['t']
        placed = False
        for cat, kws in cats.items():
            if any(kw in tt for kw in kws):
                grouped.setdefault(cat, []).append(item)
                placed = True
                break
        if not placed:
            # 按src归类
            src_cat_map = {
                'money': ['同花顺','华尔街见闻','财联社','东方财富','每经新闻','新浪财经','雪球','财联社电报','华尔街实时','第一财经','36氪'],
                'home': ['央视新闻','新华网','中国新闻网','人民网','观察者网'],
                'food': ['百度热搜','微博热搜'],
                'travel': ['IT之家','DoNews','第一财经'],
                'play': ['新浪体育','新浪娱乐','B站热门','知乎热门','知乎'],
                'life': ['网易新闻','澎湃新闻','凤凰网','环球网','网易速览']
            }
            placed_in = 'life'
            for c, srcs in src_cat_map.items():
                if item['src'] in srcs: placed_in = c; break
            grouped.setdefault(placed_in, []).append(item)
else:
    grouped = groups

# ── 行情 ──
stocks = data.get('stocks', [])
stock_rows = ''.join(
    f'<div class="si2"><span class="sn">{escape(s.get("n","--"))}</span>'
    f'<span class="sv">{escape(s.get("p","--"))}</span>'
    f'<span class="sc2 {s.get("cls","")}">{"▲" if s.get("cls")=="up" else "▼" if s.get("cls")=="down" else ""} {escape(s.get("c","--"))}</span>'
    f'<span class="bar {s.get("cls","")}" style="width:{min(abs(float(s.get("c","0").replace("%","") or 0))*5,40):.0f}px"></span></div>\n'
    for s in stocks)

# ── 汇率 ──
forex = data.get('forex', {}) or {'USD': '7.2420', 'EUR': '7.8321', 'JPY': '0.0450', 'GBP': '9.1250', 'HKD': '0.9280', 'KRW': '0.0052'}
fxm = {'USD':'美元','EUR':'欧元','JPY':'日元','GBP':'英镑','HKD':'港币','KRW':'韩元'}
fx_rows = ''.join(f'<div class="fi"><span class="fp">{fxm[k]} ({k})</span><span class="fr">{forex[k]}</span></div>\n' for k in ['USD','EUR','JPY','GBP','HKD','KRW'] if k in forex)

# ── 天气 ──
weather_html = ''
try:
    import urllib.request as u
    ctx = __import__('ssl').create_default_context(); ctx.check_hostname=False; ctx.verify_mode=__import__('ssl').CERT_NONE
    w = u.urlopen(u.Request('https://wttr.in/Beijing?format=j1&lang=zh', headers={'User-Agent':'curl/8.0'}), timeout=5, context=ctx)
    j = json.loads(w.read().decode('utf-8'))
    cc = j.get('current_condition',[{}])[0]
    tm, de, wi, hu = cc.get('temp_C','--'), cc.get('weatherDesc',[{}])[0].get('value','--'), cc.get('windspeedKmph','--'), cc.get('humidity','--')
    we = '☀️' if '晴' in de else '⛅' if '云' in de else '🌧️' if '雨' in de else '❄️' if '雪' in de else '🌫️' if '雾' in de else '🌤️'
    weather_html = f'<div class="se" id="weather"><div class="sh"><span class="si">🌤️</span><span class="st">北京天气</span></div><div class="weather-main"><span class="weather-icon">{we}</span><span class="weather-temp">{tm}°</span><span class="weather-desc">{de}</span><span class="weather-meta">💨{wi}km/h 💧{hu}%</span></div></div>'
except:
    pass

# ── 热词 ──
wf = {}
skip_words = {'报道','新闻','今日','中国','美国','市场','公司','发布','最新','可能','一个','进行','表示','以及','提到','没有','不是','正在','还是','就是','这个','已经','可以','其他'}
for m in re.finditer('[\u4e00-\u9fff]{2,5}', ' '.join(n['t'] for n in all_news)):
    w = m.group()
    if w not in skip_words: wf[w] = wf.get(w,0)+1
hw = sorted(wf.items(), key=lambda x:-x[1])[:15]

# ── 导航 ──
cat_sections = {'money':'💰 钱袋子','home':'🏠 住得安','food':'🍜 吃得香','travel':'🚗 行得畅','play':'🎮 玩得嗨'}
nav_order = ['money','home','food','travel','play']
nav_items = ''.join(f'<a href="#grp-{c}">{cat_sections[c]}</a>' for c in nav_order)

# ── 分类新闻 ──
news_html = ''
for cat in nav_order:
    items = grouped.get(cat, [])
    if not items: continue
    hi = ''
    colors = {'money':'#f59e0b','home':'#22c55e','food':'#ef4444','travel':'#3b82f6','play':'#ec4899'}
    bg = colors.get(cat, '#6b7280')
    for i, item in enumerate(items):
        ent_html = ''
        hi += f'<div class="nc" onclick="window.open(\'{item["u"]}\',\'_blank\')"><div class="nt"><span class="ni" style="background:{bg}">{i+1}</span><span class="nn">{escape(item["t"])}</span></div><div class="nm"><span class="ns" style="color:{bg}">●</span> <span class="nsrc">{escape(item["src"])}</span></div></div>\n'
    news_html += f'<div class="se" id="grp-{cat}"><div class="sh"><span class="st">{cat_sections[cat]}</span><span class="sc">{len(items)}</span></div>{hi}</div>\n'

# ── 来源 ──
src_list_html = ' · '.join(escape(s) for s in active_srcs)

# ── HTML ──
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>🌍 每日生活资讯</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0b0e16;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;min-height:100vh}}
.app{{max-width:780px;margin:0 auto;padding:0 14px 40px}}
header{{padding:16px 0 10px;position:sticky;top:0;background:rgba(11,14,22,0.9);z-index:10;backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,0.04)}}
.tb{{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}}
.title{{font-size:20px;font-weight:700;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.date{{font-size:11px;color:#5a6a7d;display:flex;gap:8px;align-items:center}}
.greeting{{color:#22c55e;font-size:11px;font-weight:500}}
.live-dot{{width:5px;height:5px;background:#ef4444;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}
.stats{{font-size:11px;color:#5a6a7d;margin:6px 0 4px}}
nav{{display:flex;gap:4px;flex-wrap:wrap;overflow-x:auto;padding-bottom:2px;scrollbar-width:none}}
nav a{{color:#6b7a8d;text-decoration:none;font-size:10px;padding:4px 12px;border-radius:14px;background:rgba(255,255,255,0.025);flex-shrink:0;transition:all .15s}}
nav a:hover{{background:rgba(59,130,246,0.08);color:#60a5fa}}
.se{{background:#111524;border:1px solid rgba(42,48,69,0.15);border-radius:12px;padding:12px;margin-bottom:10px;animation:fadeIn .3s ease-out}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
.sh{{display:flex;align-items:center;gap:8px;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid rgba(255,255,255,0.03)}}
.st{{font-size:14px;font-weight:600;letter-spacing:.3px}}
.sc{{font-size:10px;background:rgba(99,102,241,0.06);color:#818cf8;padding:0 8px;border-radius:8px;line-height:18px;margin-left:auto}}
.nc{{padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.01);cursor:pointer;margin:0 -4px;padding:7px 4px;border-radius:6px;transition:all .15s}}
.nc:last-child{{border-bottom:none}}.nc:hover{{background:rgba(255,255,255,0.015);transform:translateX(2px)}}
.nt{{display:flex;align-items:flex-start;gap:6px;font-size:13px;font-weight:500;line-height:1.4}}
.ni{{display:inline-flex;width:16px;height:16px;color:#fff;font-size:8px;font-weight:700;border-radius:3px;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px}}
.nn{{flex:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.nm{{font-size:10px;color:#3d4a5d;padding-left:22px;display:flex;align-items:center;gap:4px;margin-top:2px}}
.nsrc{{color:#5a6a7d}}
.sg{{display:grid;grid-template-columns:1fr 1fr;gap:4px}}
.si2{{display:flex;align-items:center;gap:6px;background:rgba(255,255,255,0.012);border-radius:6px;padding:6px 10px;overflow:hidden}}
.sn{{font-size:10px;color:#6b7a8d;min-width:48px}}.sv{{font-size:12px;font-weight:600;margin-left:auto}}
.sc2{{font-size:11px;font-weight:500;min-width:48px;text-align:right}}.up{{color:#22c55e}}.down{{color:#ef4444}}
.bar{{height:3px;border-radius:2px;position:absolute;bottom:0;left:0}}.bar.up{{background:#22c55e;opacity:.3}}.bar.down{{background:#ef4444;opacity:.3}}
.fg{{display:grid;grid-template-columns:1fr 1fr;gap:4px}}
.fi{{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,0.012);border-radius:5px;padding:5px 10px}}
.fp{{font-size:11px;color:#6b7a8d}}.fr{{font-size:12px;font-weight:600}}
.weather-main{{display:flex;align-items:center;gap:8px;padding:2px 0}}
.weather-icon{{font-size:28px}}.weather-temp{{font-size:20px;font-weight:700}}
.weather-desc{{font-size:13px;color:#5a6a7d}}.weather-meta{{font-size:10px;color:#4a5a6d;margin-left:auto}}
.tags{{display:flex;flex-wrap:wrap;gap:5px;padding:2px 0 4px}}
.tag{{background:rgba(99,102,241,0.05);color:#818cf8;padding:2px 10px;border-radius:12px;display:inline-flex;align-items:center;gap:3px;font-weight:500;font-size:11px;transition:all .15s}}
.tag:hover{{background:rgba(99,102,241,0.1);transform:scale(1.04)}}
.tag sup{{font-size:8px;color:#4a5a6d}}
.src-list{{font-size:10px;color:#3d4a5d;line-height:1.6;padding:2px 0;word-break:break-all}}
footer{{margin-top:4px;padding:12px 0;text-align:center;border-top:1px solid rgba(42,48,69,0.1);font-size:9px;color:#3d4a5d}}
#backTop{{position:fixed;bottom:60px;right:14px;width:34px;height:34px;border-radius:50%;background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.15);color:#818cf8;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:50;opacity:0;transition:opacity .3s}}
@media(max-width:480px){{.sg{{grid-template-columns:1fr}}.fg{{grid-template-columns:1fr 1fr}}.title{{font-size:18px}}}}
</style>
</head>
<body>
<div class="app">
<header>
<div class="tb"><span class="title">🌍 每日生活资讯</span><span><span class="live-dot"></span></span></div>
<div class="date"><span>{date_cn}</span><span class="greeting">{greeting}</span></div>
<div class="stats">{total} 条 · {len(active_srcs)} 个来源</div>
<nav>{nav_items}</nav>
</header>

<div class="se" id="market"><div class="sh"><span class="st">📊 行情</span></div><div class="sg">{stock_rows}</div></div>
<div class="se" id="fx"><div class="sh"><span class="st">💱 汇率<span style="font-size:10px;color:#4a5a6d;font-weight:400;margin-left:6px">1 CNY =</span></span></div><div class="fg">{fx_rows}</div></div>
{weather_html}

{news_html}

<div class="se" id="srcs"><div class="sh"><span class="st">📡 来源</span></div><div class="src-list">{src_list_html}</div></div>

<footer>
<p>🌍 每日生活资讯 · 自动采集 · 覆盖吃住行玩钱</p>
</footer>
</div>
<div id="backTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</div>
<script>
window.addEventListener('scroll',function(){{document.getElementById('backTop').style.opacity=window.scrollY>200?'1':'0'}});
document.querySelectorAll('nav a').forEach(function(a){{a.addEventListener('click',function(e){{e.preventDefault();var t=document.querySelector(this.getAttribute('href'));t&&t.scrollIntoView({{behavior:'smooth',block:'start'}})}})}});
var ti=0,ttls=['🌍 每日生活资讯','📰 {total}条资讯','🔍 {len(active_srcs)}个来源'];
setInterval(function(){{document.title=ttls[ti%3];ti++}},4000);
</script>
</body>
</html>'''

with open('_site/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'=== 完成: {total}条 · {len(active_srcs)}个来源 ===')
print(f'写入: index.html ({len(html)} bytes)')
