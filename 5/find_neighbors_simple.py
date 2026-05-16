# -*- coding: utf-8 -*-
"""
Упрощенная версия: анализирует карту и находит всех соседей
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    print("ОШИБКА: PIL/Pillow не установлен. Установите: pip install Pillow")
    sys.exit(1)

# Обработка ошибок
try:

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

# Загружаем definition.csv
print("\n1. Загрузка definition.csv...")
print(f"   Путь: {definition_file}")
print(f"   Существует: {os.path.exists(definition_file)}")
sys.stdout.flush()

if not os.path.exists(definition_file):
    print(f"ОШИБКА: Файл не найден!")
    sys.exit(1)

rgb_to_id = {}
id_to_name = {}

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
                except (ValueError, IndexError):
                    continue

print(f"   Загружено {len(rgb_to_id)} провинций")
sys.stdout.flush()

# Загружаем карту
print("\n2. Загрузка карты...")
print(f"   Путь: {provinces_bmp}")
print(f"   Существует: {os.path.exists(provinces_bmp)}")
sys.stdout.flush()

if not os.path.exists(provinces_bmp):
    print(f"ОШИБКА: Файл не найден!")
    sys.exit(1)

print("   Открываем изображение...")
sys.stdout.flush()
img = Image.open(provinces_bmp)
width, height = img.size
pixels = img.load()
print(f"   Размер: {width}x{height}")
sys.stdout.flush()

# Находим соседей
print("\n3. Поиск соседей (это может занять время)...")
sys.stdout.flush()
all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}

# Используем шаг 4 для ускорения
step = 4
checked = 0
total = (width // step) * (height // step)

for y in range(0, height, step):
    for x in range(0, width, step):
        try:
            current_rgb = pixels[x, y]
            
            if current_rgb in rgb_to_id:
                current_id = rgb_to_id[current_rgb]
                if current_id in PROVINCES_TO_FIX:
                    # Проверяем 4 соседних пикселя (без диагоналей для точности)
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            neighbor_rgb = pixels[nx, ny]
                            if neighbor_rgb != current_rgb and neighbor_rgb in rgb_to_id:
                                neighbor_id = rgb_to_id[neighbor_rgb]
                                all_neighbors[current_id].add(neighbor_id)
        except Exception as e:
            pass
        
        checked += 1
        if checked % 50000 == 0:
            progress = (checked / total) * 100
            print(f"   Прогресс: {progress:.1f}% ({checked}/{total})")
            sys.stdout.flush()

print("\n4. Найденные соседи:")
sys.stdout.flush()
for prov_id in sorted(PROVINCES_TO_FIX):
    neighbors = sorted(all_neighbors.get(prov_id, set()))
    name = id_to_name.get(prov_id, "?")
    print(f"   {prov_id} ({name}): {len(neighbors)} соседей - {neighbors}")
    sys.stdout.flush()

# Проверяем существующие границы
print("\n5. Проверка существующих границ...")
sys.stdout.flush()
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

print(f"   Найдено {len(existing_impassable)} существующих границ")
sys.stdout.flush()

# Генерируем новые границы
print("\n6. Генерация новых границ...")
sys.stdout.flush()
new_impassables = []
for prov_id in PROVINCES_TO_FIX:
    neighbors = all_neighbors.get(prov_id, set())
    for neighbor in neighbors:
        if (prov_id, neighbor) not in existing_impassable:
            terrain = "scary desert"
            if prov_id in [1594, 1598]:
                terrain = "scary mountain"
            new_impassables.append(f"{prov_id};{neighbor};impassable;0;0;{terrain}")
            new_impassables.append(f"{neighbor};{prov_id};impassable;0;0;{terrain}")
            existing_impassable.add((prov_id, neighbor))
            existing_impassable.add((neighbor, prov_id))
            print(f"   НОВАЯ: {prov_id} <-> {neighbor} ({terrain})")
            sys.stdout.flush()

print(f"\n{'='*60}")
print(f"Всего новых границ: {len(new_impassables)}")
print(f"{'='*60}")
sys.stdout.flush()

# Добавляем в файл
if new_impassables:
    print("\n7. Добавление в adjacencies.csv...")
    sys.stdout.flush()
    with open(adjacencies_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Находим место для вставки
    insert_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if 'impassable' in lines[i] and not lines[i].startswith('#'):
            j = i + 1
            while j < len(lines) and ('impassable' in lines[j] or (lines[j].strip().startswith('#') and 'impassable' in lines[j])):
                j += 1
            insert_idx = j
            break
    
    # Добавляем
    for imp in new_impassables:
        lines.insert(insert_idx, imp + '\n')
        insert_idx += 1
    
    with open(adjacencies_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"   ✓ Добавлено {len(new_impassables)} границ")
    sys.stdout.flush()
else:
    print("\n   ✓ Все границы уже существуют")
    sys.stdout.flush()

print("\nГотово!")
sys.stdout.flush()

except Exception as e:
    print(f"\nОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
