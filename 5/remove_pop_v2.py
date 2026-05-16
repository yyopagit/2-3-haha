# -*- coding: utf-8 -*-
"""
Удаление населения из указанных провинций (улучшенная версия)
"""

import os

PROVINCES_TO_CLEAR = [1740, 1738, 1739, 1758, 1719, 1724, 1718, 1594, 1598, 2094, 2077, 2074, 1161, 2586, 934, 931, 929]

pops_dir = os.path.join(os.path.dirname(__file__), 'history', 'pops')

def remove_province_block(lines, province_id):
    """Удалить блок провинции из списка строк"""
    result = []
    i = 0
    removed = False
    
    while i < len(lines):
        line = lines[i]
        
        # Проверяем, начинается ли строка с ID провинции
        stripped = line.strip()
        if stripped.startswith(f'{province_id} = {{'):
            # Найден блок провинции - пропускаем его
            brace_count = 1
            i += 1
            
            # Пропускаем строки до закрытия блока
            while i < len(lines) and brace_count > 0:
                current_line = lines[i]
                brace_count += current_line.count('{') - current_line.count('}')
                i += 1
            
            removed = True
            continue
        
        result.append(line)
        i += 1
    
    return result, removed

def process_file(file_path):
    """Обработать один файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        for province_id in PROVINCES_TO_CLEAR:
            lines, was_removed = remove_province_block(lines, province_id)
            if was_removed:
                modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        return False
    except Exception as e:
        print(f"Ошибка: {file_path}: {e}")
        return False

def main():
    if not os.path.exists(pops_dir):
        print(f"Папка не найдена: {pops_dir}")
        return
    
    processed = 0
    for root, dirs, files in os.walk(pops_dir):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                if process_file(file_path):
                    processed += 1
                    print(f"Обработан: {os.path.relpath(file_path, pops_dir)}")
    
    print(f"\nВсего обработано: {processed} файлов")

if __name__ == '__main__':
    main()
