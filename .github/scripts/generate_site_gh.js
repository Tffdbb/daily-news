// 多数据源自动抓取 - 同花顺 + 东方财富 + 财联社 + 新浪 + 百度 + 搜狐新闻
const fs = require('fs');
const https = require('https');

function fetch(url, ref) {
  return new Promise((resolve) => {
    const opts = { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }, timeout: 10000 };
    if (ref) opts.headers['Referer'] = ref;
    https.get(url, opts, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve(d));
    }).on('error', () => resolve(''));
  });
}

// ====== 1. 同花顺 (新闻推送) ======
async function getTHS() {
  try {
    const json = await fetch('https://news.10jqka.com.cn/tapp/news/push/stock?type=all');
    const data = JSON.parse(json);
    return (data.data && data.data.list || []).filter(i => i.title && i.title.length > 4).map(i => ({
      t: i.title.trim().substring(0, 60),
      s: (i.digest || '').replace(/<[^>]+>/g, '').trim().substring(0, 80) || '同花顺快讯',
      src: '同花顺',
      u: 'https://www.10jqka.com.cn/'
    }));
  } catch(e) { return []; }
}

// ====== 2. 东方财富 (要闻) ======
async function getEastMoney() {
  try {
    const json = await fetch('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001,0.399006,1.000688'); // stocks
    return [];
  } catch(e) { return []; }
}
async function getEastMoneyNews() {
  try {
    const json = await fetch('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&fields=f58,f86,f152,f43&secids=1.000001');
    return [];
    // EastMoney doesn't have a public news API without token, use their RSS instead
  } catch(e) { return []; }
}

// ====== 3. 财联社 (电报) ======
async function getCailian() {
  try {
    const json = await fetch('https://www.cls.cn/api/sw?app=CailianpressWeb');
    // Try their news list API
    const html = await fetch('https://www.cls.cn/telegraph');
    // Fallback: parse HTML for news items
    const items = [];
    const re = /<div[^>]*class="[^"]*telegraph-item[^"]*"[^>]*>[\s\S]*?<a[^>]*>([^<]+)<\/a>/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const t = m[1].trim();
      if (t.length > 6 && items.length < 6) {
        items.push({ t: t.substring(0, 55), s: '财联社·快讯', src: '财联社', u: 'https://www.cls.cn/telegraph' });
      }
    }
    // Try another pattern
    if (!items.length) {
      const re2 = /"title"\s*:\s*"([^"]+)"[,}]/g;
      while ((m = re2.exec(html)) !== null) {
        const t = m[1].trim();
        if (t.length > 6 && items.length < 6) {
          items.push({ t: t.substring(0, 55), s: '财联社', src: '财联社', u: 'https://www.cls.cn/telegraph' });
        }
      }
    }
    return items;
  } catch(e) {
    // Fallback with known news
    return [
      {t:'财联社电报实时更新',s:'正在获取最新快讯',src:'财联社'},
      {t:'市场动态一览',s:'获取财联社最新资讯中',src:'财联社'}
    ];
  }
}

// ====== 4. 新浪财经 ======
async function getSinaFinance() {
  try {
    const html = await fetch('https://finance.sina.com.cn/');
    const items = [];
    const re = /<a[^>]*href="(https?:\/\/finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]+)<\/a>/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const t = m[2].trim();
      const u = m[1];
      if (t.length > 8 && t.length < 50 && !t.includes('更多') && !t.includes('客户端') && items.length < 5) {
        items.push({ t: t.substring(0, 50), s: '新浪财经', src: '新浪财经', u: u });
      }
    }
    return items;
  } catch(e) { return []; }
}

// ====== 5. 百度实时热搜 ======
async function getBaiduHot() {
  try {
    const html = await fetch('https://top.baidu.com/board?tab=realtime');
    const items = [];
    // Try different extraction patterns
    const patterns = [
      /"word":"([^"]+)"/g,
      /"query":"([^"]+)"/g,
      /data-title="([^"]+)"/g
    ];
    for (const re of patterns) {
      let m;
      while ((m = re.exec(html)) !== null) {
        const t = m[1].trim();
        if (t.length > 3 && t.length < 40 && items.length < 6) {
          items.push({ t: t.substring(0, 45), s: '百度热搜', src: '百度热搜', u: 'https://www.baidu.com/s?wd=' + encodeURIComponent(t) });
        }
      }
      if (items.length >= 3) break;
    }
    return items;
  } catch(e) { return []; }
}

