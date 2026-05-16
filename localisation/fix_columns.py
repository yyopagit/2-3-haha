# -*- coding: utf-8 -*-
import os
os.chdir(r'c:\Games\Vic2LV2\Victoria 2\mod\6\localisation')
path = 'a.txt'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
fixed = 0
out = []
for line in lines:
    stripped = line.rstrip('\r\n')
    if not stripped:
        out.append(line)
        continue
    parts = stripped.split(';')
    if len(parts) == 3 and parts[-1].strip() == 'X':
        stripped = stripped + ';X;X;X;X;X'
        fixed += 1
    out.append(stripped + '\n')
with open('a_new.txt', 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(out)
with open('fixed.txt', 'w') as f:
    f.write('Fixed %d lines in a.txt - output in a_new.txt\n' % fixed)
