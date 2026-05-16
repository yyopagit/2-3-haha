# -*- coding: utf-8 -*-
"""
Находит ВСЕХ соседей для указанных провинций из adjacencies.csv
и добавляет недостающие impassable границы напрямую в файл
"""

import os

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

script_dir = os.path.dirname(os.path.abspath(__file__))
adjacencies_file = os.path.join(script_dir, 'map', 'adjacencies.csv')

print(f"Читаю {adjacencies_file}...")

# Собираем всех соседей из adjacencies.csv
all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}
existing_impassable = set()

# Первый проход: собираем всех соседей и существующие impassable
with open(adjacencies_file, 'r', encoding='utf-8') as f:
    for line in f:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('#'):
            continue
        
        parts = line_stripped.split(';')
        if len(parts) >= 2:
            try:
                from_prov = int(parts[0])
                to_prov = int(parts[1])
                
                # Собираем соседей (кроме уже impassable)
                if from_prov in PROVINCES_TO_FIX:
                    if 'impassable' not in line:
                        all_neighbors[from_prov].add(to_prov)
                    else:
                        existing_impassable.add((from_prov, to_prov))
                
                if to_prov in PROVINCES_TO_FIX:
                    if 'impassable' not in line:
                        all_neighbors[to_prov].add(from_prov)
                    else:
                        existing_impassable.add((from_prov, to_prov))
            except ValueError:
                continue

print(f"Найдено соседей для {len(PROVINCES_TO_FIX)} провинций")

# Определяем недостающие impassable границы
missing_impassable = []

for prov_id in PROVINCES_TO_FIX:
    neighbors = all_neighbors.get(prov_id, set())
    for neighbor in neighbors:
        # Проверяем обе стороны
        if (prov_id, neighbor) not in existing_impassable and (neighbor, prov_id) not in existing_impassable:
            terrain = "scary desert"
            if prov_id in [1594, 1598]:
                terrain = "scary mountain"
            missing_impassable.append((prov_id, neighbor, terrain))

print(f"Найдено {len(missing_impassable)} недостающих impassable границ")

if not missing_impassable:
    print("Все impassable границы уже добавлены!")
    exit(0)

# Читаем весь файл
with open(adjacencies_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим место для вставки (после существующих impassable для наших провинций)
# Ищем последнюю строку с impassable для наших провинций
insert_pos = len(lines)
for i in range(len(lines) - 1, -1, -1):
    line = lines[i].strip()
    if line and not line.startswith('#'):
        parts = line.split(';')
        if len(parts) >= 2:
            try:
                from_prov = int(parts[0])
                if from_prov in PROVINCES_TO_FIX or (len(parts) > 1 and int(parts[1]) in PROVINCES_TO_FIX):
                    if 'impassable' in line:
                        insert_pos = i + 1
                        break
            except ValueError:
                pass

# Если не нашли, ищем место после строки 299 (где наши impassable)
if insert_pos == len(lines):
    for i in range(299, min(400, len(lines))):
        line = lines[i].strip()
        if line and not line.startswith('#') and 'impassable' not in line:
            insert_pos = i
            break

# Формируем строки для добавления
new_lines = []
added_pairs = set()

for from_prov, to_prov, terrain in missing_impassable:
    # Добавляем прямую связь
    pair_key = tuple(sorted([from_prov, to_prov]))
    if pair_key not in added_pairs:
        new_lines.append(f"{from_prov};{to_prov};impassable;0;0;{terrain}\n")
        new_lines.append(f"{to_prov};{from_prov};impassable;0;0;{terrain}\n")
        added_pairs.add(pair_key)

# Вставляем новые строки
lines[insert_pos:insert_pos] = new_lines

# Записываем обратно
with open(adjacencies_file, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"✓ Добавлено {len(new_lines)} строк в {adjacencies_file}")
print("Готово!")
