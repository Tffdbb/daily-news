#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量化选股日追踪：记录每日TOP结果到CSV"""
import json, datetime, os, csv

CSV_FILE = 'quant_track.csv'

def main():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M')
    
    try:
        with open('quant_picks.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        print('quant_picks.json not found, skip tracking')
        return
    
    picks = data.get('picks', [])
    if not picks:
        print('No picks to track')
        return
    
    # 构建行：日期,时间,股票1(评分1),股票2(评分2),...,上证,深证
    row = [date_str, time_str]
    for p in picks[:10]:
        name = p.get('name','?')
        score = p.get('score',0)
        chg = p.get('chg',0)
        row.append(f'{name}({score}分,{chg:+.2f}%)')
    
    # 补足10只
    while len(row) < 12:
        row.append('')
    
    # 写CSV
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            headers = ['日期','时间'] + [f'TOP{i+1}' for i in range(10)]
            writer.writerow(headers)
        writer.writerow(row)
    
    print(f'量化追踪: {date_str} {time_str} → {len(picks)}只记录')

if __name__ == '__main__':
    main()
