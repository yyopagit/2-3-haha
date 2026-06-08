# -*- coding: utf-8 -*-
"""Fix duplicate D*_ADJ lines and trailing REGION keys in a.csv."""
import os

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a.csv')
ENC = 'cp1251'

with open(CSV, encoding=ENC, errors='replace') as f:
    lines = f.readlines()

seen = set()
out = []
seen_region_trio = set()

for line in lines:
    key = line.split(';', 1)[0] if line.strip() else ''
    if key in ('REGION', 'VALUE', 'VAL'):
        if key in seen_region_trio:
            continue
        seen_region_trio.add(key)
    if key.endswith('_ADJ') and key in seen:
        continue
    if key:
        if key in seen and key.startswith('D') and '_ADJ' not in key:
            continue
        seen.add(key)
    out.append(line)

with open(CSV, 'w', encoding=ENC, errors='replace', newline='') as f:
    f.writelines(out)

print('Lines:', len(lines), '->', len(out))
