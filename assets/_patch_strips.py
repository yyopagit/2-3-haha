"""Патч province strips: infra/selector — прозрачный f0; town — цифра «1» ближе к углу."""
import os
import struct
import sys

import imagecodecs
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from _dds_tools import FRAME_H, FRAME_W, get_frame, load_dds, save_dds

MOD_GFX = r"C:\Games\Vic2LV2\Victoria 2\mod\5\gfx\interface"
MOD8_GFX = r"C:\Users\Антон\Desktop\BDSM_Mod-Victoria2-main\V2BDSM\mod\8\gfx\interface"
ASSETS = os.path.dirname(__file__)


def load_dds_rgba(path: str) -> Image.Image:
    data = open(path, "rb").read()
    w = struct.unpack_from("<I", data, 16)[0]
    h = struct.unpack_from("<I", data, 12)[0]
    bpp = struct.unpack_from("<I", data, 88)[0]
    fourcc = data[84:88]
    if bpp == 32:
        return Image.frombytes("RGBA", (w, h), data[128:], "raw", "BGRA")
    pw = -(-w // 4) * 4
    ph = -(-h // 4) * 4
    fmt = 1 if fourcc == b"DXT1" else 3
    arr = imagecodecs.bcn_decode(data[128:], format=fmt, shape=(ph, pw, 4))
    return Image.fromarray(arr[:h, :w, :], "RGBA")


def empty_frame_from_fort() -> Image.Image:
    fort_path = os.path.join(MOD8_GFX, "province_fort_strip.dds")
    if not os.path.exists(fort_path):
        fort_path = os.path.join(MOD_GFX, "province_fort_strip.dds")
    fort_img, _, _ = load_dds(fort_path)
    return get_frame(fort_img, 0).convert("RGBA")


def apply_fort_alpha_mask(frame: Image.Image) -> Image.Image:
    out = frame.convert("RGBA")
    px = out.load()
    for x in range(FRAME_W):
        px[x, 0] = (0, 0, 0, 0)
        px[x, FRAME_H - 1] = (0, 0, 0, 0)
    return out


def write_bgra32(path: str, img: Image.Image, header_template: bytes | None = None) -> None:
    ref = header_template or open(
        os.path.join(MOD_GFX, "province_fort_strip.dds"), "rb"
    ).read()[:128]
    save_dds(path, img, "BGRA32", header_template=ref)


def _load_bg_image() -> Image.Image:
    bg_path = os.path.join(MOD_GFX, "province_bg.dds")
    if not os.path.exists(bg_path):
        raise FileNotFoundError(bg_path)
    bg_data = open(bg_path, "rb").read()
    w = struct.unpack_from("<I", bg_data, 16)[0]
    h = struct.unpack_from("<I", bg_data, 12)[0]
    bpp = struct.unpack_from("<I", bg_data, 88)[0]
    if bpp == 32:
        return Image.frombytes("RGBA", (w, h), bg_data[128:], "raw", "BGRA")
    import imagecodecs
    pw = -(-w // 4) * 4
    ph = -(-h // 4) * 4
    fmt = 1 if bg_data[84:88] == b"DXT1" else 3
    arr = imagecodecs.bcn_decode(bg_data[128:], format=fmt, shape=(ph, pw, 4))
    return Image.fromarray(arr[:h, :w, :], "RGBA")


def _f0_from_bg(bg_y: int) -> Image.Image:
    """Вырезать кадр 40×32 из province_bg по заданной y-координате строки здания."""
    try:
        bg = _load_bg_image()
    except FileNotFoundError:
        return empty_frame_from_fort()
    ICON_X = 23
    f0 = bg.crop((ICON_X, bg_y, ICON_X + FRAME_W, bg_y + FRAME_H)).convert("RGBA")
    return apply_fort_alpha_mask(f0)


def infra_f0_from_bg() -> Image.Image:
    """Иконка 0-уровня инфры из province_bg (строка i=2: y=358+35*2=428)."""
    return _f0_from_bg(428)


def fort_f0_from_bg() -> Image.Image:
    """Иконка 0-уровня крепости из province_bg (строка i=3: y=358+35*3=463)."""
    return _f0_from_bg(463)


def fort_f0_dim() -> Image.Image:
    """f0 крепости = dim (55%) версия strip f1 с заменой цифры '1' на '0'."""
    import subprocess
    mod_root = os.path.dirname(os.path.dirname(MOD_GFX))
    data = subprocess.run(
        ["git", "-C", mod_root, "show", "HEAD:gfx/interface/province_fort_strip.dds"],
        capture_output=True, check=True,
    ).stdout
    w = struct.unpack_from("<I", data, 16)[0]
    git_img = Image.frombytes("RGBA", (w, FRAME_H), data[128:], "raw", "BGRA")
    f1 = get_frame(git_img, 1).convert("RGBA")
    # Приглушить яркость
    arr = np.array(f1, dtype=np.float32)
    arr[:, :, :3] *= 0.55
    arr = arr.clip(0, 255).astype(np.uint8)
    dimmed = apply_fort_alpha_mask(Image.fromarray(arr, "RGBA"))
    # Заменить цифру '1' на '0'
    return draw_level_number(dimmed, "0")


def naval_f0_from_bg() -> Image.Image:
    """Иконка 0-уровня порта из province_bg (строка i=1: y=358+35*1=393)."""
    return _f0_from_bg(393)


def patch_infra_strip() -> None:
    """infra: f0 = иконка из province_bg (видна в чужих провинциях), f1-f6 = git f1-f6."""
    path = os.path.join(MOD_GFX, "province_infra_strip.dds")

    import subprocess
    data = subprocess.run(
        ["git", "-C", os.path.dirname(os.path.dirname(MOD_GFX)), "show", "HEAD:gfx/interface/province_infra_strip.dds"],
        capture_output=True,
        check=True,
    ).stdout
    w = struct.unpack_from("<I", data, 16)[0]
    git_img = Image.frombytes("RGBA", (w, 32), data[128:], "raw", "BGRA")
    n = git_img.width // FRAME_W
    print(f"infra git: {git_img.size}, {n} кадров")

    f0 = infra_f0_from_bg()
    frames = [f0]
    for i in range(1, n):
        frames.append(apply_fort_alpha_mask(get_frame(git_img, i)))

    strip = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * FRAME_W, 0), fr)

    write_bgra32(path, strip)
    t0 = sum(1 for p in get_frame(strip, 0).getdata() if p[3] == 0)
    print(f"  -> {strip.size}, f0 nz={FRAME_W * FRAME_H - t0}/1280 (from province_bg), f1-f{n - 1} content")


def _patch_strip_with_f0_from_bg(strip_name: str, f0_fn) -> None:
    """Патч стрипа: f0 из province_bg, остальные кадры из git."""
    import subprocess
    path = os.path.join(MOD_GFX, strip_name)
    mod_root = os.path.dirname(os.path.dirname(MOD_GFX))
    data = subprocess.run(
        ["git", "-C", mod_root, "show", f"HEAD:gfx/interface/{strip_name}"],
        capture_output=True,
        check=True,
    ).stdout
    w = struct.unpack_from("<I", data, 16)[0]
    git_img = Image.frombytes("RGBA", (w, FRAME_H), data[128:], "raw", "BGRA")
    n = git_img.width // FRAME_W
    f0 = f0_fn()
    frames = [f0] + [apply_fort_alpha_mask(get_frame(git_img, i)) for i in range(1, n)]
    strip = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * FRAME_W, 0), fr)
    write_bgra32(path, strip)
    t0 = sum(1 for p in get_frame(strip, 0).getdata() if p[3] == 0)
    print(f"  {strip_name}: {strip.size}, f0 nz={FRAME_W * FRAME_H - t0}/1280, f1-f{n - 1} from git")


