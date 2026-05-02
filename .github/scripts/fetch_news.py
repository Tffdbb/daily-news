#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, re, urllib.request, ssl, datetime

TIMEOUT = 10
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'}
CTX = ssl.create_default_context()
CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

def f(url):
    try: r = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=TIMEOUT, context=CTX); return r.read().decode('utf-8','replace')
    except: return ''

def pat(html, p, mn=6, mx=5):
    s=set();items=[];m=re.finditer(p,html)
    for x in m:
        if len(items)>=mx:break
        t=x.group(1).strip()
        if len(t)>=mn and len(t)<55 and t[:8] not in s and '更多' not in t and '广告' not in t: s.add(t[:8]);items.append(t)
    return items

def lk(html,p,mn=8,mx=5):
    s=set();items=[];m=re.finditer(p,html)
    for x in m:
        if len(items)>=mx:break
        t=x.group(2).strip();u=x.group(1).strip()
        if len(t)>=mn and t[:8] not in s: s.add(t[:8]);items.append({'t':t[:50],'u':u})
    return items

def s1():
    h=f('https://news.10jqka.com.cn/tapp/news/push/stock?type=all')
    if not h: return []
    try: j=json.loads(h);return [{'t':i['title'].strip()[:55],'s':'同花顺快讯','src':'同花顺','u':'https://www.10jqka.com.cn/'} for i in j.get('data',{}).get('list',[]) if i.get('title') and len(i['title'])>4][:15]
    except: return []

def s2():
    h=f('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=10')
    if not h: return []
    try:
        j=json.loads(h);return [{'t':(i.get('title') or i.get('content_text','')).replace('<em>','').replace('</em>','').strip()[:55],'s':'见闻快讯','src':'华尔街见闻','u':'https://wallstreetcn.com'+i.get('uri','') if i.get('uri') else 'https://wallstreetcn.com/'} for i in j.get('data',{}).get('items',[]) if i.get('title') or i.get('content_text')][:10]
    except: return []

def s3():
    h=f('https://www.cls.cn/');i=pat(h,r'"title"\s*:\s*"([^"]+)"',6,6)
    if len(i)<3: i=pat(h,r'"content":"([^"]{8,60})"',6,6)
    return [{'t':t,'s':'电报快讯','src':'财联社','u':'https://www.cls.cn/'} for t in i]

def s4():
    i=lk(f('https://www.yicai.com/'),r'<a[^>]*href="(https://www\.yicai\.com/news/[^"]+)"[^>]*>([^<]{8,55})</a>',8,4)
    return [{'t':x['t'][:50],'s':'一财','src':'第一财经','u':x['u']} for x in i]

def s5():
    i=lk(f('https://news.163.com/'),r'<a[^>]*href="(https://news\.163\.com/[^"]+)"[^>]*>([^<]{8,45})</a>',8,4)
    return [{'t':x['t'][:50],'s':'网易精选','src':'网易新闻','u':x['u']} for x in i]

def s6():
    i=lk(f('https://finance.sina.com.cn/'),r'<a[^>]*href="(https://finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>',8,4)
    return [{'t':x['t'][:50],'s':'财经资讯','src':'新浪财经','u':x['u']} for x in i if '更多' not in x['t'] and '客户端' not in x['t']]

def s7():
    i=lk(f('https://www.xinhuanet.com/'),r'<a[^>]*href="([^"]+\.htm)"[^>]*>([^<]{8,45})</a>',8,3)
    return [{'t':x['t'][:50],'s':'官方发布','src':'新华网','u':x['u'] if x['u'].startswith('http') else 'https://www.xinhuanet.com'+x['u']} for x in i if 'English' not in x['t'] and '更多' not in x['t']]

def s8():
    i=lk(f('https://www.people.com.cn/'),r'<a[^>]*href="(https?://[^"]*people\.com\.cn[^"]*)"[^>]*>([^<]{8,45})</a>',8,3)
    return [{'t':x['t'][:50],'s':'人民网','src':'人民网','u':x['u']} for x in i if '许可证' not in x['t'] and '广告' not in x['t'] and '更多' not in x['t']]