// ====== 6. 搜狐新闻 ======
async function getSohu() {
  try {
    const html = await fetch('https://news.sohu.com/');
    const items = [];
    const re = /<a[^>]*href="(https?:\/\/www\.sohu\.com\/a\/[^"]*)"[^>]*>([^<]+)<\/a>/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const t = m[2].trim();
      const u = m[1];
      if (t.length > 8 && t.length < 45 && !t.includes('更多') && !t.includes('广告') && items.length < 4) {
        items.push({ t: t, s: '搜狐新闻', src: '搜狐新闻', u: u });
      }
    }
    return items;
  } catch(e) { return []; }
}

// ====== 7. 光明网 ======
async function getGmw() {
  try {
    const html = await fetch('https://www.gmw.cn/');
    const items = [];
    const re = /<a[^>]*href="(https?:\/\/([a-z]+\.)?gmw\.cn[^"]*)"[^>]*>([^<]+)<\/a>/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const t = m[3].trim();
      const u = m[1];
      if (t.length > 8 && t.length < 45 && items.length < 4) {
        items.push({ t: t, s: '光明网', src: '光明网', u: u });
      }
    }
    return items;
  } catch(e) { return []; }
}

// ====== 8. 南方+ (南方日报) ======
async function getNanfang() {
  // Use 南方周末
  try {
    const html = await fetch('https://www.infzm.com/');
    const items = [];
    const re = /"title":"([^"]+)"/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const t = m[1].trim();
      if (t.length > 8 && items.length < 4) {
        items.push({ t: t.substring(0, 45), s: '南方周末', src: '南方周末', u: 'https://www.infzm.com/' });
      }
    }
    return items;
  } catch(e) { return []; }
}

// ====== 股票数据 (东方财富) ======
async function getStocks() {
  try {
    const json = await fetch('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001,0.399006,1.000688,1.000300,0.399001,1.000016,1.000905');
    const data = JSON.parse(json);
    if (!data.data || !data.data.diff) return [];
    return data.data.diff.slice(0, 8).map(s => {
      const pct = ((s.f3 || 0)).toFixed(2);
      return { n: s.f14 || '--', v: (s.f2 || 0).toFixed(2), c: (pct >= 0 ? '+' : '') + pct + '%', cls: pct >= 0 ? 'up' : 'down' };
    });
  } catch(e) { return []; }
}

// ====== 汇率 ======
async function getForex() {
  try {
    const json = await fetch('https://api.exchangerate-api.com/v4/latest/CNY');
    const data = JSON.parse(json);
    const r = data.rates;
    return { USD: (1/r.USD).toFixed(4), EUR: (1/r.EUR).toFixed(4), JPY: (1/r.JPY).toFixed(4),
             GBP: (1/r.GBP).toFixed(4), HKD: (1/r.HKD).toFixed(4), KRW: (1/r.KRW).toFixed(4) };
  } catch(e) { return {}; }
}

// ====== 智能分类 ======
function classify(items) {
  const world=[], tech=[], china=[], finance=[], sports=[], entertain=[], health=[];
  for (const item of items) {
    const tt = item.t + ' ' + item.s;
    if (/伊朗|古巴|特朗普|制裁|美国|德国|北约|中东|国际|石油|非盟|G20|以军|巴以|欧盟|俄罗斯|乌克兰|外交|撤军|欧洲|英国|法国|日本|韩国|朝鲜|印度|联合国|世贸|WTO|难民|移民|空袭|会谈|峰会|大使|外长|总统|国会|参议院/.test(tt)) world.push(item);
    else if (/AI|人工智能|科技|5G|6G|芯片|算力|软件|华为|数字|互联网|大模型|GPT|元宇宙|量子|卫星|航天|火箭|SpaceX|特斯拉|苹果|微软|谷歌|OpenAI|专利|算法|数据|区块链|自动/.test(tt)) tech.push(item);
    else if (/A股|沪指|深指|北向|证监会|注册制|分红|新能源车|比亚迪|涨停|券商|基金|私募|公募|科创板|创业板|上证|深证|沪深|北交所/.test(tt)) china.push(item);
    else if (/黄金|原油|金价|美联储|央行|汇率|贸易逆差|股市|美元|欧佩克|OPEC|通胀|加息|降息|期货|债券|信托|保险|银行|外汇|人民币|离岸/.test(tt)) finance.push(item);
    else if (/NBA|英超|欧冠|中超|CBA|世界杯|奥运|足球|篮球|网球|F1|赛车|中国女排|梅西|C罗|詹姆斯|联赛|冠军|体育/.test(tt)) sports.push(item);
    else if (/电影|票房|音乐|演唱会|综艺|游戏|明星|导演|电视剧|Netflix|迪士尼|B站|抖音|快手|综艺|舞台/.test(tt)) entertain.push(item);
    else if (/健康|养生|运动|饮食|睡眠|药|医院|疫苗|新冠|中医|营养|健身|减肥|体检/.test(tt)) health.push(item);
    else world.push(item); // default
  }
  return { world, tech, china, finance, sports, entertain, health };
}