def patch_fort_strip_f0() -> None:
    """fort_strip: f0 = dim (50%) версия f1 для плавного перехода 0→1.
    В province_bg (row i=3, y=463) тоже обновляется через update_bg_fort_icon()."""
    _patch_strip_with_f0_from_bg("province_fort_strip.dds", fort_f0_dim)


def patch_navalbase_strip_f0() -> None:
    """navalbase_strip: f0 из province_bg (строка navalbase y=393) — видна в чужих провинциях."""
    _patch_strip_with_f0_from_bg("province_navalbase_strip.dds", naval_f0_from_bg)


def patch_selector_strip() -> None:
    path = os.path.join(MOD_GFX, "province_selector_strip.dds")
    git_img = load_dds_rgba(path)
    print(f"selector: {git_img.size}")

    empty = empty_frame_from_fort()
    # f1 git = уровень 1 (f0 уровня 0 уже в province_bg)
    lvl1 = apply_fort_alpha_mask(get_frame(git_img, 1))

    strip = Image.new("RGBA", (FRAME_W * 2, FRAME_H), (0, 0, 0, 0))
    strip.paste(empty, (0, 0), empty)
    strip.paste(lvl1, (FRAME_W, 0), lvl1)

    write_bgra32(path, strip)
    trans = sum(1 for p in get_frame(strip, 0).getdata() if p[3] == 0)
    print(f"  -> {strip.size}, f0 transparent={trans}/{FRAME_W * FRAME_H}")


