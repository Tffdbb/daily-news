#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日价值资讯V4.1 - 攻击性过滤：砍广告/推广/Choice等"""
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

# 🔥 严格黑名单
BAN = set(['下载','注册','登录','会员','广告','推广','免费领取','点击领取','扫码','关注公众号','转发','抽奖','红包','签到','订阅','报名','打卡','理财通','基金申购','Choice','金融终端','客户端','APP','app'])
BAN_URL = ['tg.aspx','choice.','download','/?adid=','adid=']
SHORT_BAN = ['更多','查看','详情','点击','这里','公告','声明']

def is_good(t):
    if len(t) < 6 or len(t) > 55: return False
    for b in BAN:
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
        if len(t)>=mn and len(t)<55 and t[:8] not in s and is_good(t) and not any(b in t for b in SHORT_BAN):
            s.add(t[:8]);items.append(t)
    return items

def pat_u(html, p, mx=6):
    s=set();items=[]
    for m in re.finditer(p,html):
        if len(items)>=mx:break
        t=m.group(2).strip();u=m.group(1).strip()
        if not is_good_url(u): continue
        if len(t)>=6 and t[:8] not in s and is_good(t) and not any(b in t for b in SHORT_BAN):
            s.add(t[:8]);items.append({'t':t[:55],'u':u})
    return items

# ════ 📈 投资·财经 ════

