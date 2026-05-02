#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V5.2 - 事件共振引擎：同一件事出现在越多源=越重要+时间感知"""
import json, re, datetime, os, subprocess, sys, concurrent.futures

CTX = None
try:
    import ssl
    CTX = ssl.create_default_context()
    CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
except: pass

def curl_fetch(url, timeout_sec=6):
    try:
        r = subprocess.run(['timeout','8','curl','-sL',url,'-A','Mozilla/5.0','--connect-timeout','5','--max-time',str(timeout_sec),'-o','-','-w',''], capture_output=True, timeout=10, text=True)
        return r.stdout
    except: return ''

def urlopen(url, timeout=7):
    try:
        r = __import__('urllib.request', fromlist=['urlopen']).urlopen(__import__('urllib.request', fromlist=['Request']).Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=timeout, context=CTX)
        return r.read().decode('utf-8','replace')
    except: return ''

def f_either(url, timeout=6):
    h = curl_fetch(url, timeout)
    if len(h) < 100:
        h2 = urlopen(url, timeout+1)
        if len(h2) > len(h): return h2
    return h

BAN = set(['下载','注册','登录','会员','广告','推广','免费领取','点击领取','扫码','关注公众号','转发','抽奖','红包','签到','订阅','报名','打卡','理财通','基金申购','Choice','金融终端','客户端','APP','app'])
BAN_URL = ['tg.aspx','choice.','download','/?adid=','adid=']
BAN_TITLE = ['更多','查看','详情','点击','这里','公告','声明','网站自律','免责','隐私','服务协议']

def is_good(t):
    if len(t) < 6 or len(t) > 50: return False
    for b in BAN:
        if b in t: return False
    for b in BAN_TITLE:
        if b in t: return False
    return True

def is_good_url(u):
    for b in BAN_URL:
        if b in u.lower(): return False
    return True

def pat(html, p, mx=6, mn=6):
    s=set();items=[]
    for m in re.finditer(p,html):
        if len(items)>=mx:break
        t=m.group(1).strip()
        if len(t)>=mn and len(t)<50 and t[:8] not in s and is_good(t):
            s.add(t[:8]);items.append(t)
    return items

def pat_u(html, p, mx=6):
    s=set();items=[]
    for m in re.finditer(p,html):
        if len(items)>=mx:break
        t=m.group(2).strip();u=m.group(1).strip()
        if not is_good_url(u): continue
        if len(t)>=6 and t[:8] not in s and is_good(t):
            s.add(t[:8]);items.append({'t':t[:50],'u':u})
    return items

def s1():
    h = f_either('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    try:
        items = []
        for i in json.loads(h).get('data',{}).get('list',json.loads(h).get('data',[])):
            t = (i.get('title') or '').strip()
            if is_good(t):
                items.append({'t':t[:45],'src':'同花顺','cat':'finance','u':'https://www.10jqka.com.cn/'})
        return items[:10]
    except: return []

def s2():
    h = f_either('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=25')
    try:
        items = []
        for i in json.loads(h).get('data',{}).get('items',[]):
            t = (i.get('title') or i.get('content_text','')).replace('<em>','').replace('</em>','').strip()
            if is_good(t) and len(t) < 40:
                items.append({'t':t[:40],'src':'华尔街见闻','cat':'finance','u':'https://wallstreetcn.com/live/global'})
        return items[:10]
    except: return []

def s3():
    i = pat(f_either('https://www.cls.cn/'),r'"title"\s*:\s*"([^"]{6,50})"',10)
    return [{'t':t[:45],'src':'财联社','cat':'finance','u':'https://www.cls.cn/'} for t in i]

def s5():
    h = f_either('https://www.nbd.com.cn/')
    i = pat(h,r'"title":"([^"]{6,48})"',8)
    return [{'t':t[:42],'src':'每经新闻','cat':'finance','u':'https://www.nbd.com.cn/'} for t in i]

def s6():
    i = pat_u(f_either('https://finance.sina.com.cn/'),r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,42})</a>',8)
    return [{'t':x['t'][:40],'src':'新浪财经','cat':'finance','u':x['u']} for x in i]

def s7():
    h = f_either('https://www.yicai.com/')
    i = pat(h,r'"title":"([^"]{6,48})"',8)
    return [{'t':t[:42],'src':'第一财经','cat':'finance','u':'https://www.yicai.com/'} for t in i]

