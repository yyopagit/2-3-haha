# -*- coding: utf-8 -*-
import os
import re
import sys

# Тестируем на одном файле
test_file = r'history\pops\1836.1.1\Libya.txt'
PROVINCE_MAPPING = {1740: [1739, 1741], 1738: [1739, 1737], 1739: [1740, 1738]}

file_path = os.path.join(os.path.dirname(__file__), test_file)

print(f"Тестируем файл: {file_path}")
print(f"Существует: {os.path.exists(file_path)}")

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем провинции
    for prov_id in [1740, 1738, 1739]:
        pattern = rf'^\s*{prov_id}\s*=\s*\{{'
        if re.search(pattern, content, re.MULTILINE):
            print(f"Найдена провинция {prov_id}")
        else:
            print(f"Провинция {prov_id} не найдена")
else:
    print("Файл не найден!")

print("Тест завершен")
