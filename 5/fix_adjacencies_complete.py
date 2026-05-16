# -*- coding: utf-8 -*-
"""
Добавляет все недостающие записи для заблокированных провинций
"""

REQUIRED_NEIGHBORS = {
    929: [926, 927, 931, 934],  # Karbala
    931: [901, 907, 910, 927, 929, 934, 1156, 1158],  # Rutbah
    934: [926, 929, 930, 931, 933, 935, 1158],  # Najaf
    1161: [1155, 1157, 1159, 1164, 1173, 1175, 1178, 2586],  # Sharawrah
    1594: [1190, 1208, 1210, 1225, 1226, 1591, 1592, 1597, 1598],  # Kashgar
    1598: [1591, 1594, 1597, 2607],  # Khotan
    1718: [1717, 1719, 1720, 1722, 1724],  # In Salah
    1719: [1711, 1712, 1718, 1720, 1724, 1729, 1743, 1744],  # Ilizi
    1724: [1718, 1719, 1721, 1722, 1743],  # Tamanrasset
    1738: [1735, 1736, 1737, 1740, 1754, 1758],  # Jaghbub
    1739: [1738, 1740, 1741, 1758, 2585],  # Kufra
    1740: [1732, 1733, 1734, 1735, 1738, 1739, 1741, 1742],  # Waddan
    1758: [1754, 1759, 1760, 1761],  # Hariga
    2074: [2077, 2095, 2107, 2574],  # Gaborone
    2077: [2074, 2075, 2076, 2085, 2095, 2574],  # Tsabong
    2094: [2093, 2095, 2101, 2103, 2107, 2558],  # Kimberley
    2586: [1161, 1164, 1167, 1169, 1170, 1172, 1174],  # Al-Ahsa
}

# Определяем тип местности (desert или mountain)
TERRAIN_TYPE = {
    929: 'desert', 931: 'desert', 934: 'desert', 1161: 'desert',
    1594: 'mountain', 1598: 'mountain',
    1718: 'desert', 1719: 'desert', 1724: 'desert',
    1738: 'desert', 1739: 'desert', 1740: 'desert', 1758: 'desert',
    2074: 'desert', 2077: 'desert', 2094: 'desert', 2586: 'desert',
}

adjacencies_file = 'map/adjacencies.csv'

print("=" * 60)
print("ПРОВЕРКА И ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ ЗАПИСЕЙ")
print("=" * 60)

# Читаем файл
with open(adjacencies_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Собираем существующие записи
existing_entries = set()
for line in lines:
    line_strip = line.strip()
    if not line_strip or line_strip.startswith('#'):
        continue
    parts = line_strip.split(';')
    if len(parts) >= 3:
        try:
            from_prov = int(parts[0])
            to_prov = int(parts[1])
            adj_type = parts[2].strip()
            if adj_type == 'impassable':
                existing_entries.add((from_prov, to_prov))
        except ValueError:
            continue

# Находим недостающие записи
missing_entries = []
for prov_id, neighbors in REQUIRED_NEIGHBORS.items():
    terrain = TERRAIN_TYPE.get(prov_id, 'desert')
    for neighbor in neighbors:
        if (prov_id, neighbor) not in existing_entries:
            missing_entries.append((prov_id, neighbor, terrain))
            print(f"Отсутствует: {prov_id} → {neighbor} ({terrain})")

if not missing_entries:
    print("\n✓ Все записи присутствуют!")
else:
    print(f"\nНайдено {len(missing_entries)} недостающих записей")
    
    # Находим место для вставки (после секции "# Непроходимые провинции")
    insert_pos = -1
    for i, line in enumerate(lines):
        if '# Непроходимые провинции' in line:
            # Ищем конец блока impassable записей для наших провинций
            insert_pos = i + 1
            # Продолжаем искать до следующей секции или конца блока
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith('#') and 'Непроходимые' not in lines[j]:
                    insert_pos = j
                    break
            break
    
    if insert_pos == -1:
        # Если не нашли, ищем секцию Impassables
        for i, line in enumerate(lines):
            if '# Impassables' in line:
                insert_pos = i + 2  # После заголовка и пустой строки
                break
    
    if insert_pos == -1:
        print("ОШИБКА: Не найдена секция для вставки!")
    else:
        # Сортируем недостающие записи по номеру провинции
        missing_entries.sort()
        
        # Формируем строки для вставки
        new_lines = []
        for from_prov, to_prov, terrain in missing_entries:
            terrain_name = 'scary ' + terrain
            new_line = f"{from_prov};{to_prov};impassable;0;0;{terrain_name}\n"
            new_lines.append(new_line)
        
        # Вставляем в нужное место
        lines[insert_pos:insert_pos] = new_lines
        
        # Записываем обратно
        with open(adjacencies_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"\n✓ Добавлено {len(missing_entries)} записей в файл")
