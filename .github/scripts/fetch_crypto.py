#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""加密货币实时行情 - 通过 PRISM API 获取 Top 10，兼容各种 SSL 环境"""
import json, subprocess, sys, os

TOKENS = ['BTC', 'ETH', 'SOL', 'XRP', 'BNB', 'DOGE', 'ADA', 'AVAX', 'DOT', 'LINK']

def fetch_with_curl(symbol):
    """使用 curl 获取，最兼容 Actions 环境"""
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '6',
             f'https://api.prismapi.ai/crypto/price/{symbol}?currency=USD'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    return None

def main():
    items = []
    for sym in TOKENS:
        data = fetch_with_curl(sym)
        if data and data.get('price_usd'):
            items.append({
                'symbol': sym,
                'price': round(data['price_usd'], 2),
                'change_24h': round(data.get('change_24h_pct', 0) * 100, 2),
                'volume_24h': int(data.get('volume_24h', 0)),
                'src': 'Crypto'
            })
            print(f'  {sym}: ${items[-1]["price"]} ({items[-1]["change_24h"]:+.2f}%)')
        else:
            print(f'  {sym}: FAIL')

    with open('crypto.json', 'w', encoding='utf-8') as f:
        json.dump({'crypto': items}, f, ensure_ascii=False)
    print(f'加密货币: {len(items)}条')

if __name__ == '__main__':
    main()
