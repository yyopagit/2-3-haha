#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для определения соседних провинций для провинции 1740
"""

import sys
import os
from collections import defaultdict

# Добавляем путь к корневой папке игры
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("PIL/Pillow не установлен. Установите: pip install Pillow")
    sys.exit(1)

def get_province_rgb(province_id, definition_file):
    """Получить RGB цвет провинции из definition.csv"""
    with open(definition_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith(str(province_id) + ';'):
                parts = line.strip().split(';')
                if len(parts) >= 4:
                    return (int(parts[1]), int(parts[2]), int(parts[3]))
    return None

def get_province_name(province_id, definition_file):
    """Получить название провинции из definition.csv"""
    with open(definition_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith(str(province_id) + ';'):
                parts = line.strip().split(';')
                if len(parts) >= 5:
                    return parts[4]
    return None

def find_neighbors(province_id, map_dir='../../map'):
    """Найти соседние провинции для заданной провинции"""
    
    # Определяем абсолютные пути
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_root = os.path.join(script_dir, '..', '..')
    map_dir_abs = os.path.join(game_root, 'map')
    
    definition_file = os.path.join(map_dir_abs, 'definition.csv')
    provinces_bmp = os.path.join(map_dir_abs, 'provinces.bmp')
    
    print(f"Ищем файлы:")
    print(f"  definition.csv: {definition_file} (существует: {os.path.exists(definition_file)})")
    print(f"  provinces.bmp: {provinces_bmp} (существует: {os.path.exists(provinces_bmp)})")
    
    if not os.path.exists(definition_file):
        print(f"Файл {definition_file} не найден!")
        return []
    
    if not os.path.exists(provinces_bmp):
        print(f"Файл {provinces_bmp} не найден!")
        return []
    
    # Получаем RGB целевой провинции
    target_rgb = get_province_rgb(province_id, definition_file)
    if not target_rgb:
        print(f"Провинция {province_id} не найдена в definition.csv")
        return []
    
    target_name = get_province_name(province_id, definition_file)
    print(f"Ищем соседей для провинции {province_id} ({target_name})")
    print(f"RGB: {target_rgb}")
    
    # Загружаем карту
    img = Image.open(provinces_bmp)
    width, height = img.size
    pixels = img.load()
    
    # Создаем словарь RGB -> ID провинций
    rgb_to_id = {}
    with open(definition_file, 'r', encoding='utf-8') as f:
        for line in f:
            if ';' in line and not line.startswith('#'):
                parts = line.strip().split(';')
                if len(parts) >= 4:
                    try:
                        prov_id = int(parts[0])
                        rgb = (int(parts[1]), int(parts[2]), int(parts[3]))
                        rgb_to_id[rgb] = prov_id
                    except ValueError:
                        continue
    
    # Находим соседние провинции
    neighbors = set()
    
    # Проверяем каждый пиксель целевой провинции и его соседей
    for y in range(height):
        for x in range(width):
            current_rgb = pixels[x, y]
            
            # Если это пиксель целевой провинции
            if current_rgb == target_rgb:
                # Проверяем 4 соседних пикселя (верх, низ, лево, право)
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        neighbor_rgb = pixels[nx, ny]
                        if neighbor_rgb != target_rgb and neighbor_rgb in rgb_to_id:
                            neighbor_id = rgb_to_id[neighbor_rgb]
                            neighbors.add(neighbor_id)
    
    return sorted(list(neighbors))

if __name__ == '__main__':
    province_id = 1740
    neighbors = find_neighbors(province_id)
    
    print(f"\nНайдено {len(neighbors)} соседних провинций:")
    
    definition_file = '../../map/definition.csv'
    for neighbor_id in neighbors:
        name = get_province_name(neighbor_id, definition_file)
        print(f"  {neighbor_id}: {name}")
