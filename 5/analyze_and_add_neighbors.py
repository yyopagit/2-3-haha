# -*- coding: utf-8 -*-
"""
Анализирует adjacencies.csv, находит всех соседей для указанных провинций
и добавляет недостающие impassable границы
"""

import os

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

script_dir = os.path.dirname(os.path.abspath(__file__))
adjacencies_file = os.path.join(script_dir, 'map', 'adjacencies.csv')

# Словарь для хранения всех соседей (включая существующие impassable)
all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}
existing_impassable = set()

print("Читаю adjacencies.csv...")

# Читаем все строки файла
with open(adjacencies_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Первый проход: собираем всех соседей
for line in lines:
    line_stripped = line.strip()
    if not line_stripped or line_stripped.startswith('#'):
        continue
    
    parts = line_stripped.split(';')
    if len(parts) >= 2:
        try:
            from_prov = int(parts[0])
            to_prov = int(parts[1])
            
            # Если это impassable, добавляем в existing_impassable
            if 'impassable' in line_stripped:
                if from_prov in PROVINCES_TO_FIX or to_prov in PROVINCES_TO_FIX:
                    existing_impassable.add((from_prov, to_prov))
                    existing_impassable.add((to_prov, from_prov))
            
            # Собираем всех соседей (кроме sea и canal типов)
            if len(parts) >= 3:
                adj_type = parts[2].strip().lower()
                # Пропускаем морские и канальные соединения
                if adj_type in ['sea', 'canal']:
                    continue
            
            # Если одна из провинций - наша, добавляем в список соседей
            if from_prov in PROVINCES_TO_FIX:
                all_neighbors[from_prov].add(to_prov)
            if to_prov in PROVINCES_TO_FIX:
                all_neighbors[to_prov].add(from_prov)
        except (ValueError, IndexError):
            continue

print(f"Найдено соседей:")
for prov_id in sorted(PROVINCES_TO_FIX):
    neighbors = sorted(all_neighbors.get(prov_id, set()))
    print(f"  {prov_id}: {len(neighbors)} соседей - {neighbors}")

# Находим недостающие impassable границы
missing_impassable = []

for prov_id in PROVINCES_TO_FIX:
    neighbors = all_neighbors.get(prov_id, set())
    for neighbor in neighbors:
        # Проверяем, нет ли уже impassable границы
        if (prov_id, neighbor) not in existing_impassable:
            terrain = "scary desert"
            if prov_id in [1594, 1598]:
                terrain = "scary mountain"
            missing_impassable.append((prov_id, neighbor, terrain))

print(f"\nНайдено {len(missing_impassable)} недостающих impassable границ")

if not missing_impassable:
    print("Все impassable границы уже добавлены!")
    exit(0)

# Находим место для вставки (после строки 299, где заканчиваются наши impassable)
insert_pos = 300
for i in range(299, min(400, len(lines))):
    line = lines[i].strip()
    if line and not line.startswith('#'):
        parts = line.split(';')
        if len(parts) >= 2:
            try:
                from_prov = int(parts[0])
                if from_prov in PROVINCES_TO_FIX:
                    continue  # Это наши провинции, пропускаем
                else:
                    insert_pos = i
                    break
            except ValueError:
                insert_pos = i
                break

# Формируем новые строки (добавляем обе стороны)
new_lines = []
added_pairs = set()

for from_prov, to_prov, terrain in missing_impassable:
    pair_key = tuple(sorted([from_prov, to_prov]))
    if pair_key not in added_pairs:
        new_lines.append(f"{from_prov};{to_prov};impassable;0;0;{terrain}\n")
        new_lines.append(f"{to_prov};{from_prov};impassable;0;0;{terrain}\n")
        added_pairs.add(pair_key)
        print(f"  Добавляю: {from_prov} <-> {to_prov} ({terrain})")

# Вставляем новые строки
lines[insert_pos:insert_pos] = new_lines

# Записываем обратно
with open(adjacencies_file, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\n✓ Добавлено {len(new_lines)} строк в {adjacencies_file}")
print("Готово!")
