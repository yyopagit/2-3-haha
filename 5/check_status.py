# -*- coding: utf-8 -*-
"""
Проверяет текущее состояние непроходимых границ
"""

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

adjacencies_file = 'map/adjacencies.csv'
output_file = 'adjacencies_status.txt'

# Собираем все границы
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
                    
                    if adj_type not in ['sea', 'canal']:
                        if from_prov in PROVINCES_TO_FIX:
                            province_adjacencies[from_prov].add((to_prov, adj_type))
                        if to_prov in PROVINCES_TO_FIX:
                            province_adjacencies[to_prov].add((from_prov, adj_type))
                except ValueError:
                    pass

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 60 + "\n")
    f.write("ТЕКУЩЕЕ СОСТОЯНИЕ ГРАНИЦ\n")
    f.write("=" * 60 + "\n\n")
    
    for prov_id in sorted(PROVINCES_TO_FIX):
        adjacencies = province_adjacencies.get(prov_id, set())
        impassable = [n for n, t in adjacencies if t == 'impassable']
        other = [n for n, t in adjacencies if t != 'impassable']
        
        f.write(f"Провинция {prov_id}:\n")
        f.write(f"  Всего границ: {len(adjacencies)}\n")
        f.write(f"  Непроходимых: {len(impassable)}\n")
        f.write(f"  Других: {len(other)}\n")
        if impassable:
            f.write(f"  Непроходимые соседи: {sorted(impassable)}\n")
        if other:
            f.write(f"  Другие соседи: {sorted(other)}\n")
        f.write("\n")

print(f"Результаты сохранены в {output_file}")
