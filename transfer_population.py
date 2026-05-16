# -*- coding: utf-8 -*-
"""
Перенос населения из указанных провинций в соседние
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

def extract_province_block(lines, start_idx):
    """Извлечь блок провинции, начиная с указанной строки"""
    if start_idx >= len(lines):
        return None, start_idx
    
    block_lines = [lines[start_idx]]
    brace_count = 1
    i = start_idx + 1
    
    while i < len(lines) and brace_count > 0:
        line = lines[i]
        block_lines.append(line)
        brace_count += line.count('{') - line.count('}')
        i += 1
    
    return block_lines, i

def find_province_block(lines, province_id):
    """Найти блок провинции в списке строк"""
    for i, line in enumerate(lines):
        if re.match(rf'^\s*{province_id}\s*=\s*\{{', line):
            return i
    return -1

def add_population_to_province(lines, target_province_id, population_block):
    """Добавить население в блок провинции"""
    # Ищем блок целевой провинции
    target_idx = find_province_block(lines, target_province_id)
    
    if target_idx == -1:
        # Провинция не найдена - создаем новый блок
        # Находим место для вставки (после последней провинции или в конце)
        insert_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if re.match(r'^\s*\d+\s*=\s*\{', lines[i]):
                insert_idx = i + 1
                # Находим конец блока
                brace_count = 1
                j = i + 1
                while j < len(lines) and brace_count > 0:
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    j += 1
                insert_idx = j
                break
        
        # Создаем новый блок провинции
        new_block = [f'{target_province_id} = {{\n'] + population_block[1:]
        lines.insert(insert_idx, '\n')
        lines[insert_idx+1:insert_idx+1] = new_block
        return True
    
    # Провинция найдена - добавляем население в существующий блок
    # Находим конец блока
    brace_count = 1
    end_idx = target_idx + 1
    while end_idx < len(lines) and brace_count > 0:
        brace_count += lines[end_idx].count('{') - lines[end_idx].count('}')
        end_idx += 1
    
    # Вставляем население перед закрывающей скобкой
    # Извлекаем только содержимое блока (без первой строки с ID)
    pop_content = population_block[1:-1]  # Убираем первую строку и последнюю }
    
    # Добавляем пустую строку и содержимое
    lines.insert(end_idx - 1, '\n')
    lines[end_idx:end_idx] = pop_content
    
    return True

def merge_population_blocks(block1, block2):
    """Объединить два блока населения"""
    # Извлекаем содержимое обоих блоков (без ID и закрывающих скобок)
    content1 = block1[1:-1] if len(block1) > 2 else []
    content2 = block2[1:-1] if len(block2) > 2 else []
    
    # Объединяем и суммируем размеры одинаковых групп населения
    merged = {}
    for line in content1 + content2:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            # Парсим строку для суммирования
            if 'size =' in line:
                # Это строка с размером - нужно суммировать
                match = re.search(r'size\s*=\s*(\d+)', line)
                if match:
                    key = line.split('=')[0].strip()
                    size = int(match.group(1))
                    if key in merged:
                        # Суммируем размеры
                        old_size = int(re.search(r'size\s*=\s*(\d+)', merged[key]).group(1))
                        merged[key] = re.sub(r'size\s*=\s*\d+', f'size = {old_size + size}', merged[key])
                    else:
                        merged[key] = line
            else:
                # Обычная строка - добавляем как есть
                key = stripped.split()[0] if stripped.split() else ''
                if key and key not in merged:
                    merged[key] = line
    
    return list(merged.values())

def process_file(file_path):
    """Обработать один файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Проверяем, начинается ли строка с ID провинции для переноса
            province_found = False
            for source_province, target_provinces in PROVINCE_MAPPING.items():
                if re.match(rf'^\s*{source_province}\s*=\s*\{{', line):
                    # Найден блок провинции для переноса
                    block, next_idx = extract_province_block(lines, i)
                    
                    # Переносим население в соседние провинции
                    for target_province in target_provinces:
                        add_population_to_province(new_lines, target_province, block)
                    
                    # Пропускаем исходный блок (не добавляем его)
                    i = next_idx
                    modified = True
                    province_found = True
                    break
            
            if not province_found:
                new_lines.append(line)
                i += 1
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        return False
    except Exception as e:
        print(f"Ошибка: {file_path}: {e}")
        import traceback
        traceback.print_exc()
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
    print(f"Население перенесено из {len(PROVINCE_MAPPING)} провинций в соседние")

if __name__ == '__main__':
    main()
