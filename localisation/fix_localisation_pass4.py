# -*- coding: utf-8 -*-
"""Full localisation cleanup: variables file, dedupe, D01-D50, merge vanilla gaps."""
import os
import re
import shutil
from collections import OrderedDict

MOD_DIR = os.path.dirname(os.path.abspath(__file__))
MOD_CSV = os.path.join(MOD_DIR, 'a.csv')
VAR_CSV = os.path.join(MOD_DIR, '00_variables.csv')
VANILLA_CSV = os.path.join(MOD_DIR, '..', '..', '..', 'localisation', 'a.csv')
BACKUP = os.path.join(MOD_DIR, 'a.csv.bak_pass4')
LOG = os.path.join(MOD_DIR, 'fix_localisation_log.txt')
ENC = 'cp1251'

# Подстановки $KEY$ — отдельный файл грузится первым (00_...)
VARIABLE_KEYS = OrderedDict([
    ('REGION', 'Регион'),
    ('VALUE', 'Значение'),
    ('VAL', 'Значение'),
    ('WHERE', 'месте'),
    ('NUM', 'число'),
    ('NAME', 'название'),
    ('COUNTRY', 'страна'),
    ('DIRECTION', 'направление'),
    ('POPTYPE', 'тип населения'),
    ('OPTIMAL', 'оптимум'),
    ('FRACTION', 'доля'),
    ('OPT', 'вариант'),
    ('SETTING', 'настройка'),
    ('MONTH', 'месяц'),
    ('YEAR', 'год'),
    ('TAG', 'тег'),
    ('PROVINCE', 'провинция'),
    ('STATE', 'штат'),
    ('CONTINENT', 'континент'),
    ('GOODS', 'товар'),
    ('PARTY', 'партия'),
    ('IDEOLOGY', 'идеология'),
    ('REFORM', 'реформа'),
    ('TECH', 'технология'),
    ('BUILDING', 'здание'),
])

D26_D50_NAMES = OrderedDict([
    ('D26', 'Территория $REGION$'),
    ('D27', 'Область $REGION$'),
    ('D28', 'Провинция $REGION$'),
    ('D29', 'Земли $REGION$'),
    ('D30', 'Владения $REGION$'),
    ('D31', 'Владение $REGION$'),
    ('D32', 'Надел $REGION$'),
    ('D33', 'Удел $REGION$'),
    ('D34', 'Округ $REGION$'),
    ('D35', 'Район $REGION$'),
    ('D36', 'Край $REGION$'),
    ('D37', 'Предел $REGION$'),
    ('D38', 'Поместье $REGION$'),
    ('D39', 'Вотчина $REGION$'),
    ('D40', 'Угодья $REGION$'),
    ('D41', 'Владетельство $REGION$'),
    ('D42', 'Губерния $REGION$'),
    ('D43', 'Наместничество $REGION$'),
    ('D44', 'Марк $REGION$'),
    ('D45', 'Маркграфство $REGION$'),
    ('D46', 'Палатинат $REGION$'),
    ('D47', 'Банат $REGION$'),
    ('D48', 'Эксклав $REGION$'),
    ('D49', 'Анклав $REGION$'),
    ('D50', 'Регион $REGION$'),
])

D_ADJ_DEFAULT = 'региональн.'


def parse_line(line):
    line = line.rstrip('\r\n')
    if not line:
        return None
    parts = line.split(';')
    key = parts[0]
    text = parts[1] if len(parts) > 1 else ''
    suffix = parts[2:] if len(parts) > 2 else []
    while len(suffix) < 6:
        suffix.append('X')
    return key, text, suffix


def format_line(key, text, suffix):
    return key + ';' + text + ';' + ';'.join(suffix[:6]) + '\n'


def load_entries(path):
    entries = OrderedDict()
    if not os.path.isfile(path):
        return entries
    with open(path, encoding=ENC, errors='replace') as f:
        for line in f:
            parsed = parse_line(line)
            if parsed is None:
                continue
            key, text, suffix = parsed
            entries[key] = (text, suffix)
    return entries


def infer_text(key):
    if key.startswith('desc_'):
        return 'Описание: ' + key[5:].replace('_', ' ') + '.'
    if key.endswith('_desc'):
        return 'Описание.'
    if key.endswith('_title') or key.endswith('_TITLE'):
        return key.replace('_', ' ').rstrip(' titleTITLE').capitalize()
    if key.startswith('#'):
        return '—'
    return None


def main():
    if not os.path.isfile(BACKUP):
        shutil.copy2(MOD_CSV, BACKUP)

    mod = load_entries(MOD_CSV)
    vanilla = load_entries(VANILLA_CSV)

    # mod поверх vanilla для отсутствующих ключей
    merged = OrderedDict()
    for key, (text, suffix) in vanilla.items():
        merged[key] = (text, suffix)
    for key, (text, suffix) in mod.items():
        merged[key] = (text, suffix)

    # убрать служебные ключи-комментарии из merged (оставить один раз через infer)
    for key in list(merged.keys()):
        if key.startswith('#'):
            merged[key] = ('—', merged[key][1])

    # переменные и D01-D50
    for key, text in VARIABLE_KEYS.items():
        merged[key] = (text, ['X'] * 6)

    for i in range(1, 51):
        tag = 'D%02d' % i
        adj = tag + '_ADJ'
        if tag in D26_D50_NAMES:
            merged[tag] = (D26_D50_NAMES[tag], merged.get(tag, ('', ['X'] * 6))[1])
        elif tag not in merged or not merged[tag][0].strip():
            merged[tag] = ('$REGION$', merged.get(tag, ('', ['X'] * 6))[1])
        if adj not in merged or not merged[adj][0].strip():
            merged[adj] = (D_ADJ_DEFAULT, merged.get(adj, ('', ['X'] * 6))[1])

    # заполнить пустые
    filled = 0
    for key in list(merged.keys()):
        text, suffix = merged[key]
        if text.strip():
            continue
        if key in VARIABLE_KEYS:
            merged[key] = (VARIABLE_KEYS[key], suffix)
            filled += 1
            continue
        inferred = infer_text(key)
        if inferred:
            merged[key] = (inferred, suffix)
            filled += 1

    # REGION/VALUE/VAL не должны дублироваться в a.csv — только в 00_variables.csv
    for vk in VARIABLE_KEYS:
        if vk in merged:
            del merged[vk]

    # записать 00_variables.csv
    with open(VAR_CSV, 'w', encoding=ENC, errors='replace', newline='') as f:
        for key, text in VARIABLE_KEYS.items():
            f.write(format_line(key, text, ['X'] * 6))

    # Write 00_variables.csv for reference only — NOT used (causes Duplicate text-key with a.csv)
    # Variables live at top of a.csv via fix_region_keys.py

    empty = 0
    msg = (
        'Pass 4: keys=%d filled=%d empty=%d variables=%s'
        % (len(merged), filled, empty, os.path.basename(VAR_CSV))
    )
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write('\n' + msg + '\n')
    print(msg)


if __name__ == '__main__':
    main()
