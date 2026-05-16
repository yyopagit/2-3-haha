# -*- coding: utf-8 -*-
"""Удаляет ВСЕ лишние } перед country_event и province_event в Other.txt"""
import re
path = r'c:\Games\Vic2LV2\Victoria 2\mod\6\events\Other.txt'
with open(path, 'r', encoding='utf-8', newline='') as f:
    content = f.read()
# Нормализуем окончания строк
content = content.replace('\r\n', '\n')
n = 0
# Паттерн: лишняя } - строка только с } между закрытием события и следующим event
# Ищем: }\n}\n}\ncountry_event или }\n}\n}\nprovince_event (три } подряд)
for pattern in [
    r'\}\n\}\n\}\n(country_event\s*=\s*\{)',
    r'\}\n\}\n\}\n(province_event\s*=\s*\{)',
]:
    content, k = re.subn(pattern, r'}\n}\n\n\1', content)
    n += k
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
with open(r'c:\Games\Vic2LV2\Victoria 2\mod\6\events\fix_result.txt', 'w') as out:
    out.write(str(n))