def s8():
    i = pat_u(f_either('https://money.163.com/'),r'<a[^>]*href="(https?://money\.163\.com/[^"]+)"[^>]*>([^<]{8,48})</a>',6)
    return [{'t':x['t'][:42],'src':'网易财经','cat':'finance','u':x['u']} for x in i]

def s27():
    h = f_either('https://www.cls.cn/telegraph')
    i = pat(h,r'"content":"([^"]{8,48})"',8)
    return [{'t':t[:42],'src':'财联社电报','cat':'finance','u':'https://www.cls.cn/telegraph'} for t in i]

def s28():
    h = f_either('https://wallstreetcn.com/articles')
    i = pat(h,r'"title":"([^"]{6,48})"',6)
    return [{'t':t[:42],'src':'华尔街深度','cat':'finance','u':'https://wallstreetcn.com/articles'} for t in i]

def s11():
    h = f_either('https://www.chinanews.com.cn/')
    i = pat_u(h,r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,45})</a>',6)
    return [{'t':x['t'][:40],'src':'中国新闻网','cat':'macro','u':x['u']} for x in i]

def s12():
    i = pat_u(f_either('https://www.huanqiu.com/'),r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,45})</a>',6)
    return [{'t':x['t'][:40],'src':'环球网','cat':'macro','u':x['u']} for x in i]

def s28r():
    i = pat_u(f_either('https://www.cankaoxiaoxi.com/'),r'<a[^>]*href="(https?://[^"]*cankaoxiaoxi\.com[^"]*)"[^>]*>([^<]{8,45})</a>',6)
    return [{'t':x['t'][:40],'src':'参考消息','cat':'macro','u':x['u']} for x in i]

def s14():
    h = f_either('https://top.baidu.com/board?tab=realtime');s=set();i=[]
    for m in re.finditer(r'data-title="([^"]+)"',h):
        if len(i)>=6:break
        t=m.group(1).strip()
        if len(t)>=4 and t[:8] not in s and is_good(t): s.add(t[:8]);i.append({'t':t[:40],'src':'百度热搜','cat':'hot','u':'https://top.baidu.com/'})
    return i

def s15():
    h = f_either('https://weibo.com/ajax/side/hotSearch')
    try:
        j=json.loads(h);s=set();i=[]
        for item in j.get('data',{}).get('realtime',[]):
            t=item.get('word','')
            if t and t[:8] not in s and is_good(t) and '娱乐' not in t[:6] and '明星' not in t[:6]:
                s.add(t[:8]);i.append({'t':t[:40],'src':'微博热搜','cat':'hot','u':'https://weibo.com/'})
            if len(i)>=6:break
        return i
    except: return []

def s17():
    i = pat_u(f_either('https://www.thepaper.cn/'),r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,45})</a>',6)
    return [{'t':x['t'][:40],'src':'澎湃新闻','cat':'hot','u':x['u']} for x in i]

def s18():
    i = pat_u(f_either('https://www.ifeng.com/'),r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,42})</a>',6)
    return [{'t':x['t'][:40],'src':'凤凰网','cat':'hot','u':x['u']} for x in i]

def s19():
    i = pat_u(f_either('https://www.huxiu.com/'),r'<a[^>]*href="(https?://www\.huxiu\.com/[^"]+)"[^>]*>([^<]{8,48})</a>',6)
    return [{'t':x['t'][:42],'src':'虎嗅','cat':'tech','u':x['u']} for x in i]

def s20():
    h = f_either('https://36kr.com/')
    i = pat(h,r'"title":"([^"]{6,48})"',6)
    return [{'t':t[:42],'src':'36氪','cat':'tech','u':'https://36kr.com/'} for t in i]

def s21():
    h = f_either('https://www.ithome.com/')
    i = pat_u(h,r'<a[^>]*href="(https?://www\.ithome\.com/\d+[^"]+)"[^>]*>([^<]{8,48})</a>',8)
    return [{'t':x['t'][:40],'src':'IT之家','cat':'tech','u':x['u']} for x in i]

def s23():
    h = f_either('https://www.zhihu.com/hot')
    i = pat(h,r'"title":"([^"]{6,48})"',6)
    return [{'t':t[:40],'src':'知乎热门','cat':'oppo','u':'https://www.zhihu.com/hot'} for t in i]

