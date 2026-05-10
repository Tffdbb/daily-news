#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容增强V2：新闻价值三重升级
1. 规则摘要：从标题提取关键实体+动作，生成一句话摘要
2. 价值评分：综合评分（来源权威度+标题信息量+关键词权重）
3. Top10精选：推荐当天最有价值的新闻
（已集成 DeepSeek API 摘要，不可用时 fallback 到规则摘要）
"""
import json, re, os, datetime, requests, urllib.parse

# ── 来源权威度 ──
SOURCE_AUTHORITY = {
    '华尔街见闻': 85, '财联社': 90, '每日经济新闻': 80, '新浪财经': 75,
    '第一财经': 85, '界面新闻': 80, '21世纪经济报道': 85, '财新': 95,
    '央视': 90, '新华社': 95, '人民日报': 95, '澎湃新闻': 80,
    '36氪': 75, '虎嗅': 75, '极客公园': 75, '爱范儿': 70,
    'QbitAI': 70, '少数派': 70, 'IT之家': 65, '快科技': 65,
    '百度热搜': 40, '微博': 35, '知乎': 50, 'V2EX': 45,
    'GitHub': 60, '科技': 65, '科技日报': 80,
}

# ── 价值加分关键词 ──
HIGH_IMPACT_KW = set([
    '突破', '首发', '首次', '重磅', '里程碑', '新高', '创纪录',
    '紧急', '突发', '独家', '深度', '聚焦', '核心', '关键',
    '大跌', '暴涨', '崩盘', '涨停', '跌停', '熔断', '危机',
    '革命性', '颠覆', '全球首款', '中国首款', '获批', '落地',
    '制裁', '禁令', '关税', '加征', '反制', '合作', '签约',
])

# ── 规则摘要生成 ──
def rule_summary(item):
    """基于规则的摘要生成，不依赖API"""
    t = item.get('t', '')
    src = item.get('src', '')
    desc = item.get('desc', '')
    cat = item.get('cat', 'hot')
    
    # 如果有描述字段直接取前30字
    if desc and len(desc) > 10:
        return desc[:30] + ('...' if len(desc) > 30 else '')
    
    # 规则引擎：从标题提取关键信息
    # 模式1: "XXX发布YYY" → "XXX发布了YYY"
    m = re.match(r'^([^，,]{2,8})(发布|推出|上线|公布|宣布)(.{4,20})$', t)
    if m: return f'{m.group(1)} {m.group(2)}{m.group(3)[:18]}'
    
    # 模式2: "XXX：YYYY" → "XXX：YYYY"
    m = re.match(r'^([^：:]{2,10})[：:](.{6,})$', t)
    if m:
        body = m.group(2)[:20]
        return f'{m.group(1)}：{body}'
    
    # 模式3: 包含"涨/跌" → 提取数字信息
    if re.search(r'[涨跌]', t):
        m = re.search(r'([^，。]{4,16})[涨跌][^，。]{0,8}[%\d]', t)
        if m: return m.group(1)[:25] + '波动'
    
    # 模式4: 科技产品新闻
    tech_keys = ['芯片', '手机', '汽车', 'AI', '大模型', '系统', '软件']
    for k in tech_keys:
        if k in t:
            m = re.search(r'(.{2,8}%s.{4,20})' % k, t)
            if m: return m.group(1)[:25]
    
    # 模式5: 财经数据
    if any(k in t for k in ['A股', '股市', '基金', 'GDP', 'CPI']):
        m = re.search(r'([^，。]{6,25})', t)
        if m: return m.group(1)[:25]
    
    # 回退：取标题前25字
    return t[:25] + ('...' if len(t) > 25 else '')


# ── DeepSeek API 摘要（仅对高分新闻调用，节省配额）──
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_URL = 'https://api.deepseek.com/chat/completions'

def ds_summary(item):
    """用 DeepSeek API 生成一句话摘要，失败时返回规则摘要"""
    if not DEEPSEEK_API_KEY:
        return rule_summary(item)
    
    t = item.get('t', '')[:60]
    src = item.get('src', '')
    cat = item.get('cat', '')
    
    prompt = f'用一句话（≤30字）概括这条新闻：{t} 来源：{src}'
    
    try:
        r = requests.post(DEEPSEEK_URL, json={
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': '你是新闻摘要助手。用一句简洁的话概括新闻，不超过30字。只输出摘要，不加前缀后缀。'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 80,
            'temperature': 0.1,
            'stream': False
        }, headers={'Authorization': f'Bearer {DEEPSEEK_API_KEY}', 'Content-Type': 'application/json'}, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            summary = data['choices'][0]['message']['content'].strip().strip('"').strip("'")
            # 截断到35字
            if len(summary) > 35:
                summary = summary[:32] + '...'
            return summary
    except Exception as e:
        pass  # fallback 到规则摘要
    
    return rule_summary(item)


def batch_ds_summary(items_fallback, chunk_size=30):
    """批量调用 DeepSeek API，含退避"""
    if not DEEPSEEK_API_KEY:
        return [(i, rule_summary(i)) for i, _ in items_fallback]
    
    # 筛选需要API摘要的高分新闻（top 40%）
    scored = [(i, value_score(i)) for i, _ in items_fallback]
    scored.sort(key=lambda x: x[1], reverse=True)
    threshold = scored[len(scored)//5*2][1] if len(scored) > 5 else 0  # 前40%分界线
    api_items = [(i, s) for i, s in scored if s >= threshold and s >= 55][:20]  # 最多20条
    rule_items = [(i, s) for i, s in scored if i not in [x[0] for x in api_items]]
    
    results = {id(i): rule_summary(i) for i, _ in rule_items}
    
    # 分批调用API
    for batch_start in range(0, len(api_items), max(1, chunk_size // 5)):
        batch = api_items[batch_start:batch_start+5]
        texts = [i.get('t','')[:50] for i, _ in batch]
        
        if not texts:
            continue
        
        prompt_lines = '\n'.join([f'{j+1}. {t}' for j, t in enumerate(texts)])
        prompt = f'为以下新闻各生成一句摘要（≤20字），逐行对应输出：\n{prompt_lines}'
        
        try:
            r = requests.post(DEEPSEEK_URL, json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': '逐行输出摘要，每行对应一条新闻。只输出摘要文本，不加编号和前缀。'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 200,
                'temperature': 0.1,
                'stream': False
            }, headers={'Authorization': f'Bearer {DEEPSEEK_API_KEY}', 'Content-Type': 'application/json'}, timeout=15)
            
            if r.status_code == 200:
                result = r.json()
                summaries = result['choices'][0]['message']['content'].strip().split('\n')
                for j, (i, _) in enumerate(batch):
                    if j < len(summaries):
                        s = summaries[j].strip().strip('"').strip("'")
                        if len(s) > 35:
                            s = s[:32] + '...'
                        results[id(i)] = s
        except Exception as e:
            pass
        
        # 对未命中API的用规则摘要兜底
        for i, _ in batch:
            if id(i) not in results:
                results[id(i)] = rule_summary(i)
    
    return [(i, results.get(id(i), rule_summary(i))) for i, _ in items_fallback]


# ── 价值评分 ──
def value_score(item):
    """综合价值评分 0-100"""
    t = item.get('t', '')
    src = item.get('src', '')
    score = 50  # 基础分
    
    # 1. 来源权威度（±20）
    authority = SOURCE_AUTHORITY.get(src, 55)
    score += (authority - 50) * 0.4  # 高权威最多+18，低权威最多-6
    
    # 2. 关键词权重（±20）
    found_kw = [kw for kw in HIGH_IMPACT_KW if kw in t]
    score += min(len(found_kw) * 8, 20)
    
    # 3. 标题信息密度（±10）
    # 含数字加分，含模糊词减分
    if re.search(r'\d', t): score += 5
    if any(k in t for k in ['或', '可能', '据说', '传']): score -= 5
    if any(k in t for k in ['首次', '首个', '第一', '最']): score += 5
    
    # 4. 标题长度质量（±10）
    if 12 <= len(t) <= 35:  # 理想长度
        score += 5
    elif len(t) > 45:
        score -= 5
        score += 3 if authority > 70 else 0  # 长标题但来源权威可接受
    
    # 5. 时效性加分（按日期）
    date = item.get('date', '')
    if date:
        try:
            d = datetime.datetime.strptime(str(date)[:10], '%Y-%m-%d')
            diff = (datetime.datetime.now() - d).days
            if diff <= 1: score += 10
            elif diff <= 3: score += 5
            else: score -= 10
        except: pass
    
    return min(100, max(0, round(score, 1)))


# ── 精选推荐 ──
def pick_top(news, count=10):
    """从新闻中选出最优的N条"""
    # 至少3个来源，不同分类均匀分布
    candidates = sorted(news, key=lambda x: x.get('_vscore', 50), reverse=True)
    
    picks = []
    used_cats = {}
    used_srcs = {}
    
    for n in candidates:
        cat = n.get('cat', 'hot')
        src = n.get('src', '')
        
        # 分类限制：同分类最多3条
        if used_cats.get(cat, 0) >= 3:
            continue
        # 来源限制：同来源最多2条
        if src and used_srcs.get(src, 0) >= 2:
            continue
        
        picks.append(n)
        used_cats[cat] = used_cats.get(cat, 0) + 1
        used_srcs[src] = used_srcs.get(src, 0) + 1
        
        if len(picks) >= count:
            break
    
    return picks


# ── 主流程 ──
def main():
    with open('news_data.json', 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    # 增强所有新闻
    news = raw.get('news', [])
    items_with_sum = [(item, None) for item in news if item.get('t')]
    
    # 先算所有评分
    for item, _ in items_with_sum:
        item['_vscore'] = value_score(item)
    
    # 批量生成摘要（高分用API，低分用规则）
    if DEEPSEEK_API_KEY:
        print('DeepSeek API 可用，生成AI摘要...')
        results = batch_ds_summary(items_with_sum)
        for item, summary in results:
            item['_summary'] = summary
        print(f'AI摘要完成：{sum(1 for _,s in results if len(s)>5)}条')
    else:
        print('DeepSeek API 不可用，使用规则摘要')
        for item, _ in items_with_sum:
            item['_summary'] = rule_summary(item)
    
    # 增强分组新闻
    groups = raw.get('groups', {})
    for cat in groups:
        for item in groups[cat]:
            if not item.get('t'):
                continue
            item['_summary'] = rule_summary(item)  # 分组新闻用规则摘要（节省配额）
            item['_vscore'] = value_score(item)
    
    # 计算Top10精选
    picks = pick_top(news)
    raw['picks'] = [{'title': p['t'], 'summary': p['_summary'], 'src': p.get('src', ''),
                     'cat': p.get('cat', 'hot'), 'u': p.get('u', ''), 'score': p['_vscore']} for p in picks]
    
    # 统计
    total = len(news)
    total += sum(len(groups[c]) for c in groups)
    
    high_val = [n for n in news if n.get('_vscore', 0) >= 70]
    low_val = [n for n in news if n.get('_vscore', 0) < 40]
    
    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(raw, f, ensure_ascii=False)
    
    print(f'增强V2完成: {total}条处理')
    print(f'高价值(≥70): {len(high_val)}条')
    print(f'低价值(<40): {len(low_val)}条')
    print(f'精选推荐: {len(picks)}条')
    print(f'分类分布:')
    cat_dist = {}
    for n in news:
        c = n.get('cat', 'hot')
        cat_dist[c] = cat_dist.get(c, 0) + 1
    for c, cnt in cat_dist.items():
        print(f'  {c}: {cnt}条')
    if picks:
        print(f'\n精选Top{picks[0]["score"]:.0f}-{picks[-1]["score"]:.0f}分:')
        for i, p in enumerate(picks[:5]):
            print(f'  {i+1}. [{p["score"]:.0f}] {p["title"][:30]} | {p["summary"][:20]}...')

if __name__ == '__main__':
    main()
