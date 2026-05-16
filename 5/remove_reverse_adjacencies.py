# -*- coding: utf-8 -*-
"""
Удаляет обратные записи impassable границ
Оставляет только записи ОТ заблокированных провинций К другим
"""

PROVINCES_TO_FIX = [929, 931, 934, 1161, 1594, 1598, 1718, 1719, 1724, 1738, 1739, 1740, 1758, 2074, 2077, 2094, 2586]

adjacencies_file = 'map/adjacencies.csv'

print("=" * 60)
print("УДАЛЕНИЕ ОБРАТНЫХ ЗАПИСЕЙ IMPASSABLE")
print("=" * 60)

# Читаем файл
with open(adjacencies_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Собираем все записи от заблокированных провинций
forward_entries = set()  # Записи ОТ заблокированных провинций (ключ: "from;to")
all_entries = []  # Все строки для сохранения
removed_count = 0

# Первый проход: собираем все записи ОТ заблокированных провинций
for line in lines:
    line_strip = line.strip()
    
    if not line_strip or line_strip.startswith('#'):
        continue
    
    parts = line_strip.split(';')
    if len(parts) < 3:
        continue
    
    try:
        from_prov = int(parts[0])
        to_prov = int(parts[1])
        adj_type = parts[2].strip()
        
        if adj_type == 'impassable' and from_prov in PROVINCES_TO_FIX:
            key = f"{from_prov};{to_prov}"
            forward_entries.add(key)
    except ValueError:
        continue

# Второй проход: удаляем обратные записи
for line in lines:
    line_strip = line.strip()
    
    # Сохраняем комментарии и пустые строки
    if not line_strip or line_strip.startswith('#'):
        all_entries.append(line)
        continue
    
    parts = line_strip.split(';')
    if len(parts) < 3:
        all_entries.append(line)
        continue
    
    try:
        from_prov = int(parts[0])
        to_prov = int(parts[1])
        adj_type = parts[2].strip()
        
        if adj_type == 'impassable':
            # Если это запись ОТ заблокированной провинции - оставляем
            if from_prov in PROVINCES_TO_FIX:
                all_entries.append(line)
            # Если это обратная запись К заблокированной провинции
            elif to_prov in PROVINCES_TO_FIX:
                reverse_key = f"{to_prov};{from_prov}"
                # Если есть прямая запись - удаляем обратную
                if reverse_key in forward_entries:
                    print(f"Удалена обратная запись: {line_strip[:70]}")
                    removed_count += 1
                    continue  # Не добавляем эту строку
                else:
                    # Если прямой записи нет - оставляем (на случай если обе провинции заблокированные)
                    all_entries.append(line)
            else:
                # Другие записи - оставляем
                all_entries.append(line)
        else:
            # Не impassable записи - оставляем
            all_entries.append(line)
    except ValueError:
        # Не удалось распарсить - оставляем как есть
        all_entries.append(line)

# Записываем обратно
with open(adjacencies_file, 'w', encoding='utf-8') as f:
    f.writelines(all_entries)

print(f"\n✓ Удалено обратных записей: {removed_count}")
print(f"✓ Файл обновлен: {adjacencies_file}")
