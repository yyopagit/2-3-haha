"""
province_bg: нулевые уровни (как mod8, без электричества) + town/fort/infra/naval/selector.
town_strip: f0 пустой, f1 = только уровень 1 (бывший последний кадр).
"""
import os
import shutil
import struct
import sys

import imagecodecs
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from _dds_tools import FRAME_H, FRAME_W, get_frame, load_dds, save_dds, set_frame

ASSETS = os.path.dirname(__file__)
MOD5_GFX = r"C:\Games\Vic2LV2\Victoria 2\mod\5\gfx\interface"
BASE_GFX = r"C:\Games\Vic2LV2\Victoria 2\gfx\interface"
MOD8_GFX = r"C:\Users\Антон\Desktop\BDSM_Mod-Victoria2-main\V2BDSM\mod\8\gfx\interface"

# Позиции 40x32 в province_bg mod5 (масштаб от mod8, порядок GUI: town..selector)
BG_SLOTS = {
    "town": (22, 373),
    "fort": (22, 406),
    "infra": (22, 439),
    "naval": (20, 568),
    "selector": (69, 563),
}

# Убрать лишние слоты mod8 (электричество, ферма, шахта) на масштабированном фоне
CLEAR_SLOTS = [(22, 472), (22, 505), (22, 538)]

STRIPS_FROM_MOD8 = [
    "province_fort_strip.dds",
    "province_infra_strip.dds",
    "province_navalbase_strip.dds",
]

BAK_DDS = {
    "town": "province_fort_strip.dds.bak_frame0",  # луг «0» — отдельного town bak нет
    "fort": "province_fort_strip.dds.bak_frame0",
    "infra": "province_infra_strip.dds.bak_frame0",
    "naval": "province_navalbase_strip.dds.bak_frame0",
    "selector": "province_selector_strip.dds.bak_frame0",
}


def load_bak_frame0(name: str) -> Image.Image:
    path = os.path.join(MOD5_GFX, BAK_DDS[name])
    if not os.path.exists(path):
        path = os.path.join(MOD5_GFX, BAK_DDS[name].replace(".bak_frame0", ""))
    img, _, _ = load_dds(path)
    return get_frame(img, 0)


def load_dds_rgba(path: str) -> Image.Image:
    data = open(path, "rb").read()
    w, h = struct.unpack_from("<I", data, 16)[0], struct.unpack_from("<I", data, 12)[0]
    return Image.frombytes("RGBA", (w, h), imagecodecs.dds_decode(data))


def save_bgra32_dds(path: str, img: Image.Image) -> None:
    """32bpp BGRA — без DXT, иначе иконки 40x32 превращаются в кляксу."""
    w, h = img.size
    header = bytearray(128)
    header[0:4] = b"DDS "
    struct.pack_into("<I", header, 4, 124)
    struct.pack_into("<I", header, 12, h)
    struct.pack_into("<I", header, 16, w)
    struct.pack_into("<I", header, 20, w * 4)
    struct.pack_into("<I", header, 76, 32)
    struct.pack_into("<I", header, 80, 0x41)
    struct.pack_into("<I", header, 88, 32)
    struct.pack_into("<I", header, 92, 0x00FF0000)
    struct.pack_into("<I", header, 96, 0x0000FF00)
    struct.pack_into("<I", header, 100, 0x000000FF)
    struct.pack_into("<I", header, 104, 0xFF000000)
    struct.pack_into("<I", header, 108, 0x1000)
    with open(path, "wb") as f:
        f.write(header)
        f.write(img.convert("RGBA").tobytes("raw", "BGRA"))


def empty_frame_from_fort() -> Image.Image:
    fort_img, _, _ = load_dds(os.path.join(MOD8_GFX, "province_fort_strip.dds"))
    return get_frame(fort_img, 0)


def apply_fort_alpha_mask(frame: Image.Image) -> Image.Image:
    out = frame.convert("RGBA")
    px = out.load()
    for x in range(FRAME_W):
        px[x, 0] = (0, 0, 0, 0)
        px[x, FRAME_H - 1] = (0, 0, 0, 0)
    return out


