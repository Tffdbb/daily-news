#!/usr/bin/env node
/** A股量化选股 - 多因子策略（成交量异动 + 趋势强度 + 资金活跃）*/
const https = require('https');
const fs = require('fs');

function get(url) {
  return new Promise((resolve, reject) => {
    const proto = url.startsWith('https') ? https : http;
    proto.get(url, { timeout: 10000, headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve(d));
    }).on('error', reject);
  });
}

const FIELDS = 'f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23,f25,f37,f38,f62,f115,f152,f168,f169,f170,f171';

async function fetchStocks(page, pz) {
  // fid=f62 按成交额降序取，覆盖最活跃的股票
  const url = `https://push2.eastmoney.com/api/qt/clist/get?pn=${page}&pz=${pz}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f62&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=${FIELDS}`;
  try {
    const text = await get(url);
    const j = JSON.parse(text);
    return { stocks: j.data?.diff || [], total: j.data?.total || 0 };
  } catch { return { stocks: [], total: 0 }; }
}

function pick(stocks) {
  const candidates = [];
  for (const s of stocks) {
    const name = s.f14 || '';
    const code = s.f12 || '';
    // 过滤ST/退市
    if (name.includes('ST') || name.includes('退') || name.includes('N')) continue;
    const chg = s.f3 || 0;
    // 涨幅>1%且<18%（非涨停，但要有趋势）
    if (chg < 1.0 || chg > 18.0) continue;
    const volRatio = s.f23 || 0;
    if (volRatio < 0.8) continue; // 不放量就不看
    const turnover = s.f38 || 0;
    if (turnover < 0.5) continue;
    const pe = s.f115 || 0;
    // PE负数（亏损）不作为排除条件，但要降级
    if (pe && pe > 500) continue;
    const price = s.f2 || 0;
    const amt = (s.f62 || 0) / 1e8;
    const circCap = (s.f21 || 1) / 1e10;

    // 综合评分
    // f38字段是累计值（原始），实际换手率%在东方财富用f38=成交量/流通股本
    // 实际f38单位已是%，但值是整数如 4.31 表示4.31%
    // 如果turnover值>100说明是原始累计值，/10
    const realTurnover = turnover > 100 ? turnover / 1e8 : turnover;
    let score = 0;
    score += Math.min(chg / 5, 1.5) * 20;       // 涨幅
    score += Math.min(volRatio / 3, 1.5) * 20;   // 量比
    score += Math.min(realTurnover / 5, 1.0) * 15;   // 换手
    score += Math.min(amt / 5, 1.0) * 15;        // 成交额
    score += Math.min(circCap / 30, 1.0) * 15;   // 市值
    if (pe && pe > 10 && pe < 50) score += 15;         // PE适中

    // 换手率显示简化（f38原始值无法直接转%）
    const turnDisplay = turnover > 1e6 ? (turnover/1e8).toFixed(1) + '%' : turnover.toFixed(1) + '%';
    candidates.push({ name, code, price: price, chg, volRatio, turnover: turnDisplay, pe: Math.round(pe || 0), amt: Math.round(amt*10)/10, score: Math.round(score*10)/10 });
  }
  candidates.sort((a, b) => b.score - a.score);
  return candidates.slice(0, 10);
}

async function main() {
  let all = [];
  // 按成交额（f62）取前500只，比按涨幅更合理
  for (const page of [1, 2, 3, 4, 5]) {
    const { stocks } = await fetchStocks(page, 100);
    all = all.concat(stocks);
    if (stocks.length < 100) break;
  }
  const picks = pick(all);
  const result = { time: new Date().toLocaleString('zh-CN', {timeZone:'Asia/Shanghai'}), totalStocks: all.length, picks };
  fs.writeFileSync('quant_picks.json', JSON.stringify(result, null, 2), 'utf8');
  console.log(`扫描${all.length}只, 选出${picks.length}只`);
  for (const p of picks) {
    console.log(`  ${p.code} ${p.name} 涨幅${p.chg >= 0 ? '+' : ''}${p.chg}% 量比${p.volRatio} 换手${p.turnover}% PE${p.pe} 成交${p.amt}亿 评分${p.score}`);
  }
}

main().catch(e => { console.error(e); process.exit(1); });
