# -*- coding: utf-8 -*-
"""
Перенос населения из указанных провинций в соседние (упрощенная версия)
"""

import os
import re

# Провинции для очистки и их соседние провинции (куда переносить население)
PROVINCE_MAPPING = {
    1740: [1739, 1741],  # Waddan -> Kufra, Murzuk
    1738: [1739, 1737],  # Jaghbub -> Kufra, Tobruk
    1739: [1740, 1738],  # Kufra -> Waddan, Jaghbub
    1758: [1757, 1759],  # Farafra -> Sharm al-Shaykh, Bawiti
    1719: [1718, 1720],  # Ilizi -> In Salah, Timimoun
    1724: [1725, 1723],  # Tamanrasset -> Tunis, Panama Canal
    1718: [1719, 1717],  # In Salah -> Ilizi, Chenachene
    1594: [1595, 1593],  # Kashgar -> Ili, Tawang
    1598: [1599, 1597],  # Khotan -> Kumul, Aksu
    2094: [2095, 2093],  # Kimberley -> Dikathong, Calvinia
    2077: [2078, 2076],  # Tsabong -> Windhoek, Nokaneng
    2074: [2075, 2073],  # Gaborone -> Serowe, Masvingo
    1161: [1162, 1160],  # Sharawrah -> Bahrain, Hail
    2586: [2587, 2585],  # AlAhsa -> Kola, Matan as Sarah
    934: [935, 933],     # Najaf -> Kuwait, Nasiriyya
    931: [932, 930],     # Rutbah -> Basra, Kut
    929: [930, 928],     # Karbala -> Kut, Mendeli
}

pops_dir = os.path.join(os.path.dirname(__file__), 'history', 'pops')

def extract_block(lines, start_idx):
    """Извлечь блок провинции"""
    if start_idx >= len(lines):
        return None, start_idx
    
    block = [lines[start_idx]]
    brace_count = 1
    i = start_idx + 1
    
    while i < len(lines) and brace_count > 0:
        line = lines[i]
        block.append(line)
        brace_count += line.count('{') - line.count('}')
        i += 1
    
    return block, i

def find_block_start(lines, province_id):
    """Найти начало блока провинции"""
    for i, line in enumerate(lines):
        if re.match(rf'^\s*{province_id}\s*=\s*\{{', line):
            return i
    return -1

def add_to_province(lines, target_id, source_block):
    """Добавить население из source_block в провинцию target_id"""
    # Ищем блок целевой провинции
    target_idx = find_block_start(lines, target_id)
    
    if target_idx == -1:
        # Провинция не существует - создаем новый блок в конце файла
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
        
        # Создаем новый блок с ID целевой провинции
        new_block = [f'{target_id} = {{\n']
        # Копируем содержимое из исходного блока (без первой строки с ID)
        new_block.extend(source_block[1:])
        # Вставляем перед insert_idx
        if insert_idx < len(lines) and lines[insert_idx].strip() != '':
            lines.insert(insert_idx, '\n')
            insert_idx += 1
        lines[insert_idx:insert_idx] = new_block
        return True
    
    # Провинция существует - добавляем население
    # Находим конец блока целевой провинции
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
    
    return True

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
            line_stripped = line.strip()
            
            # Проверяем, является ли это началом блока провинции для переноса
            province_to_transfer = None
            for source_id in PROVINCE_MAPPING.keys():
                if re.match(rf'^\s*{source_id}\s*=\s*\{{', line):
                    province_to_transfer = source_id
                    break
            
            if province_to_transfer:
                # Извлекаем блок
                block, next_idx = extract_block(lines, i)
                
                # Переносим в первую соседнюю провинцию из списка
                target_provinces = PROVINCE_MAPPING[province_to_transfer]
                target_id = target_provinces[0]  # Используем первую соседнюю провинцию
                
                # Проверяем, есть ли уже эта провинция в new_lines или дальше в lines
                found_in_new = find_block_start(new_lines, target_id) != -1
                found_in_remaining = find_block_start(lines[next_idx:], target_id) != -1
                
                if found_in_new:
                    # Провинция уже есть в new_lines - добавляем туда
                    add_to_province(new_lines, target_id, block)
                elif found_in_remaining:
                    # Провинция будет дальше - добавим позже, пока просто копируем блок
                    # Но лучше добавить сейчас в new_lines
                    add_to_province(new_lines, target_id, block)
                else:
                    # Провинции нет - создаем новую
                    add_to_province(new_lines, target_id, block)
                
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
        print(f"Ошибка в {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if not os.path.exists(pops_dir):
        print(f"Папка не найдена: {pops_dir}")
        return
    
    print(f"Ищем файлы в: {pops_dir}")
    print(f"Провинции для переноса: {list(PROVINCE_MAPPING.keys())}")
    
    processed = 0
    total_files = 0
    for root, dirs, files in os.walk(pops_dir):
        for file in files:
            if file.endswith('.txt'):
                total_files += 1
                file_path = os.path.join(root, file)
                if process_file(file_path):
                    processed += 1
                    rel_path = os.path.relpath(file_path, pops_dir)
                    print(f"Обработан: {rel_path}")
    
    print(f"\nВсего файлов проверено: {total_files}")
    print(f"Обработано: {processed} файлов")
    print(f"Население перенесено из {len(PROVINCE_MAPPING)} провинций")

if __name__ == '__main__':
    main()
