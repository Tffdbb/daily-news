#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日价值资讯 - 头条引擎V3：事件共振+源多样性+精炼展示"""
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

if 5 <= h < 8:
    period_desc = '昨夜今晨'
elif 8 <= h < 12:
    period_desc = '上午要闻'
elif 12 <= h < 14:
    period_desc = '午间速报'
elif 14 <= h < 18:
    period_desc = '下午资讯'
else:
    period_desc = '今日汇总'

all_news = []
sd = data.get('news', [])
groups = data.get('groups', {})

if isinstance(sd, list):
    for item in sd:
        if isinstance(item, dict):
            t = (item.get('t') or '').strip()[:48]
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

# === 事件共振头条引擎V3 ===
resonance = data.get('resonance', {})

def extract_keys(t):
    keys=set()
    skip = set(['报道','新闻','中国','市场','公司','发布','最新','一个','进行','表示','以及','没有','不是','正在','这个','已经','可以','其他','我们','除了','并且','虽然','但是','因为','所以','今天','今年','可能','开始','之后','还有','成为','包括','数据','时间','方面','要求','通过','相关','同时','其中','应该','需要','问题'])
    for m in re.finditer('[\u4e00-\u9fff]{2,4}', t):
        w=m.group()
        if w not in skip: keys.add(w)
    return keys

headline_ban = ['Choice','金融终端','客户端','理财','下载','APP','基金','估值','嘉年华']

all_hl_candidates = []
for c in ['finance','macro','hot']:
    for item in groups.get(c, []):
        t = item.get('t','')
        if any(b in t for b in headline_ban): continue
        keys = extract_keys(t)
        rscore = 0
        for k in keys:
            if k in resonance and isinstance(resonance[k], list):
                rscore += len(resonance[k])
        item['_rscore'] = rscore
        all_hl_candidates.append(item)

# 排序：共振分高优先，同分时财经>宏观>热点
cat_priority = {'finance':0,'macro':1,'hot':2}
all_hl_candidates.sort(key=lambda x: (-x.get('_rscore', 0), cat_priority.get(x.get('cat',''), 3)))

# 源多样性：同一源最多2条
headlines = []
src_seen = {}
for item in all_hl_candidates:
    src = item.get('src','')
    cnt = src_seen.get(src, 0)
    if cnt >= 2: continue
    src_seen[src] = cnt + 1
    headlines.append(item)
    if len(headlines) >= 6: break

# 股票（真实行情由脚本启动时通过东方财富API获取）
import subprocess, json as jmod
def fetch_market():
    try:
        h = subprocess.run(['curl','-sL','https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f2,f3,f4,f12,f14&secids=1.000001,0.399001,0.399006,1.HSI,1.DJI,1.IXIC,1.SPX,113.au0'], capture_output=True, timeout=8, text=True).stdout
        j = jmod.loads(h)
        items = j.get('data',{}).get('diff',[])
        m = {'000001':'上证','399001':'深证','399006':'创业板','HSI':'恒生','DJI':'道琼斯','IXIC':'纳斯达克','SPX':'标普'}
        res = []
        for it in items:
            code = it.get('f12','')
            name = it.get('f14','') or m.get(code,code)
            price = it.get('f2',0)
            chg = it.get('f3',0) or 0
            disp = f'{chg:+.2f}%'
            if 'au0' in code: disp = f'{price:.1f}'
            res.append({'n':name,'p':f'{price:.0f}' if price > 10 else f'{price:.1f}','c':disp,'cls':'up' if chg >= 0 else 'down'})
        return res
    except: return [{'n':'上证','p':'--','c':'--','cls':''}]
stks = fetch_market()
sr = ''
for s in stks:
    sn = escape(s.get('n',''))
    sv = escape(s.get('p',''))
    sc = s.get('cls','')
    sc2 = escape(s.get('c',''))
    sr2 = escape(s.get('r',''))
    tri = '&#9650;' if sc == 'up' else '&#9660;'
    sr += '<div class="si"><span class="sn">'+sn+'</span><span class="sv">'+sv+'</span><span class="sc2 '+sc+'">'+tri+' '+sc2+' '+sr2+'</span></div>'

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

shop_items = data.get('shop', [])
ranks = data.get('ranks', [])
ghs = data.get('trending', [])
hns = data.get('hackernews', [])
zhs = data.get('zhihu', [])