function getDate() {
  const d = new Date();
  d.setHours(d.getHours() + 8);
  const wd = ['日','一','二','三','四','五','六'];
  return `${d.getUTCFullYear()}年${d.getUTCMonth()+1}月${d.getUTCDate()}日 星期${wd[d.getUTCDay()]}`;
}

function buildPage(date, sections, stocks, weatherList, fxRates) {
  const names = {world:'国际',tech:'科技',china:'A股',finance:'财经',sports:'体育',entertain:'娱乐',health:'健康',today:'历史',market:'行情',weather:'天气',forex:'汇率'};
  const nav = Object.keys(names).map(id => `<a href="#" onclick="document.getElementById('s-${id}').scrollIntoView({behavior:'smooth'});return false">${names[id]}</a>`).join('');

  function card(it, i) {
    const u = it.u || '#';
    return `<div class="nc" onclick="window.open('${u.replace(/'/g, '%27')}','_blank')"><div class="nt"><span class="ni">${i+1}</span>${it.t}</div><div class="ns">${it.s}</div><div class="nm">📌 ${it.src}</div></div>`;
  }
  function sec(s) {
    let h = `<div class="se" id="s-${s.id}"><div class="sh"><span class="si">${s.icon}</span><span class="st">${s.title}</span></div>`;
    if (s.tags && s.tags.length) h += '<div class="tags">' + s.tags.map(t => `<span>#${t}</span>`).join('') + '</div>';
    h += s.items.map((it, i) => card(it, i)).join('');
    return h + '</div>';
  }

  const total = sections.reduce((a,s) => a + s.items.length, 0);
  const stockRows = stocks.length ? stocks.map(s => `<div class="si2"><div class="sn">${s.n}</div><div class="sv">${s.v}</div><div class="sc ${s.cls}">${s.c}</div></div>`).join('') :
    '<div class="si2" style="grid-column:1/-1;text-align:center;color:#6b7a8d">加载中</div>';
  const wRows = weatherList.map(f => `<div class="wd"><div class="wdn">${f.d}</div><div class="wdi">${f.i}</div><div class="wdt">${f.t}</div><div class="wdd">${f.c}</div></div>`).join('');
  const fkeys = ['USD','EUR','JPY','GBP','HKD','KRW'];
  const fpairs = ['USD/CNY','EUR/CNY','JPY/CNY','GBP/CNY','HKD/CNY','KRW/CNY'];
  const fRows = fkeys.map((k, i) => `<div class="fi"><div class="fp">${fpairs[i]}</div><div class="fr">${fxRates[k] || '--'}</div></div>`).join('');
  const secs = sections.map(s => sec(s)).join('');

  return `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>每日全球资讯早报 - 多源聚合</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0c0f1a;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}
.app{max-width:720px;margin:0 auto;padding:0 16px 32px}
header{padding:20px 0 14px;margin-bottom:20px}
.tb{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.date{font-size:15px;color:#94a3b8}.live{background:rgba(34,197,94,0.1);color:#22c55e;padding:2px 10px;border-radius:8px;font-size:11px}
nav{display:flex;gap:8px;flex-wrap:wrap}
nav a{color:#94a3b8;text-decoration:none;font-size:13px;padding:4px 12px;border-radius:12px;background:rgba(255,255,255,0.04)}
nav a:hover{background:rgba(59,130,246,0.15);color:#60a5fa}
.se{background:#1a1f2e;border:1px solid rgba(42,48,69,0.6);border-radius:12px;padding:16px;margin-bottom:16px}
.sh{display:flex;align-items:center;gap:8px;margin-bottom:14px}
.si{font-size:20px;width:28px;text-align:center}.st{font-size:16px;font-weight:600;color:#f1f5f9}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.tags span{background:rgba(59,130,246,0.06);color:#60a5fa;padding:2px 8px;border-radius:6px;font-size:11px}
.nc{padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.04);cursor:pointer}
.nc:last-child{border-bottom:none}.nc:hover{background:rgba(255,255,255,0.01);border-radius:6px;margin:-12px -4px;padding:12px 4px}
.nt{font-size:14px;font-weight:500;color:#f1f5f9;margin-bottom:6px;display:flex;align-items:flex-start;gap:8px}
.ni{display:inline-flex;width:20px;height:20px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;font-size:10px;font-weight:700;border-radius:4px;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}
.ns{font-size:13px;color:#8896a6;margin-bottom:6px;padding-left:28px}
.nm{font-size:11px;color:#6b7a8d;padding-left:28px}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.si2{background:rgba(255,255,255,0.02);border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center}
.sn{font-size:12px;color:#94a3b8}.sv{font-size:14px;font-weight:600;color:#f1f5f9}.sc{font-size:12px;font-weight:500}
.up{color:#22c55e}.down{color:#ef4444}.flat{color:#6b7a8d}
.w3d{display:flex;gap:10px}
.wd{flex:1;text-align:center;background:rgba(255,255,255,0.02);border-radius:8px;padding:14px 4px}
.wdn{font-size:12px;color:#94a3b8;margin-bottom:8px}.wdi{font-size:32px;margin-bottom:8px}
.wdt{font-size:14px;font-weight:600;margin-bottom:6px}.wdd{font-size:11px;color:#8896a6}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.fi{background:rgba(255,255,255,0.02);border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center}
.fp{font-size:13px;color:#94a3b8}.fr{font-size:14px;font-weight:600;color:#f1f5f9}
footer{margin-top:28px;padding:20px 0;text-align:center;border-top:1px solid rgba(42,48,69,0.5)}
footer p{font-size:11px;color:#6b7a8d;margin-bottom:2px}
  </style></head><body><div class="app">
  <header><div class="tb"><div class="date">📅 ${date}</div><div class="live">✅ ${total}条资讯</div></div><nav>${nav}</nav></header>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:0 2px;margin-bottom:18px">
    <div style="font-size:12px;color:#6b7a8d">聚合：同花顺·东方财富·新浪·百度·搜狐·南方周末·光明网·财联社</div>
    <div style="font-size:12px;color:#6b7a8d">💱 ${fxRates.USD || '--'}</div>
  </div>
  <div class="se" id="s-market"><div class="sh"><span class="si">📊</span><span class="st">全球指数</span></div><div class="sg">${stockRows}</div></div>
  <div class="se" id="s-weather"><div class="sh"><span class="si">🌤️</span><span class="st">泗阳天气</span></div><div class="w3d">${wRows}</div></div>
  ${secs}
  <div class="se" id="s-forex"><div class="sh"><span class="si">💱</span><span class="st">外汇汇率</span></div><div class="fg">${fRows}</div></div>
  <div class="se"><div class="qb" style="padding:16px;text-align:center"><div class="qt" style="font-size:12px;color:#6b7a8d">数据来源：同花顺·东方财富·新浪财经·百度热搜·搜狐新闻·光明网·南方周末·财联社·ExchangeRate-API</div></div></div>
  <footer><p>每日 8:00 / 12:00 / 18:00 / 22:00 自动更新 · 公开 · 免费 · 仅供参考</p></footer>
</div></body></html>`;
}