def patch_strip_f0_transparent(strip_path: str, frames: int) -> None:
    img, fmt, header = load_dds(strip_path)
    empty = empty_frame_from_fort()
    set_frame(img, 0, empty)
    save_dds(strip_path, img, fmt, header)


def build_province_bg() -> None:
    bg = load_dds_rgba(os.path.join(MOD5_GFX, "province_bg.dds"))
    panel = bg.crop((22, 330, 62, 362))  # пустая панель для заливки

    for x, y in CLEAR_SLOTS:
        bg.paste(panel, (x, y))

    for key, (x, y) in BG_SLOTS.items():
        tile = load_bak_frame0(key).resize((FRAME_W, FRAME_H), Image.Resampling.NEAREST)
        bg.paste(tile, (x, y), tile)

    out = os.path.join(MOD5_GFX, "province_bg.dds")
    save_bgra32_dds(out, bg)
    shutil.copy2(out, os.path.join(BASE_GFX, "province_bg.dds"))
    print("province_bg.dds", bg.size, "32bpp BGRA")


def sync_strips_from_mod8() -> None:
    empty = empty_frame_from_fort()
    for name in STRIPS_FROM_MOD8:
        src = os.path.join(MOD8_GFX, name)
        for folder in (MOD5_GFX, BASE_GFX):
            dst = os.path.join(folder, name)
            shutil.copy2(src, dst)
            patch_strip_f0_transparent(dst, 8)
            print("strip", name, "->", dst)

    for name, frames in [
        ("province_selector_strip.dds", 2),
    ]:
        for folder in (MOD5_GFX, BASE_GFX):
            path = os.path.join(folder, name)
            if os.path.exists(path):
                patch_strip_f0_transparent(path, frames)


def build_town_strip() -> None:
    town_path = os.path.join(MOD5_GFX, "province_town_strip.dds")
    data = open(town_path, "rb").read()
    w, h = struct.unpack_from("<I", data, 16)[0], struct.unpack_from("<I", data, 12)[0]
    cur = Image.frombytes("RGBA", (w, h), data[128:], "raw", "BGRA")

    # Последний контентный кадр = уровень 1 (цифра «1»)
    level1 = apply_fort_alpha_mask(get_frame(cur, w // FRAME_W - 1))
    empty = empty_frame_from_fort()

    strip = Image.new("RGBA", (FRAME_W * 2, FRAME_H), (0, 0, 0, 0))
    strip.paste(empty, (0, 0), empty)
    strip.paste(level1, (FRAME_W, 0), level1)

    fort_ref = os.path.join(MOD8_GFX, "province_fort_strip.dds")
    header = bytearray(open(fort_ref, "rb").read()[:128])
    struct.pack_into("<I", header, 12, FRAME_H)
    struct.pack_into("<I", header, 16, FRAME_W * 2)
    struct.pack_into("<I", header, 20, FRAME_W * 2 * 4)
    out = os.path.join(MOD5_GFX, "province_town_strip.dds")
    with open(out, "wb") as f:
        f.write(header)
        f.write(strip.tobytes("raw", "BGRA"))

    targets = [
        os.path.join(BASE_GFX, "province_town_strip.dds"),
        os.path.join(MOD5_GFX, "province_town_infrastructure_strip.dds"),
        os.path.join(BASE_GFX, "province_town_infrastructure_strip.dds"),
    ]
    for dst in targets:
        if os.path.abspath(dst) != os.path.abspath(out):
            shutil.copy2(out, dst)

    strip.save(os.path.join(ASSETS, "province_town_strip_final.png"))
    print("province_town_strip.dds 2 frames: empty + level1")


def main():
    os.makedirs(MOD5_GFX, exist_ok=True)
    sync_strips_from_mod8()
    build_province_bg()
    build_town_strip()
    print("done")


if __name__ == "__main__":
    main()
