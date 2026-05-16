# -*- coding: utf-8 -*-
"""
Финальная версия: Перенос населения из указанных провинций в соседние
"""

import os
import re

PROVINCE_MAPPING = {
    1740: 1739,  # Waddan -> Kufra
    1738: 1739,  # Jaghbub -> Kufra  
    1739: 1741,  # Kufra -> Murzuk (изменено, чтобы избежать цикла с 1740)
    1758: 1757,  # Farafra -> Sharm al-Shaykh
    1719: 1720,  # Ilizi -> Timimoun (изменено, чтобы избежать цикла с 1718)
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

def get_block(lines, start_idx):
    """Получить блок провинции"""
    block = [lines[start_idx]]
    brace_count = 1
    i = start_idx + 1
    while i < len(lines) and brace_count > 0:
        block.append(lines[i])
        brace_count += lines[i].count('{') - lines[i].count('}')
        i += 1
    return block, i

def find_province(lines, prov_id):
    """Найти индекс начала блока провинции"""
    for i, line in enumerate(lines):
        if re.match(rf'^\s*{prov_id}\s*=\s*\{{', line):
            return i
    return -1

def add_population(new_lines, remaining_lines, target_id, source_block):
    """Добавить население в провинцию"""
    # Ищем в уже обработанных строках
    target_idx = find_province(new_lines, target_id)
    
    # Если не найдено, ищем в оставшихся строках
    if target_idx == -1:
        remaining_idx = find_province(remaining_lines, target_id)
        if remaining_idx != -1:
            # Провинция будет позже - создаем новый блок сейчас
            target_idx = -1
        else:
            # Провинции нет вообще - создаем новый блок
            target_idx = -1
    
    if target_idx == -1:
        # Создаем новый блок в конце new_lines
        insert_idx = len(new_lines)
        # Ищем последнюю провинцию для вставки после неё
        for i in range(len(new_lines)-1, -1, -1):
            if re.match(r'^\s*\d+\s*=\s*\{', new_lines[i]):
                brace_count = 1
                j = i + 1
                while j < len(new_lines) and brace_count > 0:
                    brace_count += new_lines[j].count('{') - new_lines[j].count('}')
                    j += 1
                insert_idx = j
                break
        
        new_block = [f'{target_id} = {{\n'] + source_block[1:]
        if insert_idx < len(new_lines) and new_lines[insert_idx-1].strip() != '':
            new_lines.insert(insert_idx, '\n')
            insert_idx += 1
        new_lines[insert_idx:insert_idx] = new_block
    else:
        # Добавляем в существующий блок
        brace_count = 1
        end_idx = target_idx + 1
        while end_idx < len(new_lines) and brace_count > 0:
            brace_count += new_lines[end_idx].count('{') - new_lines[end_idx].count('}')
            end_idx += 1
        
        source_content = source_block[1:-1]
        if end_idx > 0 and new_lines[end_idx - 1].strip() != '':
            new_lines.insert(end_idx - 1, '\n')
            end_idx += 1
        new_lines[end_idx-1:end_idx-1] = source_content

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
            
            for source_id in PROVINCE_MAPPING.keys():
                if re.match(rf'^\s*{source_id}\s*=\s*\{{', line):
                    province_id = source_id
                    break
            
            if province_id:
                block, next_idx = get_block(lines, i)
                target_id = PROVINCE_MAPPING[province_id]
                add_population(new_lines, lines[next_idx:], target_id, block)
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
        print(f"Ошибка в {os.path.basename(file_path)}: {e}")
        return False

def main():
    if not os.path.exists(pops_dir):
        print(f"ОШИБКА: Папка не найдена: {pops_dir}")
        input("Нажмите Enter для выхода...")
        return
    
    processed = 0
    total = 0
    
    for root, dirs, files in os.walk(pops_dir):
        for file in files:
            if file.endswith('.txt'):
                total += 1
                file_path = os.path.join(root, file)
                if process_file(file_path):
                    processed += 1
    
    print(f"Проверено файлов: {total}")
    print(f"Обработано файлов: {processed}")
    print(f"Население перенесено из {len(PROVINCE_MAPPING)} провинций")
    input("\nНажмите Enter для выхода...")

if __name__ == '__main__':
    main()
