# -*- coding: utf-8 -*-
"""Remove reserved substitution keys from a.csv (engine registers them internally)."""
import os

MOD_DIR = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(MOD_DIR, 'a.csv')
VARS = os.path.join(MOD_DIR, '00_variables.csv')
ENC = 'cp1251'

# Встроенные имена подстановок Clausewitz/Vic2 — нельзя объявлять в csv (Duplicate text-key)
RESERVED = {
    'REGION', 'VALUE', 'VAL', 'WHERE', 'NUM', 'NAME', 'COUNTRY', 'DIRECTION',
    'POPTYPE', 'OPTIMAL', 'FRACTION', 'OPT', 'SETTING', 'MONTH', 'YEAR', 'TAG',
    'PROVINCE', 'STATE', 'CONTINENT', 'GOODS', 'PARTY', 'IDEOLOGY', 'REFORM',
    'TECH', 'BUILDING',
}

if os.path.isfile(VARS):
    os.remove(VARS)

removed = 0
out = []
with open(CSV, encoding=ENC, errors='replace') as f:
    for line in f:
        key = line.split(';', 1)[0] if line.strip() else ''
        if key in RESERVED:
            removed += 1
            continue
        out.append(line)

with open(CSV, 'w', encoding=ENC, errors='replace', newline='') as f:
    f.writelines(out)

print('Removed reserved keys:', removed, 'lines left:', len(out))
