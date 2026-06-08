# -*- coding: utf-8 -*-
"""Find OOB units with home/location province owned by another country."""
import os
import re
import glob
from collections import defaultdict

MOD = r'C:\Games\Vic2LV2\Victoria 2\mod\5'
PROV_DIR = os.path.join(MOD, 'history', 'provinces')
COUNTRY_DIR = os.path.join(MOD, 'history', 'countries')
UNITS_DIR = os.path.join(MOD, 'history', 'units')
LOG = r'C:\Games\Vic2LV2\Victoria 2\Новый текстовый документ.txt'


def load_province_owners():
    owners = {}
    for path in glob.glob(os.path.join(PROV_DIR, '**', '*.txt'), recursive=True):
        m = re.search(r'(\d+)\s*-', os.path.basename(path))
        if not m:
            continue
        pid = int(m.group(1))
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                if line.startswith('owner = '):
                    owners[pid] = line.split('=', 1)[1].strip()
                    break
    return owners


def load_oob_to_country():
    mapping = defaultdict(list)
    tags = set()
    for path in glob.glob(os.path.join(COUNTRY_DIR, '*.txt')):
        tag = os.path.basename(path).split(' - ')[0].split('.')[0]
        tags.add(tag)
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                m = re.match(r'\s*oob\s*=\s*"([^"]+)"', line)
                if m:
                    mapping[m.group(1)].append(tag)
    return mapping, tags


def find_unit_in_oobs(name):
    hits = []
    for fname in os.listdir(UNITS_DIR):
        if not fname.endswith('.txt'):
            continue
        path = os.path.join(UNITS_DIR, fname)
        with open(path, encoding='cp1251', errors='replace') as f:
            text = f.read()
        if name in text:
            hits.append(fname)
    return hits


def scan_all_oob(owners, oob_to_country):
    problems = []
    for fname in os.listdir(UNITS_DIR):
        if not fname.endswith('.txt'):
            continue
        countries = oob_to_country.get(fname, [])
        country = countries[0] if len(countries) == 1 else countries
        path = os.path.join(UNITS_DIR, fname)
        with open(path, encoding='cp1251', errors='replace') as f:
            lines = f.readlines()

        in_reg = False
        in_army = False
        loc = None
        reg_name = None
        reg_home = None
        army_name = None

        for i, line in enumerate(lines):
            m = re.match(r'\s*army\s*=\s*\{', line)
            if m:
                in_army = True
                loc = None
                army_name = None
            m = re.match(r'\s*name\s*=\s*"([^"]*)"', line)
            if m and in_army and not in_reg:
                army_name = m.group(1)
            m = re.match(r'\s*location\s*=\s*(\d+)', line)
            if m and in_army:
                loc = int(m.group(1))
            m = re.match(r'\s*regiment\s*=\s*\{', line)
            if m:
                in_reg = True
                reg_name = None
                reg_home = None
            if in_reg:
                m = re.match(r'\s*name\s*=\s*"([^"]*)"', line)
                if m:
                    reg_name = m.group(1)
                m = re.match(r'\s*home\s*=\s*(\d+)', line)
                if m:
                    reg_home = int(m.group(1))
            if line.strip() == '}' and in_reg:
                in_reg = False
                if reg_home is not None and countries:
                    for c in countries:
                        ho = owners.get(reg_home)
                        lo = owners.get(loc) if loc else None
                        if ho != c:
                            problems.append({
                                'file': fname, 'country': c, 'countries': countries,
                                'unit': reg_name, 'home': reg_home, 'home_owner': ho,
                                'location': loc, 'loc_owner': lo, 'army': army_name,
                            })
            if line.strip() == '}' and in_army and not in_reg:
                in_army = False

    return problems


def main():
    owners = load_province_owners()
    oob_to_country, tags = load_oob_to_country()
    print('Province owners loaded:', len(owners))
    print('Country tags:', len(tags))

    # Log errors
    if os.path.isfile(LOG):
        pat = re.compile(r"Unit '([^']+)' is set as from another country")
        with open(LOG, encoding='utf-8', errors='replace') as f:
            log_units = pat.findall(f.read())
        print('Log errors:', len(log_units))
        for u in log_units[:5]:
            print(' ', u, '->', find_unit_in_oobs(u))

    problems = scan_all_oob(owners, oob_to_country)
    print('Home mismatch problems:', len(problems))

    by_file = defaultdict(list)
    for p in problems:
        by_file[p['file']].append(p)

    for fname in sorted(by_file.keys()):
        items = by_file[fname]
        print('\n%s (%d issues, countries=%s)' % (
            fname, len(items), items[0]['countries']))
        for p in items[:5]:
            print('  %s home=%s(%s) loc=%s(%s)' % (
                p['unit'], p['home'], p['home_owner'],
                p['location'], p['loc_owner']))

    # OOB files with no country
    orphan = [f for f in os.listdir(UNITS_DIR)
              if f.endswith('_oob.txt') and f not in oob_to_country]
    print('\nOrphan OOB files (no country ref):', orphan)

    # Countries referencing missing OOB
    missing = [t for t, f in
               [(t, m.group(1)) for t in tags
                for path in [os.path.join(COUNTRY_DIR, t + '.txt')]
                if False]]
    for path in glob.glob(os.path.join(COUNTRY_DIR, '*.txt')):
        tag = os.path.basename(path).split(' - ')[0].split('.')[0]
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                m = re.match(r'\s*oob\s*=\s*"([^"]+)"', line)
                if m and not os.path.isfile(os.path.join(UNITS_DIR, m.group(1))):
                    print('Missing OOB for', tag, ':', m.group(1))


if __name__ == '__main__':
    main()
