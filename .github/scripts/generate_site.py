#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日价值资讯 V3 - 防弹版"""
import json, os, datetime, re, sys, traceback

try:
    from html import escape
except:
    import cgi
    def escape(s, quote=False):
        return cgi.escape(s, quote)

with open('news_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
wd = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
dc = '%s月%s日 %s' % (now.month, now.day, wd[now.weekday()])
h = now.hour
gr = '早上好' if 5<=h<12 else '中午好' if 12<=h<14 else '下午好' if 14<=h<18 else '晚上好'

all_news = []
sd = data.get('news', [])
groups = data.get('groups', {})

if isinstance(sd, list):
    for item in sd:
        if isinstance(item, dict):
            t = (item.get('t') or '').strip()[:60]
            if len(t) >= 5:
                all_news.append(item)
        elif isinstance(item, list):
            for it in item:
                if isinstance(it, dict):
                    t = (it.get('t') or it.get('title') or '').strip()[:60]
                    if len(t) >= 5:
                        all_news.append({'t':t,'src':it.get('src',''),'cat':it.get('cat','hot'),'u':escape(it.get('u','#'), quote=True)})

total = len(all_news)
srcs = sorted(set(n.get('src','') for n in all_news))

cat_names = {'finance':'📈 投资·财经','macro':'🌐 宏观·天下','hot':'🔥 热点·民生','tech':'💡 科技·前沿','oppo':'🎯 机会·风向'}
cat_colors = {'finance':'#f59e0b','macro':'#3b82f6','hot':'#ef4444','tech':'#8b5cf6','oppo':'#22c55e'}
order = ['finance','macro','hot','tech','oppo']

if not any(groups.values()) and all_news:
    groups = {}
    for n in all_news:
        groups.setdefault(n.get('cat','hot'), []).append(n)

# 热词
wf = {}
skip = set(['报道','新闻','中国','市场','公司','发布','最新','一个','进行','表示','以及','没有','不是','正在','这个','已经','可以','其他','我们','除了','并且','虽然','但是','因为','所以'])
txt = ' '.join(n.get('t','') for n in all_news)
for m in re.finditer('[\u4e00-\u9fff]{2,4}', txt):
    w = m.group()
    if w not in skip:
        wf[w] = wf.get(w,0)+1
hw = sorted(wf.items(), key=lambda x:-x[1])[:12]

# 股票
stocks = data.get('stocks', [])
sr_parts = []
for s in stocks:
    s_n = escape(s.get('n',''))
    s_v = escape(s.get('p',''))
    s_cls = s.get('cls','')
    s_c = escape(s.get('c',''))
    s_r = escape(s.get('r',''))
    tri = '▲' if s_cls == 'up' else '▼'
    sr_parts.append(
        '<div class="si">'
        '<span class="sn">%s</span>'
        '<span class="sv">%s</span>'
        '<span class="sc2 %s">%s %s %s</span>'
        '</div>\n' % (s_n, s_v, s_cls, tri, s_c, s_r))
sr = ''.join(sr_parts)

forex = data.get('forex', {}) or {'USD':'7.2420','EUR':'7.8321','JPY':'0.0450','GBP':'9.1250','HKD':'0.9280'}
fxm = {'USD':'美元','EUR':'欧元','JPY':'日元','GBP':'英镑','HKD':'港币'}
fr_parts = []
for k in ['USD','EUR','JPY','GBP','HKD']:
    if k in forex:
        fr_parts.append(
            '<div class="fi">'
            '<span>%s (%s)</span>'
            '<span class="fv">%s</span>'
            '</div>\n' % (fxm[k], k, forex[k]))
fr = ''.join(fr_parts)

# 天气
wh = ''
try:
    import urllib.request as u
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    w = u.urlopen(u.Request('https://wttr.in/Beijing?format=j1&lang=zh', headers={'User-Agent':'curl/8.0'}), timeout=5, context=ctx)
    j = json.loads(w.read().decode('utf-8'))
    cc = j.get('current_condition',[{}])[0]
    tm = cc.get('temp_C','--')
    de = cc.get('weatherDesc',[{}])[0].get('value','--')
    ws = cc.get('windspeedKmph','--')
    we = '☀️' if '晴' in de else '⛅' if '云' in de else '🌧️' if '雨' in de else '🌤️'
    wh = '<div class="se" id="w"><div class="weather-bar">%s 北京 %s° %s  💨%skm/h</div></div>' % (we, tm, de, ws)
except:
    pass

# 导航
nav_parts = []
for c in order:
    nav_parts.append('<a href="#g%s">%s</a>' % (c, cat_names[c]))
nav = ''.join(nav_parts)

# 新闻块
news_parts = []
for c in order:
    items = groups.get(c, [])
    if not items:
        continue
    bg = cat_colors.get(c, '#666')
    inner = ''
    for i, item in enumerate(items):
        nn = escape(item.get('t',''))
        src = escape(item.get('src',''))
        uurl = escape(item.get('u','#'), quote=True)
        inner += (
            '<div class="nc" onclick="window.open(\'%s\',\'_blank\')">\n'
            '<div class="nt"><span class="ni" style="background:%s">%d</span>'
            '<span class="nn">%s</span></div>\n'
            '<div class="nm"><span class="ns" style="color:%s">&#9679;</span>'
            '<span class="nsrc">%s</span></div></div>\n'
        ) % (uurl, bg, i+1, nn, bg, src)
    news_parts.append(
        '<div class="se" id="g%s">'
        '<div class="sh"><span class="st">%s</span>'
        '<span class="sc">%d</span></div>\n%s</div>\n'
        % (c, cat_names[c], len(items), inner))
news_html = ''.join(news_parts)

hw_html = ''
if hw:
    hw_inner = ''.join('<span class="tg">#%s</span>' % escape(w) for w, _ in hw)
    hw_html = '<div class="se" id="h"><div class="sh"><span class="st">🔥 今日热词</span></div><div class="tgs">%s</div></div>' % hw_inner

src_html = ' · '.join(escape(s) for s in srcs)

market_html = ''
if sr:
    market_html = '<div class="se" id="m"><div class="sh"><span class="st">📊 全球市场</span></div><div class="sg">%s</div></div>' % sr

fx_html = ''
if fr:
    fx_html = '<div class="se" id="f"><div class="sh"><span class="st">💱 汇率</span><span class="sc" style="font-size:9px;color:#4a5a6d">1 CNY =</span></div><div class="fg">%s</div></div>' % fr

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>📊 每日价值资讯</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0e16;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.5;min-height:100vh}
.app{max-width:780px;margin:0 auto;padding:0 12px 40px}
header{padding:14px 0 8px;position:sticky;top:0;background:rgba(11,14,22,0.93);z-index:10;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,0.03);margin:0 -12px;padding:14px 12px 8px}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:2px}
.tl{font-size:20px;font-weight:700;background:linear-gradient(135deg,#f59e0b,#ef4444,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.sub{font-size:10px;color:#4a5a6d;display:flex;gap:8px;align-items:center;margin:3px 0 5px}
.gr{color:#22c55e;font-size:10px;font-weight:500}
.live{width:5px;height:5px;background:#ef4444;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
nav{display:flex;gap:3px;overflow-x:auto;padding-bottom:1px;scrollbar-width:none}
nav a{color:#5a6a7d;text-decoration:none;font-size:10px;padding:4px 10px;border-radius:12px;background:rgba(255,255,255,0.02);flex-shrink:0;white-space:nowrap;transition:all .15s}
nav a:hover{background:rgba(59,130,246,0.06);color:#60a5fa}
.se{background:#111524;border:1px solid rgba(42,48,69,0.12);border-radius:10px;padding:10px;margin-bottom:8px;animation:fi .3s ease}
@keyframes fi{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
.sh{display:flex;align-items:center;gap:6px;margin-bottom:4px;padding-bottom:5px;border-bottom:1px solid rgba(255,255,255,0.02)}
.st{font-size:13px;font-weight:600}
.sc{font-size:10px;color:#4a5a6d;margin-left:auto}
.nc{padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.008);cursor:pointer;margin:0 -3px;padding:6px 3px;border-radius:5px}
.nc:last-child{border-bottom:none}
.nc:hover{background:rgba(255,255,255,0.01)}
.nt{display:flex;gap:5px;font-size:13px;font-weight:500;line-height:1.4;align-items:flex-start}
.ni{display:inline-flex;width:15px;height:15px;color:#fff;font-size:8px;font-weight:700;border-radius:3px;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}
.nn{flex:1}
.nm{font-size:9px;color:#3d4a5d;padding-left:20px;display:flex;gap:3px;margin-top:1px}
.nsrc{color:#5a6a7d}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:3px}
.si{display:flex;gap:4px;background:rgba(255,255,255,0.007);border-radius:5px;padding:4px 8px;align-items:center}
.sn{font-size:9px;color:#6b7a8d;min-width:42px;flex-shrink:0}
.sv{font-size:12px;font-weight:600;margin-left:auto}
.sc2{font-size:10px;font-weight:500;min-width:50px;text-align:right;flex-shrink:0}
.up{color:#22c55e}.down{color:#ef4444}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:3px}
.fi{display:flex;justify-content:space-between;background:rgba(255,255,255,0.007);border-radius:4px;padding:3px 8px;font-size:11px}
.fv{font-weight:600}
.weather-bar{font-size:11px;color:#5a6a7d;padding:2px 0}
.tgs{display:flex;flex-wrap:wrap;gap:4px;padding:2px 0 4px}
.tg{background:rgba(99,102,241,0.04);color:#818cf8;padding:1px 8px;border-radius:10px;font-size:10px;font-weight:500}
.srcs{font-size:9px;color:#3d4a5d;line-height:1.5;padding:2px 0}
footer{padding:10px 0;text-align:center;font-size:9px;color:#333}
#bt{position:fixed;bottom:50px;right:12px;width:30px;height:30px;border-radius:50%;background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.1);color:#818cf8;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:50;opacity:0;transition:opacity .3s}
@media(max-width:480px){.sg,.fg{grid-template-columns:1fr}.tl{font-size:18px}}
</style>
</head>
<body>
<div class="app">
<header>
<div class="top"><span class="tl">📊 每日价值资讯</span><span class="live"></span></div>
<div class="sub"><span>%s</span><span class="gr">%s</span><span>%d条 · %d源</span></div>
<nav>%s</nav>
</header>
%s
%s
%s
%s
%s
<div class="se" id="s"><div class="sh"><span class="st">📡 来源</span></div><div class="srcs">%s</div></div>
<footer>📊 每2小时更新 · 投资·宏观·热点·科技·机会</footer>
</div>
<div id="bt" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</div>
<script>
var bt=document.getElementById('bt');
window.addEventListener('scroll',function(){bt.style.opacity=window.scrollY>200?1:0});
document.querySelectorAll('nav a').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();var t=document.querySelector(this.getAttribute('href'));t&&t.scrollIntoView({behavior:'smooth',block:'start'})})});
var ti=0,tt=['📊 每日价值资讯','📰 %d条','🔍 %d源'];
setInterval(function(){document.title=tt[ti%%3];ti++},4000);
</script>
</body>
</html>''' % (dc, gr, total, len(srcs), nav, market_html, fx_html, wh, hw_html, news_html, src_html, total, len(srcs))

os.makedirs('_site', exist_ok=True)
with open('_site/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('DONE: %d news, %d sources, %d bytes' % (total, len(srcs), len(html)))
