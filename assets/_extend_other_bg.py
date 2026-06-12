"""Расширить province_other_bg.dds — закрыть строку больницы на province_bg у чужих провинций."""
import os
import shutil
import struct

from PIL import Image

MOD = os.path.dirname(os.path.dirname(__file__))
MOD_GFX = os.path.join(MOD, "gfx", "interface")
BASE_GFX = os.path.join(os.path.dirname(MOD), "gfx", "interface")
ASSETS = os.path.dirname(__file__)

ICON_X = 23
FRAME_W, FRAME_H = 40, 32
ROW_H = 34
EXTRA_TOP_Y = 498  # town row в province_bg
EXTRA_H = 68       # town + hospital rows


def load_bgra(path: str) -> Image.Image:
    data = open(path, "rb").read()
    w = struct.unpack_from("<I", data, 16)[0]
    h = struct.unpack_from("<I", data, 12)[0]
    return Image.frombytes("RGBA", (w, h), data[128:], "raw", "BGRA")


def save_bgra(path: str, img: Image.Image, template_path: str) -> None:
    hdr = bytearray(open(template_path, "rb").read()[:128])
    w, h = img.size
    struct.pack_into("<I", hdr, 12, h)
    struct.pack_into("<I", hdr, 16, w)
    struct.pack_into("<I", hdr, 20, w * 4)
    with open(path, "wb") as f:
        f.write(hdr)
        f.write(img.convert("RGBA").tobytes("raw", "BGRA"))


def clear_icon_slot(row: Image.Image, row_y_in_bg: int, bg: Image.Image) -> None:
    """Заменить слот иконки пустым фоном строки (без домика больницы)."""
    slot_fill = bg.crop((ICON_X + FRAME_W, row_y_in_bg, ICON_X + FRAME_W + FRAME_W, row_y_in_bg + ROW_H))
    slot_fill = slot_fill.resize((FRAME_W, ROW_H), Image.Resampling.NEAREST)
    row.paste(slot_fill, (ICON_X, 1))


def build_extended_other_bg() -> Image.Image:
    other_path = os.path.join(MOD_GFX, "province_other_bg.dds")
    bg_path = os.path.join(MOD_GFX, "province_bg.dds")
    cur = load_bgra(other_path)
    bg = load_bgra(bg_path)

    ext = bg.crop((0, EXTRA_TOP_Y, cur.width, EXTRA_TOP_Y + EXTRA_H)).copy()
    for row_y in (498, 529):
        local = row_y - EXTRA_TOP_Y
        row = ext.crop((0, local, ext.width, local + ROW_H))
        clear_icon_slot(row, row_y, bg)
        ext.paste(row, (0, local))

    out = Image.new("RGBA", (cur.width, cur.height + EXTRA_H), (0, 0, 0, 0))
    out.paste(cur, (0, 0))
    out.paste(ext, (0, cur.height))
    return out


def main() -> None:
    out = build_extended_other_bg()
    path = os.path.join(MOD_GFX, "province_other_bg.dds")
    save_bgra(path, out, path)
    shutil.copy2(path, os.path.join(BASE_GFX, "province_other_bg.dds"))
    out.save(os.path.join(ASSETS, "province_other_bg_preview.png"))
    print(f"province_other_bg.dds: {out.size}")


if __name__ == "__main__":
    main()
