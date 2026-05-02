// 多数据源 - 同花顺 + 华尔街见闻 + 财联社 + 第一财经 + 百度 + 东方财富 + 光明网 + 南方周末 + 新浪
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

// ====== 同花顺 ======
async function getTHS() {
  try {
    const json = await fetch('https://news.10jqka.com.cn/tapp/news/push/stock?type=all');
    const data = JSON.parse(json);
    return (data.data && data.data.list || []).filter(i => i.title && i.title.length > 4).map(i => ({
      t: i.title.trim().substring(0, 60),
      s: (i.digest || '').replace(/<[^>]+>/g, '').trim().substring(0, 100) || '同花顺快讯',
      src: '同花顺',
      u: 'https://www.10jqka.com.cn/'
    }));
  } catch(e) { return []; }
}

// ====== 华尔街见闻 (API) ======
async function getWallStreet() {
  try {
    const json = await fetch('https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=8');
    const data = JSON.parse(json);
    if (data.data && data.data.items) {
      return data.data.items.filter(i => i.title || i.content_text).map(i => ({
        t: (i.title || i.content_text || '').replace(/<[^>]+>/g, '').trim().substring(0, 55),
        s: '见闻快讯',
        src: '华尔街见闻',
        u: i.uri ? 'https://wallstreetcn.com' + i.uri : 'https://wallstreetcn.com/'
      }));
    }
    return [];
  } catch(e) { return []; }
}

// ====== 财联社 (页面解析) ======
async function getCailian() {
  try {
    const html = await fetch('https://www.cls.cn/');
    const items = [];
    const re = /"title"\s*:\s*"([^"]+)"/g;
    let m;
    const seen = new Set();
    while ((m = re.exec(html)) !== null) {
      const t = m[1].trim();
      if (t.length > 6 && t.length < 55 && !seen.has(t.substring(0, 8))) {
        seen.add(t.substring(0, 8));
        items.push({ t: t, s: '电报快讯', src: '财联社', u: 'https://www.cls.cn/' });
        if (items.length >= 5) break;
      }
    }
    return items;
  } catch(e) { return []; }
}

// ====== 第一财经 ======
async function getYicai() {
  try {
    const html = await fetch('https://www.yicai.com/');
    const items = [];
    const re = /<a[^>]*href="(https:\/\/www\.yicai\.com\/news\/[^"]+)"[^>]*>([^<]{8,55})<\/a>/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const t = m[2].replace(/[<>]/g, '').trim();
      if (t.length > 8 && items.length < 4) {
        items.push({ t: t, s: '深度财经', src: '第一财经', u: m[1] });
      }
    }
    return items;
  } catch(e) { return []; }
}

// ====== 百度热搜 ======
async function getBaiduHot() {
  try {
    const html = await fetch('https://top.baidu.com/board?tab=realtime');
    const items = [];
    const patterns = [/data-title="([^"]+)"/g, /"word":"([^"]+)"/g];
    for (const re of patterns) {
      let m;
      while ((m = re.exec(html)) !== null) {
        const t = m[1].trim();
        if (t.length > 3 && t.length < 40 && items.length < 8) {
          items.push({ t: t.substring(0, 45), s: '热搜话题', src: '百度热搜', u: 'https://www.baidu.com/s?wd=' + encodeURIComponent(t) });
        }
      }
      if (items.length >= 3) break;
    }
    return items;
  } catch(e) { return []; }
}

// ====== 光明网 ======
async function getGmw() {
  try {
    const html = await fetch('https://www.gmw.cn/');
    const items = [];
    const re = /<a[^>]*href="(https?:\/\/[a-z0-9]+\.gmw\.cn[^"]*)"[^>]*>([^<]{8,40})<\/a>/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const t = m[2].trim();
      if (t.length > 8 && !t.includes('更多') && items.length < 3) {
        items.push({ t: t, s: '时政要闻', src: '光明网', u: m[1] });
      }
    }
    return items;
  } catch(e) { return []; }
}

