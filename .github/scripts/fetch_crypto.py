#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""加密货币实时行情 - 通过 PRISM API 免费获取 Top 10 币种价格"""
import json, urllib.request, sys

TOKENS = ['BTC', 'ETH', 'SOL', 'XRP', 'BNB', 'DOGE', 'ADA', 'AVAX', 'DOT', 'LINK']

def main():
    items = []
    for sym in TOKENS:
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(
                    f'https://api.prismapi.ai/crypto/price/{sym}?currency=USD',
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
                ), timeout=8
            )
            data = json.loads(r.read().decode())
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
                print(f'  {sym}: no data')
        except Exception as e:
            print(f'  {sym}: {type(e).__name__}')
    
    with open('crypto.json', 'w', encoding='utf-8') as f:
        json.dump({'crypto': items}, f, ensure_ascii=False)
    print(f'加密货币: {len(items)}条')

if __name__ == '__main__':
    main()
