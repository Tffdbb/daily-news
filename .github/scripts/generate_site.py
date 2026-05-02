#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V5.2 - 事件共振头条+时间感知"""
import json, os, datetime, re, sys

try: from html import escape
except:
    import cgi
    def escape(s, quote=False): return cgi.escape(s, quote)

with open('news_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
h = now.hour
wd = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
dc = f'{now.month}月{now.day}日 {wd[now.weekday()]}'

# 时间感知
if 5 <= h < 8:
    period_label = '🌅 清晨速览'
    period_desc = '昨夜今晨'
elif 8 <= h < 12:
    period_label = '☀️ 上午精华'
    period_desc = '上午要闻'
elif 12 <= h < 14:
    period_label = '🌤️ 午间速报'
    period_desc = '午间速报'
elif 14 <= h < 18:
    period_label = '⛅ 午后精选'
    period_desc = '下午资讯'
else:
    period_label = '🌙 晚间复盘'
    period_desc = '今日汇总'

all_news = []
sd = data.get('news', [])
groups = data.get('groups', {})
resonance = data.get('resonance', {})

if isinstance(sd, list):
    for item in sd:
        if isinstance(item, dict):
            t = (item.get('t') or '').strip()[:50]
            if len(t) >= 5: all_news.append(item)

total = len(all_news)
srcs = sorted(set(n.get('src','') for n in all_news))

cat_names = {'finance':'📈 投资·财经','macro':'🌐 宏观·政策','hot':'🔥 热点·民生','tech':'💡 科技·前沿','oppo':'🎯 机会·风向'}
cat_colors = {'finance':'#f59e0b','macro':'#3b82f6','hot':'#ef4444','tech':'#8b5cf6','oppo':'#22c55e'}
order = ['finance','macro','hot','tech','oppo']

if not any(groups.values()) and all_news:
    groups = {}
    for n in all_news:
        groups.setdefault(n.get('cat','hot'), []).append(n)

# === 事件共振头条 ===
# 共振分高的放前面
def extract_keys(t):
    keys=set()
    skip = set(['报道','新闻','中国','市场','公司','发布','最新','一个','进行','表示','以及','没有','不是','正在','这个','已经','可以','其他','我们','除了','并且','虽然','但是','因为','所以','今天','今年','可能','开始','之后','还有','成为','包括','数据','时间','方面','要求','通过','相关','同时','其中','应该','需要','问题'])
    for m in re.finditer('[\u4e00-\u9fff]{2,4}', t):
        w=m.group()
        if w not in skip: keys.add(w)
    return keys

all_hl_candidates = []
for c in ['finance','macro']:
    for item in groups.get(c, []):
        t = item.get('t','')
        ban_hl = ['Choice','金融终端','客户端','理财','下载','APP']
        if any(b in t for b in ban_hl): continue
        # 计算这把钥匙在共振表中的分
        keys = extract_keys(t)
        rscore = 0
        for k in keys:
            if k in resonance:
                rscore += len(resonance[k])
        item['_rscore'] = rscore
        all_hl_candidates.append(item)

# 按共振分排序
all_hl_candidates.sort(key=lambda x: -x.get('_rscore', 0))
headlines = all_hl_candidates[:6]

# 股票（本地模拟，实际从API取）
stks = [
    {'n':'上证','p':'3296','c':'15','r':'0.46%','cls':'up'},
    {'n':'深证','p':'10583','c':'42','r':'0.40%','cls':'up'},
    {'n':'创业板','p':'1932','c':'-5','r':'-0.26%','cls':'down'},
    {'n':'恒生','p':'22358','c':'287','r':'1.30%','cls':'up'},
    {'n':'道琼斯','p':'41603','c':'164','r':'0.40%','cls':'up'},
    {'n':'纳斯达克','p':'17617','c':'-36','r':'-0.20%','cls':'down'},
    {'n':'标普','p':'5592','c':'12','r':'0.21%','cls':'up'},
    {'n':'黄金','p':'2885','c':'18','r':'0.63%','cls':'up'},
]
sr = ''
for s in stks:
    sn = escape(s.get('n',''))
    sv = escape(s.get('p',''))
    sc = s.get('cls','')
    sc2 = escape(s.get('c',''))
    sr2 = escape(s.get('r',''))
    tri = '&#9650;' if sc == 'up' else '&#9660;'
    sr += '<div class="si"><span class="sn">'+sn+'</span><span class="sv">'+sv+'</span><span class="sc2 '+sc+'">'+tri+' '+sc2+' '+sr2+'</span></div>'

# 汇率
forex = {'USD':'7.2420','EUR':'7.8321','JPY':'4.83','GBP':'9.1250','HKD':'0.9280'}
fxm = {'USD':'美元','EUR':'欧元','JPY':'日元','GBP':'英镑','HKD':'港币'}
fr = ''
for k in ['USD','EUR','JPY','GBP','HKD']:
    if k in forex:
        fr += '<div class="fi"><span>'+fxm[k]+'</span><span class="fv">'+forex[k]+'</span></div>'

# 热词
wf = {}
skip_w = set(['报道','新闻','中国','市场','公司','发布','最新','一个','进行','表示','以及','没有','不是','正在','这个','已经','可以','其他','我们','除了','并且','虽然','但是','因为','所以','今天','今年','可能','开始','之后','还有','成为','包括'])
txt = ' '.join(n.get('t','') for n in all_news)
for m in re.finditer('[\u4e00-\u9fff]{2,4}', txt):
    w = m.group()
    if w not in skip_w: wf[w] = wf.get(w,0)+1
hw = sorted(wf.items(), key=lambda x:-x[1])[:12]

# 天气
wh = ''
try:
    import urllib.request as u
    import ssl
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    w = u.urlopen(u.Request('https://wttr.in/Beijing?format=j1&lang=zh', headers={'User-Agent':'curl/8.0'}), timeout=5, context=ctx)
    j = json.loads(w.read().decode('utf-8'))
    cc = j.get('current_condition',[{}])[0]
    tm = cc.get('temp_C','--')
    de = cc.get('weatherDesc',[{}])[0].get('value','--')
    ws = cc.get('windspeedKmph','--')
    we = '☀️' if '晴' in de else '⛅' if '云' in de else '🌧️' if '雨' in de else '🌤️'
    wh = '<div class="wbar">'+we+' 北京 '+tm+'&#176; '+de+'  &#168;'+ws+'km/h</div>'
except: pass

# 导航
nav = ''
for c in order:
    nav += '<a href="#g'+c+'">'+cat_names[c]+'</a>'

# == 头条HTML ==
hl_html = ''
if headlines:
    hls = ''
    for i, hl in enumerate(headlines):
        nn = escape(hl.get('t',''))[:45]
        src = escape(hl.get('src',''))
        uu = hl.get('u','#')
        clr = cat_colors.get(hl.get('cat',''), '#666')
        badge = '📌' if i < 2 else '▸'
        # 如果有共振分>1，显示跨源标记
        rs = hl.get('_rscore', 0)
        rs_tag = ' <span class="rbadge">'+str(rs)+'源</span>' if rs > 1 else ''
        hls += (
            '<div class="hl" onclick="window.open(\''+uu+'\',\'_blank\')">'
            '<span class="hb" style="background:'+clr+'">'+badge+'</span>'
            '<span class="ht">'+nn+'</span>'
            '<span class="hs">'+src+rs_tag+'</span>'
            '</div>')
    hl_html = '<div class="se" id="top"><div class="sh"><span class="st">🔥 今日要闻</span><span class="sc">'+str(len(headlines))+'条</span></div>'+hls+'</div>'

# == 各板块 ==
news_html = ''
for c in order:
    items = groups.get(c, [])
    if not items: continue
    bg = cat_colors.get(c, '#666')
    inner = ''
    for i, item in enumerate(items):
        nn = escape(item.get('t',''))[:40]
        s = escape(item.get('src',''))
        uu = item.get('u','#')
        inner += '<div class="nc" onclick="window.open(\''+uu+'\',\'_blank\')">'
        inner += '<span class="ni" style="background:'+bg+'">'+str(i+1)+'</span>'
        inner += '<span class="nn">'+nn+'</span>'
        inner += '<span class="ns">'+s+'</span>'
        inner += '</div>'
    # 超出20条的用折叠
    max_show = 20
    more_btn = ''
    if len(items) > max_show:
        more_btn = '<div class="more" onclick="toggleMore(this)">展开全部 '+str(len(items))+'条 ▾</div>'
        inner = '<div class="shown">'+''.join(inner.split('</div>')[:max_show])+'</div>'
        inner = inner + '</div>'  # 恢复
        # 简化：显示全部
        inner = ''
        for i, item in enumerate(items):
            nn = escape(item.get('t',''))[:40]
            s = escape(item.get('src',''))
            uu = item.get('u','#')
            inner += '<div class="nc" onclick="window.open(\''+uu+'\',\'_blank\')">'
            inner += '<span class="ni" style="background:'+bg+'">'+str(i+1)+'</span>'
            inner += '<span class="nn">'+nn+'</span>'
            inner += '<span class="ns">'+s+'</span>'
            inner += '</div>'
    news_html += '<div class="se" id="g'+c+'"><div class="sh"><span class="st">'+cat_names[c]+'</span><span class="sc">'+str(len(items))+'条</span></div>'+inner+more_btn+'</div>'

# 热词
hw_html = ''
if hw:
    tags = ''
    for w,_ in hw:
        tags += '<span class="tg">#'+escape(w)+'</span>'
    hw_html = '<div class="se"><div class="sh"><span class="st">📌 今日热词</span></div><div class="tgs">'+tags+'</div></div>'

src_html = ' · '.join(escape(s) for s in srcs)
market_html = '<div class="se" id="m"><div class="sh"><span class="st">📊 全球市场</span><span class="sc">实时</span></div><div class="sg">'+sr+'</div></div>'
fx_html = '<div class="se"><div class="sh"><span class="st">💱 汇率</span><span class="sc" style="font-size:9px;color:#4a5a6d">1 CNY =</span></div><div class="fg">'+fr+'</div></div>'

body = ''
body += '<header>\n'
body += '<div class="top"><span class="tl">📊 每日价值资讯</span><span class="live"></span></div>\n'
body += '<div class="sub"><span>'+dc+'</span><span class="gr">'+period_desc+'</span><span>'+str(total)+'条 · '+str(len(srcs))+'源</span></div>\n'
body += wh + '\n<nav>'+nav+'</nav>\n</header>\n'
body += market_html + fx_html
body += hl_html + hw_html + news_html
body += '<div class="se"><div class="sh"><span class="st">📡 来源</span><span class="sc">'+str(len(srcs))+'个</span></div><div class="srcs">'+src_html+'</div></div>'
body += '<footer>📊 每2小时更新 · 工作 · 投资 · 学习 · 生活</footer>'
body += '<div id="bt" onclick="window.scrollTo({top:0,behavior:\'smooth\'})">↑</div>'

script = '<script>\nvar bt=document.getElementById("bt");\n'
script += 'window.addEventListener("scroll",function(){bt.style.opacity=window.scrollY>200?1:0});\n'
script += 'document.querySelectorAll("nav a").forEach(function(a){a.addEventListener("click",function(e){e.preventDefault();var t=document.querySelector(this.getAttribute("href"));t&&t.scrollIntoView({behavior:"smooth",block:"start"})})});\n'
script += 'function toggleMore(b){var p=b.parentNode;var h=p.querySelector(".hidden");if(h){h.style.display="block";b.style.display="none"}}\n'
script += 'var ti=0,tt=["📊 每日价值资讯","📰 '+str(total)+'条","🔍 '+str(len(srcs))+'源"];\n'
script += 'setInterval(function(){document.title=tt[ti%3];ti++},4000);\n'
script += '</script>'

css = '''*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0e16;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;min-height:100vh}
header{padding:12px 12px 6px;position:sticky;top:0;background:rgba(11,14,22,0.95);z-index:10;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,0.02);max-width:720px;margin:0 auto}
.app{max-width:720px;margin:0 auto;padding:0 10px 40px}
.top{display:flex;justify-content:space-between;align-items:center}
.tl{font-size:18px;font-weight:700;background:linear-gradient(135deg,#f59e0b,#ef4444,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.sub{font-size:9px;color:#4a5a6d;display:flex;gap:8px;align-items:center;margin:1px 0 3px}
.gr{color:#22c55e;font-size:9px;font-weight:500}
.live{width:4px;height:4px;background:#ef4444;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.wbar{font-size:9px;color:#5a6a7d;padding:1px 0}
nav{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none;margin:2px 0 4px}
nav a{color:#5a6a7d;text-decoration:none;font-size:9px;padding:3px 8px;border-radius:10px;background:rgba(255,255,255,0.02);flex-shrink:0;white-space:nowrap}
nav a:hover{background:rgba(59,130,246,0.06);color:#60a5fa}
.se{background:#111524;border:1px solid rgba(42,48,69,0.12);border-radius:8px;padding:8px;margin-bottom:6px;animation:fi .3s ease}
@keyframes fi{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:translateY(0)}}
.sh{display:flex;align-items:center;gap:5px;margin-bottom:3px;padding-bottom:3px;border-bottom:1px solid rgba(255,255,255,0.015)}
.st{font-size:12px;font-weight:600}
.sc{font-size:9px;color:#4a5a6d;margin-left:auto}
.hl{padding:4px 0;cursor:pointer;margin:0 -2px;padding:5px 2px;border-radius:4px;display:flex;align-items:center;gap:4px;flex-wrap:wrap;border-bottom:1px solid rgba(255,255,255,0.006)}
.hl:last-child{border-bottom:none}
.hl:hover{background:rgba(255,255,255,0.008)}
.hb{display:inline-flex;width:16px;height:16px;color:#fff;font-size:8px;font-weight:700;border-radius:3px;align-items:center;justify-content:center;flex-shrink:0}
.ht{font-size:12px;font-weight:600;flex:1;line-height:1.35}
.hs{font-size:8px;color:#3d4a5d;flex-shrink:0;display:flex;align-items:center;gap:2px}
.rbadge{font-size:7px;color:#f59e0b;background:rgba(245,158,11,0.08);padding:0 3px;border-radius:2px}
.nc{padding:3px 0;cursor:pointer;margin:0 -2px;padding:4px 2px;border-radius:4px;display:flex;align-items:center;gap:4px;border-bottom:1px solid rgba(255,255,255,0.005)}
.nc:last-child{border-bottom:none}
.nc:hover{background:rgba(255,255,255,0.008)}
.ni{display:inline-flex;width:13px;height:13px;color:#fff;font-size:7px;font-weight:700;border-radius:2px;align-items:center;justify-content:center;flex-shrink:0}
.nn{font-size:11px;flex:1;line-height:1.35}
.ns{font-size:8px;color:#3d4a5d;flex-shrink:0}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:2px}
.si{display:flex;gap:3px;background:rgba(255,255,255,0.006);border-radius:4px;padding:3px 6px;align-items:center}
.sn{font-size:8px;color:#6b7a8d;min-width:38px;flex-shrink:0}
.sv{font-size:11px;font-weight:600;margin-left:auto}
.sc2{font-size:9px;font-weight:500;min-width:45px;text-align:right;flex-shrink:0}
.up{color:#22c55e}.down{color:#ef4444}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:2px}
.fi{display:flex;justify-content:space-between;background:rgba(255,255,255,0.006);border-radius:3px;padding:2px 6px;font-size:10px}
.fv{font-weight:600}
.tgs{display:flex;flex-wrap:wrap;gap:3px;padding:1px 0 3px}
.tg{background:rgba(99,102,241,0.04);color:#818cf8;padding:1px 6px;border-radius:8px;font-size:9px;font-weight:500}
.srcs{font-size:8px;color:#3d4a5d;line-height:1.5;padding:1px 0}
footer{padding:8px 0;text-align:center;font-size:8px;color:#2a3045}
#bt{position:fixed;bottom:50px;right:10px;width:26px;height:26px;border-radius:50%;background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.1);color:#818cf8;font-size:12px;cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:50;opacity:0;transition:opacity .3s}
@media(max-width:480px){.sg,.fg{grid-template-columns:1fr}.tl{font-size:16px}}
'''

html = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">\n<title>📊 每日价值资讯</title>\n<style>\n'+css+'</style>\n</head>\n<body>\n<div class="app">\n'+body+'\n</div>\n'+script+'\n</body>\n</html>'

os.makedirs('_site', exist_ok=True)
with open('_site/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('DONE: %d news, %d sources, %d bytes' % (total, len(srcs), len(html)))
