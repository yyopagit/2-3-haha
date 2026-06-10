"""Пересохранить UI-текстуры: DXT5/DXT1 -> BGRA32 (DDS) или несжатый TGA."""
import os
import struct
import sys

import imagecodecs
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from _dds_tools import decode_dxt1, read_header, save_dds

MOD_GFX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gfx", "interface")
MOD_ROOT = os.path.dirname(os.path.dirname(__file__))
REF_BGRA = os.path.join(
    r"C:\Users\Антон\Desktop\BDSM_Mod-Victoria2-main\V2BDSM\mod\8\gfx\interface",
    "resources_small.dds",
)


def git_dds_bytes(name: str) -> bytes:
    import subprocess

    r = subprocess.run(
        ["git", "-C", MOD_ROOT, "show", f"HEAD:gfx/interface/{name}"],
        capture_output=True,
        check=True,
    )
    return r.stdout


def decode_dds_rgba(path: str) -> Image.Image:
    data = open(path, "rb").read()
    w, h, fourcc, bpp = read_header(data)
    if fourcc == b"DXT1":
        return decode_dxt1(data, w, h)
    if fourcc == b"DXT5":
        pw = -(-w // 4) * 4
        ph = -(-h // 4) * 4
        arr = imagecodecs.bcn_decode(data[128:], format=3, shape=(ph, pw, 4))
        return Image.fromarray(arr[:h, :w, :], "RGBA")
    if bpp == 32:
        return Image.frombytes("RGBA", (w, h), data[128 : 128 + w * h * 4], "raw", "BGRA")
    raise ValueError(f"unsupported {path}: {fourcc!r} bpp={bpp}")


def bgra_header_template() -> bytes:
    if os.path.exists(REF_BGRA):
        return bytes(open(REF_BGRA, "rb").read()[:128])
    town = os.path.join(MOD_GFX, "province_town_strip.dds")
    return bytes(open(town, "rb").read()[:128])


def fix_resources_small() -> None:
    src = os.path.join(MOD_GFX, "resources_small.dds")
    img = decode_dds_rgba(src)
    save_dds(src, img, "BGRA32", bgra_header_template())
    print(f"resources_small.dds -> BGRA32 {img.size}")


def fix_speed_button(name: str) -> None:
    """Кнопки +/-: ванильный DXT1 DDS (без TGA — PIL ломает загрузку в Clausewitz)."""
    import shutil

    van = os.path.join(os.path.dirname(MOD_ROOT), "gfx", "interface")
    src = os.path.join(van, f"{name}.dds")
    dst = os.path.join(MOD_GFX, f"{name}.dds")
    tga = os.path.join(MOD_GFX, f"{name}.tga")
    shutil.copy2(src, dst)
    if os.path.exists(tga):
        os.remove(tga)
    print(f"{name}: vanilla DXT1 -> {dst}")


def main() -> None:
    fix_resources_small()
    fix_speed_button("button_speedup")
    fix_speed_button("button_speeddown")
    print("Done.")


if __name__ == "__main__":
    main()
