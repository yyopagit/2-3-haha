"""
Fix province_bg.dds - вставляем правильные иконки уровня 0 в фон.
Порядок строк (сверху вниз): town, fort, infra, naval, selector
Позиции иконок: x=23, y=row_y-4, размер 40x32

Ряды фона (границы найдены анализом province_bg из git):
  Row 0 (town):     row_y=358  -> icon_y=354
  Row 1 (fort):     row_y=393  -> icon_y=389
  Row 2 (infra):    row_y=427  -> icon_y=423
  Row 3 (naval):    row_y=460  -> icon_y=456
  Row 4 (selector): row_y=495  -> icon_y=491
"""
import struct, os
import imagecodecs
import numpy as np
from PIL import Image, ImageFilter

# --- Пути ---
MOD5_GFX  = r"C:\Games\Vic2LV2\Victoria 2\mod\5\gfx\interface"
MOD5_ASSETS = r"C:\Games\Vic2LV2\Victoria 2\mod\5\assets"
BG_PATH   = os.path.join(MOD5_GFX, "province_bg.dds")


# --- Вспомогательные функции ---
def load_dds_rgba(path: str) -> Image.Image:
    data = open(path, "rb").read()
    w    = struct.unpack_from("<I", data, 16)[0]
    h    = struct.unpack_from("<I", data, 12)[0]
    bpp  = struct.unpack_from("<I", data, 88)[0]
    print(f"  load {os.path.basename(path)}: {w}x{h} bpp={bpp}")
    if bpp == 32:
        return Image.frombytes("RGBA", (w, h), data[128:], "raw", "BGRA")
    else:
        return Image.frombytes("RGBA", (w, h), imagecodecs.dds_decode(data))


def save_bgra32(path: str, img: Image.Image, template_header: bytes = None):
    """Сохраняет RGBA изображение как DDS 32bpp BGRA (lossless)."""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    pix  = np.array(rgba)
    bgra = pix[:, :, [2, 1, 0, 3]].tobytes()

    if template_header is not None:
        hdr = bytearray(template_header[:128])
        struct.pack_into("<I", hdr, 12, h)
        struct.pack_into("<I", hdr, 16, w)
        struct.pack_into("<I", hdr, 20, w * 4)   # pitch
        # pixel format offset 76: size, flags, fourCC, bpp, ...
        struct.pack_into("<I", hdr, 76, 32)       # pfsize
        struct.pack_into("<I", hdr, 80, 0x41)     # flags: RGBA
        struct.pack_into("<4s", hdr, 84, b"\x00\x00\x00\x00")  # no fourCC
        struct.pack_into("<I", hdr, 88, 32)       # bpp
        struct.pack_into("<I", hdr, 92, 0x00FF0000)  # R mask
        struct.pack_into("<I", hdr, 96, 0x0000FF00)  # G mask
        struct.pack_into("<I", hdr, 100, 0x000000FF) # B mask
        struct.pack_into("<I", hdr, 104, 0xFF000000) # A mask
        hdr = bytes(hdr)
    else:
        # Строим минимальный DDS-заголовок BGRA32
        pitch = w * 4
        hdr = struct.pack(
            "<4sI124s",
            b"DDS ",
            124,
            b"\x00" * 124,
        )
        hdr = bytearray(hdr)
        struct.pack_into("<I", hdr, 8,  0x100F)   # DDSD flags
        struct.pack_into("<I", hdr, 12, h)
        struct.pack_into("<I", hdr, 16, w)
        struct.pack_into("<I", hdr, 20, pitch)
        struct.pack_into("<I", hdr, 28, 1)        # mipmap count
        struct.pack_into("<I", hdr, 76, 32)       # pfsize
        struct.pack_into("<I", hdr, 80, 0x41)     # DDPF_ALPHAPIXELS | DDPF_RGB
        struct.pack_into("<4s", hdr, 84, b"\x00\x00\x00\x00")
        struct.pack_into("<I", hdr, 88, 32)
        struct.pack_into("<I", hdr, 92, 0x00FF0000)
        struct.pack_into("<I", hdr, 96, 0x0000FF00)
        struct.pack_into("<I", hdr, 100, 0x000000FF)
        struct.pack_into("<I", hdr, 104, 0xFF000000)
        hdr = bytes(hdr)

    with open(path, "wb") as f:
        f.write(hdr)
        f.write(bgra)
    print(f"  saved {os.path.basename(path)}: {w}x{h} BGRA32, {len(bgra)//1024}KB")


