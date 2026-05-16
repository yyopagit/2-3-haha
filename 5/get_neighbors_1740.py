# -*- coding: utf-8 -*-
"""Определение соседних провинций для провинции 1740 (Kufra)"""

import os

# Пути
base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
map_dir = os.path.join(base_dir, 'map')
definition_file = os.path.join(map_dir, 'definition.csv')

print("=== Анализ провинции 1740 ===")

# Читаем информацию о провинции 1740
province_id = 1740
target_rgb = None
target_name = None

with open(definition_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('1740;'):
            parts = line.strip().split(';')
            if len(parts) >= 5:
                target_rgb = (int(parts[1]), int(parts[2]), int(parts[3]))
                target_name = parts[4]
                break

print(f"Провинция {province_id}: {target_name}")
print(f"RGB цвет: {target_rgb}")

# Пробуем использовать PIL для анализа карты
try:
    from PIL import Image
    
    provinces_bmp = os.path.join(map_dir, 'provinces.bmp')
    if not os.path.exists(provinces_bmp):
        print(f"\nОШИБКА: Файл {provinces_bmp} не найден!")
    else:
        print(f"\nЗагружаем карту: {provinces_bmp}")
        img = Image.open(provinces_bmp)
        width, height = img.size
        print(f"Размер карты: {width}x{height}")
        
        # Создаем словарь RGB -> ID
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
                        except ValueError:
                            continue
        
        print(f"Загружено {len(rgb_to_id)} провинций")
        
        # Находим соседние провинции
        neighbors = set()
        pixels = img.load()
        
        # Проверяем каждый пиксель
        checked = 0
        for y in range(0, height, 10):  # Проверяем каждый 10-й пиксель для скорости
            for x in range(0, width, 10):
                current_rgb = pixels[x, y]
                
                if current_rgb == target_rgb:
                    # Проверяем соседей
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            neighbor_rgb = pixels[nx, ny]
                            if neighbor_rgb != target_rgb and neighbor_rgb in rgb_to_id:
                                neighbor_id = rgb_to_id[neighbor_rgb]
                                neighbors.add(neighbor_id)
                checked += 1
        
        print(f"Проверено {checked} пикселей")
        
        if neighbors:
            print(f"\nНайдено {len(neighbors)} соседних провинций:")
            for neighbor_id in sorted(neighbors):
                name = id_to_name.get(neighbor_id, 'Unknown')
                print(f"  {neighbor_id}: {name}")
        else:
            print("\nСоседние провинции не найдены (возможно, нужно проверить больше пикселей)")
            
except ImportError:
    print("\nPIL/Pillow не установлен. Установите: pip install Pillow")
    print("\nБлижайшие провинции по ID (могут быть соседними):")
    nearby_ids = [1739, 1741, 1742, 1738, 1743]
    with open(definition_file, 'r', encoding='utf-8') as f:
        for line in f:
            for near_id in nearby_ids:
                if line.startswith(str(near_id) + ';'):
                    parts = line.strip().split(';')
                    if len(parts) >= 5:
                        name = parts[4]
                        print(f"  {near_id}: {name}")
                    break
