#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RSS采集器 - 国际新闻源 + 英文标题中文化"""
import json, subprocess, urllib.request, urllib.error, ssl, xml.etree.ElementTree as ET, re

def curl(url):
    try:
        r = subprocess.run(['timeout','10','curl','-sL',url,'-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','--connect-timeout','8','--max-time','9','-o','-','-w',''], capture_output=True, timeout=12, text=True)
        return r.stdout
    except: return ''

_CTX = ssl.create_default_context()
_CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
def fallback(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=10, context=_CTX)
        return r.read().decode('utf-8','replace')
    except: return ''

def f(url):
    h = curl(url)
    if len(h) < 100:
        h2 = fallback(url)
        if len(h2) > len(h): return h2
    return h

# === 简单英文标题→中文翻译（规则+字典） ===
TRANS = {
    'Trump': '特朗普', 'US': '美国', 'China': '中国', 'EU': '欧盟', 'UK': '英国',
    'Japan': '日本', 'Russia': '俄罗斯', 'Ukraine': '乌克兰', 'Israel': '以色列',
    'Iran': '伊朗', 'India': '印度', 'Korea': '韩国', 'North Korea': '朝鲜',
    'Taiwan': '台湾', 'Hong Kong': '香港', 'Australia': '澳大利亚', 'Germany': '德国',
    'France': '法国', 'Italy': '意大利', 'Canada': '加拿大', 'Vietnam': '越南',
    'Biden': '拜登', 'Xi': '习近平', 'Putin': '普京', 'Zelensky': '泽连斯基',
    'Market': '市场', 'Stock': '股票', 'Stocks': '股市', 'Oil': '原油', 'Gold': '黄金',
    'Bitcoin': '比特币', 'Crypto': '加密货币', 'AI': 'AI', 'Technology': '科技',
    'Economy': '经济', 'Trade': '贸易', 'Tariff': '关税', 'Sanctions': '制裁',
    'War': '战争', 'Peace': '和平', 'Nuclear': '核', 'Military': '军事',
    'Bank': '银行', 'Fed': '美联储', 'Central Bank': '央行', 'Rate': '利率',
    'Inflation': '通胀', 'GDP': 'GDP', 'Jobs': '就业', 'Unemployment': '失业',
    'Election': '大选', 'Vote': '投票', 'Congress': '国会', 'Senate': '参议院',
    'Climate': '气候', 'Energy': '能源', 'Green': '绿色', 'Electric': '电力/电动',
    'Apple': '苹果', 'Google': '谷歌', 'Meta': 'Meta', 'Microsoft': '微软',
    'Amazon': '亚马逊', 'Tesla': '特斯拉', 'Nvidia': '英伟达', 'Samsung': '三星',
    'Huawei': '华为', 'TikTok': 'TikTok', 'Twitter': '推特', 'X': 'X平台',
    'iPhone': 'iPhone', 'iPad': 'iPad', 'Chip': '芯片', 'Semiconductor': '半导体',
    'IPO': 'IPO', 'Merger': '并购', 'Acquisition': '收购', 'Layoff': '裁员',
    'Brexit': '英国脱欧', 'OPEC': 'OPEC', 'WTO': 'WTO', 'UN': '联合国',
    'World': '全球', 'Global': '全球', 'International': '国际', 'Domestic': '国内',
    'Report': '报告', 'Analysis': '分析', 'Survey': '调查', 'Study': '研究',
    'New': '新', 'First': '首个', 'Biggest': '最大', 'Largest': '最大',
    'Record': '创纪录', 'Crisis': '危机', 'Protest': '抗议', 'Attack': '袭击',
    'Deal': '交易', 'Plan': '计划', 'Launch': '发布', 'Release': '发布',
    'Says': '称', 'Said': '表示', 'Reported': '报道', 'Announced': '宣布',
    'Expected': '预计', 'Planned': '计划', 'Proposed': '提议',
    'to': '至', 'and': '与', 'of': '的', 'in': '在',
    'Wall Street': '华尔街', 'Silicon Valley': '硅谷', 'White House': '白宫',
    'Congress': '国会', 'Supreme Court': '最高法院', 'Pentagon': '五角大楼',
    'China': '中国', 'Chinese': '中国', 'Beijing': '北京', 'Washington': '华盛顿',
    'Moscow': '莫斯科', 'Tokyo': '东京', 'London': '伦敦', 'Paris': '巴黎',
    # 交易/经济类动词
    'slump': '暴跌', 'surge': '暴涨', 'plunge': '大跌', 'rally': '大涨',
    'gain': '上涨', 'rise': '上涨', 'fall': '下跌', 'drop': '下跌',
    'climb': '攀升', 'decline': '下滑', 'rebound': '反弹', 'recover': '复苏',
    'boost': '提振', 'hit': '冲击', 'hurt': '损害', 'benefit': '受益',
    'warn': '警告', 'urge': '敦促', 'call for': '呼吁',
    'Red Sea': '红海', 'Gaza': '加沙', 'Ukraine war': '乌克兰战争',
}

