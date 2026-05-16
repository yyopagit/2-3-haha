# -*- coding: utf-8 -*-
"""
Перенос населения из указанных провинций в соседние (финальная версия)
"""

import os
import re
import sys

PROVINCE_MAPPING = {
    1740: 1739,  # Waddan -> Kufra
    1738: 1739,  # Jaghbub -> Kufra  
    1739: 1741,  # Kufra -> Murzuk (изменено, чтобы избежать цикла)
    1758: 1757,  # Farafra -> Sharm al-Shaykh
    1719: 1720,  # Ilizi -> Timimoun (изменено, чтобы избежать цикла)
    1724: 1725,  # Tamanrasset -> Tunis
    1718: 1719,  # In Salah -> Ilizi
    1594: 1595,  # Kashgar -> Ili
    1598: 1599,  # Khotan -> Kumul
    2094: 2095,  # Kimberley -> Dikathong
    2077: 2078,  # Tsabong -> Windhoek
    2074: 2075,  # Gaborone -> Serowe
    1161: 1162,  # Sharawrah -> Bahrain
    2586: 2587,  # AlAhsa -> Kola
    934: 935,    # Najaf -> Kuwait
    931: 932,    # Rutbah -> Basra
    929: 930,    # Karbala -> Kut
}

pops_dir = os.path.join(os.path.dirname(__file__), 'history', 'pops')

def get_province_block(lines, start_idx):
    """Извлечь блок провинции"""
    if start_idx >= len(lines):
        return None, start_idx
    
    block = [lines[start_idx]]
    brace_count = 1
    i = start_idx + 1
    
    while i < len(lines) and brace_count > 0:
        block.append(lines[i])
        brace_count += lines[i].count('{') - lines[i].count('}')
        i += 1
    
    return block, i

def find_province_idx(lines, prov_id):
    """Найти индекс начала блока провинции"""
    for i, line in enumerate(lines):
        if re.match(rf'^\s*{prov_id}\s*=\s*\{{', line):
            return i
    return -1

def insert_population(lines, target_id, source_block):
    """Вставить население из source_block в провинцию target_id"""
    target_idx = find_province_idx(lines, target_id)
    
    if target_idx == -1:
        # Провинция не существует - создаем новый блок
        # Находим место для вставки (после последней провинции)
        insert_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if re.match(r'^\s*\d+\s*=\s*\{', lines[i]):
                # Находим конец этого блока
                brace_count = 1
                j = i + 1
                while j < len(lines) and brace_count > 0:
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    j += 1
                insert_idx = j
                break
        
        # Создаем новый блок
        new_block = [f'{target_id} = {{\n'] + source_block[1:]
        if insert_idx < len(lines) and lines[insert_idx-1].strip() != '':
            lines.insert(insert_idx, '\n')
            insert_idx += 1
        lines[insert_idx:insert_idx] = new_block
    else:
        # Провинция существует - добавляем население
        # Находим конец блока
        brace_count = 1
        end_idx = target_idx + 1
        while end_idx < len(lines) and brace_count > 0:
            brace_count += lines[end_idx].count('{') - lines[end_idx].count('}')
            end_idx += 1
        
        # Извлекаем содержимое исходного блока (без ID и закрывающей скобки)
        source_content = source_block[1:-1]
        
        # Вставляем перед закрывающей скобкой
        if end_idx > 0 and lines[end_idx - 1].strip() != '':
            lines.insert(end_idx - 1, '\n')
            end_idx += 1
        lines[end_idx-1:end_idx-1] = source_content

def process_file(file_path):
    """Обработать файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        i = 0
        modified = False
        
        while i < len(lines):
            line = lines[i]
            province_id = None
            
            # Проверяем, является ли это провинцией для переноса
            for source_id in PROVINCE_MAPPING.keys():
                if re.match(rf'^\s*{source_id}\s*=\s*\{{', line):
                    province_id = source_id
                    break
            
            if province_id:
                # Извлекаем блок
                block, next_idx = get_province_block(lines, i)
                target_id = PROVINCE_MAPPING[province_id]
                
                # Добавляем население в целевую провинцию
                # Проверяем, есть ли целевая провинция в new_lines или дальше
                found_in_new = find_province_idx(new_lines, target_id) != -1
                found_in_remaining = find_province_idx(lines[next_idx:], target_id) != -1
                
                if found_in_new:
                    # Добавляем в существующую провинцию в new_lines
                    insert_population(new_lines, target_id, block)
                elif found_in_remaining:
                    # Провинция будет дальше - создаем новый блок сейчас
                    insert_population(new_lines, target_id, block)
                else:
                    # Провинции нет - создаем новый блок
                    insert_population(new_lines, target_id, block)
                
                # Пропускаем исходный блок (не добавляем его)
                i = next_idx
                modified = True
            else:
                new_lines.append(line)
                i += 1
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        return False
    except Exception as e:
        print(f"Ошибка в {os.path.basename(file_path)}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def main():
    if not os.path.exists(pops_dir):
        print(f"ОШИБКА: Папка не найдена: {pops_dir}")
        return
    
    print("Начинаем перенос населения...")
    print(f"Провинции для переноса: {list(PROVINCE_MAPPING.keys())}")
    
    processed = 0
    total = 0
    
    for root, dirs, files in os.walk(pops_dir):
        for file in files:
            if file.endswith('.txt'):
                total += 1
                file_path = os.path.join(root, file)
                if process_file(file_path):
                    processed += 1
                    rel_path = os.path.relpath(file_path, pops_dir)
                    print(f"  Обработан: {rel_path}")
    
    print(f"\nПроверено файлов: {total}")
    print(f"Обработано файлов: {processed}")
    print(f"Население перенесено из {len(PROVINCE_MAPPING)} провинций в соседние")

if __name__ == '__main__':
    main()
