# -*- coding: utf-8 -*-
"""
Скрипт для удаления населения из указанных провинций
"""

import os
import re

# Список провинций для очистки
PROVINCES_TO_CLEAR = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

# Путь к папке с файлами pops
pops_dir = os.path.join(os.path.dirname(__file__), 'history', 'pops')

def remove_province_population(content, province_id):
    """Удалить блок населения для провинции"""
    # Паттерн для поиска блока провинции: "ID = {" ... "}"
    pattern = rf'^\s*{province_id}\s*=\s*\{{.*?\n\}}'
    
    # Используем DOTALL для многострочного поиска
    pattern_multiline = rf'^\s*{province_id}\s*=\s*\{{.*?\n\}}'
    
    # Удаляем блок
    content = re.sub(pattern_multiline, '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Также удаляем комментарии перед блоком, если они есть
    content = re.sub(rf'^#.*?\n\s*{province_id}\s*=\s*\{{.*?\n\}}', '', content, flags=re.MULTILINE | re.DOTALL)
    
    return content

def remove_block(lines, start_idx):
    """Удалить блок провинции, начиная с указанной строки"""
    if start_idx >= len(lines):
        return start_idx
    
    # Находим открывающую скобку
    brace_count = 0
    end_idx = start_idx
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0 and '{' in line:
            # Блок закончился на этой строке
            end_idx = i + 1
            break
        elif brace_count < 0:
            # Блок закончился
            end_idx = i + 1
            break
    
    # Удаляем блок (включая комментарий перед ним, если есть)
    remove_start = start_idx
    if start_idx > 0 and lines[start_idx - 1].strip().startswith('#'):
        remove_start = start_idx - 1
    
    # Удаляем строки
    del lines[remove_start:end_idx]
    
    return remove_start

def process_file(file_path):
    """Обработать один файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_lines = lines.copy()
        modified = False
        
        # Ищем и удаляем блоки провинций
        i = 0
        while i < len(lines):
            line = lines[i]
            # Проверяем, начинается ли строка с ID провинции
            for province_id in PROVINCES_TO_CLEAR:
                if re.match(rf'^\s*{province_id}\s*=\s*\{{', line):
                    # Найден блок провинции
                    old_len = len(lines)
                    i = remove_block(lines, i)
                    if len(lines) < old_len:
                        modified = True
                    break
            else:
                i += 1
        
        # Если содержимое изменилось, сохраняем
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        return False
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")
        return False

def main():
    """Основная функция"""
    if not os.path.exists(pops_dir):
        print(f"Папка {pops_dir} не найдена!")
        return
    
    # Обрабатываем все файлы в подпапках
    processed = 0
    for root, dirs, files in os.walk(pops_dir):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                if process_file(file_path):
                    processed += 1
                    print(f"Обработан: {file_path}")
    
    print(f"\nВсего обработано файлов: {processed}")

if __name__ == '__main__':
    main()
