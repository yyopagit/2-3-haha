# -*- coding: utf-8 -*-
"""Remove duplicate keys and fill empty localisation from vanilla."""
from collections import OrderedDict
import os
import shutil

MOD_DIR = os.path.dirname(os.path.abspath(__file__))
MOD_CSV = os.path.join(MOD_DIR, 'a.csv')
VANILLA_CSV = os.path.join(MOD_DIR, '..', '..', '..', 'localisation', 'a.csv')
BACKUP = os.path.join(MOD_DIR, 'a.csv.bak')
LOG = os.path.join(MOD_DIR, 'fix_localisation_log.txt')

ENC = 'cp1251'


def parse_line(line):
    line = line.rstrip('\r\n')
    if not line:
        return None
    parts = line.split(';')
    key = parts[0]
    text = parts[1] if len(parts) > 1 else ''
    suffix = parts[2:] if len(parts) > 2 else ['X', 'X', 'X', 'X', 'X', 'X']
    while len(suffix) < 6:
        suffix.append('X')
    return key, text, suffix


def format_line(key, text, suffix):
    return key + ';' + text + ';' + ';'.join(suffix[:6]) + '\n'


def load_csv(path):
    entries = OrderedDict()
    dup_lines = []
    with open(path, encoding=ENC, errors='replace') as f:
        for i, line in enumerate(f, 1):
            parsed = parse_line(line)
            if parsed is None:
                continue
            key, text, suffix = parsed
            if key in entries:
                dup_lines.append((key, i, entries[key][0]))
            entries[key] = (i, text, suffix, line.rstrip('\r\n'))
    return entries, dup_lines


def main():
    log = []
    if not os.path.isfile(VANILLA_CSV):
        log.append('Vanilla csv not found: ' + VANILLA_CSV)
        vanilla = {}
    else:
        vanilla_entries, _ = load_csv(VANILLA_CSV)
        vanilla = {k: (t, s) for k, (_, t, s, _) in vanilla_entries.items()}
        log.append('Vanilla keys: %d' % len(vanilla))

    mod_entries, dup_lines = load_csv(MOD_CSV)
    log.append('Mod lines parsed: %d unique keys' % len(mod_entries))
    log.append('Internal duplicate key occurrences: %d' % len(dup_lines))

    empty_before = [k for k, (_, t, _, _) in mod_entries.items() if not t.strip()]
    log.append('Empty keys before: %d' % len(empty_before))

    # Re-read keeping last occurrence per key (mod overrides)
    final = OrderedDict()
    with open(MOD_CSV, encoding=ENC, errors='replace') as f:
        for line in f:
            parsed = parse_line(line)
            if parsed is None:
                continue
            key, text, suffix = parsed
            final[key] = (text, suffix)

    removed_dups = len(mod_entries) + len(dup_lines) - len(final)
    # Actually count lines to remove
    line_count = sum(1 for _ in open(MOD_CSV, encoding=ENC, errors='replace'))
    removed_lines = line_count - len(final)

    filled = 0
    filled_from_vanilla = 0
    still_empty = []
    for key, (text, suffix) in final.items():
        if text.strip():
            continue
        if key in vanilla and vanilla[key][0].strip():
            final[key] = (vanilla[key][0], suffix)
            filled += 1
            filled_from_vanilla += 1
        else:
            still_empty.append(key)

    # Fill known mod-specific empty keys with sensible Russian text
    manual = {
        'REGION': 'Регион',
        'VALUE': 'Значение',
        'VAL': 'Значение',
        'BUDGET_TAX_POOR_DESC': 'Налог на беднейших слоёв населения.',
        'BUDGET_TAX_MIDDLE_DESC': 'Налог на средний класс.',
        'BUDGET_TAX_RICH_DESC': 'Налог на богатых.',
        'BUDGET_GOLD_DESC': 'Доход от золотого стандарта.',
        'BUDGET_MIL_COST_DESC': 'Расходы на содержание армии.',
        'BUDGET_NAT_STOCK_DESC': 'Национальные запасы.',
        'BUDGET_IND_SUP_DESC': 'Промышленные субсидии.',
        'BUDGET_EDUCATION_DESC': 'Расходы на образование.',
        'BUDGET_ADMIN_DESC': 'Административные расходы.',
        'BUDGET_SOCIAL_SPEND_DESC': 'Социальные расходы.',
        'BUDGET_MIL_SPEND_DESC': 'Военные расходы.',
        'BUDGET_TARIFF_DESC': 'Таможенные пошлины.',
        'BUDGET_TOTAL_FUNDS_DESC': 'Общий доход бюджета.',
        'BUDGET_BALANCE_DESC': 'Баланс бюджета.',
        'BUDGET_DEBT_DESC': 'Государственный долг.',
        'BUDGET_NATIONAL_BANK_DESC': 'Национальный банк.',
        'BUDGET_INTEREST_DESC': 'Проценты по долгу.',
        'CRISIS_BACK_DOWN_OTHER_DECLINE_MAP': 'Отказ от участия в кризисе.',
        'PRODUCTION_EFFICIENCY_TOOLTIP': 'Эффективность производства.',
        'RGO_NONE_EFFECT_TECH': 'Без эффекта для RGO.',
        'FACTORY_NONE_EFFECT_TECH': 'Без эффекта для фабрик.',
        'ARTISAN_NONE_EFFECT_TECH': 'Без эффекта для ремесленников.',
        'NONE_TYPE_INPUT_TECH': 'Без эффекта на вход.',
        'NONE_TYPE_OUTPUT_TECH': 'Без эффекта на выход.',
        'NONE_TYPE_THROUGHPUT_TECH': 'Без эффекта на производительность.',
        'NONE_TYPE_NONE_EFFECT_TECH': 'Без эффекта.',
        'cd_canadian_governor_generals_rights_desc': 'Права генерал-губернатора Канады.',
        'cd_sa_governor_generals_rights_desc': 'Права генерал-губернатора Южной Африки.',
        'super_conquest1_desc': 'Сверхагрессивная экспансия.',
        'peacefull_conquest1_desc': 'Мирная экспансия.',
        'new_world_desc': 'Новый Свет.',
        'REMOVE_desc_suffragette_movements': 'Удалить описание движения суфражисток.',
    }
    for key, text in manual.items():
        if key in final and not final[key][0].strip():
            final[key] = (text, final[key][1])
            filled += 1

    still_empty = [k for k, (t, _) in final.items() if not t.strip()]

    if not os.path.isfile(BACKUP):
        shutil.copy2(MOD_CSV, BACKUP)
        log.append('Backup created: a.csv.bak')

    with open(MOD_CSV, 'w', encoding=ENC, errors='replace', newline='') as f:
        for key, (text, suffix) in final.items():
            f.write(format_line(key, text, suffix))

    log.append('Removed duplicate lines: ~%d' % removed_lines)
    log.append('Filled empty keys: %d (from vanilla: %d)' % (filled, filled_from_vanilla))
    log.append('Still empty: %d' % len(still_empty))
    if still_empty[:50]:
        log.append('Sample still empty: ' + ', '.join(still_empty[:50]))

    with open(LOG, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log))
    print('\n'.join(log))


if __name__ == '__main__':
    main()
