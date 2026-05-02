#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日价值资讯 - 投资·宏观·热点·科技·机会"""
import json, os, datetime, re
from html import escape

with open('news_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
weekday_cn = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
date_cn = f'{now.year}年{now.month}月{now.day}日 {weekday_cn[now.weekday()]}'
hour = now.hour
greeting = '早上好' if 5 <= hour < 12 else '中午好' if 12 <= hour < 14 else '下午好' if 14 <= hour < 18 else '晚上好'

# ── 解析 ──
all_news = []
sd = data.get('news', [])
groups = data.get('groups', {})

if isinstance(sd, list) and sd:
    if isinstance(sd[0], dict) and 'cat' in sd[0]:
        for item in sd:
            t = (item.get('t') or '').strip()[:60]
            if len(t) < 5: continue
            all_news.append(item)
    elif isinstance(sd[0], list):
        for idx, items in enumerate(sd):
            if not items or not isinstance(items, list): continue
            for item in items:
                t = (item.get('t') or item.get('title') or '').strip()[:60]
                if len(t) < 5: continue
                all_news.append({'t':t,'src':item.get('src',''),'cat':item.get('cat','hot'),'u':escape(item.get('u','#'),quote=True)})

total = len(all_news)
active_srcs = sorted(set(n['src'] for n in all_news))

# 分类
cat_names = {'finance':'📈 投资·财经','macro':'🌐 宏观·天下','hot':'🔥 热点·民生','tech':'💡 科技·商业','oppo':'🎯 机会·风向'}
cat_colors = {'finance':'#f59e0b','macro':'#3b82f6','hot':'#ef4444','tech':'#8b5cf6','oppo':'#22c55e'}
cat_order = ['finance','macro','hot','tech','oppo']

# 用分组数据或自动分类
if any(groups.values()):
    pass
elif all_news:
    for item in all_news:
        cat = item.get('cat','hot')
        groups.setdefault(cat, []).append(item)

# ── 行情 ──
stocks = data.get('stocks', [])
stock_rows = ''.join(
    f'<div class="si2"><span class="sn">{escape(s.get("n","--"))}</span>'
    f'<span class="sv">{escape(s.get("p","--"))}</span>'
    f'<span class="sc2 {s.get("cls","")}">{"▲" if s.get("cls")=="up" else "▼" if s.get("cls")=="down" else ""} {escape(s.get("c","--"))}</span></div>\n'
    for s in stocks)

# ── 汇率 ──
forex = data.get('forex', {}) or {'USD':'7.2420','EUR':'7.8321','JPY':'0.0450','GBP':'9.1250','HKD':'0.9280','KRW':'0.0052'}
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
    weather_html = f'<div class="se" id="weather"><div class="sh"><span>🌤️</span><span class="st">北京 · 今日天气</span></div><div class="weather-main"><span class="weather-icon">{we}</span><span class="weather-temp">{tm}°</span><span class="weather-desc">{de}</span><span class="weather-meta">💨 {wi}km/h 💧 {hu}%</span></div></div>'
except:
    pass

# ── 导航 + 内容 ──
nav_items = ''.join(f'<a href="#grp-{c}">{cat_names[c]}</a>' for c in cat_order)

news_html = ''
for cat in cat_order:
    items = groups.get(cat, [])
    if not items: continue
    bg = cat_colors.get(cat, '#6b7280')
    hi = ''
    for i, item in enumerate(items):
        hi += f'<div class="nc" onclick="window.open(\'{item["u"]}\',\'_blank\')"><div class="nt"><span class="ni" style="background:{bg}">{i+1}</span><span class="nn">{escape(item["t"])}</span></div><div class="nm"><span class="ns" style="color:{bg}">●</span> <span class="nsrc">{escape(item["src"])}</span></div></div>\n'
    news_html += f'<div class="se" id="grp-{cat}"><div class="sh"><span class="st">{cat_names[cat]}</span><span class="sc">{len(items)}</span></div>{hi}</div>\n'

# ── 来源 ──
src_list_html = ' · '.join(escape(s) for s in active_srcs)

# ── 页面 ──
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>📊 每日价值资讯</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0b0e16;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;min-height:100vh}}
.app{{max-width:800px;margin:0 auto;padding:0 14px 40px}}
header{{padding:16px 0 10px;position:sticky;top:0;background:rgba(11,14,22,0.92);z-index:10;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,0.04)}}
.tb{{display:flex;justify-content:space-between;align-items:center;margin-bottom:2px}}
.title{{font-size:20px;font-weight:700;background:linear-gradient(135deg,#f59e0b,#ef4444,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.date{{font-size:11px;color:#5a6a7d;display:flex;gap:10px;align-items:center;margin:4px 0 6px}}
.greeting{{color:#22c55e;font-size:11px;font-weight:500}}
.live-dot{{width:5px;height:5px;background:#ef4444;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}
.stats{{font-size:10px;color:#4a5a6d;margin-bottom:6px}}
nav{{display:flex;gap:3px;flex-wrap:wrap;overflow-x:auto;padding-bottom:2px;scrollbar-width:none}}
nav a{{color:#6b7a8d;text-decoration:none;font-size:10px;padding:4px 10px;border-radius:12px;background:rgba(255,255,255,0.02);flex-shrink:0;transition:all .15s;white-space:nowrap}}
nav a:hover{{background:rgba(59,130,246,0.06);color:#60a5fa}}
.se{{background:#111524;border:1px solid rgba(42,48,69,0.15);border-radius:12px;padding:12px;margin-bottom:10px;animation:fadeIn .3s ease-out}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
.sh{{display:flex;align-items:center;gap:8px;margin-bottom:6px;padding-bottom:6px;border-bottom:1px solid rgba(255,255,255,0.03)}}
.st{{font-size:14px;font-weight:600}}
.sc{{font-size:10px;background:rgba(99,102,241,0.05);color:#818cf8;padding:0 8px;border-radius:8px;line-height:18px;margin-left:auto}}
.nc{{padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.008);cursor:pointer;margin:0 -4px;padding:7px 4px;border-radius:6px;transition:all .12s}}
.nc:last-child{{border-bottom:none}}
.nc:hover{{background:rgba(255,255,255,0.012);transform:translateX(2px)}}
.nt{{display:flex;align-items:flex-start;gap:6px;font-size:13px;font-weight:500;line-height:1.4}}
.ni{{display:inline-flex;width:16px;height:16px;color:#fff;font-size:8px;font-weight:700;border-radius:3px;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px}}
.nn{{flex:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.nm{{font-size:10px;color:#3d4a5d;padding-left:22px;display:flex;align-items:center;gap:4px;margin-top:1px}}
.nsrc{{color:#5a6a7d}}
.sg{{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:0}}
.si2{{display:flex;align-items:center;gap:6px;background:rgba(255,255,255,0.008);border-radius:6px;padding:4px 10px}}
.sn{{font-size:10px;color:#6b7a8d;min-width:46px;flex-shrink:0}}.sv{{font-size:12px;font-weight:600;margin-left:auto}}
.sc2{{font-size:11px;font-weight:500;min-width:44px;text-align:right;flex-shrink:0}}.up{{color:#22c55e}}.down{{color:#ef4444}}
.fg{{display:grid;grid-template-columns:1fr 1fr;gap:4px}}
.fi{{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,0.008);border-radius:5px;padding:4px 10px}}
.fp{{font-size:11px;color:#6b7a8d}}.fr{{font-size:12px;font-weight:600}}
.weather-main{{display:flex;align-items:center;gap:8px;padding:2px 0}}
.weather-icon{{font-size:26px}}
.weather-temp{{font-size:18px;font-weight:700}}
.weather-desc{{font-size:12px;color:#5a6a7d}}
.weather-meta{{font-size:10px;color:#4a5a6d;margin-left:auto}}
.src-list{{font-size:10px;color:#3d4a5d;line-height:1.6;padding:2px 0;word-break:break-all}}
.highlight-bar{{font-size:10px;background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.08);border-radius:8px;padding:6px 10px;margin-bottom:8px;color:#f87171}}
footer{{margin-top:4px;padding:12px 0;text-align:center;border-top:1px solid rgba(42,48,69,0.08);font-size:9px;color:#3d4a5d}}
#backTop{{position:fixed;bottom:60px;right:14px;width:34px;height:34px;border-radius:50%;background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.12);color:#818cf8;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:50;opacity:0;transition:opacity .3s}}
@media(max-width:480px){{.sg{{grid-template-columns:1fr}}.fg{{grid-template-columns:1fr}}.title{{font-size:18px}}}}
</style>
</head>
<body>
<div class="app">
<header>
<div class="tb">
<span class="title">📊 每日价值资讯</span>
<span><span class="live-dot"></span></span>
</div>
<div class="date"><span>{date_cn}</span><span class="greeting">{greeting}</span><span style="color:#4a5a6d;font-size:10px">{total}条 · {len(active_srcs)}源</span></div>
<nav>{nav_items}</nav>
</header>

<div class="se" id="market"><div class="sh"><span class="st">📊 全球市场</span></div><div class="sg">{stock_rows}</div></div>
<div class="se" id="fx"><div class="sh"><span class="st">💱 汇率<span style="font-size:10px;color:#4a5a6d;font-weight:400;margin-left:4px">1 CNY =</span></span></div><div class="fg">{fx_rows}</div></div>
{weather_html}

{news_html}

<div class="se" id="srcs"><div class="sh"><span class="st">📡 数据来源</span></div><div class="src-list">{src_list_html}</div></div>

<footer>
<p>📊 每日价值资讯 · 投资·宏观·热点·科技·机会</p>
</footer>
</div>
<div id="backTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</div>
<script>
window.addEventListener('scroll',function(){{document.getElementById('backTop').style.opacity=window.scrollY>200?'1':'0'}});
document.querySelectorAll('nav a').forEach(function(a){{a.addEventListener('click',function(e){{e.preventDefault();var t=document.querySelector(this.getAttribute('href'));t&&t.scrollIntoView({{behavior:'smooth',block:'start'}})}})}});
var ti=0,ttls=['📊 每日价值资讯','📰 {total}条','🔍 {len(active_srcs)}源'];
setInterval(function(){{document.title=ttls[ti%3];ti++}},4000);
</script>
</body>
</html>'''

with open('_site/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'=== 完成: {total}条 · {len(active_srcs)}个来源 ===')
print(f'写入: index.html ({len(html)} bytes)')
