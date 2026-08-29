# -*- coding: utf-8 -*-
"""Recolor province header modifier bars to light parchment. No overlay plate."""
from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BG = ROOT / "gfx" / "interface" / "province_bg.dds"
SRC = ROOT / "_re" / "province_bg_src.dds"
PREVIEW = ROOT / "_re" / "_mod_icon_preview" / "province_bg.png"


def write_dds_bgra(img: Image.Image, path: Path):
    w, h = img.size
    rgba = np.array(img.convert("RGBA"))
    bgra = rgba[..., [2, 1, 0, 3]].tobytes()
    header = bytearray(128)
    header[0:4] = b"DDS "
    struct.pack_into("<I", header, 4, 124)
    struct.pack_into("<I", header, 8, 0x81007)
    struct.pack_into("<I", header, 12, h)
    struct.pack_into("<I", header, 16, w)
    struct.pack_into("<I", header, 20, w * h * 4)
    struct.pack_into("<I", header, 76, 32)
    struct.pack_into("<I", header, 80, 0x41)
    struct.pack_into("<I", header, 88, 32)
    struct.pack_into("<I", header, 92, 0x00FF0000)
    struct.pack_into("<I", header, 96, 0x0000FF00)
    struct.pack_into("<I", header, 100, 0x000000FF)
    struct.pack_into("<I", header, 104, 0xFF000000)
    struct.pack_into("<I", header, 108, 0x1000)
    path.write_bytes(bytes(header) + bgra)


def recolor_header_bars(arr: np.ndarray) -> np.ndarray:
    """Keep marble grain; map burgundy fill of the two header strips to cool paper."""
    rgb = arr[..., :3].astype(np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    yy = np.arange(arr.shape[0])[:, None]
    xx = np.arange(arr.shape[1])[None, :]

    lum = 0.35 * r + 0.40 * g + 0.25 * b
    gold = (r > 140) & ((r - g) < 55) & ((g - b) > 18)
    outer = (r < 24) & (g < 20) & (b < 18)
    marble = (r > g + 6) & (r > b + 2) & (g < 100) & (r < 180) & (lum < 130)
    in_bars = ((yy >= 22) & (yy <= 56) | (yy >= 63) & (yy <= 86)) & (xx >= 11) & (xx <= 390)
    mask = in_bars & (marble | ((lum < 50) & (r >= g))) & ~gold & ~outer

    t = np.clip((lum - 12.0) / 95.0, 0.0, 1.0)
    # same paper as the body of this window, not a yellow or glowing plate
    lo = np.array([176.0, 174.0, 162.0])
    hi = np.array([214.0, 212.0, 198.0])
    paper = lo + (hi - lo) * t[..., None]
    rgb[mask] = paper[mask]
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return arr


def main():
    if not SRC.exists():
        raise SystemExit("missing _re/province_bg_src.dds")
    im = Image.open(SRC).convert("RGBA")
    out = Image.fromarray(recolor_header_bars(np.array(im)), "RGBA")
    write_dds_bgra(out, BG)
    out.save(PREVIEW)
    out.crop((0, 0, 401, 120)).resize((802, 240), Image.Resampling.NEAREST).save(
        PREVIEW.parent / "province_bg_header.png"
    )
    print("rewrote", BG, out.size)


if __name__ == "__main__":
    main()
