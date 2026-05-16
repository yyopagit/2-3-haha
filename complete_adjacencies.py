# -*- coding: utf-8 -*-
"""
Находит ВСЕ соседние провинции для указанных провинций и добавляет недостающие непроходимые границы
"""

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

script_dir = os.path.dirname(os.path.abspath(__file__))
adjacencies_file = os.path.join(script_dir, 'map', 'adjacencies.csv')

# Словарь для хранения всех соседей каждой провинции
all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}

# Читаем adjacencies.csv и находим ВСЕХ соседей (игнорируя только sea и canal)
with open(adjacencies_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            parts = line.split(';')
            if len(parts) >= 2:
                try:
                    from_prov = int(parts[0])
                    to_prov = int(parts[1])
                    adj_type = parts[2].strip() if len(parts) > 2 else ''
                    
                    # Игнорируем только sea и canal, все остальное - соседи
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
                    existing_impassable.add((to_prov, from_prov))
                except ValueError:
                    pass

# Генерируем недостающие impassable границы
new_impassables = []
for prov_id in PROVINCES_TO_FIX:
    neighbors = all_neighbors.get(prov_id, set())
    print(f"\nПровинция {prov_id}: найдено {len(neighbors)} соседей")
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
            print(f"  НОВАЯ граница: {prov_id} <-> {neighbor}")

print(f"\n{'='*60}")
print(f"Всего новых непроходимых границ: {len(new_impassables)}")
print(f"{'='*60}")

# Добавляем в файл
if new_impassables:
    with open(adjacencies_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Находим место для вставки (после существующих impassable, перед другими блоками)
    insert_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if 'impassable' in lines[i] and not lines[i].startswith('#'):
            # Ищем конец блока impassable
            j = i + 1
            while j < len(lines) and ('impassable' in lines[j] or (lines[j].strip().startswith('#') and 'impassable' in lines[j])):
                j += 1
            insert_idx = j
            break
    
    # Добавляем новые границы
    for imp in new_impassables:
        lines.insert(insert_idx, imp + '\n')
        insert_idx += 1
    
    with open(adjacencies_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"\n✓ Добавлено {len(new_impassables)} непроходимых границ в {adjacencies_file}")
else:
    print("\n✓ Все непроходимые границы уже существуют")
