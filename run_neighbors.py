# -*- coding: utf-8 -*-
import os
import sys

# Создаем файл результата сразу
result_file = 'neighbors_result.txt'
print(f"Создаю файл: {result_file}", flush=True)

try:
    result = open(result_file, 'w', encoding='utf-8')
    print("Файл создан", flush=True)
    
    result.write("НАЧАЛО РАБОТЫ\n")
    result.flush()
    
    # Импорт PIL
    try:
        from PIL import Image
        result.write("PIL импортирован\n")
        result.flush()
    except ImportError:
        result.write("ОШИБКА: PIL не установлен\n")
        result.flush()
        sys.exit(1)
    
    # Проверка файлов
    map_dir = 'map'
    definition_file = os.path.join(map_dir, 'definition.csv')
    provinces_bmp = os.path.join(map_dir, 'provinces.bmp')
    
    result.write(f"Проверка файлов:\n")
    result.write(f"  definition.csv: {os.path.exists(definition_file)}\n")
    result.write(f"  provinces.bmp: {os.path.exists(provinces_bmp)}\n")
    result.flush()
    
    if os.path.exists(provinces_bmp):
        size = os.path.getsize(provinces_bmp)
        result.write(f"  Размер provinces.bmp: {size} байт\n")
        result.flush()
        
        # Открываем карту
        img = Image.open(provinces_bmp)
        width, height = img.size
        result.write(f"  Размер карты: {width}x{height}\n")
        result.flush()
        
        result.write("Карта загружена успешно!\n")
        result.flush()
    
    result.write("ТЕСТ ЗАВЕРШЕН\n")
    result.close()
    print("Файл записан и закрыт", flush=True)
    
except Exception as e:
    print(f"ОШИБКА: {e}", flush=True)
    import traceback
    traceback.print_exc(file=sys.stdout)
    if 'result' in locals() and result:
        result.write(f"ОШИБКА: {e}\n")
        result.write(traceback.format_exc())
        result.close()

print("Готово", flush=True)
