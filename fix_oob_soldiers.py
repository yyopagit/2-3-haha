# -*- coding: utf-8 -*-
"""Remove OOB regiments when home province lacks soldier pops (subunit.cpp:913)."""
import os
import re
import glob
import shutil
from collections import defaultdict

MOD = os.path.dirname(os.path.abspath(__file__))
POPS_DIR = os.path.join(MOD, 'history', 'pops')
UNITS_DIR = os.path.join(MOD, 'history', 'units')
BACKUP_DIR = os.path.join(MOD, 'history', 'units_backup_pass4')
LOG = os.path.join(MOD, 'fix_oob_log.txt')

BRIGADE_SOLDIERS = 3000


def load_soldiers_by_province():
    soldiers = defaultdict(int)
    prov_re = re.compile(r'^(\d+)\s*=\s*\{')
    pop_re = re.compile(r'^\s*soldiers\s*=\s*\{')
    size_re = re.compile(r'^\s*size\s*=\s*(\d+)')
    for path in glob.glob(os.path.join(POPS_DIR, '1836.1.1', '*.txt')):
        current = None
        in_soldiers = False
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                m = prov_re.match(line)
                if m:
                    current = int(m.group(1))
                    in_soldiers = False
                    continue
                if pop_re.match(line):
                    in_soldiers = True
                    continue
                if in_soldiers:
                    m = size_re.match(line)
                    if m and current is not None:
                        soldiers[current] += int(m.group(1))
                    if line.strip() == '}':
                        in_soldiers = False
    return soldiers


def clean_army_block(block, soldiers, usage):
    header = []
    regiments = []
    i = 1
    while i < len(block) - 1:
        line = block[i]
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
        avail = soldiers.get(home, 0)
        used = usage[home]
        if home is None or used + BRIGADE_SOLDIERS > avail:
            removed += 1
            continue
        usage[home] += BRIGADE_SOLDIERS
        kept.append(reg_block)

    if not kept:
        return [], removed, True
    out = [block[0]]
    out.extend(header)
    for reg in kept:
        out.extend(reg)
    out.append(block[-1])
    return out, removed, False


def clean_oob_file(path, soldiers):
    with open(path, encoding='cp1251', errors='replace') as f:
        lines = f.readlines()
    usage = defaultdict(int)
    out = []
    i = 0
    removed_reg = 0
    removed_army = 0
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
            cleaned, rm, rm_army = clean_army_block(block, soldiers, usage)
            removed_reg += rm
            if rm_army:
                removed_army += 1
            else:
                out.extend(cleaned)
            continue
        out.append(line)
        i += 1
    return out, removed_reg, removed_army


def main():
    soldiers = load_soldiers_by_province()
    print('Provinces with soldiers data:', len(soldiers))
    if not os.path.isdir(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    total_reg = 0
    total_army = 0
    files_changed = 0
    log_lines = []

    for fname in sorted(os.listdir(UNITS_DIR)):
        if not fname.endswith('.txt'):
            continue
        path = os.path.join(UNITS_DIR, fname)
        new_lines, rm_reg, rm_army = clean_oob_file(path, soldiers)
        if rm_reg or rm_army:
            shutil.copy2(path, os.path.join(BACKUP_DIR, fname))
            with open(path, 'w', encoding='cp1251', errors='replace', newline='') as f:
                f.writelines(new_lines)
            files_changed += 1
            total_reg += rm_reg
            total_army += rm_army
            log_lines.append('%s: -%d regiments, -%d armies' % (fname, rm_reg, rm_army))

    summary = 'Pass 4 soldiers: files=%d regiments=%d armies=%d' % (
        files_changed, total_reg, total_army)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write('\n' + summary + '\n')
        f.write('\n'.join(log_lines[:40]))
        if len(log_lines) > 40:
            f.write('\n... and %d more files' % (len(log_lines) - 40))
    print(summary)
    for line in log_lines[:15]:
        print(line)


if __name__ == '__main__':
    main()
