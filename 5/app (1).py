from __future__ import annotations

from pathlib import Path
from typing import List, Set, Tuple
import time
from functools import wraps
import logging
import urllib.parse
import zipfile
import io
import sys
import os
import socket

from flask import Flask, abort, request, send_from_directory, Response

# Пытаемся импортировать psutil для управления процессами
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# Определяем BASE_DIR до использования в функциях
BASE_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_NAME = SCRIPT_PATH.name


def get_safe_path(relative_path: str) -> Path:
    """
    Преобразует относительный путь в безопасный абсолютный путь внутри BASE_DIR.
    Предотвращает path traversal атаки.
    """
    # Нормализуем путь и убираем начальные слеши
    normalized = Path(relative_path).parts if relative_path else ()
    
    # Строим путь относительно BASE_DIR
    safe_path = BASE_DIR
    for part in normalized:
        if part in ('.', '..') or not part:
            continue
        safe_path = safe_path / part
    
    # Проверяем, что путь всё ещё внутри BASE_DIR
    try:
        safe_path.resolve().relative_to(BASE_DIR.resolve())
    except ValueError:
        abort(404)  # Попытка выйти за пределы BASE_DIR
    
    return safe_path


def discover_items(directory: Path) -> Tuple[List[str], List[str]]:
    """
    Возвращает кортеж (список папок, список файлов) в указанной директории.
    Пропускает временные/скрытые файлы и папки.
    """
    folders: List[str] = []
    files: List[str] = []
    
    try:
        for path in directory.iterdir():
            # Пропускаем скрытые файлы и временные файлы
            if path.name.startswith("~$") or path.name.startswith('.'):
                continue
            
            # Пропускаем служебные файлы
            if path.name in ('server.log', 'app.py', 'app (1).py'):
                continue
            
            if path.is_dir():
                folders.append(path.name)
            elif path.is_file():
                files.append(path.name)
    except PermissionError:
        # Логирование будет доступно после инициализации logger
        pass
    
    return sorted(folders), sorted(files)


def discover_downloadable_files(directory: Path) -> Set[str]:
    """
    Return a set of non-hidden filenames in the given directory that are safe to serve.
    Skips temporary/lock files that start with '~$' and hidden files starting with '.'.
    """
    _, files = discover_items(directory)
    return set(files)


def create_zip_from_folder(folder_path: Path, base_path: Path, compress: bool = True) -> io.BytesIO:
    """
    Создаёт ZIP-архив из указанной папки.
    base_path используется для определения относительных путей в архиве.
    compress=True для максимального сжатия (по умолчанию включено).
    """
    zip_buffer = io.BytesIO()
    
    # Используем ZIP_DEFLATED (со сжатием) для уменьшения размера или ZIP_STORED (без сжатия) для скорости
    compression = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    
    # compresslevel доступен только в Python 3.7+, используем максимальное сжатие (9)
    try:
        # Python 3.7+ поддерживает compresslevel (9 = максимальное сжатие)
        with zipfile.ZipFile(zip_buffer, 'w', compression, compresslevel=9 if compress else 0) as zip_file:
            # Рекурсивно обходим все файлы в папке
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    # Пропускаем скрытые и служебные файлы
                    if file_path.name.startswith("~$") or file_path.name.startswith('.'):
                        continue
                    if file_path.name in ('server.log', 'app.py', 'app (1).py'):
                        continue
                    
                    try:
                        # Вычисляем относительный путь для архива
                        relative_path = file_path.relative_to(base_path)
                        # Добавляем файл в архив (используем оптимизированный метод)
                        zip_file.write(file_path, relative_path, compress_type=compression)
                    except (PermissionError, OSError) as e:
                        logger.warning(f"Could not add {file_path} to zip: {e}")
                        continue
    except TypeError:
        # Для старых версий Python без compresslevel
        with zipfile.ZipFile(zip_buffer, 'w', compression) as zip_file:
            # Рекурсивно обходим все файлы в папке
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    # Пропускаем скрытые и служебные файлы
                    if file_path.name.startswith("~$") or file_path.name.startswith('.'):
                        continue
                    if file_path.name in ('server.log', 'app.py', 'app (1).py'):
                        continue
                    
                    try:
                        # Вычисляем относительный путь для архива
                        relative_path = file_path.relative_to(base_path)
                        # Добавляем файл в архив
                        zip_file.write(file_path, relative_path, compress_type=compression)
                    except (PermissionError, OSError) as e:
                        logger.warning(f"Could not add {file_path} to zip: {e}")
                        continue
    
    zip_buffer.seek(0)
    return zip_buffer


