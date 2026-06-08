# -*- coding: utf-8 -*-
import re, glob, os
from collections import Counter

MOD = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(MOD, 'fix_oob_apply.py'), encoding='utf-8').read().split('def main')[0])

owners = load_province_owners()
oob_to, _ = load_oob_to_countries()

problems = []
for fname in os.listdir(os.path.join(MOD, 'history', 'units')):
    if not fname.endswith('.txt'):
        continue
    countries = [c for c in oob_to.get(fname, []) if c not in REMOVE_OOB_COUNTRIES]
    if not countries:
        continue
    path = os.path.join(MOD, 'history', 'units', fname)
    with open(path, encoding='cp1251', errors='replace') as f:
        lines = f.readlines()
    in_army = False
    in_reg = False
    loc = None
    reg_home = None
    reg_name = None
    for line in lines:
        if re.match(r'\s*army\s*=\s*\{', line):
            in_army = True
            loc = None
        m = re.match(r'\s*location\s*=\s*(\d+)', line)
        if m and in_army:
            loc = int(m.group(1))
        if re.match(r'\s*regiment\s*=\s*\{', line):
            in_reg = True
            reg_home = None
            reg_name = None
        if in_reg:
            m = re.match(r'\s*name\s*=\s*"([^"]*)"', line)
            if m:
                reg_name = m.group(1)
            m = re.match(r'\s*home\s*=\s*(\d+)', line)
            if m:
                reg_home = int(m.group(1))
        if line.strip() == '}' and in_reg:
            in_reg = False
            if not regiment_valid(reg_home, loc, countries, owners):
                problems.append((fname, reg_name, reg_home, owners.get(reg_home), loc, owners.get(loc)))
        if line.strip() == '}' and in_army and not in_reg:
            in_army = False

print('Remaining invalid regiments:', len(problems))
for p in problems[:30]:
    print(p)

LOG = r'C:\Games\Vic2LV2\Victoria 2\Новый текстовый документ.txt'
if os.path.isfile(LOG):
    pat = re.compile(r"Unit '([^']+)' is set as from another country")
    with open(LOG, encoding='utf-8', errors='replace') as f:
        log_units = set(pat.findall(f.read()))
    still = []
    for fname in os.listdir(os.path.join(MOD, 'history', 'units')):
        path = os.path.join(MOD, 'history', 'units', fname)
        with open(path, encoding='cp1251', errors='replace') as f:
            text = f.read()
        for u in log_units:
            if u in text:
                still.append((u, fname))
    print('Log units still in OOB files:', len(still))
    for u, f in still[:25]:
        print(' ', u, '->', f)
