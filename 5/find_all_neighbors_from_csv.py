# -*- coding: utf-8 -*-
"""
Находит ВСЕХ соседей для указанных провинций из adjacencies.csv
и добавляет недостающие impassable границы
"""

import os

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

script_dir = os.path.dirname(os.path.abspath(__file__))
adjacencies_file = os.path.join(script_dir, 'map', 'adjacencies.csv')
result_file = os.path.join(script_dir, 'vse_sosedi.txt')

# Собираем всех соседей из adjacencies.csv
all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}

print(f"Поиск всех соседей в {adjacencies_file}...")

with open(adjacencies_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split(';')
        if len(parts) >= 2:
            try:
                from_prov = int(parts[0])
                to_prov = int(parts[1])
                
                if from_prov in PROVINCES_TO_FIX:
                    # Пропускаем уже существующие impassable
                    if 'impassable' not in line:
                        all_neighbors[from_prov].add(to_prov)
            except ValueError:
                continue

# Также проверяем обратные связи
with open(adjacencies_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split(';')
        if len(parts) >= 2:
            try:
                from_prov = int(parts[0])
                to_prov = int(parts[1])
                
                if to_prov in PROVINCES_TO_FIX:
                    if 'impassable' not in line:
                        all_neighbors[to_prov].add(from_prov)
            except ValueError:
                continue

# Выводим результаты
with open(result_file, 'w', encoding='utf-8') as out:
    out.write("=" * 60 + "\n")
    out.write("ВСЕ СОСЕДИ ДЛЯ УКАЗАННЫХ ПРОВИНЦИЙ\n")
    out.write("=" * 60 + "\n\n")
    
    total_neighbors = 0
    for prov_id in sorted(PROVINCES_TO_FIX):
        neighbors = sorted(all_neighbors.get(prov_id, set()))
        out.write(f"Провинция {prov_id}: {len(neighbors)} соседей\n")
        out.write(f"  {neighbors}\n\n")
        total_neighbors += len(neighbors)
    
    out.write(f"\nВсего найдено соседей: {total_neighbors}\n")
    
    # Проверяем существующие impassable
    out.write("\n" + "=" * 60 + "\n")
    out.write("ПРОВЕРКА СУЩЕСТВУЮЩИХ IMPASSABLE\n")
    out.write("=" * 60 + "\n\n")
    
    existing_impassable = set()
    with open(adjacencies_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'impassable' in line and not line.startswith('#'):
                parts = line.split(';')
                if len(parts) >= 2:
                    try:
                        from_prov = int(parts[0])
                        to_prov = int(parts[1])
                        if from_prov in PROVINCES_TO_FIX or to_prov in PROVINCES_TO_FIX:
                            existing_impassable.add((from_prov, to_prov))
                    except ValueError:
                        pass
    
    out.write(f"Существующих impassable: {len(existing_impassable)}\n\n")
    
    # Находим недостающие
    out.write("=" * 60 + "\n")
    out.write("НЕДОСТАЮЩИЕ IMPASSABLE ГРАНИЦЫ\n")
    out.write("=" * 60 + "\n\n")
    
    missing = []
    for prov_id in PROVINCES_TO_FIX:
        neighbors = all_neighbors.get(prov_id, set())
        for neighbor in neighbors:
            if (prov_id, neighbor) not in existing_impassable:
                terrain = "scary desert"
                if prov_id in [1594, 1598]:
                    terrain = "scary mountain"
                missing.append((prov_id, neighbor, terrain))
                out.write(f"  {prov_id} → {neighbor} ({terrain})\n")
    
    out.write(f"\nВсего недостающих: {len(missing)}\n")

print(f"\nРезультаты сохранены в: {result_file}")
print(f"Найдено соседей для {len(PROVINCES_TO_FIX)} провинций")
