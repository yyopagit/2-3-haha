# -*- coding: utf-8 -*-
"""
Быстрая версия: анализирует карту и находит всех соседей
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    print("ОШИБКА: PIL/Pillow не установлен")
    sys.exit(1)

PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

script_dir = os.path.dirname(os.path.abspath(__file__))
map_dir = os.path.join(script_dir, 'map')
definition_file = os.path.join(map_dir, 'definition.csv')
provinces_bmp = os.path.join(map_dir, 'provinces.bmp')
adjacencies_file = os.path.join(map_dir, 'adjacencies.csv')
result_file = os.path.join(script_dir, 'neighbors_result.txt')

# Создаем файл сразу в самом начале, ДО всех операций
result = None
try:
    result = open(result_file, 'w', encoding='utf-8')
    result.write("Файл создан\n")
    result.flush()
except Exception as e:
    print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать файл результатов: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc(file=sys.stderr)
    result = None

def out(msg):
    if result:
        try:
            result.write(msg + '\n')
            result.flush()
        except Exception as e:
            print(f"Ошибка записи в файл: {e}", flush=True)
    print(msg, flush=True)

try:
    out("=" * 60)
    out("АНАЛИЗ КАРТЫ И ПОИСК ВСЕХ СОСЕДЕЙ")
    out("=" * 60)

    # Загружаем definition.csv
    out("\n1. Загрузка definition.csv...")
    if not os.path.exists(definition_file):
        out(f"ОШИБКА: Файл не найден!")
        sys.exit(1)

    rgb_to_id = {}
    id_to_name = {}

    # Пробуем разные кодировки для definition.csv
    encodings = ['utf-8', 'cp1251', 'latin-1', 'iso-8859-1']
    f = None
    for enc in encodings:
        try:
            f = open(definition_file, 'r', encoding=enc, errors='ignore')
            # Пробуем прочитать первую строку
            f.readline()
            f.seek(0)  # Возвращаемся в начало
            break
        except UnicodeDecodeError:
            if f:
                f.close()
            continue
    
    if not f:
        out(f"ОШИБКА: Не удалось открыть файл {definition_file} ни с одной кодировкой!")
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
    if not os.path.exists(provinces_bmp):
        out(f"ОШИБКА: Файл не найден!")
        sys.exit(1)

    img = Image.open(provinces_bmp)
    width, height = img.size
    pixels = img.load()
    out(f"   Размер: {width}x{height}")

    # Находим соседей по каждому пикселю для максимальной точности
    out("\n3. Поиск соседей (анализ по каждому пикселю)...")
    all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}

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
                    if current_id in PROVINCES_TO_FIX:
                        # Проверяем 8 направлений (4 основных + 4 диагональных) для лучшего покрытия
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
            if checked % 100000 == 0:
                progress = (checked / total) * 100
                out(f"   Прогресс: {progress:.1f}%")

    out("\n4. Найденные соседи:")
    for prov_id in sorted(PROVINCES_TO_FIX):
        neighbors = sorted(all_neighbors.get(prov_id, set()))
        name = id_to_name.get(prov_id, "?")
        out(f"   {prov_id} ({name}): {len(neighbors)} соседей - {neighbors}")

    # Проверяем существующие границы
    out("\n5. Проверка существующих границ...")
    existing_impassable = set()
    # Пробуем разные кодировки для adjacencies.csv
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
    
    if not f:
        out(f"ОШИБКА: Не удалось открыть файл {adjacencies_file}!")
        sys.exit(1)
    
    with f:
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

    out(f"   Найдено {len(existing_impassable)} существующих границ")

    # Генерируем новые границы
    out("\n6. Генерация новых границ...")
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
                out(f"   НОВАЯ: {prov_id} <-> {neighbor} ({terrain})")

    out(f"\n{'='*60}")
    out(f"Всего новых границ: {len(new_impassables)}")
    out(f"{'='*60}")

    # Добавляем в файл
    if new_impassables:
        out("\n7. Добавление в adjacencies.csv...")
        # Читаем файл с правильной кодировкой
        encodings = ['utf-8', 'cp1251', 'latin-1', 'iso-8859-1']
        lines = None
        used_encoding = 'utf-8'
        for enc in encodings:
            try:
                with open(adjacencies_file, 'r', encoding=enc, errors='ignore') as f:
                    lines = f.readlines()
                    used_encoding = enc
                    break
            except UnicodeDecodeError:
                continue
        
        if lines is None:
            out("ОШИБКА: Не удалось прочитать adjacencies.csv!")
            sys.exit(1)
        
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
        
        # Записываем с той же кодировкой, что и читали (или utf-8 если это не сработает)
        try:
            with open(adjacencies_file, 'w', encoding=used_encoding, errors='ignore') as f:
                f.writelines(lines)
        except Exception:
            # Если не получилось, пробуем utf-8
            with open(adjacencies_file, 'w', encoding='utf-8', errors='ignore') as f:
                f.writelines(lines)
        
        out(f"   ✓ Добавлено {len(new_impassables)} границ")
    else:
        out("\n   ✓ Все границы уже существуют")

    out("\nГотово!")
    
except Exception as e:
    out(f"\nОШИБКА: {e}")
    import traceback
    out(traceback.format_exc())
    sys.exit(1)
finally:
    if result:
        result.close()
