# -*- coding: utf-8 -*-
import os
import sys

print("Начало работы...")
sys.stdout.flush()

try:
    from PIL import Image
    print("PIL импортирован")
    sys.stdout.flush()
except ImportError:
    print("ОШИБКА: PIL не установлен")
    sys.exit(1)

script_dir = os.path.dirname(os.path.abspath(__file__))
map_dir = os.path.join(script_dir, 'map')
definition_file = os.path.join(map_dir, 'definition.csv')
provinces_bmp = os.path.join(map_dir, 'provinces.bmp')

print(f"Проверка файлов:")
print(f"  definition.csv: {os.path.exists(definition_file)}")
print(f"  provinces.bmp: {os.path.exists(provinces_bmp)}")
sys.stdout.flush()

if os.path.exists(provinces_bmp):
    print("Открываем карту...")
    sys.stdout.flush()
    img = Image.open(provinces_bmp)
    print(f"Размер: {img.size}")
    sys.stdout.flush()

print("Готово!")
sys.stdout.flush()
