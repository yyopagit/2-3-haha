"""Собрать province_town_strip: 32bpp BGRA (как fort), без DXT-сжатия."""
import os
import shutil
import struct
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from _dds_tools import FRAME_H, FRAME_W, get_frame, load_dds

ASSETS = os.path.dirname(__file__)
MOD_GFX = r"C:\Games\Vic2LV2\Victoria 2\mod\5\gfx\interface"
BASE_GFX = r"C:\Games\Vic2LV2\Victoria 2\gfx\interface"
MOD8 = r"C:\Users\Антон\Desktop\BDSM_Mod-Victoria2-main\V2BDSM\mod\8\gfx\interface"


ART_W, ART_H = 36, 26
ART_X, ART_Y = 2, 0


def downscale_art(img: Image.Image) -> Image.Image:
    """Даунскейл PNG до внутренней области (36x26), не на весь кадр."""
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
    frame = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    frame.paste(scaled, (ART_X, ART_Y), scaled)
    return frame


def erase_old_number(frame: Image.Image) -> Image.Image:
    """Закрасить угол, где генератор нарисовал старую цифру."""
    out = frame.copy()
    patch = out.crop((4, 16, 28, 30)).resize((20, 15), Image.Resampling.BOX)
    out.paste(patch, (20, 16))
    return out


DIGIT_FONT_SIZE = 14
DIGIT_X, DIGIT_Y = 28, 15


def draw_level_number(frame: Image.Image, digit: str) -> Image.Image:
    out = erase_old_number(frame)
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/timesbd.ttf", DIGIT_FONT_SIZE)
    except OSError:
        try:
            font = ImageFont.truetype("times.ttf", DIGIT_FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()
    x, y = DIGIT_X, DIGIT_Y
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
        draw.text((x + dx, y + dy), digit, fill=(0, 0, 0, 255), font=font)
    draw.text((x, y), digit, fill=(255, 255, 255, 255), font=font)
    return out


def empty_frame_from_fort() -> Image.Image:
    """Пустой кадр 0: полная прозрачность, как province_fort_strip."""
    fort_path = os.path.join(MOD8, "province_fort_strip.dds")
    fort_img, _, _ = load_dds(fort_path)
    return get_frame(fort_img, 0)


def apply_fort_alpha_mask(frame: Image.Image) -> Image.Image:
    """Контентные кадры: прозрачны только строки 0 и 31 (как у форта)."""
    out = frame.convert("RGBA")
    px = out.load()
    for x in range(FRAME_W):
        px[x, 0] = (0, 0, 0, 0)
        px[x, FRAME_H - 1] = (0, 0, 0, 0)
    return out


def write_bgra32_dds(path: str, img: Image.Image) -> None:
    fort_ref = os.path.join(MOD8, "province_fort_strip.dds")
    header = bytearray(open(fort_ref, "rb").read()[:128])
    w, h = img.size
    struct.pack_into("<I", header, 12, h)
    struct.pack_into("<I", header, 16, w)
    struct.pack_into("<I", header, 20, w * 4)
    with open(path, "wb") as f:
        f.write(header)
        f.write(img.convert("RGBA").tobytes("raw", "BGRA"))


def patch_existing_town_alpha():
    """Починить alpha в уже собранном town_strip без пересборки из PNG."""
    town_path = os.path.join(MOD_GFX, "province_town_strip.dds")
    fort_path = os.path.join(MOD8, "province_fort_strip.dds")
    data = open(town_path, "rb").read()
    header = bytearray(data[:128])
    w, h = struct.unpack_from("<I", data, 16)[0], struct.unpack_from("<I", data, 12)[0]
    town = Image.frombytes("RGBA", (w, h), data[128:], "raw", "BGRA")
    fort = load_dds(fort_path)[0]
    town.paste(get_frame(fort, 0), (0, 0), get_frame(fort, 0))
    for i in range(1, w // FRAME_W):
        fr = apply_fort_alpha_mask(town.crop((i * FRAME_W, 0, (i + 1) * FRAME_W, FRAME_H)))
        town.paste(fr, (i * FRAME_W, 0), fr)
    write_bgra32_dds(town_path, town)
    shutil.copy2(town_path, os.path.join(BASE_GFX, "province_town_strip.dds"))
    shutil.copy2(town_path, os.path.join(MOD_GFX, "province_town_infrastructure_strip.dds"))
    shutil.copy2(town_path, os.path.join(BASE_GFX, "province_town_infrastructure_strip.dds"))
    for i in range(w // FRAME_W):
        f = town.crop((i * FRAME_W, 0, (i + 1) * FRAME_W, FRAME_H))
        trans = sum(1 for p in f.getdata() if p[3] == 0)
        print(f"frame{i}: transparent={trans}/{FRAME_W * FRAME_H}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--patch-alpha":
        patch_existing_town_alpha()
        return
    lvl1 = apply_fort_alpha_mask(
        draw_level_number(
            fit_art_in_frame(downscale_art(Image.open(os.path.join(ASSETS, "city_town_level2.png")))), "1"
        )
    )
    empty = empty_frame_from_fort()  # f0 прозрачный — уровень 0 с province_bg

    strip = Image.new("RGBA", (FRAME_W * 2, FRAME_H), (0, 0, 0, 0))
    strip.paste(empty, (0, 0), empty)
    strip.paste(lvl1, (FRAME_W, 0), lvl1)

    strip.save(os.path.join(ASSETS, "province_town_strip_preview.png"))
    lvl1.save(os.path.join(ASSETS, "city_town_f1_40x32.png"))

    os.makedirs(MOD_GFX, exist_ok=True)
    out = os.path.join(MOD_GFX, "province_town_strip.dds")
    write_bgra32_dds(out, strip)
    shutil.copy2(out, os.path.join(BASE_GFX, "province_town_strip.dds"))

    infra_copy = os.path.join(MOD_GFX, "province_town_infrastructure_strip.dds")
    shutil.copy2(out, infra_copy)
    shutil.copy2(out, os.path.join(BASE_GFX, "province_town_infrastructure_strip.dds"))

    d = open(out, "rb").read()
    img_check = Image.frombytes("RGBA", strip.size, d[128:], "raw", "BGRA")
    for i in range(2):
        f = img_check.crop((i * FRAME_W, 0, (i + 1) * FRAME_W, FRAME_H))
        trans = sum(1 for p in f.getdata() if p[3] == 0)
        print(f"frame{i}: transparent={trans}/{FRAME_W * FRAME_H}")
    print("saved", out, strip.size, "2 frames, digit at", DIGIT_X, DIGIT_Y)


if __name__ == "__main__":
    main()  # или: py _build_town_strip.py --patch-alpha
