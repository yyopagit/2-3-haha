# -*- coding: utf-8 -*-
"""
Автоматический перенос населения из указанных провинций в соседние
"""

import os
import re
from collections import defaultdict

PROVINCE_MAPPING = {
    1740: 1739,  # Waddan -> Kufra
    1738: 1739,  # Jaghbub -> Kufra  
    1739: 1741,  # Kufra -> Murzuk
    1758: 1757,  # Farafra -> Sharm al-Shaykh
    1719: 1720,  # Ilizi -> Timimoun
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
    """Извлекает блок провинции, включая открывающую и закрывающую скобки."""
    block = [lines[start_idx]]
    brace_count = 1
    i = start_idx + 1
    while i < len(lines) and brace_count > 0:
        block.append(lines[i])
        brace_count += lines[i].count('{') - lines[i].count('}')
        i += 1
    return block, i

def find_province_block_indices(lines, prov_id):
    """Находит начальный и конечный индексы блока провинции."""
    start_idx = -1
    for i, line in enumerate(lines):
        if re.match(rf'^\s*{prov_id}\s*=\s*\{{', line) or line.strip().startswith(f'{prov_id} = {{'):
            start_idx = i
            break
    
    if start_idx == -1:
        return -1, -1

    brace_count = 1
    end_idx = start_idx + 1
    while end_idx < len(lines) and brace_count > 0:
        brace_count += lines[end_idx].count('{') - lines[end_idx].count('}')
        end_idx += 1
    
    return start_idx, end_idx

def add_population_to_target(lines, target_id, pop_block_content):
    """Добавляет содержимое блока населения в целевую провинцию."""
    start_idx, end_idx = find_province_block_indices(lines, target_id)

    if start_idx == -1:
        # Если целевой провинции нет, создаем новый блок в конце файла
        # Ищем последнее определение провинции, чтобы вставить после него
        insert_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if re.match(r'^\s*\d+\s*=\s*\{', lines[i]):
                _, last_prov_end_idx = find_province_block_indices(lines, int(re.match(r'^\s*(\d+)', lines[i]).group(1)))
                insert_idx = last_prov_end_idx
                break
        
        new_block_lines = [f'\n{target_id} = {{\n'] + pop_block_content + ['}\n']
        lines[insert_idx:insert_idx] = new_block_lines
        print(f"  Добавлен новый блок для провинции {target_id}")
    else:
        # Если целевая провинция существует, вставляем содержимое перед ее закрывающей скобкой
        # pop_block_content уже не содержит внешних скобок
        lines[end_idx - 1:end_idx - 1] = pop_block_content
        print(f"  Население добавлено в существующую провинцию {target_id}")

def process_file(file_path):
    """Обрабатывает один файл pops, перенося население."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_lines = list(lines) # Копия для сравнения
        modified = False
        
        # Собираем все блоки населения для переноса
        pops_to_transfer = defaultdict(list)
        provinces_to_remove_blocks = []

        i = 0
        while i < len(lines):
            line = lines[i]
            matched_source_id = None
            for source_id in PROVINCE_MAPPING.keys():
                # Проверяем как с пробелами, так и с табуляциями
                stripped = line.strip()
                if (re.match(rf'^\s*{source_id}\s*=\s*\{{', line) or 
                    stripped.startswith(f'{source_id} = {{') or
                    stripped.startswith(f'{source_id}=')):
                    matched_source_id = source_id
                    break
            
            if matched_source_id:
                block_start_idx = i
                block_content, next_idx = get_block(lines, block_start_idx)
                
                # Извлекаем только внутреннее содержимое блока (без внешних скобок)
                inner_block_content = block_content[1:-1]
                target_id = PROVINCE_MAPPING[matched_source_id]
                pops_to_transfer[target_id].extend(inner_block_content)
                provinces_to_remove_blocks.append((matched_source_id, block_start_idx, next_idx))
                print(f"  Найден блок провинции {matched_source_id} (строки {block_start_idx+1}-{next_idx}), будет перенесен в {target_id}")
                i = next_idx
                modified = True
            else:
                i += 1
        
        if not modified:
            return False
        
        # Удаляем блоки из исходных провинций (в обратном порядке, чтобы индексы не сбивались)
        for prov_id, start_idx, end_idx in sorted(provinces_to_remove_blocks, key=lambda x: x[1], reverse=True):
            del lines[start_idx:end_idx]
            print(f"  Удален блок провинции {prov_id}")
            modified = True

        # Добавляем население в целевые провинции
        for target_id, pop_content in pops_to_transfer.items():
            add_population_to_target(lines, target_id, pop_content)
            modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        return False
    except Exception as e:
        print(f"Ошибка при обработке {os.path.basename(file_path)}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if not os.path.exists(pops_dir):
        print(f"ОШИБКА: Папка не найдена: {pops_dir}")
        input("Нажмите Enter для выхода...")
        return
    
    print("=" * 60)
    print("ПЕРЕНОС НАСЕЛЕНИЯ ИЗ УКАЗАННЫХ ПРОВИНЦИЙ В СОСЕДНИЕ")
    print("=" * 60)
    print(f"\nПровинции для переноса: {sorted(PROVINCE_MAPPING.keys())}")
    print(f"Всего провинций: {len(PROVINCE_MAPPING)}")
    print(f"\nНачинаем обработку файлов в: {pops_dir}\n")
    
    processed_files_count = 0
    total_files_count = 0
    
    for root, dirs, files in os.walk(pops_dir):
        for file in files:
            if file.endswith('.txt'):
                total_files_count += 1
                file_path = os.path.join(root, file)
                print(f"Обработка файла: {os.path.relpath(file_path, pops_dir)}")
                if process_file(file_path):
                    processed_files_count += 1
                    print(f"  ✓ Файл обработан успешно\n")
                else:
                    print(f"  - Файл не требует изменений\n")
    
    print(f"\n" + "=" * 60)
    print(f"РЕЗУЛЬТАТЫ:")
    print(f"  Проверено файлов: {total_files_count}")
    print(f"  Обработано файлов: {processed_files_count}")
    print(f"  Население перенесено из {len(PROVINCE_MAPPING)} провинций")
    print("=" * 60)
    # input("\nНажмите Enter для выхода...")

if __name__ == '__main__':
    main()