def create_zip_from_selected_items(items: List[dict], current_path: str = "") -> io.BytesIO:
    """
    Создаёт ZIP-архив из выбранных файлов и папок.
    items - список словарей с ключами 'type' ('file' или 'folder') и 'path' (относительный путь).
    """
    zip_buffer = io.BytesIO()
    compression = zipfile.ZIP_DEFLATED
    
    try:
        with zipfile.ZipFile(zip_buffer, 'w', compression, compresslevel=9) as zip_file:
            for item in items:
                item_type = item.get('type')
                item_path = item.get('path', '')
                
                if not item_path:
                    continue
                
                # Декодируем путь
                decoded_path = urllib.parse.unquote(item_path)
                
                # Получаем безопасный путь
                target_path = get_safe_path(decoded_path)
                
                if item_type == 'file':
                    # Добавляем файл
                    if target_path.exists() and target_path.is_file():
                        try:
                            # Используем имя файла как путь в архиве
                            zip_file.write(target_path, target_path.name, compress_type=compression)
                        except (PermissionError, OSError) as e:
                            logger.warning(f"Could not add file {target_path} to zip: {e}")
                
                elif item_type == 'folder':
                    # Добавляем всю папку
                    if target_path.exists() and target_path.is_dir():
                        try:
                            # Рекурсивно добавляем все файлы из папки
                            for file_path in target_path.rglob('*'):
                                if file_path.is_file():
                                    # Пропускаем скрытые и служебные файлы
                                    if file_path.name.startswith("~$") or file_path.name.startswith('.'):
                                        continue
                                    if file_path.name in ('server.log', 'app.py', 'app (1).py'):
                                        continue
                                    
                                    try:
                                        # Относительный путь от папки
                                        relative_path = file_path.relative_to(target_path)
                                        # Путь в архиве: имя_папки/относительный_путь
                                        archive_path = f"{target_path.name}/{relative_path}"
                                        zip_file.write(file_path, archive_path, compress_type=compression)
                                    except (PermissionError, OSError) as e:
                                        logger.warning(f"Could not add {file_path} to zip: {e}")
                        except (PermissionError, OSError) as e:
                            logger.warning(f"Could not process folder {target_path}: {e}")
    except TypeError:
        # Для старых версий Python без compresslevel
        with zipfile.ZipFile(zip_buffer, 'w', compression) as zip_file:
            for item in items:
                item_type = item.get('type')
                item_path = item.get('path', '')
                
                if not item_path:
                    continue
                
                decoded_path = urllib.parse.unquote(item_path)
                target_path = get_safe_path(decoded_path)
                
                if item_type == 'file':
                    if target_path.exists() and target_path.is_file():
                        try:
                            zip_file.write(target_path, target_path.name, compress_type=compression)
                        except (PermissionError, OSError) as e:
                            logger.warning(f"Could not add file {target_path} to zip: {e}")
                
                elif item_type == 'folder':
                    if target_path.exists() and target_path.is_dir():
                        try:
                            for file_path in target_path.rglob('*'):
                                if file_path.is_file():
                                    if file_path.name.startswith("~$") or file_path.name.startswith('.'):
                                        continue
                                    if file_path.name in ('server.log', 'app.py', 'app (1).py'):
                                        continue
                                    
                                    try:
                                        relative_path = file_path.relative_to(target_path)
                                        archive_path = f"{target_path.name}/{relative_path}"
                                        zip_file.write(file_path, archive_path, compress_type=compression)
                                    except (PermissionError, OSError) as e:
                                        logger.warning(f"Could not add {file_path} to zip: {e}")
                        except (PermissionError, OSError) as e:
                            logger.warning(f"Could not process folder {target_path}: {e}")
    
    zip_buffer.seek(0)
    return zip_buffer


