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


def patch_infra_strip() -> None:
    """infra: f0 прозрачный (уровень 0 = карета с province_bg), f1-f6 = git f1-f6."""
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

    empty = empty_frame_from_fort()
    frames = [empty]
    for i in range(1, n):
        frames.append(apply_fort_alpha_mask(get_frame(git_img, i)))

    strip = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * FRAME_W, 0), fr)

    write_bgra32(path, strip)
    t0 = sum(1 for p in get_frame(strip, 0).getdata() if p[3] == 0)
    print(f"  -> {strip.size}, f0 empty (transparent={t0}/1280), f1-f{n - 1} content")


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


def draw_level_number(
    frame: Image.Image, digit: str, x: int = DIGIT_X, y: int = DIGIT_Y
) -> Image.Image:
    """Цифра в правом нижнем углу (как git town), font 14 — влезает над строкой 31."""
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
    src = os.path.join(ASSETS, "city_town_level2.png")
    if not os.path.exists(src):
        raise FileNotFoundError(src)

    empty = empty_frame_from_fort()
    art = downscale_art(Image.open(src))
    lvl1 = apply_fort_alpha_mask(draw_level_number(fit_art_in_frame(art), "1"))

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
    print("=== patch selector ===")
    patch_selector_strip()
    print("=== patch town ===")
    patch_town_strip()
    print("Done.")


if __name__ == "__main__":
    main()
