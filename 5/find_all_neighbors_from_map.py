# -*- coding: utf-8 -*-
"""
Анализирует карту provinces.bmp и находит ВСЕХ соседей для указанных провинций
Затем добавляет недостающие непроходимые границы в adjacencies.csv
"""

import os
import sys
try:
    from PIL import Image
except ImportError:
    print("ОШИБКА: PIL/Pillow не установлен. Установите: pip install Pillow")
    sys.exit(1)
from collections import defaultdict

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

script_dir = os.path.dirname(os.path.abspath(__file__))
map_dir = os.path.join(script_dir, 'map')
definition_file = os.path.join(map_dir, 'definition.csv')
provinces_bmp = os.path.join(map_dir, 'provinces.bmp')
adjacencies_file = os.path.join(map_dir, 'adjacencies.csv')

print("=" * 60)
print("АНАЛИЗ КАРТЫ И ПОИСК ВСЕХ СОСЕДЕЙ")
print("=" * 60)
sys.stdout.flush()

# Загружаем definition.csv для получения RGB цветов провинций
print("\n1. Загрузка definition.csv...")
rgb_to_id = {}
id_to_name = {}
id_to_rgb = {}

print(f"   Путь к definition.csv: {definition_file}")
print(f"   Существует: {os.path.exists(definition_file)}")
print(f"   Путь: {definition_file}")
print(f"   Существует: {os.path.exists(definition_file)}")
sys.stdout.flush()
if not os.path.exists(definition_file):
    print(f"ОШИБКА: Файл {definition_file} не найден!")
    sys.exit(1)

with open(definition_file, 'r', encoding='utf-8') as f:
    for line in f:
        if ';' in line and not line.startswith('#'):
            parts = line.strip().split(';')
            if len(parts) >= 5:
                try:
                    prov_id = int(parts[0])
                    rgb = (int(parts[1]), int(parts[2]), int(parts[3]))
                    name = parts[4]
                    rgb_to_id[rgb] = prov_id
                    id_to_name[prov_id] = name
                    id_to_rgb[prov_id] = rgb
                except (ValueError, IndexError):
                    continue

print(f"   Загружено {len(rgb_to_id)} провинций")

# Загружаем карту
print("\n2. Загрузка карты provinces.bmp...")
print(f"   Путь к provinces.bmp: {provinces_bmp}")
print(f"   Существует: {os.path.exists(provinces_bmp)}")
print(f"   Путь: {provinces_bmp}")
print(f"   Существует: {os.path.exists(provinces_bmp)}")
sys.stdout.flush()
if not os.path.exists(provinces_bmp):
    print(f"ОШИБКА: Файл {provinces_bmp} не найден!")
    sys.exit(1)

img = Image.open(provinces_bmp)
width, height = img.size
pixels = img.load()
print(f"   Размер карты: {width}x{height}")

# Находим всех соседей для каждой провинции
print("\n3. Поиск соседей на карте...")
all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}

# Проверяем каждый пиксель и его соседей
checked = 0
for y in range(0, height, 2):  # Проверяем каждый 2-й пиксель для скорости
    for x in range(0, width, 2):
        current_rgb = pixels[x, y]
        
        # Проверяем, является ли это одной из наших провинций
        if current_rgb in rgb_to_id:
            current_id = rgb_to_id[current_rgb]
            if current_id in PROVINCES_TO_FIX:
                # Проверяем 8 соседних пикселей (включая диагонали)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            neighbor_rgb = pixels[nx, ny]
                            if neighbor_rgb != current_rgb and neighbor_rgb in rgb_to_id:
                                neighbor_id = rgb_to_id[neighbor_rgb]
                                all_neighbors[current_id].add(neighbor_id)
        checked += 1
        if checked % 100000 == 0:
            print(f"   Проверено {checked} пикселей...")

print("\n4. Найденные соседи:")
for prov_id in sorted(PROVINCES_TO_FIX):
    neighbors = sorted(all_neighbors.get(prov_id, set()))
    name = id_to_name.get(prov_id, "?")
    print(f"   {prov_id} ({name}): {len(neighbors)} соседей - {neighbors}")

# Находим существующие impassable границы
print("\n5. Проверка существующих непроходимых границ...")
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

print(f"   Найдено {len(existing_impassable)} существующих непроходимых границ")

# Генерируем недостающие impassable границы
print("\n6. Генерация недостающих непроходимых границ...")
new_impassables = []
for prov_id in PROVINCES_TO_FIX:
    neighbors = all_neighbors.get(prov_id, set())
    for neighbor in neighbors:
        if (prov_id, neighbor) not in existing_impassable:
            # Определяем тип (desert или mountain)
            terrain = "scary desert"
            if prov_id in [1594, 1598]:
                terrain = "scary mountain"
            new_impassables.append(f"{prov_id};{neighbor};impassable;0;0;{terrain}")
            new_impassables.append(f"{neighbor};{prov_id};impassable;0;0;{terrain}")
            existing_impassable.add((prov_id, neighbor))
            existing_impassable.add((neighbor, prov_id))
            print(f"   НОВАЯ: {prov_id} <-> {neighbor} ({terrain})")

print(f"\n{'='*60}")
print(f"Всего новых непроходимых границ: {len(new_impassables)}")
print(f"{'='*60}")

# Добавляем в файл
if new_impassables:
    with open(adjacencies_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Находим место для вставки (после существующих impassable)
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

print("\nГотово!")
