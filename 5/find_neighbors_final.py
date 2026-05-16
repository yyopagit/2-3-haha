# -*- coding: utf-8 -*-
"""
Анализирует карту provinces.bmp и находит ВСЕХ соседей для указанных провинций
Записывает результаты в файл и добавляет недостающие непроходимые границы
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    with open('neighbors_error.txt', 'w', encoding='utf-8') as f:
        f.write("ОШИБКА: PIL/Pillow не установлен. Установите: pip install Pillow\n")
    sys.exit(1)

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

script_dir = os.path.dirname(os.path.abspath(__file__))
map_dir = os.path.join(script_dir, 'map')
definition_file = os.path.join(map_dir, 'definition.csv')
provinces_bmp = os.path.join(map_dir, 'provinces.bmp')
adjacencies_file = os.path.join(map_dir, 'adjacencies.csv')
log_file = os.path.join(script_dir, 'neighbors_log.txt')

# Создаем лог-файл сразу
try:
    log = open(log_file, 'w', encoding='utf-8')
except Exception as e:
    print(f"Не удалось создать лог-файл: {e}")
    log = None

def log_print(msg):
    if log:
        log.write(msg + '\n')
        log.flush()
    print(msg)
    sys.stdout.flush()

try:
    log_print("=" * 60)
    log_print("АНАЛИЗ КАРТЫ И ПОИСК ВСЕХ СОСЕДЕЙ")
    log_print("=" * 60)

    # Загружаем definition.csv
    log_print("\n1. Загрузка definition.csv...")
    if not os.path.exists(definition_file):
        log_print(f"ОШИБКА: Файл {definition_file} не найден!")
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

    log_print(f"   Загружено {len(rgb_to_id)} провинций")

    # Загружаем карту
    log_print("\n2. Загрузка карты...")
    if not os.path.exists(provinces_bmp):
        log_print(f"ОШИБКА: Файл {provinces_bmp} не найден!")
        sys.exit(1)

    img = Image.open(provinces_bmp)
    width, height = img.size
    pixels = img.load()
    log_print(f"   Размер: {width}x{height}")

    # Находим соседей
    log_print("\n3. Поиск соседей (это может занять время)...")
    all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}

    # Используем шаг 3 для баланса скорости и точности
    step = 3
    checked = 0
    total = (width // step) * (height // step)

    for y in range(0, height, step):
        for x in range(0, width, step):
            try:
                current_rgb = pixels[x, y]
                
                if current_rgb in rgb_to_id:
                    current_id = rgb_to_id[current_rgb]
                    if current_id in PROVINCES_TO_FIX:
                        # Проверяем 4 соседних пикселя
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < width and 0 <= ny < height:
                                neighbor_rgb = pixels[nx, ny]
                                if neighbor_rgb != current_rgb and neighbor_rgb in rgb_to_id:
                                    neighbor_id = rgb_to_id[neighbor_rgb]
                                    all_neighbors[current_id].add(neighbor_id)
            except Exception:
                pass
            
            checked += 1
            if checked % 100000 == 0:
                progress = (checked / total) * 100
                log_print(f"   Прогресс: {progress:.1f}% ({checked}/{total})")

    log_print("\n4. Найденные соседи:")
    for prov_id in sorted(PROVINCES_TO_FIX):
        neighbors = sorted(all_neighbors.get(prov_id, set()))
        name = id_to_name.get(prov_id, "?")
        log_print(f"   {prov_id} ({name}): {len(neighbors)} соседей - {neighbors}")

    # Проверяем существующие границы
    log_print("\n5. Проверка существующих границ...")
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

    log_print(f"   Найдено {len(existing_impassable)} существующих границ")

    # Генерируем новые границы
    log_print("\n6. Генерация новых границ...")
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
                log_print(f"   НОВАЯ: {prov_id} <-> {neighbor} ({terrain})")

    log_print(f"\n{'='*60}")
    log_print(f"Всего новых границ: {len(new_impassables)}")
    log_print(f"{'='*60}")

    # Добавляем в файл
    if new_impassables:
        log_print("\n7. Добавление в adjacencies.csv...")
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
        
        log_print(f"   ✓ Добавлено {len(new_impassables)} границ")
    else:
        log_print("\n   ✓ Все границы уже существуют")

    log_print("\nГотово!")
    
except Exception as e:
    log_print(f"\nОШИБКА: {e}")
    import traceback
    log_print(traceback.format_exc())
    sys.exit(1)
finally:
    if log:
        log.close()
