import os
import sys

file_path = os.path.join(os.path.dirname(__file__), 'neighbors_result.txt')
print(f"Попытка создать файл: {file_path}", file=sys.stderr, flush=True)

try:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("Тест\n")
    print("Файл создан!", file=sys.stderr, flush=True)
    print(f"Путь существует: {os.path.exists(file_path)}", file=sys.stderr, flush=True)
except Exception as e:
    print(f"ОШИБКА: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc(file=sys.stderr)
