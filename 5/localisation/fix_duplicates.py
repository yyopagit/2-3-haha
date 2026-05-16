# -*- coding: utf-8 -*-
# Fix duplicate IDs by line number (second occurrence only). File in cp1251.
import sys
path = r'c:\Games\Vic2LV2\Victoria 2\mod\6\localisation\a.csv'
log_path = r'c:\Games\Vic2LV2\Victoria 2\mod\6\localisation\fix_dup_log.txt'
def log(msg):
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
    print(msg)
with open(log_path, 'w', encoding='utf-8') as f:
    f.write('')
with open(path, 'r', encoding='cp1251', errors='replace', newline='') as f:
    lines = f.readlines()
log('Total lines: %d' % len(lines))

# 1-based line number -> (old_id, new_id) — второе вхождение получает новый ID
replacements = {
    22729: ('djibuti_expansion_title', 'djibuti_expansion2_title'),
    22730: ('djibuti_expansion_desc', 'djibuti_expansion2_desc'),
    23754: ('EVTNAME99912113', 'EVTNAME99912113b'),
    23755: ('EVTDESC99912113', 'EVTDESC99912113b'),
    23756: ('EVTOPTA99912113', 'EVTOPTA99912113b'),
    23775: ('CANAL_11', 'CANAL_11_otranto'),
    23776: ('CANAL_12', 'CANAL_12_yucatan'),
    23777: ('CANAL_13', 'CANAL_13_florida'),
    23778: ('CANAL_14', 'CANAL_14_florida2'),
    23829: ('EVTNAME10110669', 'EVTNAME10110669_otranto'),
    23830: ('EVTDESC10110669', 'EVTDESC10110669_otranto'),
    23982: ('EVTNAME422034', 'EVTNAME422034_primor'),
    24026: ('Exchange_EvtOptEnable', 'Exchange_EvtOptEnable2'),
    24027: ('Exchange_EvtOptRequest', 'Exchange_EvtOptRequest2'),
    24031: ('Exchange_EvtOptDisable', 'Exchange_EvtOptDisable2'),
    24033: ('Exchange_EvtDesc', 'Exchange_EvtDesc2'),
    24034: ('exchange_settings_dec_title', 'exchange_settings_dec_title2'),
    24035: ('exchange_settings_dec_desc', 'exchange_settings_dec_desc2'),
    24185: ('EVTNAME122223332', 'EVTNAME122223332b'),
    24186: ('EVTDESC122223332', 'EVTDESC122223332b'),
    24187: ('EVTOPTA122223332', 'EVTOPTA122223332b'),
    24261: ('BYZ_ap', 'BYZ_ap2'),
    24281: ('EVTDESC99912115', 'EVTDESC999121115'),
}

for line_1based, (old_id, new_id) in sorted(replacements.items()):
    i = line_1based - 1
    if i < 0 or i >= len(lines):
        log('Skip line %d (out of range)' % line_1based)
        continue
    line = lines[i]
    prefix = old_id + ';'
    if line.startswith(prefix):
        lines[i] = new_id + line[len(old_id):]
        log('Line %d: %s -> %s' % (line_1based, old_id, new_id))
    else:
        sample = line[:60].replace('\r', '\\r').replace('\n', '\\n')
        log('Line %d: expected start %r; got %r' % (line_1based, prefix, sample))

with open(path, 'w', encoding='cp1251', errors='replace', newline='') as f:
    f.writelines(lines)
log('Done.')