def s25():
    h = f_either('https://www.donews.com/')
    i = pat_u(h,r'<a[^>]*href="(https?://www\.donews\.com/[^"]+)"[^>]*>([^<]{8,48})</a>',6)
    return [{'t':x['t'][:42],'src':'DoNews','cat':'oppo','u':x['u']} for x in i]

def _run_src(fn):
    try: return fn() or []
    except: return []

def main():
    sources = [s1,s2,s3,s5,s6,s7,s8,s27,s28,s11,s12,s28r,s14,s15,s17,s18,s19,s20,s21,s23,s25]
    print(f'Collected {len(sources)} sources')
    all_items = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(_run_src, fn): i for i, fn in enumerate(sources)}
        try:
            for f in concurrent.futures.as_completed(futs, timeout=60):
                try:
                    items = f.result(timeout=3)
                    if items: all_items.extend(items)
                except: pass
        except concurrent.futures.TimeoutError:
            for f in futs: f.cancel()
    
    # === 事件共振引擎 ===
    # 对每条新闻提取关键词 (2-5字)
    def extract_keys(t):
        keys=set()
        # 专名匹配：2-4字重复出现的关键词
        for m in re.finditer('[\u4e00-\u9fff]{2,4}', t):
            w=m.group()
            if w not in ['报道','新闻','中国','市场','公司','发布','最新','一个','进行','表示','以及','没有','不是','正在','这个','已经','可以','其他','我们','除了','并且','虽然','但是','因为','所以','今天','今年','可能','开始','之后','还有','成为','包括','数据','时间','方面','要求','通过','相关','同时','其中','应该','需要','问题','发展','关系','情况','时候','信息','结果','行业','增长','首次','需求']:
                keys.add(w)
        return ','.join(sorted(keys))
    
    for n in all_items:
        n['_key'] = extract_keys(n.get('t',''))
    
    # 计算每个事件的共振次数（多少个不同来源报同一组关键词）
    from collections import defaultdict
    resonance = defaultdict(lambda:{'sources':set(),'cats':set(),'count':0})
    for n in all_items:
        k = n['_key']
        if k and len(k) > 2:
            resonance[k]['sources'].add(n.get('src',''))
            resonance[k]['cats'].add(n.get('cat',''))
            resonance[k]['count'] += 1
    
    # 给每条新闻加上共振分
    for n in all_items:
        k = n['_key']
        r = resonance.get(k, {})
        src_count = len(r.get('sources', set()))
        n['_resonance'] = src_count  # 同一事件出现在多少不同来源
    
    # 去重
    seen=set();news=[]
    for n in all_items:
        k=n.get('t','')[:12]
        if k and k not in seen and is_good(n.get('t','')):
            seen.add(k);news.append(n)
    
    print(f'Raw: {len(all_items)}, Deduped: {len(news)}')
    
    # === 分组 ===
    grouped = {'finance':[],'macro':[],'hot':[],'tech':[],'oppo':[]}
    for n in news:
        cat = n.get('cat','hot')
        if cat not in grouped: cat = 'hot'
        grouped[cat].append(n)
    
    # 每个源分组内最多12条
    for cat in grouped:
        src_limit={}; filtered=[]
        for n in grouped[cat]:
            src=n.get('src','')
            cnt=src_limit.get(src,0)
            if cnt>=12: continue
            src_limit[src]=cnt+1; filtered.append(n)
        grouped[cat]=filtered[:40 if cat=='finance' else 20]
    
    total = sum(len(v) for v in grouped.values())
    
    # 输出共振统计
    print(f'\n🔊 事件共振（跨源影响力前10）:')
    top_events = sorted(resonance.items(), key=lambda x:-len(x[1]['sources']))[:10]
    for k,v in top_events:
        print(f'  [{len(v["sources"])}源] {k}')
    
    stks = []
    fx = {}
    
    with open('news_data.json','w',encoding='utf-8') as f:
        json.dump({'news':news,'groups':grouped,'resonance':{k:list(v['sources']) for k,v in top_events}},f,ensure_ascii=False)
    
    for k,v in grouped.items():
        print(f'  {k}: {len(v)}')
    print('Done:', total, 'news')
    print('Sources:', sorted(set(n['src'] for n in news)))

if __name__ == '__main__':
    main()
