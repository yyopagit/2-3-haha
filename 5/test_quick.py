# -*- coding: utf-8 -*-
import os
import sys

result_file = 'neighbors_result.txt'

# Создаем файл сразу
with open(result_file, 'w', encoding='utf-8') as f:
    f.write("Тест запуска скрипта\n")
    f.write(f"Рабочая директория: {os.getcwd()}\n")
    
    try:
        from PIL import Image
        f.write("PIL импортирован успешно\n")
        
        map_dir = os.path.join('map')
        provinces_bmp = os.path.join(map_dir, 'provinces.bmp')
        
        if os.path.exists(provinces_bmp):
            f.write(f"Файл карты найден: {provinces_bmp}\n")
            img = Image.open(provinces_bmp)
            f.write(f"Размер карты: {img.size}\n")
            f.write("Карта загружена успешно\n")
        else:
            f.write(f"Файл карты НЕ найден: {provinces_bmp}\n")
            
    except Exception as e:
        f.write(f"ОШИБКА: {e}\n")
        import traceback
        f.write(traceback.format_exc())

print(f"Результат сохранен в {result_file}")
