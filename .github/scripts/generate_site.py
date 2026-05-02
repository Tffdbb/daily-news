#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
labels = data.get('labels', [])

for idx, items in enumerate(sources_data):
    if not items or not isinstance(items, list):
        continue
    for item in items:
        t = (item.get('t') or item.get('title') or '').strip()[:60]
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
    '国际': '美国|特朗普|拜登|欧盟|北约|联合国|俄罗斯|乌克兰|伊朗|以色列|巴勒斯坦|中东|亚洲|欧洲|非洲|美洲|全球|国际|外交|制裁|关税|WTO|G7|G20|贸易战|地缘|冲突|战争|和平|难民|核武器|导弹|战机|军舰|大使|领事|访问|峰会|谈判|协议|退出|世卫|气候|巴黎协定|人权|海外',
    '科技': 'AI|人工智能|芯片|半导体|华为|苹果|微软|谷歌|Meta|特斯拉|SpaceX|5G|6G|量子|算法|大模型|GPT|LLM|机器人|自动驾驶|云计算|区块链|NFT|元宇宙|VR|AR|激光雷达|传感器|操作系统|手机|iPhone|高通|英伟达|AMD|英特尔|台积电|三星|OPPO|vivo|荣耀|蔚来|小鹏|理想|比亚迪|互联网|软件|数据|安全|黑客|漏洞|专利|创新|科技',
    'A股民生': 'A股|上证|深证|创业板|科创板|北交所|股市|股票|基金|理财|保险|银行|利率|降息|加息|存款|贷款|住房|公积金|房贷|房价|地产|土地|税收|个税|财政|发改委|央企|国企|GDP|CPI|PPI|涨幅|跌幅|沪深|千亿|亿|万亿|证监会|交易所|募集|涨停|跌停',
    '财经': '美股|标普|纳斯达克|道指|期货|黄金|原油|大宗商品|数字货币|比特币|区块链|交易所|IPO|上市|融资|投资|资本|私募|风投|资产|估值|财报|营收|利润|市值|分红|回购|经济|消费|通胀|通缩|美联储|央行|美元|欧元|日元|英镑',
    '体育': '金牌|银牌|铜牌|奥运|亚运|世界杯|欧冠|NBA|CBA|中超|英超|西甲|意甲|德甲|法甲|网球|F1|电竞|运动员|教练|选手|冠军|决赛|半决赛|资格赛|世锦赛|马拉松|游泳|田径|体操|跳水|举重|乒乓球|羽毛球|足球|篮球|排球|中国足球|国足|联赛|赛事|竞技|球队|主场|客场',
    '文娱': '电影|票房|音乐|演唱会|综艺|游戏|明星|导演|电视剧|Netflix|迪士尼|B站|抖音|快手|舞台|广告|视频|直播|演出|娱乐|微博|热搜|热门',
    '健康': '疫情|疫苗|新冠|病毒|疾病|诊断|治疗|患者|医院|医生|手术|药物|药品|药监|FDA|临床|传染病|癌症|糖尿病|高血压|心脏|大脑|基因|干细胞|中医|中药|营养|健身|食品|安全|污染|环境'
}
cat_order = ['国际', '科技', 'A股民生', '财经', '体育', '文娱', '健康']
cat_icons = {'国际': '🌍', '科技': '🔬', 'A股民生': '📊', '财经': '💰', '体育': '⚽', '文娱': '🎬', '健康': '❤️', '其他': '📌'}
cat_colors = {'国际': '#3b82f6', '科技': '#8b5cf6', 'A股民生': '#f59e0b', '财经': '#10b981', '体育': '#22c55e', '文娱': '#ec4899', '健康': '#ef4444'}
cat_short = {'国际': 'guoji', '科技': 'keji', 'A股民生': 'agu', '财经': 'caijing', '体育': 'tiyu', '文娱': 'wenyu', '健康': 'jiankang'}

def get_importance(title):
    hk = ['重磅','突发','紧急','大跌','暴涨','宣布','发布','警告','协议','制裁','战争','冲突','崩盘','熔断']
    sc = sum(1 for k in hk if k in title)
    return ('🔥 重磅' if sc >= 2 else '⚡ 关注' if sc >= 1 else None)

