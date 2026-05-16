# -*- coding: utf-8 -*-
"""
Детальный анализ соседей с уменьшенным шагом для точности
Проверяет провинции 1732 и 1740
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    print("ОШИБКА: PIL/Pillow не установлен")
    sys.exit(1)

# Проверяемые провинции
CHECK_PROVINCES = [1732, 1740]
PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

script_dir = os.path.dirname(os.path.abspath(__file__))
map_dir = os.path.join(script_dir, 'map')
definition_file = os.path.join(map_dir, 'definition.csv')
provinces_bmp = os.path.join(map_dir, 'provinces.bmp')
result_file = os.path.join(script_dir, 'neighbors_detailed_result.txt')

# Открываем файл для результатов
result_f = None
try:
    result_f = open(result_file, 'w', encoding='utf-8')
except Exception as e:
    print(f"ОШИБКА: Не удалось создать файл результатов: {e}", flush=True)
    result_f = None

def out(msg):
    print(msg, flush=True)
    if result_f:
        try:
            result_f.write(msg + '\n')
            result_f.flush()
        except:
            pass

try:
    out("=" * 60)
    out("ДЕТАЛЬНЫЙ АНАЛИЗ СОСЕДЕЙ (ШАГ 1 - КАЖДЫЙ ПИКСЕЛЬ)")
    out("=" * 60)

    # Загружаем definition.csv
    out("\n1. Загрузка definition.csv...")
    rgb_to_id = {}
    id_to_name = {}

    encodings = ['utf-8', 'cp1251', 'latin-1', 'iso-8859-1']
    f = None
    for enc in encodings:
        try:
            f = open(definition_file, 'r', encoding=enc, errors='ignore')
            f.readline()
            f.seek(0)
            break
        except UnicodeDecodeError:
            if f:
                f.close()
            continue

    if not f:
        out(f"ОШИБКА: Не удалось открыть файл {definition_file}!")
        if result_f:
            result_f.close()
        sys.exit(1)

    with f:
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

    out(f"   Загружено {len(rgb_to_id)} провинций")

    # Загружаем карту
    out("\n2. Загрузка карты...")
    img = Image.open(provinces_bmp)
    width, height = img.size
    pixels = img.load()
    out(f"   Размер: {width}x{height}")

    # Анализируем соседей по каждому пикселю для максимальной точности
    out("\n3. Поиск соседей (анализ по каждому пикселю)...")
    out(f"   Всего пикселей для проверки: {width * height:,}")
    all_neighbors = {prov: set() for prov in CHECK_PROVINCES + PROVINCES_TO_FIX}

    # Используем шаг 1 для проверки каждого пикселя
    step = 1
    checked = 0
    total = width * height

    for y in range(0, height, step):
        for x in range(0, width, step):
            try:
                current_rgb = pixels[x, y]
                
                if current_rgb in rgb_to_id:
                    current_id = rgb_to_id[current_rgb]
                    if current_id in all_neighbors:
                        # Проверяем 4 соседних пикселя + 4 диагональных (8 направлений)
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), 
                                        (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < width and 0 <= ny < height:
                                neighbor_rgb = pixels[nx, ny]
                                if neighbor_rgb != current_rgb and neighbor_rgb in rgb_to_id:
                                    neighbor_id = rgb_to_id[neighbor_rgb]
                                    all_neighbors[current_id].add(neighbor_id)
            except Exception:
                pass
            
            checked += 1
            if checked % 500000 == 0:
                progress = (checked / total) * 100
                out(f"   Прогресс: {progress:.1f}% ({checked:,} / {total:,})")

    out("\n4. Найденные соседи:")
    for prov_id in sorted(CHECK_PROVINCES):
        neighbors = sorted(all_neighbors.get(prov_id, set()))
        name = id_to_name.get(prov_id, "?")
        out(f"   {prov_id} ({name}): {len(neighbors)} соседей - {neighbors}")

    # Также показываем для всех наших провинций
    out("\n5. Все провинции для исправления:")
    for prov_id in sorted(PROVINCES_TO_FIX):
        neighbors = sorted(all_neighbors.get(prov_id, set()))
        name = id_to_name.get(prov_id, "?")
        out(f"   {prov_id} ({name}): {len(neighbors)} соседей - {neighbors}")

    # Проверяем существующие границы для проверяемых провинций
    out("\n6. Проверка существующих границ в adjacencies.csv...")
    adjacencies_file = os.path.join(map_dir, 'adjacencies.csv')
    existing_impassable = set()

    encodings = ['utf-8', 'cp1251', 'latin-1', 'iso-8859-1']
    f = None
    for enc in encodings:
        try:
            f = open(adjacencies_file, 'r', encoding=enc, errors='ignore')
            f.readline()
            f.seek(0)
            break
        except UnicodeDecodeError:
            if f:
                f.close()
            continue

    if f:
        with f:
            for line in f:
                if 'impassable' in line and not line.startswith('#'):
                    parts = line.split(';')
                    if len(parts) >= 2:
                        try:
                            from_prov = int(parts[0])
                            to_prov = int(parts[1])
                            if from_prov in CHECK_PROVINCES or to_prov in CHECK_PROVINCES:
                                existing_impassable.add((from_prov, to_prov))
                        except ValueError:
                            pass

    out(f"\nСуществующие impassable границы для проверяемых провинций:")
    for from_prov, to_prov in sorted(existing_impassable):
        if from_prov in CHECK_PROVINCES:
            out(f"   {from_prov} -> {to_prov}")

    # Проверяем недостающие
    out("\n7. Проверка недостающих границ:")
    for prov_id in CHECK_PROVINCES:
        neighbors = all_neighbors.get(prov_id, set())
        missing = []
        for neighbor in neighbors:
            if (prov_id, neighbor) not in existing_impassable and (neighbor, prov_id) not in existing_impassable:
                missing.append(neighbor)
        if missing:
            out(f"   {prov_id}: недостают границы с {missing}")
        else:
            out(f"   {prov_id}: все границы присутствуют ✓")

    out("\nГотово!")
    out(f"\nРезультаты сохранены в: {result_file}")
except Exception as e:
    out(f"\nОШИБКА: {e}")
    import traceback
    out(traceback.format_exc())
finally:
    if result_f:
        result_f.close()
