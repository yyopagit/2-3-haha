# -*- coding: utf-8 -*-
"""Remove invalid OOB regiments and oob refs for broken/missing countries."""
import os
import re
import glob
import shutil
from collections import defaultdict

MOD = os.path.dirname(os.path.abspath(__file__))
PROV_DIR = os.path.join(MOD, 'history', 'provinces')
COUNTRY_DIR = os.path.join(MOD, 'history', 'countries')
UNITS_DIR = os.path.join(MOD, 'history', 'units')
BACKUP_DIR = os.path.join(MOD, 'history', 'units_backup')
LOG = os.path.join(MOD, 'fix_oob_log.txt')

# Страны с отсутствующим OOB или явно неверным определением — убираем oob полностью
REMOVE_OOB_COUNTRIES = {
    'ASH', 'AYS', 'BAG', 'BEN', 'BYG', 'BYN', 'DAR', 'DCH', 'FUG', 'GEL',
    'GOB', 'GOD', 'HAR', 'ISA', 'KAA', 'KAF', 'MAS', 'OIO', 'TIG', 'VAI',
    'COL',   # Columbia с канадским capital/culture
    'LEV',   # общий LIB_oob с Liberia
    'NAM',   # общий LIB_oob с Liberia
}

ORPHAN_OOB_DELETE = {'KRA_oob.txt', 'SHI_oob.txt'}


def parse_owner_line(line):
    val = line.split('=', 1)[1].strip()
    if '#' in val:
        val = val.split('#')[0].strip()
    return val


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
                    owners[pid] = parse_owner_line(line)
                    break
    return owners


def load_oob_to_countries():
    mapping = defaultdict(list)
    country_oob = {}
    for path in glob.glob(os.path.join(COUNTRY_DIR, '*.txt')):
        tag = os.path.basename(path).split(' - ')[0].split('.')[0]
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                m = re.match(r'\s*oob\s*=\s*"([^"]+)"', line)
                if m:
                    fname = m.group(1)
                    mapping[fname].append(tag)
                    country_oob[tag] = (path, fname, line)
    return mapping, country_oob


def regiment_valid(home, location, countries, owners):
    if home is None:
        return False
    home_owner = owners.get(home)
    if home_owner is None or home_owner not in countries:
        return False
    if location is not None:
        loc_owner = owners.get(location)
        if loc_owner is None or loc_owner not in countries:
            return False
    return True


def clean_oob_file(path, countries, owners):
    with open(path, encoding='cp1251', errors='replace') as f:
        lines = f.readlines()

    out = []
    i = 0
    removed_regiments = 0
    removed_armies = 0

    while i < len(lines):
        line = lines[i]
        if re.match(r'\s*army\s*=\s*\{', line):
            block = [line]
            i += 1
            depth = 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count('{') - lines[i].count('}')
                i += 1
            cleaned, rm_reg, rm_army = clean_army_block(block, countries, owners)
            removed_regiments += rm_reg
            if rm_army:
                removed_armies += 1
            else:
                out.extend(cleaned)
            continue

        out.append(line)
        i += 1

    return out, removed_regiments, removed_armies


def clean_army_block(block, countries, owners):
    header = []
    regiments = []
    footer = []
    loc = None
    i = 1
    while i < len(block) - 1:
        line = block[i]
        m = re.match(r'\s*location\s*=\s*(\d+)', line)
        if m:
            loc = int(m.group(1))
            header.append(line)
            i += 1
            continue
        m = re.match(r'\s*name\s*=\s*"', line)
        if m and not regiments:
            header.append(line)
            i += 1
            continue
        if re.match(r'\s*regiment\s*=\s*\{', line):
            reg_block = [line]
            i += 1
            depth = 1
            while i < len(block) - 1 and depth > 0:
                reg_block.append(block[i])
                depth += block[i].count('{') - block[i].count('}')
                i += 1
            regiments.append(reg_block)
            continue
        header.append(line)
        i += 1

    kept = []
    removed = 0
    for reg_block in regiments:
        home = None
        for rl in reg_block:
            m = re.match(r'\s*home\s*=\s*(\d+)', rl)
            if m:
                home = int(m.group(1))
        if regiment_valid(home, loc, countries, owners):
            kept.append(reg_block)
        else:
            removed += 1

    if not kept:
        return [], removed, True

    out = [block[0]]
    out.extend(header)
    for reg in kept:
        out.extend(reg)
    out.append(block[-1])
    return out, removed, False


def remove_oob_from_countries(country_oob):
    removed = []
    for tag in REMOVE_OOB_COUNTRIES:
        if tag not in country_oob:
            continue
        path, _, line = country_oob[tag]
        with open(path, encoding='utf-8', errors='replace') as f:
            content = f.read()
        if line.strip() not in content:
            continue
        new_content = content.replace(line, '# removed invalid oob: ' + line.strip() + '\n')
        with open(path, 'w', encoding='utf-8', errors='replace', newline='') as f:
            f.write(new_content)
        removed.append(tag)
    return removed


def main():
    owners = load_province_owners()
    oob_to_countries, country_oob = load_oob_to_countries()
    log = []

    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    total_reg = 0
    total_army = 0
    files_changed = 0

    for fname in sorted(os.listdir(UNITS_DIR)):
        if not fname.endswith('.txt'):
            continue
        if fname in ORPHAN_OOB_DELETE:
            src = os.path.join(UNITS_DIR, fname)
            dst = os.path.join(BACKUP_DIR, fname)
            shutil.move(src, dst)
            log.append('Deleted orphan OOB: ' + fname)
            continue

        countries = oob_to_countries.get(fname)
        if not countries:
            continue
        # Не чистим OOB если все страны-владельцы в списке удаления
        active = [c for c in countries if c not in REMOVE_OOB_COUNTRIES]
        if not active:
            src = os.path.join(UNITS_DIR, fname)
            dst = os.path.join(BACKUP_DIR, fname)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                with open(src, 'w', encoding='cp1251', errors='replace', newline='') as f:
                    f.write('# armies removed - no valid country\n')
                log.append('Emptied OOB (no valid country): ' + fname)
            continue

        path = os.path.join(UNITS_DIR, fname)
        new_lines, rm_reg, rm_army = clean_oob_file(path, active, owners)
        if rm_reg or rm_army:
            shutil.copy2(path, os.path.join(BACKUP_DIR, fname))
            with open(path, 'w', encoding='cp1251', errors='replace', newline='') as f:
                f.writelines(new_lines)
            files_changed += 1
            total_reg += rm_reg
            total_army += rm_army
            log.append('%s: removed %d regiments, %d armies (countries=%s)' % (
                fname, rm_reg, rm_army, ','.join(active)))

    removed_tags = remove_oob_from_countries(country_oob)
    log.append('Removed oob ref from countries: ' + ', '.join(removed_tags))

    summary = (
        'OOB files changed: %d, regiments removed: %d, armies removed: %d, '
        'countries unlinked: %d' % (files_changed, total_reg, total_army, len(removed_tags))
    )
    log.insert(0, summary)
    with open(LOG, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log))
    print(summary)
    for line in log[1:11]:
        print(line)


if __name__ == '__main__':
    main()