nav = ''
for c in order:
    nav += '<a href="#g'+c+'">'+cat_names[c]+'</a>'
if shop_items:
    nav += '<a href="#gshop">📋 热议</a>'
if ghs:
    nav += '<a href="#gtrending">🏆 GitHub</a>'
if zhs:
    nav += '<a href="#gzhihu">💬 知乎</a>'

# 头条
hl_html = ''
if headlines:
    hls = ''
    for i, hl in enumerate(headlines):
        nn = escape(hl.get('t',''))[:45]
        src = escape(hl.get('src',''))
        uu = hl.get('u','#')
        clr = cat_colors.get(hl.get('cat',''), '#666')
        badge = '📌' if i < 2 else '▸'
        rs = hl.get('_rscore', 0)
        rs_tag = ' <span class="rbadge">'+str(rs)+'源</span>' if rs > 1 else ''
        hls += '<div class="hl" onclick="window.open(\''+uu+'\',\'_blank\',\'noopener,noreferrer\')"><span class="hb" style="background:'+clr+'">'+badge+'</span><span class="ht">'+nn+'</span><span class="hs">'+src+rs_tag+'</span></div>'
    hl_html = '<div class="se" id="top"><div class="sh"><span class="st">🔥 今日要闻</span><span class="sc">'+str(len(headlines))+'条</span></div>'+hls+'</div>'

# 各板块
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
        inner += '<div class="nc" onclick="window.open(\''+uu+'\',\'_blank\',\'noopener,noreferrer\')"><span class="ni" style="background:'+bg+'">'+str(i+1)+'</span><span class="nn">'+nn+'</span><span class="ns">'+s+'</span></div>'
    news_html += '<div class="se" id="g'+c+'"><div class="sh"><span class="st">'+cat_names[c]+'</span><span class="sc">'+str(len(items))+'条</span></div>'+inner+'</div>'

# 热词
hw_html = ''
if hw:
    tags = ''
    for w,_ in hw:
        tags += '<span class="tg">#'+escape(w)+'</span>'
    hw_html = '<div class="se"><div class="sh"><span class="st">📌 今日热词</span></div><div class="tgs">'+tags+'</div></div>'

src_html = ' · '.join(escape(s) for s in srcs)
market_html = '<div class="se" id="m"><div class="sh"><span class="st">📊 全球市场</span><span class="sc">实时</span></div><div class="sg">'+sr+'</div></div>'
# 贵金属
metals = data.get('metals', [])
metal_html = ''
if metals:
    mi = ''
    for m in metals:
        n = escape(m.get('name',''))
        p = escape(m.get('price',''))
        ch = escape(m.get('change',''))
        cls = 'up' if ch.startswith('+') else 'down' if ch.startswith('-') else ''
        mi += '<div class="ri"><span class="rn">'+n+'</span><span class="sv">'+p+'</span><span class="rv '+cls+'">'+ch+'</span></div>'
    metal_html = '<div class="se"><div class="sh"><span class="st">🥇 贵金属</span><span class="sc">实时</span></div><div class="rg">'+mi+'</div></div>'

# 成交额排行
volumes = data.get('volumes', [])
vol_html = ''
if volumes:
    vi = ''
    for i, v in enumerate(volumes[:8]):
        n = escape(v.get('name',''))
        cd = escape(v.get('code',''))
        pr = escape(v.get('price',''))
        ch = escape(v.get('change',''))
        vl = escape(v.get('vol',''))
        cls = 'up' if ch.startswith('+') else 'down' if ch.startswith('-') else ''
        ci = cd[-4:] if len(cd) >= 4 else cd
        vi += '<div class="vi"><span class="vr">'+str(i+1)+'</span><span class="vn">'+n+'</span><span class="vp">'+pr+'</span><span class="vc '+cls+'">'+ch+'</span><span class="vv">'+vl+'</span></div>'
    vol_html = '<div class="se"><div class="sh"><span class="st">📊 A股成交额排行</span><span class="sc">'+str(len(volumes))+'只</span></div>'+vi+'</div>'