def get_frame0_40x32(strip_path: str) -> Image.Image:
    """Берёт первый фрейм (40x32) из стрип-файла."""
    img = load_dds_rgba(strip_path)
    return img.crop((0, 0, 40, 32)).convert("RGBA")


# --- Источники иконок ---
# Оригинальный frame0 для форт/инфра/флот/селектор = из bak_frame0 файлов
def load_original_f0(name: str) -> Image.Image:
    """Загружает оригинальный frame0 (40x32) из bak_frame0 файла."""
    # navalbase - имя файла отличается от ключа "naval"
    strip_name = "navalbase" if name == "naval" else name
    bak = os.path.join(MOD5_GFX, f"province_{strip_name}_strip.dds.bak_frame0")
    img = load_dds_rgba(bak)
    # bak содержит весь оригинальный стрип (без добавленного прозрачного frame0)
    # frame0 = первые 40 пикселей по ширине
    return img.crop((0, 0, 40, 32)).convert("RGBA")


def load_city_icon() -> Image.Image:
    """Загружает сгенерированную картинку города и масштабирует до 40x32."""
    src = os.path.join(MOD5_ASSETS, "city_town_level1.png")
    img = Image.open(src).convert("RGBA")
    print(f"  city source: {img.size}")

    # Многошаговое уменьшение BOX + резкость
    target = (40, 32)
    current = img
    while current.width > target[0] * 2 or current.height > target[1] * 2:
        half_w = max(target[0], current.width // 2)
        half_h = max(target[1], current.height // 2)
        current = current.resize((half_w, half_h), Image.BOX)

    icon = current.resize(target, Image.LANCZOS)
    icon = icon.filter(ImageFilter.UnsharpMask(radius=0.6, percent=120, threshold=2))
    return icon


# --- Позиции вставки иконок ---
# Порядок по buildings.txt (сверху вниз в списке зданий провинции):
#   province_selector → naval_base → railroad(infra) → fort → town_infrastructure
# row_y = верхняя граница строки (найдена по границам кнопок в province_bg из git)
# icon_x = 23, icon_y = row_y - 4 (из GUI: position = { x=23 y=-4 })
BUILDING_ROWS = [
    ("selector", 358),   # 1-й в buildings.txt - province_selector
    ("naval",    393),   # 2-й - naval_base
    ("infra",    427),   # 3-й - railroad (infrastructure)
    ("fort",     460),   # 4-й - fort
    ("town",     495),   # 5-й - town_infrastructure
]
ICON_X = 23
ICON_W = 40
ICON_H = 32


def main():
    print("=== Fix province_bg.dds ===\n")

    # 1. Загрузить оригинальный (git) province_bg как основу
    print("1. Загружаем git-версию province_bg...")
    bg = load_dds_rgba(BG_PATH)
    bg = bg.convert("RGBA")
    print(f"   bg size: {bg.size}")

    # Заголовок НЕ копируем из оригинала — строим чистый BGRA32 заголовок

    # 2. Подготавливаем иконки для каждого здания
    print("\n2. Подготавливаем иконки...")

    icons = {}
    # Город - сгенерированная картинка
    print(" [town] city_town_level1.png ->")
    icons["town"] = load_city_icon()
    icons["town"].save(os.path.join(MOD5_ASSETS, "_preview_bg_town_icon.png"))

    # Остальные - оригинальный frame0 из bak файлов
    for name in ["fort", "infra", "naval", "selector"]:
        print(f" [{name}]")
        icons[name] = load_original_f0(name)
        icons[name].save(os.path.join(MOD5_ASSETS, f"_preview_bg_{name}_icon.png"))

    # 3. Вставляем иконки в фон
    print("\n3. Вставляем иконки в province_bg...")
    for name, row_y in BUILDING_ROWS:
        icon_y = row_y - 4
        icon = icons[name]
        assert icon.size == (ICON_W, ICON_H), f"Wrong size for {name}: {icon.size}"

        # Вставляем с учётом alpha
        bg.paste(icon, (ICON_X, icon_y), mask=icon.split()[3])
        print(f"   [{name}] pasted at ({ICON_X}, {icon_y})")

    # 4. Сохраняем
    print("\n4. Сохраняем province_bg.dds (BGRA32)...")
    save_bgra32(BG_PATH, bg)   # Чистый BGRA32 заголовок (DDSD_PITCH, без DDSD_LINEARSIZE)

    # Сохраняем превью для проверки
    preview = bg.crop((0, 330, 200, 545))
    preview.save(os.path.join(MOD5_ASSETS, "_preview_province_bg_buildings.png"))
    print("   preview saved: _preview_province_bg_buildings.png")
    print("\nDone!")


if __name__ == "__main__":
    main()