def guess_summary(title):
    """从标题自然语言提取一句话精要"""
    t = title.strip()
    if len(t) <= 20:
        return ''
    prefix_removed = re.sub(r'^(快讯|消息|独家|重磅|突发|最新|实录|公告|解读|评论|周报|早报|晚报|早知道|盘前|盘中|盘后|收评|午评|早盘)：?\s*', '', t)
    nums = re.findall(r'[\d,.]+%?|千亿|万亿|亿|万', prefix_removed[:30])
    entities = re.findall('^[\u4e00-\u9fff]{2,4}', prefix_removed)
    verbs = re.findall(r'(宣布|发布|启动|推出|达成|签署|裁定|通过|批准|否决|调查|起诉|警告|制裁|呼吁|称|表示|指出|强调|要求|禁止|限制)', prefix_removed)
    parts = []
    if entities and len(entities[0]) >= 2:
        parts.append(entities[0])
    if nums:
        parts.append(' '.join(nums[:2]))
    if verbs:
        parts.append(verbs[0].replace('称','').replace('表示','').replace('指出','') or '')
    s = ' · '.join(p for p in parts if p)[:40]
    return s

def extract_entities(title):
    """从标题提取实体标签：公司/国家/人名/概念"""
    entities = []
    # 知名公司/组织
    companies = ['苹果','华为','微软','谷歌','Meta','特斯拉','阿里','腾讯','字节','百度','亚马逊','台积电','三星','小米','比亚迪','美团','京东','拼多多','宁德时代','中芯','OPPO','vivo','蔚来','小鹏','理想','OpenAI','SpaceX','英伟达','AMD','英特尔','高通','联邦','NASA','欧佩克','OPEC','IMF','世行']
    countries = ['中国','美国','俄罗斯','欧盟','英国','日本','德国','法国','印度','巴西','韩国','澳大利亚','以色列','伊朗','乌克兰','沙特','土耳其']
    # 提取
    for co in companies:
        if co in title: entities.append(co)
    for ct in countries:
        if ct in title: entities.append(ct)
    # 提取数字相关（百分比、金额等）
    money = re.findall(r'[千万亿]?[美欧日]?[元美元欧元日圆]|[\d,.]+亿|\d+[万亿]', title)
    if money: entities.append(money[0][:8])
    return list(set(entities))[:3]

def calc_hot_score(item, all_items):
    t = item['t']
    sc = 10 + (2 if len(t)<20 else 0) + (3 if re.search(r'\d',t) else 0) + (5 if '！' in t or '!' in t else 0)
    imp = get_importance(t)
    if imp == '🔥 重磅': sc += 10
    elif imp == '⚡ 关注': sc += 5
    if item['src'] in ['同花顺','华尔街见闻','财联社']: sc += 2
    return round(sc, 1)

# ── 分类 ──
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