# 量化选股
quants = data.get('quant', [])
q_html = ''
if quants:
    qi = ''
    for i, q in enumerate(quants):
        n = escape(q.get('name',''))
        cd = escape(q.get('code',''))
        ch = escape(str(q.get('chg','')))
        vl = escape(str(q.get('volRatio','')))
        sc = escape(str(q.get('score','')))
        pe = escape(str(q.get('pe','')))
        tb = escape(str(q.get('turnover','')))
        cls = 'up' if ch and float(ch) >= 0 else 'down'
        ch_s = ('+'+ch+'%') if ch and float(ch) >= 0 else (ch+'%' if ch else '')
        ci = cd[-4:] if len(cd) >= 4 else cd
        qi += '<div class="qi" onclick="alert('+"'"+cd+' '+n+"'"+')"><span class="qr">'+str(i+1)+'</span><span class="qn">'+n+'</span><span class="qch '+cls+'">'+ch_s+'</span><span class="qpe">PE'+pe+'</span><span class="qsc">'+sc+'</span></div>'
    q_html = '<div class="se"><div class="sh"><span class="st">📈 量化选股</span><span class="sc">多因子评分</span></div>'+qi+'</div>'

# GitHub Trending
gh_html = ''
if ghs:
    gi = ''
    for i, r in enumerate(ghs[:10]):
        n = escape(r.get('t',''))
        d = escape(r.get('desc',''))
        st = r.get('stars',0)
        ln = escape(r.get('lang',''))
        uu = r.get('u','#')
        stars_tag = ''
        if st: stars_tag = ' <span style="color:#f59e0b">&#9733;'+str(st)+'</span>'
        lang_tag = (' <span style="color:#4a5a6d;font-size:7px">'+ln+'</span>') if ln else ''
        gi += '<div class="nc" onclick="window.open(\''+uu+'\',\'_blank\',\'noopener,noreferrer\')"><span class="ni" style="background:#24292e">'+str(i+1)+'</span><span class="nn">'+n[:40]+'</span><span class="ns">'+lang_tag+stars_tag+'</span></div>'
    gh_html = '<div class="se" id="gtrending"><div class="sh"><span class="st">&#127942; GitHub 今日热榜</span><span class="sc">'+str(len(ghs))+'个项目</span></div>'+gi+'</div>'

# 知乎热榜
zh_html = ''
if zhs:
    zi = ''
    for i, z in enumerate(zhs[:8]):
        t = escape(z.get('t',''))[:42]
        uu = z.get('u','#')
        zi += '<div class="nc" onclick="window.open(\''+uu+'\',\'_blank\',\'noopener,noreferrer\')"><span class="ni" style="background:#0066ff">'+str(i+1)+'</span><span class="nn">'+t+'</span><span class="ns">知乎</span></div>'
    zh_html = '<div class="se" id="gzhihu"><div class="sh"><span class="st">&#128172; 知乎热榜</span><span class="sc">'+str(len(zhs))+'条</span></div>'+zi+'</div>'

fx_html = ''  # 不再单独显示汇率

# 热卖榜
shop_html = ''
if shop_items:
    shop_inner = ''
    for i, item in enumerate(shop_items[:15]):
        nn = escape(item.get('t',''))[:45]
        s = escape(item.get('src','热议'))
        uu = item.get('u','#')
        shop_inner += '<div class="nc" onclick="window.open(\''+uu+'\',\'_blank\',\'noopener,noreferrer\')"><span class="ni" style="background:#f97316">'+str(i+1)+'</span><span class="nn">'+nn+'</span><span class="ns">'+s+'</span></div>'
    shop_html = '<div class="se" id="gshop"><div class="sh"><span class="st">📋 热议话题</span><span class="sc">'+str(len(shop_items))+'条</span></div>'+shop_inner+'</div>'

body = ''
body += '<header>'
body += '<div class="top"><span class="tl">📊 每日价值资讯</span><span class="live"></span></div>'
body += '<div class="sub"><span>'+dc+'</span><span class="gr">'+period_desc+'</span><span>'+str(total)+'条 · '+str(len(srcs))+'源</span></div>'
body += wh + '<nav>'+nav+'</nav></header>'
# 平台流量排名行
rank_html = ''
if ranks:
    rank_inner = ''
    for r in ranks[:13]:
        n = r.get('name','')
        rk = r.get('rank',0)
        if n and rk:
            rank_inner += '<div class="ri"><span class="rn">'+n+'</span><span class="rv">#'+str(rk)+'</span></div>'
    if rank_inner:
        rank_html = '<div class="se"><div class="sh"><span class="st">📊 平台访问量排名</span><span class="sc">Tranco全球</span></div><div class="rg">'+rank_inner+'</div></div>'

