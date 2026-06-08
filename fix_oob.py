# -*- coding: utf-8 -*-
"""Analyze and fix OOB / subunit country mismatches."""
import os
import re
import glob

MOD = r'C:\Games\Vic2LV2\Victoria 2\mod\5'
PROV_DIR = os.path.join(MOD, 'history', 'provinces')
COUNTRY_DIR = os.path.join(MOD, 'history', 'countries')
UNITS_DIR = os.path.join(MOD, 'history', 'units')
LOG_FILES = [
    os.path.join(MOD, 'complete_output.txt'),
    os.path.join(MOD, 'test_ps.txt'),
    r'C:\Games\Vic2LV2\Victoria 2\Новый текстовый документ.txt',
]


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


def load_country_tags():
    tags = set()
    oob_refs = {}
    for path in glob.glob(os.path.join(COUNTRY_DIR, '*.txt')):
        base = os.path.basename(path)
        tag = base.split(' - ')[0].split('.')[0]
        tags.add(tag)
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                m = re.match(r'\s*oob\s*=\s*"([^"]+)"', line)
                if m:
                    oob_refs[tag] = m.group(1)
    return tags, oob_refs


def parse_oob(path):
    blocks = []
    current = None
    with open(path, encoding='cp1251', errors='replace') as f:
        for line in f:
            m = re.match(r'\s*(army|navy)\s*=\s*\{', line)
            if m:
                current = {'type': m.group(1), 'location': None, 'regiments': [], 'ships': []}
                continue
            if current is None:
                continue
            m = re.match(r'\s*location\s*=\s*(\d+)', line)
            if m:
                current['location'] = int(m.group(1))
            m = re.match(r'\s*regiment\s*=\s*\{', line)
            if m:
                current['regiments'].append({'home': None, 'name': ''})
                continue
            if current['regiments']:
                m = re.match(r'\s*home\s*=\s*(\d+)', line)
                if m:
                    current['regiments'][-1]['home'] = int(m.group(1))
                m = re.match(r'\s*name\s*=\s*"([^"]*)"', line)
                if m:
                    current['regiments'][-1]['name'] = m.group(1)
            if line.strip() == '}':
                if current['regiments'] or current['ships'] or current['location'] is not None:
                    blocks.append(current)
                current = None
    return blocks


def parse_log_errors():
    pattern = re.compile(r"Unit '([^']+)' is set as from another country")
    errors = []
    for log in LOG_FILES:
        if not os.path.isfile(log) or os.path.getsize(log) == 0:
            continue
        with open(log, encoding='utf-8', errors='replace') as f:
            text = f.read()
        errors.extend(pattern.findall(text))
    return errors


def main():
    owners = load_province_owners()
    tags, oob_refs = load_country_tags()
    print('Countries:', len(tags))
    print('OOB references:', len(oob_refs))
    print('Existing OOB files:', os.listdir(UNITS_DIR))

    # Check NET_oob mismatches
    net_path = os.path.join(UNITS_DIR, 'NET_oob.txt')
    if os.path.isfile(net_path):
        for block in parse_oob(net_path):
            loc = block['location']
            loc_owner = owners.get(loc, '?')
            for reg in block['regiments']:
                home = reg['home']
                home_owner = owners.get(home, '?')
                if home_owner != 'NET' or loc_owner != 'NET':
                    print('NET mismatch:', reg['name'], 'loc', loc, loc_owner, 'home', home, home_owner)

    errors = parse_log_errors()
    print('Log subunit errors:', len(errors))
    if errors:
        print('Sample:', errors[:20])

    missing_oob = [tag for tag, fname in oob_refs.items() if not os.path.isfile(os.path.join(UNITS_DIR, fname))]
    print('Missing OOB files (use vanilla):', len(missing_oob))


if __name__ == '__main__':
    main()