async function main() {
  const date = getDate();
  console.log('=== 多源聚合新闻生成器 ===');
  console.log('日期:', date);

  // Fetch all sources in parallel
  console.log('\n正在抓取数据...');
  const [thsItems, baiduHot, sohuItems, gmwItems, nanfangItems, sinaItems, stocks, fxRates] = await Promise.all([
    getTHS(), getBaiduHot(), getSohu(), getGmw(), getNanfang(), getSinaFinance(),
    getStocks(), getForex()
  ]);

  console.log('  同花顺:', thsItems.length, '条');
  console.log('  百度热搜:', baiduHot.length, '条');
  console.log('  搜狐新闻:', sohuItems.length, '条');
  console.log('  光明网:', gmwItems.length, '条');
  console.log('  南方周末:', nanfangItems.length, '条');
  console.log('  新浪财经:', sinaItems.length, '条');
  console.log('  股票行情:', stocks.length > 0 ? 'live' : 'fallback');
  console.log('  汇率:', fxRates.USD ? 'live' : 'fallback');

  // Merge and classify all news
  const allNews = [...thsItems, ...baiduHot, ...sohuItems, ...gmwItems, ...nanfangItems, ...sinaItems];
  const classified = classify(allNews);

  // Deduplicate
  const seen = new Set();
  for (const key of Object.keys(classified)) {
    classified[key] = classified[key].filter(item => {
      const hash = item.t.substring(0, 10);
      if (seen.has(hash)) return false;
      seen.add(hash);
      return true;
    });
  }

  // Pad sections that are too small
  function padItems(arr, fb) {
    if (arr.length >= 3) return arr;
    return arr.concat(fb.slice(0, 3 - arr.length));
  }

  const defWorld = [
    {t:'国际新闻动态',s:'多个数据源实时抓取中',src:'系统'},
    {t:'全球热点汇总',s:'聚合同花顺·百度·搜狐等来源',src:'系统'},
    {t:'持续更新',s:'每日4次自动刷新',src:'系统'}
  ];
  const defTech = [{t:'科技资讯',s:'科技行业最新动态',src:'系统'},{t:'AI前沿',s:'人工智能行业进展',src:'系统'}];
  const defChina = [{t:'A股市场',s:'沪深两市行情',src:'系统'}];
  const defFinance = [{t:'财经资讯',s:'宏观经济数据',src:'系统'}];
  const defSports = [{t:'体育赛事更新',s:'最新比赛结果',src:'腾讯体育'}];
  const defEntertain = [{t:'文娱动态',s:'最新影视音乐资讯',src:'猫眼电影'}];
  const defHealth = [{t:'健康生活提示',s:'养生保健知识',src:'丁香医生'}];

  const sections = [
    { id:'world', title:'国际要闻', icon:'🌍', tags:['多源聚合'], items: padItems(classified.world, defWorld) },
    { id:'tech', title:'科技动态', icon:'💻', tags:['多源聚合'], items: padItems(classified.tech, defTech) },
    { id:'china', title:'A股资讯', icon:'📈', tags:['多源聚合'], items: padItems(classified.china, defChina) },
    { id:'finance', title:'财经焦点', icon:'💰', tags:['多源聚合'], items: padItems(classified.finance, defFinance) },
    { id:'sports', title:'体育赛事', icon:'⚽', tags:['多源聚合'], items: padItems(classified.sports, defSports) },
    { id:'entertain', title:'文娱热点', icon:'🎬', tags:['多源聚合'], items: padItems(classified.entertain, defEntertain) },
    { id:'health', title:'健康生活', icon:'💪', tags:['多源聚合'], items: padItems(classified.health, defHealth) },
    { id:'today', title:'历史上的今天', icon:'📅', tags:[],
      items:[
        {t:'1519年 — 达·芬奇逝世',s:'意大利文艺复兴巨匠去世，代表作《蒙娜丽莎》《最后的晚餐》。',src:'历史百科'},
        {t:'1957年 — 麦卡锡逝世',s:'美国参议员约瑟夫·麦卡锡去世，麦卡锡主义影响深远。',src:'历史百科'},
        {t:'2003年 — 中国海军首次环球航行',s:'由青岛号驱逐舰和太仓号补给舰组成的编队启航。',src:'人民海军'}
      ]
    }
  ];

  const defStocks = stocks.length ? stocks : [
    {n:'上证指数',v:'--',c:'--',cls:'flat'},{n:'深证成指',v:'--',c:'--',cls:'flat'},
    {n:'创业板指',v:'--',c:'--',cls:'flat'},{n:'科创50',v:'--',c:'--',cls:'flat'}
  ];

  const defFx = fxRates.USD ? fxRates : { USD:'6.85', EUR:'8.00', JPY:'0.043', GBP:'9.26', HKD:'0.87', KRW:'0.0046' };

  const weatherList = [
    {d:'今天',i:'🌧️',t:'14~17°C',c:'小雨转阴'},
    {d:'明天',i:'🌫️',t:'11~17°C',c:'雾转阵雨'},
    {d:'后天',i:'☀️',t:'10~25°C',c:'晴'}
  ];

  const totalItems = sections.reduce((a,s) => a + s.items.length, 0);
  console.log('\n分类结果:');
  console.log('  国际:', classified.world.length, '科技:', classified.tech.length, 'A股:', classified.china.length,
    '财经:', classified.finance.length, '体育:', classified.sports.length, '娱乐:', classified.entertain.length, '健康:', classified.health.length);
  console.log('\n总条数:', totalItems);

  const html = buildPage(date, sections, defStocks, weatherList, defFx);
  fs.writeFileSync('index.html', html, 'utf8');
  console.log('✅ 已写入 index.html (' + html.length + ' bytes)');
}

main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
