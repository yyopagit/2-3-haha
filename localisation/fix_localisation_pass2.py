# -*- coding: utf-8 -*-
"""Fill remaining empty localisation keys and add missing GUI keys."""
import os
import re

MOD_DIR = os.path.dirname(os.path.abspath(__file__))
MOD_CSV = os.path.join(MOD_DIR, 'a.csv')
ENC = 'cp1251'

# Ручные переводы для пустых ключей и desc_* без текста
MANUAL = {
    'REGION': 'Регион',
    'VALUE': 'Значение',
    'VAL': 'Значение',
    'xxxx': '—',
    'desc_fascist_welfare': 'Государство расширяет социальные программы в духе корпоративизма.',
    'desc_beer_hall_putsch': 'Неудачная попытка государственного переворота.',
    'REMOVE_desc_immigrant_employment': 'Иммигрантам разрешено работать наравне с коренным населением.',
    'REMOVE_desc_no_immigrant_employment': 'Иммигрантам отказано в праве на работу.',
    'BATTLE_OF': 'Битва при',
    'SIEGE_OF': 'Осада',
    'fast_manchu_desc': 'Быстрая мобилизация маньчжурских сил.',
    'not_fast_manchu_desc': 'Мобилизация маньчжурских сил замедлена.',
    'korea_yes_desc': 'Корея приняла предложение.',
    'jap_banzai_end_desc': 'Банzai-атака отражена.',
    'ne_trogat': 'Торговое соглашение.',
    'can_and_saf_content_end': 'Конец контента Канады и Южной Африки.',
    'exchange_settings_dec_desc2': 'Настройки биржи.',
    'MESSAGE_SETTING_TRUE': 'Включено',
    '#': '—',
    '########################################': '—',
    '##############################################################': '—',
    '###################################################################': '—',
    '######################################################################': '—',
    '##################################################': '—',
    '###############################################################': '—',
    '##### military': '—',
    '##### Industry': '—',
    '##### Budget': '—',
    '##### Technology': '—',
    '##### Politics': '—',
    '##### People': '—',
    '##### Trade ': '—',
    '##### Diplomacy ': '—',
    '##### General': '—',
    '##### Tutorial ': '—',
    '##### Miltary Medium': '—',
    '##### Production Medium': '—',
    '##### Budget Intermediary': '—',
    '# Meta Server': '—',
    '# Unit Names': '—',
    '# Abilities': '—',
    '# Naming Conventions': '—',
    '# Trait Tags': '—',
    '# Trait Names': '—',
    '# Rebels': '—',
    '# Crime and Corruption Buildings': '—',
    '# Mapmode Buttons': '—',
    '# Actions': '—',
    '# Buliding Names': '—',
    '# Building Names': '—',
    '# Factory tech names': '—',
}


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


def infer_from_key(key):
    if key.startswith('desc_') and not key.startswith('REMOVE_desc_'):
        base = key[5:]
        return 'Описание: ' + base.replace('_', ' ') + '.'
    if key.startswith('REMOVE_desc_'):
        base = key[12:]
        return 'Удалить: ' + base.replace('_', ' ') + '.'
    if key.endswith('_desc'):
        return 'Описание события или решения.'
    if key.endswith('_title'):
        return key[:-6].replace('_', ' ').capitalize()
    return None


def main():
    lines_out = []
    filled = 0
    added = 0
    existing = set()

    with open(MOD_CSV, encoding=ENC, errors='replace') as f:
        for line in f:
            parsed = parse_line(line)
            if parsed is None:
                lines_out.append(line)
                continue
            key, text, suffix = parsed
            existing.add(key)
            if not text.strip():
                if key in MANUAL:
                    text = MANUAL[key]
                    filled += 1
                else:
                    inferred = infer_from_key(key)
                    if inferred:
                        text = inferred
                        filled += 1
            lines_out.append(format_line(key, text, suffix))

    for key, text in MANUAL.items():
        if key not in existing and key in ('REGION', 'VALUE', 'VAL'):
            lines_out.append(format_line(key, text, ['X'] * 6))
            added += 1

    with open(MOD_CSV, 'w', encoding=ENC, errors='replace', newline='') as f:
        f.writelines(lines_out)

    empty = 0
    with open(MOD_CSV, encoding=ENC, errors='replace') as f:
        for line in f:
            p = parse_line(line)
            if p and not p[1].strip():
                empty += 1

    log = 'Filled: %d, Added keys: %d, Remaining empty: %d' % (filled, added, empty)
    with open(os.path.join(MOD_DIR, 'fix_localisation_log.txt'), 'a', encoding='utf-8') as f:
        f.write('\nPass 2: ' + log + '\n')
    print(log)


if __name__ == '__main__':
    main()