def s1():
    """同花顺快讯"""
    h = f_either('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    try:
        items = []
        for i in json.loads(h).get('data',{}).get('list',json.loads(h).get('data',[])):
            t = (i.get('title') or '').strip()
            if is_good(t) and not any(b in t for b in SHORT_BAN):
                items.append({'t':t[:50],'src':'同花顺','cat':'finance','u':'https://www.10jqka.com.cn/'})
        return items[:8]
    except: return []

def s2():
    """华尔街见闻"""
    h = f_either('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=20')
    try:
        items = []
        for i in json.loads(h).get('data',{}).get('items',[]):
            t = (i.get('title') or i.get('content_text','')).replace('<em>','').replace('</em>','').strip()
            if is_good(t) and len(t) < 45:
                items.append({'t':t[:45],'src':'华尔街见闻','cat':'finance','u':'https://wallstreetcn.com/live/global'})
        return items[:8]
    except: return []

def s3():
    """财联社"""
    i = pat(f_either('https://www.cls.cn/'),r'"title"\s*:\s*"([^"]{6,55})"',8)
    return [{'t':t,'src':'财联社','cat':'finance','u':'https://www.cls.cn/'} for t in i]

def s4():
    """东方财富 - 过滤广告"""
    h = f_either('https://www.eastmoney.com/')
    i = pat_u(h,r'<a[^>]*href="(https?://[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'东方财富','cat':'finance','u':x['u']} for x in i]

def s5():
    """每经新闻"""
    h = f_either('https://www.nbd.com.cn/')
    i = pat(h,r'"title":"([^"]{6,50})"',6)
    return [{'t':t[:45],'src':'每经新闻','cat':'finance','u':'https://www.nbd.com.cn/'} for t in i]

def s6():
    """新浪财经"""
    i = pat_u(f_either('https://finance.sina.com.cn/'),r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>',6)
    return [{'t':x['t'][:45],'src':'新浪财经','cat':'finance','u':x['u']} for x in i]

def s7():
    """第一财经"""
    h = f_either('https://www.yicai.com/')
    i = pat(h,r'"title":"([^"]{6,50})"',6)
    return [{'t':t[:45],'src':'第一财经','cat':'finance','u':'https://www.yicai.com/'} for t in i]

def s8():
    """网易财经"""
    i = pat_u(f_either('https://money.163.com/'),r'<a[^>]*href="(https?://money\.163\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'网易财经','cat':'finance','u':x['u']} for x in i]

def s9():
    """雪球"""
    h = f_either('https://www.xueqiu.com/')
    i = pat(h,r'"title":"([^"]{6,45})"',4)
    return [{'t':t[:40],'src':'雪球','cat':'finance','u':'https://xueqiu.com/'} for t in i]

def s27():
    """财联社电报"""
    h = f_either('https://www.cls.cn/telegraph')
    i = pat(h,r'"content":"([^"]{8,50})"',6)
    return [{'t':t[:45],'src':'财联社电报','cat':'finance','u':'https://www.cls.cn/telegraph'} for t in i]

# ════ 🌐 宏观·天下 ════

def s10():
    """央视新闻"""
    i = pat_u(f_either('https://news.cctv.com/'),r'<a[^>]*href="(https?://news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'央视新闻','cat':'macro','u':x['u']} for x in i]

def s11():
    """中国新闻网"""
    h = f_either('https://www.chinanews.com.cn/')
    i = pat_u(h,r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'中国新闻网','cat':'macro','u':x['u']} for x in i]

def s12():
    """环球网"""
    i = pat_u(f_either('https://www.huanqiu.com/'),r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'环球网','cat':'macro','u':x['u']} for x in i]

def s13():
    """人民网"""
    h = f_either('https://www.people.com.cn/')
    i = pat_u(h,r'<a[^>]*href="(http[^"]*people\.com\.cn[^"]*)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'人民网','cat':'macro','u':x['u']} for x in i]

def s28():
    """参考消息"""
    i = pat_u(f_either('https://www.cankaoxiaoxi.com/'),r'<a[^>]*href="(https?://[^"]*cankaoxiaoxi\.com[^"]*)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'参考消息','cat':'macro','u':x['u']} for x in i]

# ════ 🔥 热点·民生 ════

def s14():
    """百度热搜"""
    h = f_either('https://top.baidu.com/board?tab=realtime');s=set();i=[]
    for m in re.finditer(r'data-title="([^"]+)"',h):
        if len(i)>=8:break
        t=m.group(1).strip()
        if len(t)>=4 and t[:8] not in s and is_good(t): s.add(t[:8]);i.append({'t':t[:45],'src':'百度热搜','cat':'hot','u':'https://top.baidu.com/'})
    return i

def s15():
    """微博热搜 - 过滤娱乐"""
    h = f_either('https://weibo.com/ajax/side/hotSearch')
    try:
        j=json.loads(h);s=set();i=[]
        for item in j.get('data',{}).get('realtime',[]):
            t=item.get('word','')
            if t and t[:8] not in s and is_good(t) and '娱乐' not in t[:6] and '明星' not in t[:6]:
                s.add(t[:8]);i.append({'t':t[:45],'src':'微博热搜','cat':'hot','u':'https://weibo.com/'})
            if len(i)>=6:break
        return i
    except: return []

def s16():
    """网易新闻"""
    i = pat_u(f_either('https://news.163.com/'),r'<a[^>]*href="(https://news\.163\.com/[^"]+)"[^>]*>([^<]{8,45})</a>',6)
    return [{'t':x['t'][:45],'src':'网易新闻','cat':'hot','u':x['u']} for x in i]

def s17():
    """澎湃新闻"""
    i = pat_u(f_either('https://www.thepaper.cn/'),r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'澎湃新闻','cat':'hot','u':x['u']} for x in i]

def s18():
    """凤凰网"""
    i = pat_u(f_either('https://www.ifeng.com/'),r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})</a>',6)
    return [{'t':x['t'][:45],'src':'凤凰网','cat':'hot','u':x['u']} for x in i]

# ════ 💡 科技·前沿 ════

def s19():
    """虎嗅"""
    i = pat_u(f_either('https://www.huxiu.com/'),r'<a[^>]*href="(https?://www\.huxiu\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'虎嗅','cat':'tech','u':x['u']} for x in i]

def s20():
    """36氪"""
    h = f_either('https://36kr.com/')
    i = pat(h,r'"title":"([^"]{6,50})"',6)
    return [{'t':t[:45],'src':'36氪','cat':'tech','u':'https://36kr.com/'} for t in i]

def s21():
    """IT之家"""
    h = f_either('https://www.ithome.com/')
    i = pat_u(h,r'<a[^>]*href="(https?://www\.ithome\.com/\d+[^"]+)"[^>]*>([^<]{8,50})</a>',8)
    return [{'t':x['t'][:45],'src':'IT之家','cat':'tech','u':x['u']} for x in i]

# ════ 🎯 机会·风向 ════

def s23():
    """知乎热门"""
    h = f_either('https://www.zhihu.com/hot')
    i = pat(h,r'"title":"([^"]{6,50})"',8)
    return [{'t':t[:45],'src':'知乎热门','cat':'oppo','u':'https://www.zhihu.com/hot'} for t in i]

def s24():
    """雪球热议"""
    h = f_either('https://xueqiu.com/')
    i = pat(h,r'"text":"([^"]{8,50})"',6)
    return [{'t':t[:40],'src':'雪球热议','cat':'oppo','u':'https://xueqiu.com/'} for t in i]

def s25():
    """DoNews"""
    h = f_either('https://www.donews.com/')
    i = pat_u(h,r'<a[^>]*href="(https?://www\.donews\.com/[^"]+)"[^>]*>([^<]{8,50})</a>',6)
    return [{'t':x['t'][:45],'src':'DoNews','cat':'oppo','u':x['u']} for x in i]

def s26():
    """华尔街深度"""
    h = f_either('https://wallstreetcn.com/articles')
    i = pat(h,r'"title":"([^"]{6,50})"',6)
    return [{'t':t[:45],'src':'华尔街深度','cat':'oppo','u':'https://wallstreetcn.com/articles'} for t in i]

def _run_src(fn):
    try: return fn() or []
    except: return []

def main():
    sources = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s27,s10,s11,s12,s13,s28,s14,s15,s16,s17,s18,s19,s20,s21,s23,s24,s25,s26]
    print(f'Collected {len(sources)} sources')
    news = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(_run_src, fn): i for i, fn in enumerate(sources)}
        try:
            for f in concurrent.futures.as_completed(futs, timeout=60):
                try:
                    items = f.result(timeout=3)
                    if items: news.extend(items)
                except: pass
        except concurrent.futures.TimeoutError:
            for f in futs: f.cancel()
    
    # 去重
    seen=set();deduped=[]
    for n in news:
        k=n.get('t','')[:12]
        if k and k not in seen and is_good(n.get('t','')):
            seen.add(k);deduped.append(n)
    
    # 每个源最多10条
    src_limit = {}
    deduped2 = []
    for n in deduped:
        src = n.get('src','')
        cnt = src_limit.get(src, 0)
        if cnt >= 10: continue
        src_limit[src] = cnt + 1
        deduped2.append(n)
    deduped = deduped2
    
    grouped = {'finance':[],'macro':[],'hot':[],'tech':[],'oppo':[]}
    for n in deduped:
        cat = n.get('cat','hot')
        if cat not in grouped: cat = 'hot'
        grouped[cat].append(n)
    
    # finance给更多权重
    for cat in grouped:
        max_n = 35 if cat == 'finance' else 20
        grouped[cat] = grouped[cat][:max_n]
    
    stks = [
        {'n':'上证指数','p':'3296','c':'15','r':'0.46%','cls':'up'},
        {'n':'深证成指','p':'10583','c':'42','r':'0.40%','cls':'up'},
        {'n':'创业板指','p':'1932','c':'-5','r':'-0.26%','cls':'down'},
        {'n':'恒生指数','p':'22358','c':'287','r':'1.30%','cls':'up'},
        {'n':'道琼斯','p':'41603','c':'164','r':'0.40%','cls':'up'},
        {'n':'纳斯达克','p':'17617','c':'-36','r':'-0.20%','cls':'down'},
        {'n':'标普500','p':'5592','c':'12','r':'0.21%','cls':'up'},
        {'n':'黄金','p':'2885','c':'18','r':'0.63%','cls':'up'},
    ]
    fx = {'USD':'7.2420','EUR':'7.8321','JPY':'4.83','GBP':'9.1250','HKD':'0.9280'}
    
    with open('news_data.json','w',encoding='utf-8') as f:
        json.dump({'news':deduped,'groups':grouped,'stocks':stks,'forex':fx},f,ensure_ascii=False)
    
    for k,v in grouped.items():
        print(f'  {k}: {len(v)}')
    print('Done:', len(deduped), 'news')
    print('Sources:', sorted(set(n['src'] for n in deduped)))

if __name__ == '__main__':
    main()
