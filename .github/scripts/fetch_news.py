#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环球资讯早报 - 数据采集器（混合工具版：curl + urllib 双引擎）"""
import json, re, datetime, os, subprocess, sys

# ===== 双引擎采集 =====
# curl 模式：硬超时 10 秒，不会被阻塞
def f(url):
    try:
        r = subprocess.run(
            ['timeout', '10', 'curl', '-sL', url,
             '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
             '--connect-timeout', '8', '--max-time', '9',
             '-o', '-', '-w', ''],
            capture_output=True, timeout=12, text=True
        )
        return r.stdout
    except:
        return ''

# fallback: urllib（当 curl 不可用或返回空时）
import urllib.request, ssl
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_HDR = {'User-Agent': 'Mozilla/5.0'}

def fallback(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=_HDR), timeout=8, context=_CTX)
        return r.read().decode('utf-8', 'replace')
    except:
        return ''

def fetch(url):
    h = f(url)
    if len(h) < 100:
        h2 = fallback(url)
        if len(h2) > len(h):
            return h2
    return h

# ===== 解析工具 =====
def pat(html, p, mn=6, mx=5):
    s=set();items=[];m=re.finditer(p,html)
    for x in m:
        if len(items)>=mx:break
        t=x.group(1).strip()
        if len(t)>=mn and len(t)<55 and t[:8] not in s and '更多' not in t and '广告' not in t:
            s.add(t[:8]);items.append(t)
    return items

def lk(html,p,mn=8,mx=5):
    s=set();items=[];m=re.finditer(p,html)
    for x in m:
        if len(items)>=mx:break
        t=x.group(2).strip();u=x.group(1).strip()
        if len(t)>=mn and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'u':u})
    return items

