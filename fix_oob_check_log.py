# -*- coding: utf-8 -*-
import re, os
LOG = r'C:\Games\Vic2LV2\Victoria 2\Новый текстовый документ.txt'
UNITS = r'C:\Games\Vic2LV2\Victoria 2\mod\5\history\units'
pat = re.compile(r"Unit '([^']+)' is set as from another country")
with open(LOG, encoding='utf-8', errors='replace') as f:
    units = pat.findall(f.read())
print('Log error units:', len(units))
still = []
for u in units:
    found = []
    for fname in os.listdir(UNITS):
        path = os.path.join(UNITS, fname)
        with open(path, encoding='cp1251', errors='replace') as f:
            if u in f.read():
                found.append(fname)
    if found:
        still.append((u, found))
    else:
        print('REMOVED:', u)
print('Still present:', len(still))
for u, fs in still[:20]:
    print(u, '->', fs)
