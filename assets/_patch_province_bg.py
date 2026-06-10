"""
Патчит province_bg.dds: вставляет иконки уровня 0 в правильном порядке.
Сохраняет файл в оригинальном формате DXT5 (не конвертирует в BGRA32).
"""
import struct, os, imagecodecs
import numpy as np
from PIL import Image, ImageFilter
import quicktex.s3tc.bc3 as bc3

MOD5_GFX   = r"C:\Games\Vic2LV2\Victoria 2\mod\5\gfx\interface"
MOD5_ASSETS= r"C:\Games\Vic2LV2\Victoria 2\mod\5\assets"
BG_PATH    = os.path.join(MOD5_GFX, "province_bg.dds")


# ─── загрузка / сохранение ───────────────────────────────────────────────────

def load_dds_rgba(path: str) -> tuple[Image.Image, bytes]:
    """Возвращает (RGBA Image, оригинальный заголовок 128 байт).
    
    Для DXT/BCn: декодирует с правильными padded-размерами (кратными 4),
    затем обрезает до реального размера из заголовка.
    """
    data = open(path, "rb").read()
    w    = struct.unpack_from("<I", data, 16)[0]
    h    = struct.unpack_from("<I", data, 12)[0]
    bpp  = struct.unpack_from("<I", data, 88)[0]
    fourcc = data[84:88]
    print(f"  load {os.path.basename(path)}: {w}x{h} bpp={bpp} fourcc={fourcc!r}")
    if bpp == 32:
        img = Image.frombytes("RGBA", (w, h), data[128:], "raw", "BGRA")
    else:
        # BCn: блоки 4x4, размеры должны быть кратны 4 при декодировании
        pw = -(-w // 4) * 4
        ph = -(-h // 4) * 4
        # DXT1/BC1 = format 1, DXT5/BC3 = format 3
        bcn_fmt = 1 if fourcc == b"DXT1" else 3
        arr = imagecodecs.bcn_decode(data[128:], format=bcn_fmt, shape=(ph, pw, 4))
        img = Image.fromarray(arr[:h, :w, :], "RGBA")
    return img, data[:128]


def encode_dxt5(img: Image.Image) -> bytes:
    """Кодирует RGBA Image в DXT5 через quicktex."""
    import quicktex
    # quicktex требует кратность 4
    w, h = img.size
    pw = (w + 3) & ~3
    ph = (h + 3) & ~3
    if pw != w or ph != h:
        padded = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        padded.paste(img, (0, 0))
    else:
        padded = img.convert("RGBA")

    raw_data = padded.tobytes("raw", "RGBA")
    tex = quicktex.RawTexture.frombytes(raw_data, pw, ph)
    enc = bc3.BC3Encoder(5)
    result = enc.encode(tex)
    return bytes(result)


def save_dxt5(path: str, img: Image.Image, orig_header: bytes):
    """Сохраняет RGBA Image как DDS DXT5, сохраняя оригинальный заголовок."""
    compressed = encode_dxt5(img)
    # Патчим заголовок: linearSize = размер сжатых данных
    hdr = bytearray(orig_header)
    struct.pack_into("<I", hdr, 20, len(compressed))  # linearSize
    # Убеждаемся что флаги правильные для DXT5
    flags = struct.unpack_from("<I", hdr, 8)[0]
    flags = (flags | 0x80000) & ~0x8   # LINEARSIZE=1, PITCH=0
    struct.pack_into("<I", hdr, 8, flags)
    with open(path, "wb") as f:
        f.write(bytes(hdr))
        f.write(compressed)
    print(f"  saved {os.path.basename(path)}: DXT5 {img.size}, {len(compressed)//1024}KB compressed")


# ─── иконки ──────────────────────────────────────────────────────────────────

def load_git_strip_f0(git_file: str) -> Image.Image:
    """Загружает frame0 (40x32) из git-версии стрипа."""
    import subprocess
    mod_root = os.path.dirname(os.path.dirname(MOD5_GFX))
    data = subprocess.run(
        ["git", "-C", mod_root, "show", f"HEAD:gfx/interface/{git_file}"],
        capture_output=True,
        check=True,
    ).stdout
    img, _ = load_dds_rgba_from_bytes(data)
    return img.crop((0, 0, 40, 32)).convert("RGBA")


def load_dds_rgba_from_bytes(data: bytes) -> tuple[Image.Image, bytes]:
    w = struct.unpack_from("<I", data, 16)[0]
    h = struct.unpack_from("<I", data, 12)[0]
    bpp = struct.unpack_from("<I", data, 88)[0]
    fourcc = data[84:88]
    if bpp == 32:
        img = Image.frombytes("RGBA", (w, h), data[128:], "raw", "BGRA")
    else:
        pw = -(-w // 4) * 4
        ph = -(-h // 4) * 4
        bcn_fmt = 1 if fourcc == b"DXT1" else 3
        arr = imagecodecs.bcn_decode(data[128:], format=bcn_fmt, shape=(ph, pw, 4))
        img = Image.fromarray(arr[:h, :w, :], "RGBA")
    return img, data[:128]


def load_bak_f0(strip_name: str) -> Image.Image:
    """Загружает frame0 уровня 0 (40x32) из git-оригинала стрипа."""
    git_files = {
        "selector": "province_selector_strip.dds",
        "navalbase": "province_navalbase_strip.dds",
        "infra": "province_infra_strip.dds",
        "fort": "province_fort_strip.dds",
        "town_bak0": "province_town_strip.dds",
    }
    return load_git_strip_f0(git_files[strip_name])


def load_city_icon() -> Image.Image:
    """Масштабирует сгенерированную картинку города до 40x32."""
    src = os.path.join(MOD5_ASSETS, "city_town_level1.png")
    img = Image.open(src).convert("RGBA")
    print(f"  city source: {img.size}")
    # Многошаговое BOX-уменьшение + резкость
    cur = img
    target = (40, 32)
    while cur.width > target[0] * 2 or cur.height > target[1] * 2:
        cur = cur.resize((max(target[0], cur.width//2),
                          max(target[1], cur.height//2)), Image.BOX)
    cur = cur.resize(target, Image.LANCZOS)
    cur = cur.filter(ImageFilter.UnsharpMask(radius=0.6, percent=120, threshold=2))
    return cur


# ─── позиции иконок ──────────────────────────────────────────────────────────
# Порядок по buildings.txt: selector→naval→infra→fort→town
# row_y = y первого разделителя строки в province_bg.dds (найден анализом)
# icon_y = row_y + 1  (центровка: высота строки 34px, иконка 32px -> 1px сверху)

BUILDING_ROWS = [
    ("selector",  "selector",  358),
    ("naval",     "navalbase", 393),
    ("infra",     "infra",     427),
    ("fort",      "fort",      460),
    ("town",      "town_bak0", 495),   # frame0 из оригинального town bak (деревня с "0")
]
ICON_X = 23
ICON_Y_OFFSET = 1  # row_y + ICON_Y_OFFSET


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=== Patch province_bg.dds ===\n")

    # 1. Загрузить оригинальный DXT5
    print("1. Загружаем DXT5 оригинал...")
    bg, orig_header = load_dds_rgba(BG_PATH)
    bg = bg.convert("RGBA")

    # 2. Иконки
    print("\n2. Загружаем иконки...")
    icons = {}
    for (key, strip, row_y) in BUILDING_ROWS:
        icons[key] = load_bak_f0(strip)
        icons[key].save(os.path.join(MOD5_ASSETS, f"_patch_icon_{key}.png"))

    # 3. Вставка
    print("\n3. Вставляем иконки...")
    for (key, _, row_y) in BUILDING_ROWS:
        icon_y = row_y + ICON_Y_OFFSET
        icon   = icons[key]
        assert icon.size == (40, 32), f"Bad size for {key}: {icon.size}"
        bg.paste(icon, (ICON_X, icon_y), mask=icon.split()[3])
        print(f"   [{key}] -> x={ICON_X} y={icon_y}")

    # 4. Сохранить обратно в DXT5
    print("\n4. Перекодируем и сохраняем DXT5...")
    save_dxt5(BG_PATH, bg, orig_header)

    # Превью
    bg.crop((0, 330, 280, 540)).save(
        os.path.join(MOD5_ASSETS, "_patch_preview.png"))
    print("   preview: _patch_preview.png")
    print("\nDone!")


if __name__ == "__main__":
    main()
