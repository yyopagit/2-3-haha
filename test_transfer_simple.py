# -*- coding: utf-8 -*-
import os
import re
from collections import defaultdict

PROVINCE_MAPPING = {
    1740: 1739,  # Waddan -> Kufra
    1738: 1739,  # Jaghbub -> Kufra  
    1739: 1741,  # Kufra -> Murzuk
}

pops_dir = os.path.join(os.path.dirname(__file__), 'history', 'pops')
test_file = os.path.join(pops_dir, '1836.1.1', 'Libya.txt')

def get_block(lines, start_idx):
    """Извлекает блок провинции"""
    block = [lines[start_idx]]
    brace_count = 1
    i = start_idx + 1
    while i < len(lines) and brace_count > 0:
        block.append(lines[i])
        brace_count += lines[i].count('{') - lines[i].count('}')
        i += 1
    return block, i

def find_province_block_indices(lines, prov_id):
    """Находит индексы блока провинции"""
    start_idx = -1
    for i, line in enumerate(lines):
        if re.match(rf'^\s*{prov_id}\s*=\s*\{{', line):
            start_idx = i
            break
    
    if start_idx == -1:
        return -1, -1

    brace_count = 1
    end_idx = start_idx + 1
    while end_idx < len(lines) and brace_count > 0:
        brace_count += lines[end_idx].count('{') - lines[end_idx].count('}')
        end_idx += 1
    
    return start_idx, end_idx

print(f"Тестирование на файле: {test_file}")
with open(test_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Проверяем наличие провинций
for prov_id in [1740, 1738, 1739]:
    start, end = find_province_block_indices(lines, prov_id)
    if start != -1:
        print(f"Провинция {prov_id} найдена: строки {start+1}-{end}")
    else:
        print(f"Провинция {prov_id} НЕ найдена")

# Проверяем целевую провинцию
start, end = find_province_block_indices(lines, 1741)
if start != -1:
    print(f"Целевая провинция 1741 найдена: строки {start+1}-{end}")
else:
    print(f"Целевая провинция 1741 НЕ найдена")
