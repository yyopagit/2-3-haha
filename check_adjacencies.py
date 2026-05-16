# -*- coding: utf-8 -*-
"""
Проверяет текущее состояние непроходимых границ для указанных провинций
"""

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

adjacencies_file = 'map/adjacencies.csv'

# Собираем все границы для каждой провинции
province_adjacencies = {prov: set() for prov in PROVINCES_TO_FIX}

with open(adjacencies_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            parts = line.split(';')
            if len(parts) >= 2:
                try:
                    from_prov = int(parts[0])
                    to_prov = int(parts[1])
                    adj_type = parts[2].strip() if len(parts) > 2 else ''
                    
                    # Учитываем все типы границ (не только impassable)
                    if adj_type not in ['sea', 'canal']:
                        if from_prov in PROVINCES_TO_FIX:
                            province_adjacencies[from_prov].add((to_prov, adj_type))
                        if to_prov in PROVINCES_TO_FIX:
                            province_adjacencies[to_prov].add((from_prov, adj_type))
                except ValueError:
                    pass

print("=" * 60)
print("ТЕКУЩЕЕ СОСТОЯНИЕ ГРАНИЦ ДЛЯ УКАЗАННЫХ ПРОВИНЦИЙ")
print("=" * 60)

for prov_id in sorted(PROVINCES_TO_FIX):
    adjacencies = province_adjacencies.get(prov_id, set())
    impassable_count = sum(1 for _, adj_type in adjacencies if adj_type == 'impassable')
    other_count = len(adjacencies) - impassable_count
    
    print(f"\nПровинция {prov_id}:")
    print(f"  Всего границ: {len(adjacencies)}")
    print(f"  Непроходимых: {impassable_count}")
    print(f"  Других: {other_count}")
    
    if adjacencies:
        print(f"  Соседи:")
        for neighbor, adj_type in sorted(adjacencies):
            print(f"    -> {neighbor} ({adj_type})")

print("\n" + "=" * 60)
print("Проверка завершена")