# ===== 36 个数据源 =====
def s1():
    h=fetch('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    if not h: return []
    try:
        j=json.loads(h);return [{'t':i['title'].strip()[:55],'s':'同花顺快讯','src':'同花顺','u':'https://www.10jqka.com.cn/'} for i in j.get('data',{}).get('list',j.get('data',[])) if i.get('title','') ][:15]
    except: return []

def s2():
    h=fetch('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=10')
    if not h: return []
    try:
        j=json.loads(h);return [{'t':(i.get('title') or i.get('content_text','')).replace('<em>','').replace('</em>','').strip()[:55],'s':'实时快讯','src':'华尔街见闻','u':'https://wallstreetcn.com/live/global'} for i in j.get('data',{}).get('items',[]) if (i.get('title') or i.get('content_text','')) ][:6]
    except: return []

def s3():
    h=fetch('https://www.cls.cn/');i=pat(h,r'"title"\s*:\s*"([^"]+)"',6,6)
    if len(i)<3: i=pat(h,r'"content":"([^"]{8,60})"',6,6)
    return [{'t':t,'s':'电报快讯','src':'财联社','u':'https://www.cls.cn/'} for t in i]

def s4():
    i=lk(fetch('https://www.yicai.com/'),r'<a[^>]*href="(https://www\.yicai\.com/news/[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'一财','src':'第一财经','u':x['u']} for x in i]

def s5():
    i=lk(fetch('https://news.163.com/'),r'<a[^>]*href="(https://news\.163\.com/[^"]+)"[^>]*>([^<]{8,45})</a>',8,5)
    return [{'t':x['t'][:50],'s':'网易精选','src':'网易新闻','u':x['u']} for x in i]

def s6():
    i=lk(fetch('https://finance.sina.com.cn/'),r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>',8,5)
    return [{'t':x['t'][:50],'s':'财经资讯','src':'新浪财经','u':x['u']} for x in i if '更多' not in x['t'] and '登录' not in x['t']]

def s7():
    i=lk(fetch('https://www.xinhuanet.com/'),r'<a[^>]*href="([^"]+\.htm)"[^>]*>([^<]{8,45})</a>',8,3)
    return [{'t':x['t'][:50],'s':'官方发布','src':'新华网','u':x['u'] if x['u'].startswith('http') else 'https://www.xinhuanet.com'+x['u']} for x in i]

def s8():
    i=lk(fetch('https://www.people.com.cn/'),r'<a[^>]*href="(https?://[^"]*people\.com\.cn[^"]*)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'人民网','src':'人民网','u':x['u']} for x in i if '许可证' not in x['t'] and '视觉' not in x['t']]

def s9():
    i=lk(fetch('https://www.chinanews.com.cn/'),r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'即时新闻','src':'中国新闻网','u':x['u']} for x in i]

def s10():
    i=lk(fetch('https://news.cctv.com/'),r'<a[^>]*href="(https?://news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'央视报道','src':'央视新闻','u':x['u']} for x in i]

def s11():
    i=lk(fetch('https://www.ifeng.com/'),r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})</a>',8,5)
    return [{'t':x['t'][:50],'s':'凤凰网评','src':'凤凰网','u':x['u']} for x in i if '查看' not in x['t'] and '广告' not in x['t']]

def s12():
    i=lk(fetch('https://www.caixin.com/'),r'<a[^>]*href="(https?://www\.caixin\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'财新独家','src':'财新网','u':x['u']} for x in i]

def s13():
    i=lk(fetch('https://www.nbd.com.cn/'),r'<a[^>]*href="(https?://www\.nbd\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'每经资讯','src':'每日经济新闻','u':x['u']} for x in i]

def s14():
    i=lk(fetch('https://www.stcn.com/'),r'<a[^>]*href="(https?://www\.stcn\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'券商中国','src':'证券时报','u':x['u']} for x in i]

def s15():
    i=lk(fetch('https://www.cs.com.cn/'),r'<a[^>]*href="(https?://www\.cs\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'中证报','src':'中国证券报','u':x['u']} for x in i]

def s16():
    h=fetch('https://www.ithome.com/rss/');i=[];s=set()
    for m in re.finditer(r'<title><!\[CDATA\[([^\]]+)\]\]></title>',h):
        if len(i)>=4: break
        t=m.group(1).strip()
        if len(t)>=6 and t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'s':'IT资讯','src':'IT之家','u':'https://www.ithome.com/'})
    return i

def s17():
    h=fetch('https://top.baidu.com/board?tab=realtime');i=[];s=set()
    for p in [r'data-title="([^"]+)"',r'"word":"([^"]+)"']:
        for m in re.finditer(p,h):
            if len(i)>=6:break
            t=m.group(1).strip()
            if len(t)>=4 and t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'s':'热搜榜','src':'百度热搜','u':'https://top.baidu.com/board?tab=realtime'})
    return i

def s18():
    i=lk(fetch('https://www.thepaper.cn/'),r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'深度报道','src':'澎湃新闻','u':x['u']} for x in i]

def s19():
    h=fetch('https://36kr.com/');i=pat(h,r'"title":"([^"]{6,50})"',6,4)
    if len(i)<2: i=pat(h,r'"widgetTitle":"([^"]{6,50})"',6,4)
    return [{'t':t[:45],'s':'科技商业','src':'36氪','u':'https://36kr.com/'} for t in i]

def s20():
    i=lk(fetch('https://www.donews.com/'),r'<a[^>]*href="(https?://www\.donews\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'互联网资讯','src':'Donews','u':x['u']} for x in i]

def s21():
    i=lk(fetch('https://sports.sina.com.cn/'),r'<a[^>]*href="(https?://sports\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'体育资讯','src':'新浪体育','u':x['u']} for x in i if '更多' not in x['t'] and '登录' not in x['t']]

def s22():
    h=fetch('https://www.huxiu.com/');s=set();i=[]
    for m in re.finditer(r'<h2[^>]*>([^<]+)</h2>',h):
        if len(i)>=3:break
        t=m.group(1).strip()
        if len(t)>=6 and t[:8] not in s and '24小时' not in t and '文章' not in t: s.add(t[:8]);i.append({'t':t[:50],'s':'商业洞察','src':'虎嗅','u':'https://www.huxiu.com/'})
    return i

def s23():
    i=lk(fetch('https://health.people.com.cn/'),r'<a[^>]*href="(https?://health\.people\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'健康资讯','src':'人民健康','u':x['u']} for x in i if '人民' not in x['t'] and '免责' not in x['t']]

def s24():
    h=fetch('https://www.toutiao.com/');i=[];s=set()
    for p in [r'"title":"([^"]{6,50})"',r'"abstract":"([^"]{6,50})"',r'"word":"([^"]{6,50})"']:
        for m in re.finditer(p,h):
            if len(i)>=5:break
            t=m.group(1).strip()
            if len(t)>=4 and t[:8] not in s and '广告' not in t: s.add(t[:8]);i.append({'t':t[:50],'s':'今日头条','src':'今日头条','u':'https://www.toutiao.com/'})
    return i

def s25():
    i=lk(fetch('https://www.eastmoney.com/'),r'<a[^>]*href="(https?://[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'财经资讯','src':'东方财富','u':x['u']} for x in i if any(k in x['t'] for k in ['A股','股市','基金','行情','投资','美元','央行','上涨','下跌','涨停','跌停'])]

def s26():
    i=lk(fetch('https://xueqiu.com/'),r'<a[^>]*href="(https?://xueqiu\.com/\d+/\d+[^"]*)"[^>]*>([^<]{6,50})</a>',6,5)
    return [{'t':x['t'][:50],'s':'投资者社区','src':'雪球','u':x['u']} for x in i]

def s27():
    i=lk(fetch('https://www.huanqiu.com/'),r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'国际视野','src':'环球网','u':x['u']} for x in i]

def s28():
    i=lk(fetch('https://www.guancha.cn/'),r'<a[^>]*href="(https?://www\.guancha\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'深度观察','src':'观察者网','u':x['u']} for x in i]

def s29():
    i=lk(fetch('https://ent.sina.com.cn/'),r'<a[^>]*href="(https?://ent\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'文娱资讯','src':'新浪娱乐','u':x['u']} for x in i if '更多' not in x['t'] and '登录' not in x['t']]

def s30():
    i=lk(fetch('https://sports.163.com/'),r'<a[^>]*href="(https?://sports\.163\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'体育赛事','src':'网易体育','u':x['u']} for x in i if '更多' not in x['t']]

def s31():
    h=fetch('https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all')
    if not h: return []
    try:
        j=json.loads(h);items=[];s=set()
        for v in j.get('data',{}).get('list',[]):
            t=v.get('title','')
            if t and len(t)>=4 and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'s':'B站热门','src':'B站热门','u':'https://www.bilibili.com/video/'+str(v.get('aid',''))})
            if len(items)>=4:break
        return items
    except: return []

def s32():
    h=fetch('https://weibo.com/ajax/side/hotSearch')
    if not h: return []
    try:
        j=json.loads(h);items=[];s=set()
        for item in j.get('data',{}).get('realtime',[]):
            t=item.get('word','')
            if t and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'s':'微博热搜','src':'微博热搜','u':'https://weibo.com/'})
            if len(items)>=5:break
        return items
    except: return []

def s33():
    h=fetch('https://www.jd.com/');i=[];s=set()
    for m in re.finditer(r'<a[^>]*href="(https?://item\.jd\.com/[^"]+)"[^>]*title="([^"]{6,50})"',h):
        if len(i)>=4:break
        t=m.group(2).strip()
        if t[:8] not in s and '广告' not in t: s.add(t[:8]);i.append({'t':t[:50],'s':'京东好物','src':'京东','u':m.group(1)})
    return i

def s34():
    h=fetch('https://www.douyin.com/');i=[];s=set()
    for m in re.finditer(r'"title":"([^"]{4,50})"',h):
        if len(i)>=4:break
        t=m.group(1).strip()
        if t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'s':'抖音热点','src':'抖音','u':'https://www.douyin.com/'})
    return i

def s35():
    h=fetch('https://music.163.com/discover/toplist');i=[];s=set()
    for m in re.finditer(r'<a[^>]*href="/song[^"]*"[^>]*>([^<]{6,40})</a>',h):
        if len(i)>=3:break
        t=m.group(1).strip()
        if t[:8] not in s: s.add(t[:8]);i.append({'t':t[:50],'s':'热歌推荐','src':'网易云音乐','u':'https://music.163.com/'})
    return i

def s36():
    i=lk(fetch('https://www.smzdm.com/'),r'<a[^>]*href="(https?://[^"]*smzdm\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,5)
    return [{'t':x['t'][:50],'s':'好价推荐','src':'什么值得买','u':x['u']} for x in i]

# ===== 主函数 =====
def main():
    all_sources = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16,s17,s18,s19,s20,s21,s22,s23,s24,s25,s26,s27,s28,s29,s30,s31,s32,s33,s34,s35,s36]
    news = []
    
    for fn in all_sources:
        try:
            items = fn()
            if items:
                news.extend(items)
                print(f'  {fn.__name__}: {len(items)} items')
        except:
            print(f'  {fn.__name__}: FAILED')
    
    # 去重
    seen = set()
    deduped = []
    for n in news:
        key = n.get('t','')[:10]
        if key and key not in seen and len(n.get('t','')) >= 4:
            seen.add(key)
            deduped.append(n)
    
    print(f'\n总计: {len(news)} raw → {len(deduped)} deduped')
    
    # 行情数据
    stocks = [
        {'n':'恒生指数','p':'20536.47','c':'-156.35','r':'-0.76%'},{'n':'上证指数','p':'3684.32','c':'13.45','r':'0.37%'},
        {'n':'深证成指','p':'11842.14','c':'55.82','r':'0.47%'},{'n':'创业板指','p':'2488.65','c':'8.23','r':'0.33%'},
        {'n':'道琼斯','p':'42918.72','c':'218.34','r':'0.51%'},{'n':'纳斯达克','p':'19217.94','c':'-46.21','r':'-0.24%'},
        {'n':'标普500','p':'5820.14','c':'14.23','r':'0.25%'},{'n':'日经225','p':'39245.31','c':'-124.56','r':'-0.32%'}
    ]
    forex = {'USD':'7.2420','EUR':'7.8321','JPY':'0.0450','GBP':'9.1250','HKD':'0.9280','KRW':'0.0052'}
    
    output = {'news': deduped, 'stocks': stocks, 'forex': forex, 'labels': []}
    
    # 获取天气（curl 模式，超时可靠）
    try:
        wh = subprocess.run(['curl', '-s', 'wttr.in/Beijing?format=j1'], capture_output=True, text=True, timeout=10)
        if wh.stdout:
            wj = json.loads(wh.stdout)
            cc = wj.get('current_condition',[{}])[0]
            output['weather'] = {
                'temp_C': cc.get('temp_C','--'),
                'weatherDesc': [{'value': cc.get('weatherDesc',[{}])[0].get('value','--')}],
                'windspeedKmph': cc.get('windspeedKmph','--'),
                'humidity': cc.get('humidity','--')
            }
    except:
        pass
    
    with open('news_data.json','w',encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    print(f'已写入 news_data.json ({len(deduped)}条)')

if __name__ == '__main__':
    main()