# ── 行情 ──
stocks = data.get('stocks', [])
stock_rows = ''.join(
    f'<div class="si2"><span class="sn">{escape(s.get("n","--"))}</span>'
    f'<span class="sv">{escape(s.get("v","--"))}</span>'
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
    import urllib.request, ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    w = urllib.request.urlopen(urllib.request.Request('https://wttr.in/Beijing?format=j1&lang=zh', headers={'User-Agent':'curl/8.0'}), timeout=5, context=ctx)
    j = json.loads(w.read().decode('utf-8'))
    cc = j.get('current_condition',[{}])[0]
    tm, de, wi, hu = cc.get('temp_C','--'), cc.get('weatherDesc',[{}])[0].get('value','--'), cc.get('windspeedKmph','--'), cc.get('humidity','--')
    we = '☀️' if '晴' in de else '⛅' if '云' in de else '🌧️' if '雨' in de else '❄️' if '雪' in de else '🌫️' if '雾' in de else '🌤️'
    weather_html = f'<div class="se" id="weather"><div class="sh"><span class="si">🌤️</span><span class="st">北京天气</span></div><div class="weather-main"><span class="weather-icon">{we}</span><span class="weather-temp">{tm}°</span><span class="weather-desc">{de}</span><span class="weather-meta">💨{wi}km/h 💧{hu}%</span></div></div>'
except:
    pass

# ── 热词 ──
wf = {}
for m in re.finditer('[\u4e00-\u9fff]{2,5}', ' '.join(n['t'] for n in all_news)):
    w = m.group()
    if w not in ('报道','新闻','今日','中国','美国','市场','公司','发布','最新','可能','一个','进行','表示','以及','提到'):
        wf[w] = wf.get(w,0)+1
hw = sorted(wf.items(), key=lambda x:-x[1])[:15]
tags_html = ''.join(f'<span class="tag" style="font-size:{(10+min(c,10)*0.6):.0f}px">{escape(w)}<sup>{c}</sup></span>' for w,c in hw)

# ── 来源分布 ──
all_srcs = ['同花顺','华尔街见闻','财联社','第一财经','网易','新浪财经','新华网','人民网','中国新闻网','央视新闻','凤凰网','财新网','每经','证券时报','中证报','IT之家','百度','澎湃新闻','36氪','Donews','新浪体育','虎嗅','人民健康','今日头条','东方财富','雪球','环球网','观察者网','新浪娱乐','网易体育','B站热门','微博热搜','京东','抖音','网易云音乐','什么值得买']
src_stats = [(s, sum(1 for n in all_news if n['src']==s)) for s in all_srcs if sum(1 for n in all_news if n['src']==s)>0]
src_stats.sort(key=lambda x:-x[1])
mc = max(s[1] for s in src_stats) if src_stats else 1
cp = ['#3b82f6','#8b5cf6','#ec4899','#f59e0b','#22c55e','#10b981','#ef4444','#06b6d4','#84cc16','#e11d48','#14b8a6','#6366f1']
src_bars_html = ''.join(f'<div class="src-bar" style="animation-delay:{i*0.05}s"><div class="src-bar-label">{escape(s)}</div><div class="src-bar-track"><div class="src-bar-fill" style="width:{c/mc*100:.0f}%;background:{cp[i%len(cp)]}"></div></div><div class="src-bar-num">{c}</div></div>\n' for i,(s,c) in enumerate(src_stats))
src_list_html = ' · '.join(escape(s) for s in active_srcs)

# ── 导航 ──
nav_html = ''.join(f'<a href="#cat-{cat_short.get(n,n)}">{n}</a>\n' for n in ['国际','科技','A股','财经','体育','文娱','健康'])

# ── 热点新闻 ──
all_hot = sorted([(calc_hot_score(n,all_news),n) for n in all_news], key=lambda x:-x[0])
hot_picks = [n for _,n in all_hot[:6]]
hot_section = ''
if hot_picks:
    hi = ''.join(f'<div class="hc" onclick="window.open(\'{n["u"]}\',\'_blank\')"><span class="hn">{get_importance(n["t"]) or "🔥"}</span><span class="ht">{escape(n["t"])}</span><span class="hs">{escape(n["src"])}</span></div>\n' for n in hot_picks)
    hot_section = f'<div class="se" id="hot"><div class="sh"><span class="si">🔥</span><span class="st">热门速览</span><span class="sc">{len(hot_picks)}</span></div><div class="hot-grid">{hi}</div></div>'

# ── 分类新闻 ──
news_html = ''
for cat in cat_order:
    items = classified.get(cat,[])
    if cat!='其他' and not items:
        continue
    if not items:
        continue
    icon, bg, cid = cat_icons.get(cat,'📌'), cat_colors.get(cat,'#6b7280'), cat_short.get(cat,cat)
    hi = ''
    for i,item in enumerate(items):
        imp = get_importance(item['t'])
        tag = f'<span class="imp {imp.split()[0]}" style="display:{"inline" if imp else "none"}">{imp.split()[0]}</span>' if imp else ''
        sm = guess_summary(escape(item['t']))
        sm_html = f'<div class="nsm">{sm}</div>' if sm else ''
        ent = extract_entities(item['t'])
        ent_html = ''.join(f'<span class="et">{escape(e)}</span>' for e in ent) if ent else ''
        hi += f'<div class="nc" onclick="window.open(\'{item["u"]}\',\'_blank\')"><div class="nt"><span class="ni" style="background:{bg}">{i+1}</span>{tag}<span class="nn">{escape(item["t"])}</span></div>{sm_html}<div class="nm"><span class="ns" style="color:{bg}">●</span> {escape(item["src"])} {ent_html}</div></div>\n'
    news_html += f'<div class="se" id="cat-{cid}"><div class="sh"><span class="si">{icon}</span><span class="st">{cat}</span><span class="sc">{len(items)}</span></div>{hi}</div>\n'

# ── HTML 模板（用简单 replace 替换） ──
HTML_TPL = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>🌍 每日全球资讯</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#080b14;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;overflow-x:hidden;min-height:100vh}
.app{max-width:760px;margin:0 auto;padding:0 14px 40px}
header{padding:16px 0 8px;margin-bottom:10px;position:sticky;top:0;background:rgba(8,11,20,0.88);z-index:10;backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid rgba(42,48,69,0.15)}
.tb{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.title{font-size:22px;font-weight:700;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;background-size:200%200%}
.date{font-size:12px;color:#5a6a7d;margin-bottom:2px;display:flex;gap:6px;align-items:center}
.greeting{color:#22c55e;font-weight:500;font-size:12px}
.live{display:inline-flex;align-items:center;gap:4px;background:rgba(239,68,68,0.06);color:#ef4444;padding:2px 10px;border-radius:10px;font-size:10px}
.live-dot{width:5px;height:5px;background:#ef4444;border-radius:50%;display:inline-block;animation:pulse 1.5s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
.stats{display:flex;gap:8px;font-size:11px;color:#5a6a7d;margin-top:6px}
.stats span{background:rgba(255,255,255,0.02);padding:2px 10px;border-radius:6px}
.stats b{color:#e2e8f0;font-weight:600}
nav{display:flex;gap:4px;flex-wrap:wrap;margin-top:8px;overflow-x:auto;white-space:nowrap;padding-bottom:2px;scrollbar-width:none}
nav a{color:#6b7a8d;text-decoration:none;font-size:11px;padding:4px 14px;border-radius:14px;background:rgba(255,255,255,0.03);flex-shrink:0;transition:all .2s}
nav a:hover{background:rgba(59,130,246,0.1);color:#60a5fa}
.se{background:#0f1420;border:1px solid rgba(42,48,69,0.2);border-radius:12px;padding:12px 12px 6px;margin-bottom:10px;transition:all .2s;animation:fadeIn .3s ease-out}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.sh{display:flex;align-items:center;gap:8px;margin-bottom:6px;padding-bottom:6px;border-bottom:1px solid rgba(255,255,255,0.02)}
.si{font-size:16px;width:22px;text-align:center}.st{font-size:14px;font-weight:600;color:#f1f5f9;letter-spacing:.3px}
.sc{font-size:10px;background:rgba(99,102,241,0.08);color:#818cf8;padding:0 8px;border-radius:8px;line-height:18px;margin-left:auto}
.nc{padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.01);cursor:pointer;margin:0 -4px;padding:6px 4px;border-radius:6px;transition:all .15s}
.nc:last-child{border-bottom:none}.nc:hover{background:rgba(255,255,255,0.02);transform:translateX(2px)}
.nc:active{background:rgba(255,255,255,0.03);transform:scale(.98)}
.nt{font-size:13px;font-weight:500;color:#f1f5f9;margin-bottom:1px;display:flex;align-items:flex-start;gap:6px;line-height:1.4}
.ni{display:inline-flex;width:16px;height:16px;color:#fff;font-size:8px;font-weight:700;border-radius:3px;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px}
.nn{flex:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.nm{font-size:10px;color:#3d4a5d;padding-left:22px;display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.nsm{font-size:11px;color:#6b7a8d;padding-left:21px;margin:1px 0 2px;line-height:1.3;font-style:italic;border-left:2px solid rgba(59,130,246,0.15);padding-left:10px}
.et{display:inline-block;font-size:8px;background:rgba(99,102,241,0.06);color:#818cf8;padding:0 6px;border-radius:3px;line-height:14px;border:1px solid rgba(99,102,241,0.08);font-style:normal}
.ns{font-size:7px;margin-right:1px}
.hot-grid{display:flex;flex-direction:column;gap:3px}
.hc{display:flex;align-items:center;gap:6px;padding:6px 8px;border-radius:8px;cursor:pointer;transition:all .15s;background:rgba(255,255,255,0.008);border-left:2px solid rgba(239,68,68,0.3)}
.hc:hover{background:rgba(239,68,68,0.04);transform:translateX(2px)}
.hn{flex-shrink:0;font-size:12px}.ht{flex:1;font-size:13px;color:#f1f5f9;font-weight:500}
.hs{flex-shrink:0;font-size:9px;color:#4a5a6d;background:rgba(255,255,255,0.03);padding:2px 8px;border-radius:6px}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:4px}
.si2{display:flex;align-items:center;gap:6px;background:rgba(255,255,255,0.015);border-radius:6px;padding:6px 10px;position:relative;overflow:hidden}
.sn{font-size:10px;color:#6b7a8d;min-width:50px}.sv{font-size:12px;font-weight:600;color:#f1f5f9;margin-left:auto;font-variant-numeric:tabular-nums}
.sc2{font-size:11px;font-weight:500;min-width:50px;text-align:right}.up{color:#22c55e}.down{color:#ef4444}
.bar{height:3px;border-radius:2px;position:absolute;bottom:0;left:0;transition:width .5s}.bar.up{background:#22c55e;opacity:.3}.bar.down{background:#ef4444;opacity:.3}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:4px}
.fi{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,0.015);border-radius:5px;padding:5px 10px}
.fp{font-size:11px;color:#6b7a8d}.fr{font-size:12px;font-weight:600;color:#f1f5f9;font-variant-numeric:tabular-nums}
.tags{display:flex;flex-wrap:wrap;gap:5px;padding:2px 0 6px}
.tag{background:rgba(99,102,241,0.05);color:#818cf8;padding:2px 10px;border-radius:12px;display:inline-flex;align-items:center;gap:3px;font-weight:500;transition:all .2s}
.tag:hover{background:rgba(99,102,241,0.12);transform:scale(1.04);cursor:default}
.tag sup{font-size:9px;color:#4a5a6d}
.weather-main{display:flex;align-items:center;gap:8px;padding:2px 0 0}.weather-icon{font-size:28px}
.weather-temp{font-size:20px;font-weight:700;color:#f1f5f9}.weather-desc{font-size:13px;color:#5a6a7d}
.weather-meta{font-size:10px;color:#4a5a6d;margin-left:auto}
.src-section{margin-bottom:8px}
.src-bar{display:flex;align-items:center;gap:6px;margin-bottom:2px;animation:fadeOut .3s both}
@keyframes fadeOut{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:translateX(0)}}
.src-bar-label{width:72px;font-size:10px;color:#6b7a8d;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.src-bar-track{flex:1;height:5px;background:rgba(255,255,255,0.03);border-radius:3px;overflow:hidden}
.src-bar-fill{height:100%;border-radius:3px;transition:width .6s ease-out}
.src-bar-num{width:20px;font-size:10px;color:#6b7a8d;text-align:right}
.src-list{font-size:10px;color:#3d4a5d;line-height:1.5;padding:4px 0}
.bottom-nav{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}
.bottom-nav a{color:#5a6a7d;text-decoration:none;font-size:10px;padding:2px 10px;border-radius:10px;background:rgba(255,255,255,0.02)}
footer{margin-top:4px;padding:10px 0;text-align:center;border-top:1px solid rgba(42,48,69,0.15)}
footer p{font-size:9px;color:#3d4a5d;margin-bottom:1px}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1e293b;color:#f1f5f9;padding:8px 20px;border-radius:10px;font-size:12px;opacity:0;transition:opacity .3s;pointer-events:none;z-index:100;box-shadow:0 4px 20px rgba(0,0,0,.3)}
#backTop{position:fixed;bottom:70px;right:16px;width:36px;height:36px;border-radius:50%;background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);color:#818cf8;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:50;opacity:0;transition:opacity .3s}
@media(max-width:480px){.sg{grid-template-columns:1fr}.fg{grid-template-columns:1fr 1fr}.title{font-size:19px}}
</style>
</head>
<body>
<div class="app">
<header>
<div class="tb">
<span class="title"><span>🌍</span> 每日全球资讯</span>
<span class="live"><span class="live-dot"></span> LIVE</span>
</div>
<div class="date"><span>__DATE__</span><span class="greeting">__GREETING__</span></div>
<div class="stats"><span><b id="totalC">__TOTAL__</b> 条新闻</span><span><b id="srcC">__ACTIVE__</b> 个来源</span></div>
<nav>__NAV__</nav>
</header>

__HOT__

<div class="se" id="stocks"><div class="sh"><span class="si">📊</span><span class="st">行情速览</span></div><div class="sg">__STOCKS__</div></div>
<div class="se" id="forex"><div class="sh"><span class="si">💱</span><span class="st">汇率</span><span class="sc">1 CNY</span></div><div class="fg">__FOREX__</div></div>
__WEATHER__
<div class="se" id="tags"><div class="sh"><span class="si">🏷️</span><span class="st">今日热词</span></div><div class="tags">__TAGS__</div></div>

__NEWS__

<div class="se" id="sources"><div class="sh"><span class="si">📡</span><span class="st">来源分布</span><span class="sc">__SRC_COUNT__</span></div><div class="src-section">__SRCBARS__</div><div class="src-list">__SRCLIST__</div></div>

<footer>
<div class="bottom-nav">__NAV__</div>
<p>🌍 每日全球资讯 · 自动采集 · 智能分类</p>
</footer>
</div>
<div id="toast" class="toast"></div>
<div id="backTop" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</div>

<script>
(function(){
function anim(el,t,d){if(!el)return;var s=parseInt(el.textContent)||0,df=t-s,t0=performance.now();function f(ts){var p=Math.min((ts-t0)/d,1),v=Math.floor(s+df*p*(2-p));el.textContent=v;p<1&&requestAnimationFrame(f)}requestAnimationFrame(f)}
document.addEventListener('DOMContentLoaded',function(){anim(document.getElementById('totalC'),__TOTAL__,500);anim(document.getElementById('srcC'),__ACTIVE__,500)});
document.querySelectorAll('nav a,.bottom-nav a').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();var t=document.querySelector(this.getAttribute('href'));t&&t.scrollIntoView({behavior:'smooth',block:'start'})})});
window.addEventListener('scroll',function(){document.getElementById('backTop').style.opacity=window.scrollY>300?'1':'0'});
var ti=0,ttls=['🌍 每日全球资讯','📰 __TOTAL__条新闻','🔍 __ACTIVE__个来源'];
setInterval(function(){document.title=ttls[ti%ttls.length];ti++},4000);
document.addEventListener('visibilitychange',function(){document.hidden||(document.title='🌍 每日全球资讯',setTimeout(function(){ti=0},2000))});
})();
</script>
</body>
</html>'''

html = HTML_TPL.replace('__DATE__', date_cn).replace('__GREETING__', greeting)
html = html.replace('__TOTAL__', str(total)).replace('__ACTIVE__', str(active_count))
html = html.replace('__NAV__', nav_html).replace('__HOT__', hot_section)
html = html.replace('__STOCKS__', stock_rows).replace('__FOREX__', fx_rows)
html = html.replace('__WEATHER__', weather_html).replace('__TAGS__', tags_html)
html = html.replace('__NEWS__', news_html)
html = html.replace('__SRCBARS__', src_bars_html).replace('__SRCLIST__', src_list_html)
html = html.replace('__SRC_COUNT__', str(active_count))

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'=== 完成: {total}条 · {active_count}个来源 ===')
print(f'写入: index.html ({len(html)} bytes)')