# Внутренний размер арта и смещение — как у оригинального town bak f1 (не на весь 40x32)
ART_W, ART_H = 36, 26
ART_X, ART_Y = 2, 4


def downscale_art(img: Image.Image) -> Image.Image:
    """Даунскейл PNG до размера внутренней области (не на весь кадр)."""
    img = img.convert("RGBA")
    w, h = img.size
    tr = ART_W / ART_H
    if w / h > tr:
        nw = int(h * tr)
        img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
    else:
        nh = int(w / tr)
        img = img.crop((0, (h - nh) // 2, w, (h + nh) // 2))

    cw, ch = img.size
    mw = max(ART_W, (cw // ART_W) * ART_W)
    mh = max(ART_H, (ch // ART_H) * ART_H)
    img = img.crop(((cw - mw) // 2, (ch - mh) // 2, (cw + mw) // 2, (ch + mh) // 2))

    while mw > ART_W * 4 or mh > ART_H * 4:
        mw = max(ART_W, mw // 4)
        mh = max(ART_H, mh // 4)
        img = img.resize((mw, mh), Image.Resampling.BOX)

    img = img.resize((ART_W, ART_H), Image.Resampling.BOX)
    return img.filter(ImageFilter.UnsharpMask(radius=0.6, percent=90, threshold=2))


def fit_art_in_frame(scaled: Image.Image) -> Image.Image:
    """Вставить арт в 40x32 с отступами сверху/снизу (как у fort/infra)."""
    frame = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    frame.paste(scaled, (ART_X, ART_Y), scaled)
    return frame


def erase_old_number(frame: Image.Image) -> Image.Image:
    out = frame.copy()
    patch = out.crop((4, 16, 28, 30)).resize((20, 15), Image.Resampling.BOX)
    out.paste(patch, (20, 16))
    return out


DIGIT_FONT_SIZE = 14
DIGIT_X, DIGIT_Y = 28, 15


def _draw_digit_no_erase(
    frame: Image.Image, digit: str, x: int = DIGIT_X, y: int = DIGIT_Y
) -> Image.Image:
    """Нарисовать цифру БЕЗ erase_old_number — для синтезированных frame без встроенной цифры."""
    out = frame.copy()
    draw = ImageDraw.Draw(out)
    # Arial Bold — без засечек, чище рендерится на маленьких размерах
    for path in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
                 "C:/Windows/Fonts/timesbd.ttf"):
        try:
            font = ImageFont.truetype(path, DIGIT_FONT_SIZE)
            break
        except OSError:
            continue
    else:
        font = ImageFont.load_default()
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        draw.text((x + dx, y + dy), digit, fill=(0, 0, 0, 255), font=font)
    draw.text((x, y), digit, fill=(255, 255, 255, 255), font=font)
    return out


def draw_level_number(
    frame: Image.Image, digit: str, x: int = DIGIT_X, y: int = DIGIT_Y
) -> Image.Image:
    """Цифра в правом нижнем углу (как git town), font 14 — влезает над строкой 31.
    Использует erase_old_number — только для frame взятых из git-стрипов с уже нарисованной цифрой."""
    out = erase_old_number(frame)
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/timesbd.ttf", DIGIT_FONT_SIZE)
    except OSError:
        try:
            font = ImageFont.truetype("times.ttf", DIGIT_FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
        draw.text((x + dx, y + dy), digit, fill=(0, 0, 0, 255), font=font)
    draw.text((x, y), digit, fill=(255, 255, 255, 255), font=font)
    return out


def patch_town_strip() -> None:
    path = os.path.join(MOD_GFX, "province_town_strip.dds")

    src_path = os.path.join(ASSETS, "city_town_level2.png")
    if not os.path.exists(src_path):
        raise FileNotFoundError(src_path)

    src = Image.open(src_path).convert("RGBA")
    arr = np.array(src)  # shape (1024, 1536, 4) — 3 кадра по 512x1024

    # Закрашиваем цифру "2" в кадре 3 (x=1024..1535) текстурой травы
    # из нижнего левого угла того же кадра
    grass = arr[850:1024, 1024:1196].copy()   # чистая трава, ~172x174
    gh, gw = grass.shape[:2]
    d_x0, d_y0, d_x1, d_y1 = 1215, 625, 1455, 940
    dw, dh = d_x1 - d_x0, d_y1 - d_y0
    arr = arr.copy()
    for ty in range(0, dh, gh):
        for tx in range(0, dw, gw):
            ey, ex = min(ty + gh, dh), min(tx + gw, dw)
            arr[d_y0 + ty : d_y0 + ey, d_x0 + tx : d_x0 + ex] = grass[:ey - ty, :ex - tx]

    # Даунскейлим весь спрайт-лист (1536x1024), как в _build_town_strip.py.
    # Один кадр 512x1024 даёт w/h < ART ratio → вертикальный кроп и «кусок» города.
    cleaned = Image.fromarray(arr, "RGBA")
    art = downscale_art(cleaned)
    base = apply_fort_alpha_mask(fit_art_in_frame(art))
    lvl1 = _draw_digit_no_erase(base, "1")

    empty = empty_frame_from_fort()

    strip = Image.new("RGBA", (FRAME_W * 2, FRAME_H), (0, 0, 0, 0))
    strip.paste(empty, (0, 0), empty)
    strip.paste(lvl1, (FRAME_W, 0), lvl1)

    write_bgra32(path, strip)
    import shutil

    for copy_name in (
        "province_town_infrastructure_strip.dds",
    ):
        shutil.copy2(path, os.path.join(MOD_GFX, copy_name))

    # Проверка качества: сравнить с предыдущей версией если есть
    old_path = path + ".before_patch"
    if os.path.exists(old_path):
        old = load_dds_rgba(old_path)
        old_f1 = np.array(old.crop((FRAME_W, 0, FRAME_W * 2, FRAME_H)).convert("RGB"))
        new_f1 = np.array(lvl1.convert("RGB"))
        diff = float(np.abs(old_f1.astype(int) - new_f1.astype(int)).mean())
        print(f"town: diff f1 vs backup = {diff:.1f} (ожидается >0 из-за цифры)")

    lvl1.save(os.path.join(ASSETS, "city_town_f1_40x32.png"))
    strip.save(os.path.join(ASSETS, "province_town_strip_preview.png"))
    trans = sum(1 for p in get_frame(strip, 0).getdata() if p[3] == 0)
    print(f"  -> {strip.size}, f0 transparent={trans}/{FRAME_W * FRAME_H}")
    print(f"  art {ART_W}x{ART_H} at ({ART_X},{ART_Y}), digit '1' at ({DIGIT_X}, {DIGIT_Y})")


def main():
    # Бэкап town перед пересборкой
    town_path = os.path.join(MOD_GFX, "province_town_strip.dds")
    if os.path.exists(town_path):
        import shutil
        shutil.copy2(town_path, town_path + ".before_patch")

    print("=== patch infra ===")
    patch_infra_strip()
    print("=== patch fort f0 ===")
    patch_fort_strip_f0()
    print("=== patch navalbase f0 ===")
    patch_navalbase_strip_f0()
    print("=== patch selector ===")
    patch_selector_strip()
    print("=== patch town ===")
    patch_town_strip()
    print("Done.")


if __name__ == "__main__":
    main()
