#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, datetime

# Load Python data
with open('news_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

all_news = []
src_count = {}
sources_data = data.get('news', [])
labels = data.get('labels', [])

total_news = 0
active_sources = set()

for idx, items in enumerate(sources_data):
    if not items or not isinstance(items, list):
        continue
    for item in items:
        if 't' in item or 'title' in item:
            entry = {
                't': item.get('t', item.get('title', ''))[:55],
                's': item.get('s', '资讯'),
                'src': item.get('src', labels[idx] if idx < len(labels) else str(idx)),
                'u': item.get('u', '#')
            }
            all_news.append(entry)
            active_sources.add(entry['src'])
    src_label = labels[idx] if idx < len(labels) else str(idx)
    if items:
        src_count[src_label] = len(items)
        total_news += len(items)

total = len(all_news)
active_count = len(active_sources)

# Classify
keywords = {
    '国际': '美国|特朗普|拜登|欧盟|北约|联合国|俄罗斯|乌克兰|伊朗|以色列|巴勒斯坦|中东|亚洲|欧洲|非洲|美洲|全球|国际|外交|制裁|关税|WTO|G7|G20|贸易战|地缘|冲突|战争|和平|难民|核武器|导弹|战机|军舰|大使|领事|访问|峰会|谈判|协议|退出|加入|世卫|气候|巴黎协定|人权',
    '科技': 'AI|人工智能|芯片|半导体|华为|苹果|微软|谷歌|Meta|特斯拉|SpaceX|5G|6G|量子|算法|大模型|GPT|LLM|机器人|自动驾驶|云计算|区块链|NFT|元宇宙|VR|AR|激光雷达|传感器|操作系统|手机|iPhone|高通|英伟达|AMD|英特尔|台积电|三星|小米|OPPO|vivo|荣耀|蔚来|小鹏|理想|比亚迪|互联网|软件|数据|安全|黑客|漏洞|专利|创新|科技',
    '体育': '金牌|银牌|铜牌|奥运|亚运|世界杯|欧冠|NBA|CBA|中超|英超|西甲|意甲|德甲|法甲|网球|F1|电竞|运动员|教练|选手|冠军|决赛|半决赛|资格赛|预选赛|世锦赛|马拉松|游泳|田径|体操|跳水|举重|乒乓球|羽毛球|足球|篮球|排球|中国足球|国足|联赛|赛事|竞技|球队|主场|客场',
    '文娱': '电影|票房|音乐|演唱会|综艺|游戏|明星|导演|电视剧|Netflix|迪士尼|B站|抖音|快手|舞台|广告|视频|直播|演出',
    '健康': '疫情|疫苗|新冠|病毒|疾病|诊断|治疗|患者|医院|医生|手术|药物|药品|药监|FDA|临床|疫苗|传染病|癌症|糖尿病|高血压|心脏|大脑|基因|干细胞|中医|中药|营养|健身|食品|安全|污染|环境',
    'A股民生': 'A股|上证|深证|创业板|科创板|北交所|股市|股票|基金|理财|保险|银行|利率|降息|加息|存款|贷款|住房|公积金|房贷|房价|地产|土地|税收|个税|财政|发改委|央企|国企|GDP|CPI|PPI|涨幅|跌幅|沪深|千亿|亿|万亿|证监会|交易所',
    '财经': '美股|标普|纳斯达克|道指|期货|黄金|原油|大宗商品|数字货币|比特币|区块链|交易所|IPO|上市|融资|投资|资本|私募|风投|资产|估值|财报|营收|利润|市值|分红|回购|经济|消费|通胀|通缩|美联储|央行'
}

cat_order = ['国际', '科技', 'A股民生', '财经', '体育', '文娱', '健康']

classified = {c: [] for c in cat_order}
other = []
used = set()

for item in all_news:
    tt = item['t'].lower()
    placed = False
    for cat, kws in keywords.items():
        for kw in kws.split('|'):
            kw = kw.strip().lower()
            if kw and kw in tt:
                classified[cat].append(item)
                used.add(id(item))
                placed = True
                break
        if placed:
            break
    if not placed:
        other.append(item)

if other:
    classified['其他'] = other

# Build date
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
date_str = f'{now.year}年{now.month}月{now.day}日 {weekday_names[now.weekday()]}'

# Stock data
stocks = data.get('stocks', [])
stock_rows = ''
if stocks:
    for s in stocks:
        n = s.get('n', '--')
        v = s.get('v', '--')
        c = s.get('c', '--')
        cls = s.get('cls', '')
        stock_rows += f'<tr><td>{n}</td><td class="{cls}">{v}</td><td class="{cls}">{c}</td></tr>\n'
if not stock_rows:
    stock_rows = '<tr><td colspan="3">暂无数据</td></tr>'

# Forex data
forex = data.get('forex', {})
if not forex:
    forex = {'USD': '7.2420', 'EUR': '7.8321', 'JPY': '0.0450', 'GBP': '9.1250', 'HKD': '0.9280', 'KRW': '0.0052'}
fx_names = {'USD': '美元', 'EUR': '欧元', 'JPY': '日元', 'GBP': '英镑', 'HKD': '港币', 'KRW': '韩元'}
fx_rows = ''
for k in ['USD', 'EUR', 'JPY', 'GBP', 'HKD', 'KRW']:
    if k in forex:
        fx_rows += f'<tr><td>{fx_names[k]}({k})</td><td>{forex[k]}</td><td>1 CNY</td></tr>\n'

# Source label
label_text = ' · '.join(labels[:40])

# Build news cards
cat_icons = {'国际': '\U0001f30d', '科技': '\U0001f50c', 'A股民生': '\U0001f4c8', '财经': '\U0001f4b0', '体育': '\u26bd', '文娱': '\U0001f3ac', '健康': '\u2764\ufe0f', '其他': '\U0001f4c5'}
cat_colors = {'国际': '#e74c3c', '科技': '#3498db', 'A股民生': '#e67e22', '财经': '#1abc9c', '体育': '#2ecc71', '文娱': '#9b59b6', '健康': '#e91e63', '其他': '#95a5a6'}

news_html = ''
for cat in cat_order:
    items = classified.get(cat, []) + (classified.get('其他', []) if cat == '其他' else [])
    if cat != '其他' and not classified.get(cat):
        continue
    if not items:
        continue
    icon = cat_icons.get(cat, '\U0001f4c5')
    bg = cat_colors.get(cat, '#95a5a6')
    cards_html = ''
    for item in items:
        t = item['t'][:55]
        s = item['s']
        src = item['src']
        u = item['u']
        src_badge = f'<span class="src">{src}</span>' if src in labels else ''
        cards_html += f'<a href="{u}" class="news-card" target="_blank" rel="noopener">{src_badge}<span class="title">{t}</span><span class="source">{s}</span></a>\n'
    news_html += f'<div class="section"><h2 style="border-left:4px solid {bg};padding-left:12px">{icon} {cat} <span class="badge">{len(items)}</span></h2><div class="news-grid">\n{cards_html}</div></div>\n'

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>\U0001f30d 每日全球资讯</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#0d1117;color:#e6edf3;line-height:1.6;min-height:100vh}}
.container{{max-width:1200px;margin:0 auto;padding:16px 12px}}
h1{{font-size:1.5em;margin:16px 0 8px;background:linear-gradient(135deg,#58a6ff,#bc8cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.subtitle{{color:#8b949e;font-size:0.85em;margin-bottom:16px;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:baseline}}
.subtitle .labels{{font-size:0.78em;color:#58a6ff;width:100%;line-height:1.8}}
.badge{{display:inline-block;background:#30363d;color:#e6edf3;border-radius:10px;padding:0 8px;font-size:0.7em;vertical-align:middle;font-weight:400;margin-left:6px}}
.section{{margin-bottom:20px}}
.section h2{{font-size:1.05em;margin-bottom:8px;display:flex;align-items:center}}
.news-grid{{display:grid;grid-template-columns:1fr;gap:6px}}
@media(min-width:640px){{.news-grid{{grid-template-columns:1fr 1fr}}}}
.news-card{{display:flex;flex-direction:column;padding:8px 10px;background:#161b22;border:1px solid #30363d;border-radius:6px;text-decoration:none;color:#e6edf3;transition:all 0.2s}}
.news-card:hover{{background:#1c2128;border-color:#58a6ff;transform:translateX(2px)}}
.news-card .title{{font-size:0.88em;line-height:1.4;margin-bottom:4px}}
.news-card .source{{font-size:0.74em;color:#8b949e}}
.news-card .src{{display:inline-block;font-size:0.65em;background:#1f6feb33;color:#58a6ff;padding:1px 6px;border-radius:3px;margin-bottom:3px;align-self:flex-start}}
.stocks-section{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin-bottom:20px}}
.stocks-section h3{{font-size:0.95em;margin-bottom:8px;color:#7ee787}}
table{{width:100%;border-collapse:collapse;font-size:0.84em}}
th,td{{text-align:left;padding:5px 8px;border-bottom:1px solid #30363d}}
th{{color:#8b949e;font-weight:400;font-size:0.8em}}
.up{{color:#3fb950;font-weight:500}}
.down{{color:#f85149;font-weight:500}}
footer{{text-align:center;color:#484f58;font-size:0.75em;padding:24px 0 12px;border-top:1px solid #21262d;margin-top:16px}}
a{{color:#58a6ff;text-decoration:none}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}}
@media(max-width:480px){{.grid-2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="container">
<h1>\U0001f30d 每日全球资讯</h1>
<div class="subtitle">
<span>{date_str}</span>
<span style="color:#8b949e;background:#21262d;padding:0 8px;border-radius:4px;font-size:0.8em">{total}条 &middot; {active_count}个来源</span>
<span class="labels">{label_text}</span>
</div>
<div class="grid-2">
<div class="stocks-section"><h3>\U0001f4ca 行情</h3><table><thead><tr><th>指数</th><th>最新</th><th>涨跌幅</th></tr></thead><tbody>
{stock_rows}</tbody></table></div>
<div class="stocks-section"><h3>\U0001f4b1 汇率(1 CNY)</h3><table><thead><tr><th>货币</th><th>汇率</th><th>基准</th></tr></thead><tbody>
{fx_rows}</tbody></table></div>
</div>
{news_html}
<footer>数据来源: 同花顺/华尔街见闻/财联社/第一财经/百度/新浪/新华/人民/央视/凤凰/网易/澎湃/36氪/IT之家/B站/微博/京东/抖音/网易云音乐/什么值得买等 &middot; 每日自动更新 &middot; {date_str.split(" ")[0]}</footer>
</div>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'=== 完成: {total}条 · {active_count}个来源 ===')
print(f'写入: index.html ({len(html)} bytes)')