// ====== 南方周末 ======
async function getInfzm() {
  try {
    const html = await fetch('https://www.infzm.com/');
    const items = [];
    const re = /"title":"([^"]+)"/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const t = m[1].trim();
      if (t.length > 8 && items.length < 4) {
        items.push({ t: t.substring(0, 45), s: '深度报道', src: '南方周末', u: 'https://www.infzm.com/' });
      }
    }
    return items;
  } catch(e) { return []; }
}

// ====== 新浪财经 ======
async function getSina() {
  try {
    const html = await fetch('https://finance.sina.com.cn/');
    const items = [];
    const re = /<a[^>]*href="(https?:\/\/finance\.sina\.com\.cn[^"]*)"[^>]*>([^<]{8,45})<\/a>/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      const t = m[2].trim();
      if (!t.includes('更多') && !t.includes('客户端') && items.length < 4) {
        items.push({ t: t.substring(0, 50), s: '财经资讯', src: '新浪财经', u: m[1] });
      }
    }
    return items;
  } catch(e) { return []; }
}

// ====== 股票数据 ======
async function getStocks() {
  try {
    const json = await fetch('https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001,0.399006,1.000688,1.000300,1.000016,1.000905,0.399001');
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
  const world=[], tech=[], china=[], finance=[], sports=[], entertain=[], health=[], other=[];
  for (const item of items) {
    const tt = item.t + ' ' + item.s;
    if (/NBA|英超|欧冠|中超|CBA|世界杯|奥运|足球|篮球|网球|F1|赛车|羽毛球|乒乓球|女排|梅西|C罗|詹姆斯|联赛|冠军|体育|比赛|决赛|金牌|金牌|银牌/.test(tt)) sports.push(item);
    else if (/AI|人工智能|科技|5G|6G|芯片|算力|软件|华为|数字|互联网|大模型|GPT|元宇宙|量子|卫星|航天|火箭|SpaceX|特斯拉|苹果|微软|谷歌|OpenAI|专利|算法|数据|区块链|自动化|智能|机器人|电动车|光伏|新能源|储能/.test(tt)) tech.push(item);
    else if (/电影|票房|音乐|演唱会|综艺|游戏|明星|导演|电视剧|Netflix|迪士尼|B站|抖音|快手|综艺|舞台|广告|视频|直播|演出/.test(tt)) entertain.push(item);
    else if (/健康|养生|运动|饮食|睡眠|药|医院|疫苗|新冠|中医|营养|健身|减肥|体检|医保|医疗/.test(tt)) health.push(item);
    else if (/A股|沪指|深指|北向|证监会|注册制|分红|涨停|券商|基金|私募|公募|科创板|创业板|上证|深证|沪深|北交所|股份|股票|上市|退市|财报|业绩/.test(tt)) china.push(item);
    else if (/黄金|原油|金价|美联储|央行|汇率|贸易|逆差|美元|欧佩克|OPEC|通胀|加息|降息|期货|债券|信托|保险|银行|外汇|人民币|离岸|经济|GDP|CPI|财报|利润|营收/.test(tt)) finance.push(item);
    else if (/伊朗|古巴|特朗普|制裁|美国|德国|北约|中东|国际|石油|非盟|G20|以军|巴以|欧盟|俄罗斯|乌克兰|外交|撤军|欧洲|英国|法国|日本|韩国|朝鲜|印度|联合国|世贸|WTO|难民|移民|空袭|会谈|峰会|大使|外长|总统|国会|参议院|地震|海啸|间谍|爆炸|袭击|逮捕/.test(tt)) world.push(item);
    else if (/公积金|贷款|房地产|楼市|房价|租房|消费|购物|旅游|五一|假期|高速|公路/.test(tt)) other.push(item);
    else world.push(item);
  }
  return { world, tech, china, finance, sports, entertain, health, other };
}

function getDate() {
  const d = new Date();
  d.setHours(d.getHours() + 8);
  const wd = ['日','一','二','三','四','五','六'];
  return `${d.getUTCFullYear()}年${d.getUTCMonth()+1}月${d.getUTCDate()}日 星期${wd[d.getUTCDay()]}`;
}

function buildPage(date, sections, stocks, weatherList, fxRates, stats) {
  const names = {world:'国际',tech:'科技',china:'A股',finance:'财经',sports:'体育',entertain:'娱乐',health:'健康',today:'历史',market:'行情',weather:'天气',forex:'汇率'};
  const nav = Object.keys(names).map(id => `<a href="#" onclick="document.getElementById('s-${id}').scrollIntoView({behavior:'smooth'});return false">${names[id]}</a>`).join('');

  function card(it, i) {
    const u = it.u || '#';
    return `<div class="nc" onclick="window.open('${u.replace(/'/g, "%27")}','_blank')"><div class="nt"><span class="ni">${i+1}</span>${it.t}</div><div class="ns">${it.s}</div><div class="nm">📌 ${it.src}</div></div>`;
  }
  function sec(s) {
    let h = `<div class="se" id="s-${s.id}"><div class="sh"><span class="si">${s.icon}</span><span class="st">${s.title}</span><span class="scount">${s.items.length}</span></div>`;
    if (s.tags && s.tags.length) h += '<div class="tags">' + s.tags.map(t => `<span>#${t}</span>`).join('') + '</div>';
    h += s.items.map((it, i) => card(it, i)).join('');
    return h + '</div>';
  }

  const total = sections.reduce((a,s) => a + s.items.length, 0);
  const stockRows = stocks.length ? stocks.map(s => `<div class="si2"><div class="sn">${s.n}</div><div class="sv">${s.v}</div><div class="sc ${s.cls}">${s.c}</div></div>`).join('') :
    '<div class="si2" style="grid-column:1/-1;text-align:center;color:#6b7a8d">行情加载中</div>';
  const wRows = weatherList.map(f => `<div class="wd"><div class="wdn">${f.d}</div><div class="wdi">${f.i}</div><div class="wdt">${f.t}</div><div class="wdd">${f.c}</div></div>`).join('');
  const fkeys = ['USD','EUR','JPY','GBP','HKD','KRW'];
  const fpairs = ['USD/CNY','EUR/CNY','JPY/CNY','GBP/CNY','HKD/CNY','KRW/CNY'];
  const fRows = fkeys.map((k, i) => `<div class="fi"><div class="fp">${fpairs[i]}</div><div class="fr">${fxRates[k] || '--'}</div></div>`).join('');
  const secs = sections.map(s => sec(s)).join('');

  const sourceList = ['同花顺','华尔街见闻','财联社','第一财经','百度热搜','光明网','南方周末','新浪财经','东方财富'];
  const sourceStr = sourceList.join(' · ');

  return `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>每日全球资讯早报</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0c0f1a;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}
.app{max-width:780px;margin:0 auto;padding:0 16px 40px}
header{padding:24px 0 10px;border-bottom:1px solid rgba(42,48,69,0.4);margin-bottom:20px}
.tb{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.date{font-size:14px;color:#94a3b8}.live{background:rgba(34,197,94,0.1);color:#22c55e;padding:2px 10px;border-radius:8px;font-size:11px;letter-spacing:0.3px}
nav{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
nav a{color:#8896a6;text-decoration:none;font-size:13px;padding:5px 14px;border-radius:14px;background:rgba(255,255,255,0.03);transition:all 0.15s}
nav a:hover{background:rgba(59,130,246,0.12);color:#60a5fa}
.se{background:#161b2a;border:1px solid rgba(42,48,69,0.5);border-radius:12px;padding:16px;margin-bottom:14px;transition:border-color 0.15s}
.se:hover{border-color:rgba(59,130,246,0.15)}
.sh{display:flex;align-items:center;gap:8px;margin-bottom:14px}
.si{font-size:20px;width:28px;text-align:center}.st{font-size:16px;font-weight:600;color:#f1f5f9}
.scount{font-size:11px;background:rgba(99,102,241,0.1);color:#818cf8;padding:0 8px;border-radius:8px;line-height:20px}
.nc{padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);cursor:pointer;margin:0 -4px;padding:10px 4px;border-radius:4px}
.nc:last-child{border-bottom:none}.nc:hover{background:rgba(255,255,255,0.02)}
.nt{font-size:14px;font-weight:500;color:#f1f5f9;margin-bottom:5px;display:flex;align-items:flex-start;gap:8px}
.ni{display:inline-flex;width:20px;height:20px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;font-size:10px;font-weight:700;border-radius:4px;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px}
.ns{font-size:13px;color:#7c8a9c;margin-bottom:4px;padding-left:28px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.nm{font-size:11px;color:#5a6a7d;padding-left:28px}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.si2{background:rgba(255,255,255,0.02);border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center}
.sn{font-size:12px;color:#94a3b8}.sv{font-size:14px;font-weight:600;color:#f1f5f9}.sc{font-size:12px;font-weight:500}
.up{color:#22c55e}.down{color:#ef4444}.flat{color:#6b7a8d}
.w3d{display:flex;gap:10px}
.wd{flex:1;text-align:center;background:rgba(255,255,255,0.02);border-radius:8px;padding:14px 4px}
.wdn{font-size:12px;color:#94a3b8;margin-bottom:6px}.wdi{font-size:30px;margin-bottom:6px}
.wdt{font-size:14px;font-weight:600;margin-bottom:4px}.wdd{font-size:11px;color:#7c8a9c}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.fi{background:rgba(255,255,255,0.02);border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center}
.fp{font-size:13px;color:#94a3b8}.fr{font-size:14px;font-weight:600;color:#f1f5f9}
footer{margin-top:32px;padding:20px 0;text-align:center;border-top:1px solid rgba(42,48,69,0.4)}
footer p{font-size:11px;color:#5a6a7d;margin-bottom:3px}
  </style></head><body><div class="app">
  <header><div class="tb"><div class="date">📅 ${date}</div><div class="live">${total}条 · 聚合${stats.sources}个来源</div></div>
  <nav>${nav}</nav></header>
  <div style="display:flex;justify-content:space-between;align-items:center;padding:0 2px;margin-bottom:18px">
    <div style="font-size:12px;color:#5a6a7d">点击标题查看详情</div>
    <div style="font-size:12px;color:#5a6a7d">USD/CNY ${fxRates.USD || '--'}</div>
  </div>
  <div class="se" id="s-market"><div class="sh"><span class="si">📊</span><span class="st">全球指数</span><span class="scount">${stocks.length}</span></div><div class="sg">${stockRows}</div></div>
  <div class="se" id="s-weather"><div class="sh"><span class="si">🌤️</span><span class="st">泗阳天气</span></div><div class="w3d">${wRows}</div></div>
  ${secs}
  <div class="se" id="s-forex"><div class="sh"><span class="si">💱</span><span class="st">外汇汇率</span><span class="scount">6</span></div><div class="fg">${fRows}</div></div>
  <div class="se" style="border-style:dashed"><div style="padding:16px;text-align:center;font-size:11px;color:#5a6a7d;line-height:1.7">${sourceStr}<br>每日 08:00 / 12:00 / 18:00 / 22:00 自动更新 · 公开 · 免费 · 仅供参考</div></div>
  <footer><p>📡 数据仅供个人参考 · 不构成投资建议</p></footer>
</div></body></html>`;
}

async function main() {
  const date = getDate();
  console.log('=== 多源聚合新闻 (' + date + ') ===');

  const [ths, wscn, cls, yicai, baidu, gmw, infzm, sina, stocks, fx] = await Promise.all([
    getTHS(), getWallStreet(), getCailian(), getYicai(), getBaiduHot(), getGmw(), getInfzm(), getSina(),
    getStocks(), getForex()
  ]);

  const sources = {};
  [ths, wscn, cls, yicai, baidu, gmw, infzm, sina].forEach(arr => {
    arr.forEach(i => { sources[i.src] = (sources[i.src] || 0) + 1; });
  });
  console.log('\n来源:');
  Object.entries(sources).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
  console.log('  股票:', stocks.length > 0 ? 'live ✅' : 'fallback');
  console.log('  汇率:', fx.USD ? 'live ✅' : 'fallback');

  const allNews = [...ths, ...wscn, ...cls, ...yicai, ...baidu, ...gmw, ...infzm, ...sina];
  const classified = classify(allNews);

  const seen = new Set();
  for (const key of Object.keys(classified)) {
    classified[key] = classified[key].filter(item => {
      const hash = item.t.substring(0, 8);
      if (seen.has(hash)) return false;
      seen.add(hash);
      return true;
    });
  }

  console.log('\n分类:');
  let totalItems = 0;
  Object.entries(classified).forEach(([k,v]) => {
    if (v.length && k !== 'other') { console.log(`  ${k}: ${v}`); totalItems += v.length; }
  });

  const sections = [
    { id:'world', title:'国际要闻', icon:'🌍', tags:[], items: classified.world.length > 1 ? classified.world : classified.world.concat([{t:'国际新闻动态',s:'多源实时聚合',src:'系统'}]) },
    { id:'tech', title:'科技动态', icon:'💻', tags:[], items: classified.tech.length > 1 ? classified.tech : classified.tech.concat([{t:'科技前沿',s:'关注AI与数字产业',src:'系统'}]) },
    { id:'china', title:'A股/民生', icon:'📈', tags:[], items: (classified.china.length + classified.other.length) > 1 ? [...classified.china, ...classified.other] : [{t:'A股市场',s:'沪深两市动态',src:'系统'}] },
    { id:'finance', title:'财经焦点', icon:'💰', tags:[], items: classified.finance.length > 1 ? classified.finance : classified.finance.concat([{t:'金融市场',s:'宏观经济与资本动态',src:'系统'}]) },
    { id:'sports', title:'体育赛事', icon:'⚽', tags:[], items: classified.sports.length > 1 ? classified.sports : [{t:'体育资讯',s:'最新赛事情报',src:'系统'}] },
    { id:'entertain', title:'文娱热点', icon:'🎬', tags:[], items: classified.entertain.length > 1 ? classified.entertain : [{t:'文化娱乐',s:'影视音乐游戏动态',src:'系统'}] },
    { id:'health', title:'健康生活', icon:'💪', tags:[], items: classified.health.length > 1 ? classified.health : [{t:'健康养生',s:'医疗健康资讯',src:'系统'}] },
    { id:'today', title:'历史上的今天', icon:'📅', tags:[],
      items:[
        {t:'1519 — 达·芬奇逝世',s:'意大利文艺复兴巨匠，《蒙娜丽莎》《最后的晚餐》作者',src:'历史百科'},
        {t:'1957 — 麦卡锡逝世',s:'美国参议员约瑟夫·麦卡锡，麦卡锡主义主导者',src:'历史百科'},
        {t:'2003 — 中国海军首次环球航行',s:'青岛号驱逐舰和太仓号补给舰编队启航',src:'人民海军'}
      ]
    }
  ];

  const total = sections.reduce((a,s) => a + s.items.length, 0);
  console.log('\n展示:', total, '条 | 来源:', Object.keys(sources).length);
  console.log('  同花顺:', ths.length, '| 华尔街见闻:', wscn.length, '| 财联社:', cls.length);
  console.log('  第一财经:', yicai.length, '| 百度热搜:', baidu.length, '| 光明网:', gmw.length);
  console.log('  南方周末:', infzm.length, '| 新浪财经:', sina.length);

  const html = buildPage(date, sections,
    stocks.length ? stocks : [{n:'上证指数',v:'--',c:'--',cls:'flat'},{n:'深证成指',v:'--',c:'--',cls:'flat'},{n:'创业板指',v:'--',c:'--',cls:'flat'},{n:'科创50',v:'--',c:'--',cls:'flat'}],
    [{d:'今天',i:'🌧️',t:'14~17°C',c:'小雨转阴'},{d:'明天',i:'🌫️',t:'11~17°C',c:'雾转阵雨'},{d:'后天',i:'☀️',t:'10~25°C',c:'晴'}],
    fx.USD ? fx : { USD:'6.85',EUR:'8.00',JPY:'0.043',GBP:'9.26',HKD:'0.87',KRW:'0.0046' },
    { sources: Object.keys(sources).length }
  );

  fs.writeFileSync('index.html', html, 'utf8');
  console.log('\n✅ 生成:', html.length, 'bytes');
}

main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
