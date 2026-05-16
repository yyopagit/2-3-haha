# -*- coding: utf-8 -*-
"""
Анализ и очистка adjacencies.csv от дубликатов и ошибок
"""

import sys
from collections import defaultdict

PROVINCES_TO_CHECK = [929, 931, 934, 1161, 1594, 1598, 1718, 1719, 1724, 1738, 1739, 1740, 1758, 2074, 2077, 2094, 2586]

adjacencies_file = 'map/adjacencies.csv'

print("=" * 60)
print("АНАЛИЗ ADJACENCIES.CSV")
print("=" * 60)

# Собираем все записи
all_lines = []
all_adjacencies = {}
duplicates = []
errors = []

with open(adjacencies_file, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        all_lines.append((line_num, line))
        line_strip = line.strip()
        
        if not line_strip or line_strip.startswith('#'):
            continue
            
        parts = line_strip.split(';')
        if len(parts) < 2:
            continue
            
        try:
            from_prov = int(parts[0])
            to_prov = int(parts[1])
            adj_type = parts[2].strip() if len(parts) > 2 else ''
            
            key = f"{from_prov};{to_prov}"
            
            # Проверка на дубликаты
            if key in all_adjacencies:
                duplicates.append((line_num, key, all_adjacencies[key], adj_type))
            else:
                all_adjacencies[key] = (line_num, adj_type)
                
        except ValueError:
            errors.append((line_num, line_strip))

print(f"\n1. ОБЩАЯ СТАТИСТИКА:")
print(f"   Всего строк: {len(all_lines)}")
print(f"   Всего записей (без комментариев): {len(all_adjacencies)}")
print(f"   Дубликатов найдено: {len(duplicates)}")
print(f"   Ошибок парсинга: {len(errors)}")

if duplicates:
    print(f"\n2. ДУБЛИКАТЫ (первые 20):")
    for i, (line_num, key, (orig_line, orig_type), dup_type) in enumerate(duplicates[:20], 1):
        print(f"   {i}. Строка {line_num}: {key} (тип: {dup_type})")
        print(f"      Оригинал в строке {orig_line}: {key} (тип: {orig_type})")

if errors:
    print(f"\n3. ОШИБКИ ПАРСИНГА (первые 10):")
    for i, (line_num, line) in enumerate(errors[:10], 1):
        print(f"   {i}. Строка {line_num}: {line[:80]}")

# Проверка для наших провинций
print(f"\n4. ПРОВЕРКА ЗАБЛОКИРОВАННЫХ ПРОВИНЦИЙ:")
province_counts = defaultdict(set)

for key, (line_num, adj_type) in all_adjacencies.items():
    parts = key.split(';')
    from_prov = int(parts[0])
    to_prov = int(parts[1])
    
    if from_prov in PROVINCES_TO_CHECK:
        province_counts[from_prov].add(to_prov)
    if to_prov in PROVINCES_TO_CHECK:
        province_counts[to_prov].add(from_prov)

for prov in sorted(PROVINCES_TO_CHECK):
    neighbors = sorted(province_counts.get(prov, set()))
    print(f"   {prov}: {len(neighbors)} соседей - {neighbors}")

# Проверка на отсутствующие обратные записи для impassable
print(f"\n5. ПРОВЕРКА ОБРАТНЫХ ЗАПИСЕЙ ДЛЯ IMPASSABLE:")
missing_reverse = []

for key, (line_num, adj_type) in all_adjacencies.items():
    if adj_type == 'impassable':
        parts = key.split(';')
        from_prov = int(parts[0])
        to_prov = int(parts[1])
        reverse_key = f"{to_prov};{from_prov}"
        
        if reverse_key not in all_adjacencies:
            missing_reverse.append((line_num, key))

if missing_reverse:
    print(f"   Найдено {len(missing_reverse)} записей без обратных:")
    for i, (line_num, key) in enumerate(missing_reverse[:10], 1):
        print(f"   {i}. Строка {line_num}: {key}")
else:
    print("   ✓ Все записи имеют обратные")

print("\n" + "=" * 60)
print("АНАЛИЗ ЗАВЕРШЕН")
print("=" * 60)