# Note: ALLOWED_FILES will be recomputed per request to avoid stale state
ALLOWED_FILES = discover_downloadable_files(BASE_DIR)

app = Flask(__name__)

# Оптимизация производительности Flask
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Отключаем кеширование для динамических файлов
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB максимум для загрузки
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Отключаем красивое форматирование JSON

# Настройка логирования
# Убеждаемся, что вывод идёт в консоль (sys.stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler('server.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Настраиваем корневой логгер
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = []  # Очищаем существующие обработчики
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# Настраиваем логгер приложения
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Настраиваем логгер Flask для вывода в консоль
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)
flask_logger.addHandler(console_handler)
flask_logger.addHandler(file_handler)




def requires_auth(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr
        logger.info(f"Access from {client_ip} to {request.path}")
        return view_func(*args, **kwargs)
    return wrapper




def generate_breadcrumbs(current_path: str) -> str:
    """Генерирует HTML для навигационных хлебных крошек."""
    if not current_path:
        return '<a href="/">🏠 Главная</a>'
    
    parts = current_path.split('/')
    breadcrumbs = ['<a href="/">🏠 Главная</a>']
    path_so_far = ''
    
    for i, part in enumerate(parts):
        if part:
            path_so_far += '/' + part if path_so_far else part
            is_last = (i == len(parts) - 1)
            if is_last:
                breadcrumbs.append(f'<span>{part}</span>')
            else:
                encoded_path = urllib.parse.quote(path_so_far)
                breadcrumbs.append(f'<a href="/browse/{encoded_path}">{part}</a>')
    
    return ' / '.join(breadcrumbs)


def generate_directory_listing(directory: Path, current_path: str = "") -> str:
    """Генерирует HTML для списка папок и файлов."""
    folders, files = discover_items(directory)
    
    breadcrumbs = generate_breadcrumbs(current_path)
    
    # Формируем кнопку "Скачать все (ZIP)"
    if current_path:
        download_all_encoded = urllib.parse.quote(current_path)
        download_url = f"/download_folder/{download_all_encoded}"
    else:
        # Для корневой папки используем специальный маршрут
        download_url = "/download_all"
    
    download_all_button = f'<a href="{download_url}" class="download-all-button" title="Скачать всю текущую папку как ZIP-архив">📦 Скачать все (ZIP)</a>'
    download_selected_button = '<button id="download-selected-btn" class="download-selected-button" onclick="downloadSelected()" disabled title="Скачать выбранные файлы и папки">📥 Скачать выбранные</button>'
    
    items_html = []
    
    # Добавляем папки с чекбоксами
    for folder in folders:
        encoded_path = urllib.parse.quote(f"{current_path}/{folder}" if current_path else folder)
        download_encoded = urllib.parse.quote(f"{current_path}/{folder}" if current_path else folder)
        folder_id = f"folder_{len(items_html)}"
        items_html.append(
            f'<li class="item-row">'
            f'<input type="checkbox" class="item-checkbox" data-type="folder" data-path="{download_encoded}" id="{folder_id}"> '
            f'<label for="{folder_id}">📁 <a href="/browse/{encoded_path}">{folder}/</a></label> '
            f'<a href="/download_folder/{download_encoded}" class="download-link" title="Скачать папку как ZIP-архив">📦 Скачать ZIP</a>'
            f'</li>'
        )
    
    # Добавляем файлы с чекбоксами
    for file in files:
        encoded_path = urllib.parse.quote(f"{current_path}/{file}" if current_path else file)
        file_id = f"file_{len(items_html)}"
        items_html.append(
            f'<li class="item-row">'
            f'<input type="checkbox" class="item-checkbox" data-type="file" data-path="{encoded_path}" id="{file_id}"> '
            f'<label for="{file_id}">📄 <a href="/download/{encoded_path}">{file}</a></label>'
            f'</li>'
        )
    
    if not items_html:
        items_html.append('<li><em>Папка пуста</em></li>')
    
    html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <title>Файловый менеджер</title>
        <style>
          body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f5f5;
          }}
          .breadcrumbs {{
            background-color: #fff;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          }}
          .breadcrumbs a {{
            color: #0066cc;
            text-decoration: none;
          }}
          .breadcrumbs a:hover {{
            text-decoration: underline;
          }}
          .breadcrumbs span {{
            color: #333;
            font-weight: bold;
          }}
          .file-list {{
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          }}
          .file-list h3 {{
            margin-top: 0;
            color: #333;
          }}
          .file-list ul {{
            list-style: none;
            padding: 0;
          }}
          .file-list li {{
            padding: 8px;
            margin: 5px 0;
            border-radius: 3px;
          }}
          .file-list li:hover {{
            background-color: #f0f0f0;
          }}
          .file-list a {{
            color: #0066cc;
            text-decoration: none;
            font-size: 16px;
          }}
          .file-list a:hover {{
            text-decoration: underline;
          }}
          .download-link {{
            margin-left: 10px;
            color: #28a745;
            font-size: 14px;
            padding: 2px 8px;
            background-color: #f0f8f0;
            border-radius: 3px;
            text-decoration: none;
          }}
          .download-link:hover {{
            background-color: #e0f0e0;
            text-decoration: none;
          }}
          .download-all-button {{
            display: inline-block;
            margin-bottom: 15px;
            padding: 12px 24px;
            background-color: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: background-color 0.3s;
          }}
          .download-all-button:hover {{
            background-color: #218838;
            text-decoration: none;
            color: white;
          }}
          .download-selected-button {{
            display: inline-block;
            margin-left: 10px;
            padding: 12px 24px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: background-color 0.3s;
          }}
          .download-selected-button:hover:not(:disabled) {{
            background-color: #0056b3;
          }}
          .download-selected-button:disabled {{
            background-color: #6c757d;
            cursor: not-allowed;
            opacity: 0.6;
          }}
          .item-row {{
            display: flex;
            align-items: center;
            gap: 8px;
          }}
          .item-checkbox {{
            width: 18px;
            height: 18px;
            cursor: pointer;
            flex-shrink: 0;
          }}
          .item-row label {{
            flex: 1;
            cursor: pointer;
            margin: 0;
          }}
          .item-row label a {{
            pointer-events: auto;
          }}
        </style>
        <script>
          function updateDownloadButton() {{
            const checkboxes = document.querySelectorAll('.item-checkbox:checked');
            const btn = document.getElementById('download-selected-btn');
            if (checkboxes.length > 0) {{
              btn.disabled = false;
              btn.textContent = `📥 Скачать выбранные (${{checkboxes.length}})`;
            }} else {{
              btn.disabled = true;
              btn.textContent = '📥 Скачать выбранные';
            }}
          }}
          
          function downloadSelected() {{
            const checkboxes = document.querySelectorAll('.item-checkbox:checked');
            if (checkboxes.length === 0) {{
              alert('Выберите файлы или папки для скачивания');
              return;
            }}
            
            const items = Array.from(checkboxes).map(cb => {{
              return {{
                type: cb.dataset.type,
                path: cb.dataset.path
              }};
            }});
            
            // Создаём форму для отправки данных
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/download_selected';
            
            items.forEach((item, index) => {{
              const typeInput = document.createElement('input');
              typeInput.type = 'hidden';
              typeInput.name = `items[${{index}}][type]`;
              typeInput.value = item.type;
              form.appendChild(typeInput);
              
              const pathInput = document.createElement('input');
              pathInput.type = 'hidden';
              pathInput.name = `items[${{index}}][path]`;
              pathInput.value = item.path;
              form.appendChild(pathInput);
            }});
            
            document.body.appendChild(form);
            form.submit();
          }}
          
          // Обновляем кнопку при изменении чекбоксов
          document.addEventListener('DOMContentLoaded', function() {{
            const checkboxes = document.querySelectorAll('.item-checkbox');
            checkboxes.forEach(cb => {{
              cb.addEventListener('change', updateDownloadButton);
            }});
            updateDownloadButton();
          }});
        </script>
      </head>
      <body>
        <div class="breadcrumbs">
          {breadcrumbs}
        </div>
        <div class="file-list">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0;">📂 Содержимое папки</h3>
            <div>
              {download_all_button}
              {download_selected_button}
            </div>
          </div>
          <ul>
            {''.join(items_html)}
          </ul>
        </div>
      </body>
    </html>
    """
    return html


@app.route("/", methods=["GET"])
@requires_auth
def index() -> str:
    t0 = time.perf_counter()
    html = generate_directory_listing(BASE_DIR, "")
    dt = (time.perf_counter() - t0) * 1000
    logger.info(f"Index generated in {dt:.1f} ms for {request.remote_addr}")
    return Response(html, mimetype="text/html; charset=utf-8")


@app.route("/browse/<path:folder_path>", methods=["GET"])
@requires_auth
def browse_folder(folder_path: str) -> str:
    t0 = time.perf_counter()
    target_dir = get_safe_path(folder_path)
    
    if not target_dir.exists() or not target_dir.is_dir():
        logger.warning(f"Attempt to browse non-existent folder '{folder_path}' from {request.remote_addr}")
        abort(404)
    
    html = generate_directory_listing(target_dir, folder_path)
    dt = (time.perf_counter() - t0) * 1000
    logger.info(f"Folder listing generated in {dt:.1f} ms for '{folder_path}' from {request.remote_addr}")
    return Response(html, mimetype="text/html; charset=utf-8")


@app.route("/download/<path:filepath>", methods=["GET"])
@requires_auth
def download_file(filepath: str):
    client_ip = request.remote_addr
    t0 = time.perf_counter()
    
    # Получаем безопасный путь к файлу
    target_file = get_safe_path(filepath)
    
    # Проверяем, что это файл и он существует
    if not target_file.exists() or not target_file.is_file():
        logger.warning(f"Attempt to download non-existent file '{filepath}' from {client_ip}")
        abort(404)
    
    # Получаем директорию и имя файла для send_from_directory
    file_dir = target_file.parent
    file_name = target_file.name
    
    logger.info(f"File download: '{filepath}' by {client_ip} (validated in {(time.perf_counter()-t0)*1000:.1f} ms)")
    return send_from_directory(str(file_dir), file_name, as_attachment=True)


@app.route("/download_all", methods=["GET"])
@requires_auth
def download_all():
    """Скачивает корневую папку (BASE_DIR) как ZIP-архив."""
    client_ip = request.remote_addr
    t0 = time.perf_counter()
    
    try:
        # Создаём ZIP-архив из корневой папки (с максимальным сжатием)
        # Используем parent BASE_DIR как базовый путь
        zip_buffer = create_zip_from_folder(BASE_DIR, BASE_DIR.parent, compress=True)
        
        # Получаем содержимое ZIP-файла
        zip_data = zip_buffer.getvalue()
        zip_size = len(zip_data)
        
        # Имя файла для скачивания
        folder_name = BASE_DIR.name if BASE_DIR.name else "all_files"
        zip_filename = f"{folder_name}.zip"
        
        logger.info(f"Root folder download as {zip_filename} ({zip_size} bytes) by {client_ip} (created in {(time.perf_counter()-t0)*1000:.1f} ms)")
        
        # Возвращаем ZIP-файл с оптимизированными заголовками
        response = Response(
            zip_data,
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{zip_filename}"',
                'Content-Length': str(zip_size),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        # Отключаем буферизацию для больших файлов
        response.direct_passthrough = False
        return response
    except Exception as e:
        logger.error(f"Error creating zip for root folder: {e}")
        abort(500)


@app.route("/download_selected", methods=["POST"])
@requires_auth
def download_selected():
    """Скачивает выбранные файлы и папки в одном ZIP-архиве."""
    client_ip = request.remote_addr
    t0 = time.perf_counter()
    
    # Получаем выбранные элементы из формы
    items = []
    
    # Обрабатываем данные формы (items[0][type], items[0][path], items[1][type], и т.д.)
    i = 0
    while True:
        item_type = request.form.get(f'items[{i}][type]')
        item_path = request.form.get(f'items[{i}][path]')
        
        if not item_type or not item_path:
            break
        
        items.append({
            'type': item_type,
            'path': item_path
        })
        i += 1
    
    if not items:
        logger.warning(f"No items selected for download from {client_ip}")
        abort(400)
    
    try:
        # Создаём ZIP-архив из выбранных элементов
        zip_buffer = create_zip_from_selected_items(items)
        
        # Получаем содержимое ZIP-файла
        zip_data = zip_buffer.getvalue()
        zip_size = len(zip_data)
        
        # Имя файла для скачивания
        zip_filename = f"selected_items_{int(time.time())}.zip"
        
        logger.info(f"Selected items download: {len(items)} items as {zip_filename} ({zip_size} bytes) by {client_ip} (created in {(time.perf_counter()-t0)*1000:.1f} ms)")
        
        # Возвращаем ZIP-файл
        response = Response(
            zip_data,
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{zip_filename}"',
                'Content-Length': str(zip_size),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        response.direct_passthrough = False
        return response
    except Exception as e:
        logger.error(f"Error creating zip for selected items: {e}")
        abort(500)


@app.route("/download_folder/<path:folder_path>", methods=["GET"])
@requires_auth
def download_folder(folder_path: str):
    client_ip = request.remote_addr
    t0 = time.perf_counter()
    
    # Получаем безопасный путь к папке
    target_folder = get_safe_path(folder_path)
    
    # Проверяем, что это папка и она существует
    if not target_folder.exists() or not target_folder.is_dir():
        logger.warning(f"Attempt to download non-existent folder '{folder_path}' from {client_ip}")
        abort(404)
    
    try:
        # Создаём ZIP-архив из папки (с максимальным сжатием)
        # Используем parent папки как базовый путь, чтобы в архиве была только сама папка
        zip_buffer = create_zip_from_folder(target_folder, target_folder.parent, compress=True)
        
        # Получаем содержимое ZIP-файла
        zip_data = zip_buffer.getvalue()
        zip_size = len(zip_data)
        
        # Имя файла для скачивания
        folder_name = target_folder.name
        zip_filename = f"{folder_name}.zip"
        
        logger.info(f"Folder download: '{folder_path}' as {zip_filename} ({zip_size} bytes) by {client_ip} (created in {(time.perf_counter()-t0)*1000:.1f} ms)")
        
        # Возвращаем ZIP-файл с оптимизированными заголовками
        response = Response(
            zip_data,
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{zip_filename}"',
                'Content-Length': str(zip_size),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        # Отключаем буферизацию для больших файлов
        response.direct_passthrough = False
        return response
    except Exception as e:
        logger.error(f"Error creating zip for '{folder_path}': {e}")
        abort(500)


# Simple endpoint without filesystem access to diagnose hanging
@app.route("/plain", methods=["GET"])  # no auth
def plain() -> Response:
    return Response("PLAIN OK", mimetype="text/plain; charset=utf-8")


# Lightweight healthcheck endpoint for quick availability tests
@app.route("/health", methods=["GET"])  # no auth for health
def health() -> str:
    return "OK"


# Avoid browser hanging on missing favicon
@app.route("/favicon.ico", methods=["GET"])  # no auth
def favicon():
    return ("", 204)


def kill_other_instances():
    """Закрывает другие запущенные копии этого скрипта."""
    # Флаг для отключения функции (по умолчанию отключена из-за проблем)
    ENABLE_KILL_OTHER_INSTANCES = False
    
    if not ENABLE_KILL_OTHER_INSTANCES:
        # Функция отключена - просто проверяем порт
        try:
            SERVER_PORT = 50001
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', SERVER_PORT))
            sock.close()
            
            if result == 0:
                print(f"Внимание: порт {SERVER_PORT} уже занят другим процессом.", flush=True)
                print("Закройте другой экземпляр сервера вручную или измените порт.", flush=True)
        except Exception:
            pass
        return
    
    current_pid = os.getpid()
    killed_count = 0
    
    # Нормализуем пути для сравнения
    script_path_normalized = str(SCRIPT_PATH.resolve()).lower()
    script_name_normalized = SCRIPT_NAME.lower()
    
    print(f"Ищу процессы с путем: {script_path_normalized}", flush=True)
    
    if PSUTIL_AVAILABLE:
        # Используем psutil для поиска и закрытия процессов
        try:
            for proc in psutil.process_iter():
                try:
                    proc_pid = proc.pid
                    # Пропускаем текущий процесс - это критически важно!
                    if proc_pid == current_pid:
                        continue
                    
                    # Проверяем, что это процесс Python
                    try:
                        proc_name = proc.name().lower()
                        if 'python' not in proc_name and 'py' not in proc_name:
                            continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    
                    # Получаем командную строку процесса
                    try:
                        cmdline = proc.cmdline()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    
                    if not cmdline or len(cmdline) < 2:
                        continue
                    
                    # Проверяем, что это наш скрипт
                    # Обычно скрипт - это последний аргумент в командной строке Python
                    script_found = False
                    
                    # Проверяем все аргументы, но приоритет - последнему
                    for i, arg in enumerate(cmdline):
                        try:
                            arg_path = Path(arg).resolve()
                            arg_path_normalized = str(arg_path).lower()
                            
                            # Точное совпадение пути
                            if arg_path_normalized == script_path_normalized:
                                script_found = True
                                break
                        except (ValueError, OSError):
                            # Если не удалось создать Path, проверяем строковое совпадение
                            arg_normalized = str(arg).lower()
                            if arg_normalized == script_path_normalized:
                                script_found = True
                                break
                    
                    if script_found:
                        # Дополнительная проверка - убеждаемся, что это не текущий процесс
                        if proc_pid == current_pid:
                            print(f"ПРЕДУПРЕЖДЕНИЕ: Попытка закрыть текущий процесс {proc_pid}! Пропускаем.", flush=True)
                            continue
                        
                        try:
                            print(f"Найден процесс {proc_pid}, закрываю...", flush=True)
                            proc.terminate()
                            # Ждём немного для корректного завершения
                            proc.wait(timeout=3)
                            killed_count += 1
                            print(f"Закрыт процесс {proc_pid}", flush=True)
                        except psutil.TimeoutExpired:
                            # Если процесс не завершился, принудительно закрываем
                            proc.kill()
                            killed_count += 1
                            print(f"Принудительно закрыт процесс {proc_pid}", flush=True)
                        except psutil.NoSuchProcess:
                            pass  # Процесс уже завершился
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            print(f"Ошибка при поиске процессов: {e}", flush=True)
    else:
        # Альтернативный метод: проверяем порт и пытаемся закрыть через socket
        # Это менее надёжно, но работает без дополнительных библиотек
        try:
            # Проверяем, занят ли порт
            SERVER_PORT = 50012
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', SERVER_PORT))
            sock.close()
            
            if result == 0:
                # Порт занят, но без psutil мы не можем точно найти процесс
                print(f"Внимание: порт {SERVER_PORT} занят. Установите psutil для автоматического закрытия других копий.", flush=True)
                print("Команда: py -m pip install psutil", flush=True)
        except Exception as e:
            print(f"Не удалось проверить порт: {e}", flush=True)
    
    if killed_count > 0:
        print(f"Закрыто {killed_count} других копий скрипта", flush=True)
        time.sleep(1)  # Даём время на освобождение порта
    elif PSUTIL_AVAILABLE:
        print("Других копий скрипта не найдено", flush=True)


if __name__ == "__main__":
    # Убеждаемся, что вывод идёт в консоль
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Сохраняем PID текущего процесса для дополнительной проверки
    current_pid = os.getpid()
    print(f"Текущий процесс PID: {current_pid}", flush=True)
    
    # Закрываем другие копии перед запуском
    print("Проверка других копий скрипта...", flush=True)
    try:
        kill_other_instances()
        
        # Проверяем, что мы все еще живы
        if os.getpid() != current_pid:
            print("ОШИБКА: PID изменился! Процесс был закрыт!", flush=True)
            sys.exit(1)
        
        print(f"Проверка завершена. Текущий процесс {current_pid} продолжает работу.", flush=True)
    except Exception as e:
        print(f"ОШИБКА при проверке других копий: {e}", flush=True)
        print("Продолжаем запуск несмотря на ошибку...", flush=True)
        import traceback
        traceback.print_exc()
    
    # Выводим информацию о запуске в консоль
    # Порт сервера
    SERVER_PORT = 50001
    EXTERNAL_IP = "217.10.41.213"
    
    print("=" * 60, flush=True)
    print("Запуск Flask сервера...", flush=True)
    print(f"Хост: 0.0.0.0 (доступен извне)", flush=True)
    print(f"Порт: {SERVER_PORT}", flush=True)
    print(f"Внешний IP: {EXTERNAL_IP}", flush=True)
    print(f"Базовая директория: {BASE_DIR}", flush=True)
    print(f"Доступные файлы: {len(ALLOWED_FILES)}", flush=True)
    print("=" * 60, flush=True)
    print(f"Сервер запущен! Откройте в браузере:", flush=True)
    print(f"  Локально: http://localhost:{SERVER_PORT}", flush=True)
    print(f"  Извне: http://{EXTERNAL_IP}:{SERVER_PORT}", flush=True)
    print("Для остановки нажмите Ctrl+C", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)  # Пустая строка для читаемости
    
    # Также логируем в файл
    logger.info(f"Starting Flask server on 0.0.0.0:{SERVER_PORT}")
    logger.info(f"External access: http://{EXTERNAL_IP}:{SERVER_PORT}")
    logger.info(f"Available files: {list(ALLOWED_FILES)}")
    logger.info("Server will log all connections to server.log")
    
    try:
        # Включаем вывод Flask в консоль
        # Flask по умолчанию выводит информацию о запуске только в debug режиме
        # Поэтому выводим вручную
        print(f" * Running on http://0.0.0.0:{SERVER_PORT}/ (Press CTRL+C to quit)", flush=True)
        print(f" * Running on http://127.0.0.1:{SERVER_PORT}/ (Press CTRL+C to quit)", flush=True)
        print(f" * External access: http://{EXTERNAL_IP}:{SERVER_PORT}/ (Press CTRL+C to quit)", flush=True)
        print(flush=True)
        
        # Оптимизированные настройки для производительности
        app.run(
            host="0.0.0.0", 
            port=SERVER_PORT, 
            debug=False, 
            threaded=True,  # Многопоточность для параллельных запросов
            use_reloader=False,
            processes=1  # Один процесс, но много потоков
        )
    except KeyboardInterrupt:
        print("\n" + "=" * 60, flush=True)
        print("Сервер остановлен пользователем", flush=True)
        print("=" * 60, flush=True)
        logger.info("Server stopped by user")
    except Exception as e:
        print(f"\nОШИБКА при запуске сервера: {e}", flush=True)
        logger.error(f"Failed to start server: {e}")
        raise