body += market_html + metal_html + vol_html + q_html + gh_html + rank_html + shop_html + zh_html
body += hl_html + hw_html + news_html
body += '<div class="se"><div class="sh"><span class="st">📡 来源</span><span class="sc">'+str(len(srcs))+'个</span></div><div class="srcs">'+src_html+'</div></div>'
body += '<footer>📊 每2小时更新 · 工作 · 投资 · 学习 · 生活</footer>'
body += '<div id="bt" onclick="window.scrollTo({top:0,behavior:\'smooth\'})">↑</div>'

script = '<script>var bt=document.getElementById("bt");window.addEventListener("scroll",function(){bt.style.opacity=window.scrollY>200?1:0});document.querySelectorAll("nav a").forEach(function(a){a.addEventListener("click",function(e){e.preventDefault();var t=document.querySelector(this.getAttribute("href"));t&&t.scrollIntoView({behavior:"smooth",block:"start"})})});var ti=0,tt=["📊 每日价值资讯","📰 '+str(total)+'条","🔍 '+str(len(srcs))+'源"];setInterval(function(){document.title=tt[ti%3];ti++},4000);</script>'

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
.fg,.rg{display:grid;grid-template-columns:1fr 1fr;gap:2px}
.fi{display:flex;justify-content:space-between;background:rgba(255,255,255,0.006);border-radius:3px;padding:2px 6px;font-size:10px}
.fv{font-weight:600}
.ri{display:flex;justify-content:space-between;background:rgba(255,255,255,0.006);border-radius:3px;padding:2px 6px;font-size:10px}
.rn{color:#6b7a8d}
.rv{font-weight:600;color:#818cf8}
.vi{display:flex;gap:2px;background:rgba(255,255,255,0.006);border-radius:3px;padding:2px 6px;font-size:9px;align-items:center}
.vr{color:#4a5a6d;min-width:10px;text-align:center}
.vn{flex:1;font-weight:500}
.vp{min-width:40px;text-align:right}
.vc{min-width:42px;text-align:right}
.vv{color:#3d4a5d;min-width:35px;text-align:right}
.qi{display:flex;gap:2px;background:rgba(255,255,255,0.006);border-radius:3px;padding:3px 6px;font-size:9px;align-items:center;cursor:pointer}
.qi:last-child{border-bottom:none}
.qr{color:#4a5a6d;min-width:10px;text-align:center}
.qn{flex:1;font-weight:500}
.qch{min-width:44px;text-align:right;font-weight:600}
.qpe{color:#3d4a5d;min-width:34px;text-align:right}
.qsc{color:#818cf8;min-width:22px;text-align:right;font-weight:600}
.tgs{display:flex;flex-wrap:wrap;gap:3px;padding:1px 0 3px}
.tg{background:rgba(99,102,241,0.04);color:#818cf8;padding:1px 6px;border-radius:8px;font-size:9px;font-weight:500}
.srcs{font-size:8px;color:#3d4a5d;line-height:1.5;padding:1px 0}
footer{padding:8px 0;text-align:center;font-size:8px;color:#2a3045}
#bt{position:fixed;bottom:50px;right:10px;width:26px;height:26px;border-radius:50%;background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.1);color:#818cf8;font-size:12px;cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:50;opacity:0;transition:opacity .3s}
@media(max-width:480px){.sg,.fg{grid-template-columns:1fr}.tl{font-size:16px}}
'''

html = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">\n<meta http-equiv=Content-Security-Policy content=\"default-src &#39;self&#39;; style-src &#39;unsafe-inline&#39; &#39;self&#39;; script-src &#39;unsafe-inline&#39; &#39;self&#39;; img-src &#39;self&#39; data: https:; connect-src &#39;self&#39;; frame-src &#39;none&#39;; object-src &#39;none&#39;\">\n<title>📊 每日价值资讯</title>\n<style>\n'+css+'</style>\n</head>\n<body>\n<div class="app">\n'+body+'\n</div>\n'+script+'\n</body>\n</html>'

os.makedirs('_site', exist_ok=True)
with open('_site/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('DONE: %d news, %d sources, %d bytes' % (total, len(srcs), len(html)))
