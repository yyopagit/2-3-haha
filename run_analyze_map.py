# -*- coding: utf-8 -*-
"""Простой скрипт для поиска всех соседей через карту"""

import os
import sys

# Создаем файл сразу
result_file = 'neighbors_result.txt'
print(f"Создаю файл: {result_file}", flush=True)

try:
    f = open(result_file, 'w', encoding='utf-8')
    f.write("НАЧАЛО РАБОТЫ\n")
    f.flush()
    print("Файл создан", flush=True)
except Exception as e:
    print(f"ОШИБКА создания файла: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

try:
    f.write("Импорт библиотек...\n")
    f.flush()
    
    from PIL import Image
    f.write("PIL импортирован\n")
    f.flush()
    
    PROVINCES_TO_FIX = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]
    
    map_dir = 'map'
    definition_file = os.path.join(map_dir, 'definition.csv')
    provinces_bmp = os.path.join(map_dir, 'provinces.bmp')
    
    f.write("Загрузка definition.csv...\n")
    f.flush()
    
    rgb_to_id = {}
    id_to_name = {}
    
    with open(definition_file, 'r', encoding='utf-8') as df:
        for line in df:
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
    
    f.write(f"Загружено {len(rgb_to_id)} провинций\n")
    f.flush()
    
    f.write("Загрузка карты...\n")
    f.flush()
    
    img = Image.open(provinces_bmp)
    width, height = img.size
    pixels = img.load()
    
    f.write(f"Размер карты: {width}x{height}\n")
    f.flush()
    
    # Находим соседей
    f.write("Поиск соседей...\n")
    f.flush()
    
    all_neighbors = {prov: set() for prov in PROVINCES_TO_FIX}
    
    step = 5
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
            if checked % 50000 == 0:
                progress = (checked / total) * 100
                f.write(f"Прогресс: {progress:.1f}%\n")
                f.flush()
    
    # Выводим результаты
    f.write("\n" + "=" * 60 + "\n")
    f.write("НАЙДЕННЫЕ СОСЕДИ:\n")
    f.write("=" * 60 + "\n\n")
    
    for prov_id in sorted(PROVINCES_TO_FIX):
        neighbors = sorted(all_neighbors.get(prov_id, set()))
        name = id_to_name.get(prov_id, "?")
        f.write(f"{prov_id} ({name}): {len(neighbors)} соседей\n")
        f.write(f"  {neighbors}\n\n")
    
    f.write("\nГотово!\n")
    f.close()
    print("Файл записан", flush=True)
    
except Exception as e:
    import traceback
    error_msg = f"ОШИБКА: {e}\n{traceback.format_exc()}"
    f.write(error_msg)
    f.close()
    print(error_msg, file=sys.stderr, flush=True)