def s9():
    i=lk(f('https://www.chinanews.com.cn/'),r'<a[^>]*href="(https?://www\.chinanews\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'即时新闻','src':'中国新闻网','u':x['u']} for x in i]

def s10():
    i=lk(f('https://news.cctv.com/'),r'<a[^>]*href="(https?://news\.cctv\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,3)
    return [{'t':x['t'][:50],'s':'央视报道','src':'央视新闻','u':x['u']} for x in i]

def s11():
    i=lk(f('https://www.ifeng.com/'),r'<a[^>]*href="(https?://[^"]*ifeng\.com[^"]*)"[^>]*>([^<]{8,45})</a>',8,4)
    return [{'t':x['t'][:50],'s':'凤凰网评','src':'凤凰网','u':x['u']} for x in i if '查看' not in x['t'] and '更多' not in x['t'] and 'PHOENIX' not in x['t']]

def s12():
    i=lk(f('https://www.caixin.com/'),r'<a[^>]*href="(https?://www\.caixin\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,3)
    return [{'t':x['t'][:50],'s':'财新独家','src':'财新网','u':x['u']} for x in i]

def s13():
    i=lk(f('https://www.nbd.com.cn/'),r'<a[^>]*href="(https?://www\.nbd\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'每经资讯','src':'每日经济新闻','u':x['u']} for x in i]

def s14():
    i=lk(f('https://www.stcn.com/'),r'<a[^>]*href="(https?://www\.stcn\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'券商中国','src':'证券时报','u':x['u']} for x in i]

def s15():
    i=lk(f('https://www.cs.com.cn/'),r'<a[^>]*href="(https?://www\.cs\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,3)
    return [{'t':x['t'][:50],'s':'中证报','src':'中国证券报','u':x['u']} for x in i]

def s16():
    h=f('https://www.ithome.com/rss/');i=[];s=set()
    for m in re.finditer(r'<title><!\[CDATA\[([^\]]+)\]\]></title>',h):
        if len(i)>=4: break
        t=m.group(1).strip()
        if len(t)>4 and t!='IT之家' and t[:8] not in s: s.add(t[:8]);i.append(t)
    if len(i)<2:
        first=True
        for m in re.finditer(r'<title>([^<]+)</title>',h):
            if len(i)>=4:break
            if first:first=False;continue
            t=m.group(1).strip()
            if len(t)>4 and t[:8] not in s: s.add(t[:8]);i.append(t)
    return [{'t':t[:50],'s':'科技资讯','src':'IT之家','u':'https://www.ithome.com/'} for t in i]

def s17():
    h=f('https://top.baidu.com/board?tab=realtime');i=[];s=set()
    for p in [r'data-title="([^"]+)"',r'"word":"([^"]+)"']:
        for m in re.finditer(p,h):
            if len(i)>=6:break
            t=m.group(1).strip()
            if len(t)>3 and t[:6] not in s: s.add(t[:6]);i.append(t)
        if len(i)>=4:break
    return [{'t':t[:40],'s':'热搜话题','src':'百度热搜','u':'https://www.baidu.com/s?wd='+urllib.request.quote(t)} for t in i]

def s18():
    i=lk(f('https://www.thepaper.cn/'),r'<a[^>]*href="(https?://www\.thepaper\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'深度报道','src':'澎湃新闻','u':x['u']} for x in i]

def s19():
    h=f('https://36kr.com/');i=pat(h,r'"title":"([^"]{6,50})"',6,4)
    if len(i)<2: i=pat(h,r'"widgetTitle":"([^"]{6,50})"',6,4)
    return [{'t':t[:45],'s':'科技商业','src':'36氪','u':'https://36kr.com/'} for t in i]

def s20():
    i=lk(f('https://www.donews.com/'),r'<a[^>]*href="(https?://www\.donews\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,3)
    return [{'t':x['t'][:50],'s':'互联网资讯','src':'Donews','u':x['u']} for x in i]

def s21():
    i=lk(f('https://sports.sina.com.cn/'),r'<a[^>]*href="(https?://sports\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'体育资讯','src':'新浪体育','u':x['u']} for x in i if '更多' not in x['t'] and '频道' not in x['t']]

def s22():
    h=f('https://www.huxiu.com/');s=set();i=[]
    for m in re.finditer(r'<h2[^>]*>([^<]+)</h2>',h):
        if len(i)>=3:break
        t=m.group(1).strip()
        if len(t)>6 and t[:8] not in s: s.add(t[:8]);i.append(t)
    return [{'t':t[:45],'s':'深度商业','src':'虎嗅','u':'https://www.huxiu.com/'} for t in i]

def s23():
    i=lk(f('https://health.people.com.cn/'),r'<a[^>]*href="(https?://health\.people\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,3)
    return [{'t':x['t'][:50],'s':'健康资讯','src':'人民健康','u':x['u']} for x in i if '人民' not in x['t'] and '健康' not in x['t']]

def s24():
    h=f('https://www.toutiao.com/');i=[];s=set()
    for p in [r'"title":"([^"]{6,50})"',r'"abstract":"([^"]{6,50})"',r'"word":"([^"]{6,50})"']:
        for m in re.finditer(p,h):
            if len(i)>=5:break
            t=m.group(1).strip()
            if len(t)>5 and t[:6] not in s and '{{' not in t and 'var' not in t: s.add(t[:6]);i.append(t)
        if len(i)>=3:break
    return [{'t':t[:40],'s':'热点话题','src':'今日头条','u':'https://www.toutiao.com/'} for t in i]

def s25():
    i=lk(f('https://www.eastmoney.com/'),r'<a[^>]*href="(https?://[^"]*eastmoney\.com[^"]*)"[^>]*>([^<]{6,50})</a>',6,5)
    return [{'t':x['t'][:50],'s':'财经资讯','src':'东方财富','u':x['u']} for x in i if any(k in x['t'] for k in ['股','涨','跌','亿','元','A股','市场','投资','基金','行情','板块'])]

def s26():
    i=lk(f('https://xueqiu.com/'),r'<a[^>]*href="(https?://xueqiu\.com/\d+/\d+[^"]*)"[^>]*>([^<]{6,50})</a>',6,4)
    return [{'t':x['t'][:50],'s':'投资者社区','src':'雪球','u':x['u']} for x in i]

def s27():
    i=lk(f('https://www.huanqiu.com/'),r'<a[^>]*href="(https?://[^"]*huanqiu\.com[^"]*)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'国际视野','src':'环球网','u':x['u']} for x in i]

def s28():
    i=lk(f('https://www.guancha.cn/'),r'<a[^>]*href="(https?://www\.guancha\.cn/[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'深度观察','src':'观察者网','u':x['u']} for x in i]

def s29():
    i=lk(f('https://ent.sina.com.cn/'),r'<a[^>]*href="(https?://ent\.sina\.com\.cn[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'文娱资讯','src':'新浪娱乐','u':x['u']} for x in i if '更多' not in x['t'] and '频道' not in x['t']]

def s30():
    i=lk(f('https://sports.163.com/'),r'<a[^>]*href="(https?://sports\.163\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'体育赛事','src':'网易体育','u':x['u']} for x in i if '更多' not in x['t'] and '直播' not in x['t']]

def s31():
    """B站热门"""
    h=f('https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all')
    if not h: return []
    try:
        j=json.loads(h);items=j.get('data',{}).get('list',[])
        return [{'t':i.get('title','')[:50],'s':f"播放:{i.get('stat',{}).get('view',0)//10000}万",'src':'B站热门','u':'https://www.bilibili.com/video/'+i.get('bvid','')} for i in items if i.get('title')][:4]
    except: return []

def s32():
    """微博热搜"""
    h=f('https://weibo.com/ajax/side/hotSearch')
    if not h: return []
    try:
        j=json.loads(h);items=j.get('data',{}).get('realtime',[])
        return [{'t':i.get('word','')[:40],'s':f"热搜#{i.get('rank',0)}",'src':'微博热搜','u':'https://s.weibo.com/weibo?q='+urllib.request.quote(i.get('word',''))} for i in items if i.get('word') and len(i['word'])>4][:8]
    except: return []

def s33():
    """京东热门"""
    h=f('https://www.jd.com/');i=[];s=set()
    for m in re.finditer(r'<a[^>]*href="(https?://item\.jd\.com/[^"]+)"[^>]*title="([^"]{6,50})"',h):
        if len(i)>=4:break
        t=m.group(2).strip()
        if len(t)>5 and t[:8] not in s and '广告' not in t and '更多' not in t: s.add(t[:8]);i.append({'t':t[:50],'u':m.group(1)})
    if len(i)<2:
        for m in re.finditer(r'"title":"([^"]{6,50})"',h):
            if len(i)>=4:break
            t=m.group(1).strip()
            if len(t)>5 and t[:8] not in s and '{{' not in t and 'var ' not in t: s.add(t[:8]);i.append({'t':t[:50],'u':'https://www.jd.com/'})
    return [{'t':x['t'][:50],'s':'热卖商品','src':'京东','u':x['u']} for x in i]

def s34():
    """抖音热点"""
    h=f('https://www.douyin.com/');i=[];s=set()
    for m in re.finditer(r'"title":"([^"]{4,50})"',h):
        if len(i)>=4:break
        t=m.group(1).strip()
        if len(t)>4 and t[:8] not in s and '{{' not in t and 'var' not in t and '\\x' not in t: s.add(t[:8]);i.append(t)
    return [{'t':t[:40],'s':'热门视频','src':'抖音','u':'https://www.douyin.com/'} for t in i]

def s35():
    """网易云音乐"""
    h=f('https://music.163.com/discover/toplist');i=[];s=set()
    for m in re.finditer(r'<a[^>]*href="/song[^"]*"[^>]*>([^<]{6,40})</a>',h):
        if len(i)>=3:break
        t=m.group(1).strip()
        if len(t)>5 and t[:8] not in s: s.add(t[:8]);i.append(t)
    return [{'t':t[:40],'s':'热歌榜','src':'网易云音乐','u':'https://music.163.com/'} for t in i]

def s36():
    """什么值得买"""
    i=lk(f('https://www.smzdm.com/'),r'<a[^>]*href="(https?://[^"]*smzdm\.com[^"]+)"[^>]*>([^<]{8,50})</a>',8,4)
    return [{'t':x['t'][:50],'s':'好价推荐','src':'什么值得买','u':x['u']} for x in i]

def gs():
    h=f('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001,0.399006,1.000688,1.000300,1.000016,1.000905,0.399001')
    if not h: return []
    try: j=json.loads(h);return [{'n':s.get('f14','--'),'v':f"{s.get('f2',0):.2f}",'c':f"{'+' if s.get('f3',0)>=0 else ''}{s.get('f3',0):.2f}%",'cls':'up' if s.get('f3',0)>=0 else 'down'} for s in j.get('data',{}).get('diff',[])[:8]]
    except: return []

def gf():
    h=f('https://api.exchangerate-api.com/v4/latest/CNY')
    if not h: return {}
    try:
        j=json.loads(h);r=j.get('rates',{});fx={}
        for s in ['USD','EUR','JPY','GBP','HKD','KRW']:
            if s in r and r[s]>0: fx[s]=f"{1/r[s]:.4f}"
        return fx
    except: return {}

if __name__=='__main__':
    now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    print(f'=== Python采集器 ({now.month}月{now.day}日) ===')
    srcs=[('同花顺',s1),('华尔街见闻',s2),('财联社',s3),('第一财经',s4),('网易',s5),('新浪财经',s6),('新华网',s7),('人民网',s8),('中国新闻网',s9),('央视新闻',s10),('凤凰网',s11),('财新网',s12),('每经',s13),('证券时报',s14),('中证报',s15),('IT之家',s16),('百度',s17),('澎湃新闻',s18),('36氪',s19),('Donews',s20),('新浪体育',s21),('虎嗅',s22),('人民健康',s23),('今日头条',s24),('东方财富',s25),('雪球',s26),('环球网',s27),('观察者网',s28),('新浪娱乐',s29),('网易体育',s30),('B站热门',s31),('微博热搜',s32),('京东',s33),('抖音',s34),('网易云音乐',s35),('什么值得买',s36)]
    al=[];cnt={}
    for n,fx in srcs:
        try: items=fx()
        except: items=[]
        al.append(items)
        if items: cnt[n]=len(items)
    print(f'来源({len(cnt)}): {sum(cnt.values())} 条')
    for k,v in sorted(cnt.items(),key=lambda x:-x[1]): print(f'  {k}:{v}')
    st=gs();fx=gf()
    print(f'  股票: {"live" if st else "fallback"} | 汇率: {"live" if fx else "fallback"}')
    lbs=['同花顺','华尔街见闻','财联社','第一财经','网易','新浪财经','新华网','人民网','中国新闻网','央视新闻','凤凰网','财新网','每经','证券时报','中证报','IT之家','百度','澎湃新闻','36氪','Donews','新浪体育','虎嗅','人民健康','今日头条','东方财富','雪球','环球网','观察者网','新浪娱乐','网易体育','B站热门','微博热搜','京东','抖音','网易云音乐','什么值得买']
    out={'date':now.strftime('%Y年%m月%d日 %A'),'sources':{k:v for k,v in sorted(cnt.items(),key=lambda x:-x[1])},'news':al,'labels':lbs,'stocks':st,'forex':fx,'timestamp':now.isoformat()}
    with open('news_data.json','w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False)
    print('\n写入: news_data.json')
    print('=== Python采集完成 ===')
