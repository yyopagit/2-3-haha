# -*- coding: utf-8 -*-
"""
Находит все соседние провинции для указанных провинций из adjacencies.csv
"""

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

adjacencies_file = 'map/adjacencies.csv'

# Словарь для хранения всех соседей каждой провинции
all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}

# Читаем adjacencies.csv и находим всех соседей
with open(adjacencies_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            parts = line.split(';')
            if len(parts) >= 2:
                try:
                    from_prov = int(parts[0])
                    to_prov = int(parts[1])
                    adj_type = parts[2].strip() if len(parts) > 2 else ''
                    
                    # Игнорируем sea и canal, но учитываем все остальные типы
                    if adj_type not in ['sea', 'canal']:
                        if from_prov in PROVINCES_TO_FIX:
                            all_neighbors[from_prov].add(to_prov)
                        if to_prov in PROVINCES_TO_FIX:
                            all_neighbors[to_prov].add(from_prov)
                except ValueError:
                    pass

# Находим существующие impassable границы
existing_impassable = set()
with open(adjacencies_file, 'r', encoding='utf-8') as f:
    for line in f:
        if 'impassable' in line and not line.startswith('#'):
            parts = line.split(';')
            if len(parts) >= 2:
                try:
                    from_prov = int(parts[0])
                    to_prov = int(parts[1])
                    existing_impassable.add((from_prov, to_prov))
                except ValueError:
                    pass

# Генерируем недостающие impassable границы
new_impassables = []
for prov_id in PROVINCES_TO_FIX:
    neighbors = all_neighbors.get(prov_id, set())
    print(f"\nПровинция {prov_id}: соседей {len(neighbors)}")
    for neighbor in sorted(neighbors):
        if (prov_id, neighbor) not in existing_impassable:
            # Определяем тип (desert или mountain)
            terrain = "scary desert"
            if prov_id in [1594, 1598]:
                terrain = "scary mountain"
            new_impassables.append(f"{prov_id};{neighbor};impassable;0;0;{terrain}")
            new_impassables.append(f"{neighbor};{prov_id};impassable;0;0;{terrain}")
            existing_impassable.add((prov_id, neighbor))
            existing_impassable.add((neighbor, prov_id))
            print(f"  Добавлена граница: {prov_id} <-> {neighbor}")

print(f"\nВсего новых непроходимых границ: {len(new_impassables)}")

# Добавляем в файл
if new_impassables:
    with open(adjacencies_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Находим место для вставки (после существующих impassable)
    insert_idx = len(lines)
    for i, line in enumerate(lines):
        if '# Обратные непроходимые границы' in line:
            # Ищем конец блока обратных границ
            j = i + 1
            while j < len(lines) and ('impassable' in lines[j] or lines[j].strip().startswith('#')):
                j += 1
            insert_idx = j
            break
        elif i > 0 and 'impassable' in lines[i-1] and not 'impassable' in line and not line.startswith('#') and line.strip():
            insert_idx = i
            break
    
    # Добавляем новые границы
    for imp in new_impassables:
        lines.insert(insert_idx, imp + '\n')
        insert_idx += 1
    
    with open(adjacencies_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"Добавлено {len(new_impassables)} непроходимых границ в {adjacencies_file}")
else:
    print("Все непроходимые границы уже существуют")
