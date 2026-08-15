# -*- coding: utf-8 -*-
"""Remove mod localisation keys identical to vanilla (reduce duplicate warnings)."""
import os
import shutil
from collections import OrderedDict

MOD_DIR = os.path.dirname(os.path.abspath(__file__))
MOD_CSV = os.path.join(MOD_DIR, 'a.csv')
VANILLA_CSV = os.path.join(MOD_DIR, '..', '..', '..', 'localisation', 'a.csv')
BACKUP = os.path.join(MOD_DIR, 'a.csv.bak2')
LOG = os.path.join(MOD_DIR, 'fix_localisation_log.txt')
ENC = 'cp1251'


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
    with open(path, encoding=ENC, errors='replace') as f:
        for line in f:
            parsed = parse_line(line)
            if parsed is None:
                continue
            key, text, suffix = parsed
            entries[key] = (text, suffix)
    return entries


def main():
    vanilla = load_entries(VANILLA_CSV)
    mod = load_entries(MOD_CSV)

    kept = OrderedDict()
    removed = []

    for key, (text, suffix) in mod.items():
        if key in vanilla and vanilla[key][0] == text and '$' not in text:
            removed.append(key)
        else:
            kept[key] = (text, suffix)

    if not os.path.isfile(BACKUP):
        shutil.copy2(MOD_CSV, BACKUP)

    with open(MOD_CSV, 'w', encoding=ENC, errors='replace', newline='') as f:
        for key, (text, suffix) in kept.items():
            f.write(format_line(key, text, suffix))

    msg = (
        'Pass 3: removed %d identical vanilla keys, kept %d keys'
        % (len(removed), len(kept))
    )
    with open(LOG, 'a', encoding='utf-8') as out:
        out.write('\n' + msg + '\n')
    print(msg)


if __name__ == '__main__':
    main()