def simple_translate(text):
    """中文化英文章标题"""
    if not re.search('[a-zA-Z]', text):
        return text  # 已经是中文
    
    result = text
    
    # 先处理多词短语（长优先）
    for eng in sorted(TRANS.keys(), key=len, reverse=True):
        if eng in result and TRANS[eng] not in result:
            result = result.replace(eng, TRANS[eng])
    
    # 去掉URL/标签等
    result = re.sub(r'https?://\S+', '', result)
    result = re.sub(r'#\w+', '', result)
    result = re.sub(r'@\w+', '', result)
    result = result.strip()
    
    # 如果还是纯英文，加"[英]"前缀提示
    if re.match('^[A-Za-z0-9 .,:;!?\'\"]+$', result):
        result = '[英] ' + result[:40]
    
    return result

def parse_rss(xml_text, src, max_items=6):
    items = []
    if not xml_text.strip(): return items
    try:
        root = ET.fromstring(xml_text)
        for entry in root.iter('item'):
            titles = entry.find('title')
            links = entry.find('link')
            t = (titles.text or '').strip() if titles is not None else ''
            u = (links.text or '').strip() if links is not None else ''
            if not t or len(t) < 8: continue
            t = re.sub(r'<[^>]+>', '', t)
            t = simple_translate(t)
            if t[:6] not in [x[:6] for x in [y['t'] for y in items]]:
                items.append({'t':t, 'u':u, 'src':src})
        if not items:
            for entry in root.iter('entry'):
                titles = entry.find('title')
                links = entry.find('link')
                t = (titles.text or '').strip() if titles is not None else ''
                u = (links.get('href') or '') if links is not None else ''
                if not t or len(t) < 8: continue
                t = re.sub(r'<[^>]+>', '', t)
                t = simple_translate(t)
                if t[:6] not in [x[:6] for x in [y['t'] for y in items]]:
                    items.append({'t':t, 'u':u, 'src':src})
    except: pass
    
    # 过滤英文残留（标题里不能超过40%英文字母）
    filtered = []
    for item in items:
        t = item['t']
        eng_ratio = sum(1 for c in t if c.isascii() and c.isalpha()) / max(len(t), 1)
        if eng_ratio > 0.6:
            # 英文太多，压缩
            item['t'] = item['t'][:35] + '...'
        filtered.append(item)
    
    return filtered[:max_items]

def collect():
    all_news = []
    sources = {
        'BBC': 'https://feeds.bbci.co.uk/news/rss.xml',
        'Reuters': 'https://www.reutersagency.com/feed/',
        'Guardian': 'https://www.theguardian.com/world/rss',
        'NYT': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
        'TechCrunch': 'https://techcrunch.com/feed/',
        'Hacker News': 'https://hnrss.org/frontpage',
        'The Verge': 'https://www.theverge.com/rss/index.xml',
    }
    for name, url in sources.items():
        html = f(url)
        items = parse_rss(html, name, 5)
        print(f'  {name}: {len(items)} items')
        all_news.extend(items)
    return all_news

if __name__ == '__main__':
    news = collect()
    with open('rss_news.json', 'w', encoding='utf-8') as f:
        json.dump({'rss': news}, f, ensure_ascii=False)
    print(f'RSS collector done: {len(news)} items')
