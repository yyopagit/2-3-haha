# -*- coding: utf-8 -*-
"""Build gfx/interface/modifiers.(dds|tga): keep vanilla frames 1-20, append CHI icons."""
from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np
from collections import deque

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
VANILLA = ROOT / "_re" / "modifiers.dds"
ASSETS = ROOT / "_re" / "icon_assets"
OUT_DDS = ROOT / "gfx" / "interface" / "modifiers.dds"
OUT_TGA = ROOT / "gfx" / "interface" / "modifiers.tga"
PREVIEW = ROOT / "_re" / "_mod_icon_preview" / "new_strip.png"

CELL = 32
HIRES = 128

PAL = {
    "green": ((230, 255, 200), (92, 176, 58), (24, 52, 16)),
    "red": ((255, 210, 210), (196, 42, 46), (62, 10, 12)),
    "gold": ((255, 246, 170), (214, 168, 28), (92, 64, 8)),
    "orange": ((255, 214, 150), (226, 118, 22), (96, 44, 6)),
    "crimson": ((255, 176, 176), (176, 16, 32), (52, 4, 8)),
    "dark": ((220, 140, 140), (96, 8, 16), (28, 2, 4)),
    "blue": ((190, 230, 255), (36, 118, 204), (8, 36, 88)),
    "teal": ((180, 255, 230), (16, 158, 132), (6, 56, 48)),
    "brown": ((236, 196, 150), (164, 96, 36), (64, 32, 10)),
    "purple": ((236, 196, 255), (140, 56, 186), (52, 16, 78)),
    "slate": ((230, 234, 238), (118, 126, 136), (32, 36, 42)),
}


def shade_mask(mask: Image.Image, pal_name: str) -> Image.Image:
    hi, mid, dark = [np.array(c, dtype=np.float32) for c in PAL[pal_name]]
    h = np.array(mask, dtype=np.float32) / 255.0
    if h.max() <= 0:
        return Image.new("RGBA", mask.size, (0, 0, 0, 0))

    yy, xx = np.mgrid[0:h.shape[0], 0:h.shape[1]]
    grad = np.clip(1.15 - (xx + yy) / (h.shape[0] + h.shape[1]), 0.35, 1.0)
    blur = np.array(mask.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255.0
    gy, gx = np.gradient(blur)
    ndotl = np.clip(0.42 + (-gx * 2.4 + -gy * 3.0) + 0.22 * grad, 0.0, 1.0)
    lum = np.clip(h * (0.28 + 0.72 * ndotl), 0.0, 1.0)
    t = lum
    rgb = np.zeros(h.shape + (3,), dtype=np.float32)
    for i in range(3):
        rgb[..., i] = np.where(
            t < 0.55,
            dark[i] + (mid[i] - dark[i]) * (t / 0.55),
            mid[i] + (hi[i] - mid[i]) * ((t - 0.55) / 0.45),
        )
    spec = (ndotl ** 12) * h
    rgb = np.clip(rgb + spec[..., None] * 70.0, 0, 255)

    alpha = np.clip(h * 270.0, 0, 255)
    dil = np.array(
        mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(0.9)),
        dtype=np.float32,
    )
    fringe = np.clip(dil - alpha, 0, 255) * 0.62
    out = np.zeros(h.shape + (4,), dtype=np.uint8)
    out[..., :3] = rgb.astype(np.uint8)
    out[..., 3] = np.clip(alpha + fringe, 0, 255).astype(np.uint8)
    fringe_mask = (fringe > 10) & (alpha < 50)
    out[fringe_mask, :3] = (out[fringe_mask, :3] * 0.12).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    return img.resize((CELL, CELL), Image.Resampling.LANCZOS)


def canvas():
    im = Image.new("L", (HIRES, HIRES), 0)
    return im, ImageDraw.Draw(im)


def canvas_rgba():
    im = Image.new("RGBA", (HIRES, HIRES), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im, "RGBA")


def normalize_icon(im: Image.Image, pad=5) -> Image.Image:
    """Same visual weight as vanilla: content fills ~22px, centered."""
    a = np.array(im)[..., 3]
    ys, xs = np.where(a > 18)
    if len(xs) == 0:
        return im
    crop = im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    box = CELL - pad * 2
    scale = min(box / crop.size[0], box / crop.size[1])
    nw = max(1, int(round(crop.size[0] * scale)))
    nh = max(1, int(round(crop.size[1] * scale)))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    out.paste(crop, ((CELL - nw) // 2, (CELL - nh) // 2), crop)
    return out


def finish_rgba(im: Image.Image) -> Image.Image:
    """Downscale, even size, dark fringe."""
    arr = np.array(im)
    alpha = arr[..., 3].astype(np.float32)
    mask = Image.fromarray(alpha.astype(np.uint8), "L")
    dil = np.array(
        mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(0.9)),
        dtype=np.float32,
    )
    fringe = np.clip(dil - alpha, 0, 255) * 0.7
    out = arr.copy()
    add = fringe > 8
    out[add, 0] = (out[add, 0] * 0.15).astype(np.uint8)
    out[add, 1] = (out[add, 1] * 0.15).astype(np.uint8)
    out[add, 2] = (out[add, 2] * 0.15).astype(np.uint8)
    out[..., 3] = np.clip(alpha + fringe, 0, 255).astype(np.uint8)
    small = Image.fromarray(out, "RGBA").resize((CELL, CELL), Image.Resampling.LANCZOS)
    return normalize_icon(small)


def knockout_black(im: Image.Image) -> Image.Image:
    arr = np.array(im.convert("RGBA"))
    h, w = arr.shape[:2]
    vis = np.zeros((h, w), dtype=bool)
    q = deque([(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)])
    while q:
        y, x = q.popleft()
        if vis[y, x]:
            continue
        r, g, b, _a = arr[y, x]
        if int(r) + int(g) + int(b) > 48:
            continue
        vis[y, x] = True
        arr[y, x, 3] = 0
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and not vis[ny, nx]:
                q.append((ny, nx))
    return Image.fromarray(arr)


def add_slash(im: Image.Image) -> Image.Image:
    """Strike only over existing pixels — does not grow the silhouette."""
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).line((8, 9, 23, 22), fill=(28, 10, 8, 255), width=2)
    src = np.array(im)
    ov = np.array(overlay)
    ov[src[..., 3] < 40] = 0
    out = im.copy()
    out.alpha_composite(Image.fromarray(ov, "RGBA"))
    return out


def from_photo(path: Path, tint=(1.0, 1.0, 1.0), crack=False, knockout=True) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    if knockout:
        im = knockout_black(im)
    im = im.resize((HIRES, HIRES), Image.Resampling.LANCZOS)
    arr = np.array(im).astype(np.float32)
    arr[..., 0] *= tint[0]
    arr[..., 1] *= tint[1]
    arr[..., 2] *= tint[2]
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    im = finish_rgba(Image.fromarray(arr, "RGBA"))
    if crack:
        im = add_slash(im)
    return im


def to_vanilla_red(im: Image.Image) -> Image.Image:
    """Light-red like vanilla hammer: pink highlight, salmon body."""
    hi = np.array((255.0, 205.0, 205.0))
    mid = np.array((214.0, 96.0, 98.0))
    dark = np.array((88.0, 22.0, 24.0))
    arr = np.array(im)
    rgb = arr[..., :3].astype(np.float32)
    a = arr[..., 3]
    lum = np.clip((0.30 * rgb[..., 0] + 0.50 * rgb[..., 1] + 0.20 * rgb[..., 2]) / 255.0, 0, 1)
    t = np.clip(lum * 1.28 + 0.12, 0, 1)
    out = np.zeros_like(rgb)
    for i in range(3):
        out[..., i] = np.where(
            t < 0.50,
            dark[i] + (mid[i] - dark[i]) * (t / 0.50),
            mid[i] + (hi[i] - mid[i]) * ((t - 0.50) / 0.50),
        )
    arr[..., :3] = np.clip(out, 0, 255).astype(np.uint8)
    arr[a < 12, :3] = 0
    return Image.fromarray(arr)


def grade_toward_vanilla(im: Image.Image, t: float, protect_blue=False) -> Image.Image:
    """Blend original toward vanilla light-red. Blue water stays blue."""
    t = float(np.clip(t, 0.0, 1.0))
    if t <= 0.001:
        return im
    src = np.array(im).astype(np.float32)
    dst = np.array(to_vanilla_red(im)).astype(np.float32)
    out = src.copy()
    out[..., :3] = src[..., :3] * (1.0 - t) + dst[..., :3] * t
    if protect_blue:
        r, g, b = src[..., 0], src[..., 1], src[..., 2]
        water = (b > r + 6) & (b > g - 4) & (src[..., 3] > 20)
        tw = t * 0.10
        out[water, :3] = src[water, :3] * (1.0 - tw) + dst[water, :3] * tw
    out[..., 3] = src[..., 3]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def g_empty_bowl(severity=0):
    tints = (
        (1.00, 1.00, 1.00),
        (0.95, 0.78, 0.52),
        (0.88, 0.42, 0.32),
        (0.52, 0.24, 0.18),
    )
    return from_photo(ASSETS / "bowl.png", tints[min(severity, 3)], crack=severity >= 2)


def g_crown(severity=0):
    # Official CK3 prestige crown (already has alpha). Brighten the dark bronze so it reads at 32px.
    tints = (
        (1.55, 1.35, 0.78),
        (1.40, 0.95, 0.48),
        (1.25, 0.50, 0.36),
        (0.95, 0.30, 0.24),
        (0.52, 0.16, 0.14),
    )
    return from_photo(
        ASSETS / "ck3_prestige_01.png",
        tints[min(severity, 4)],
        crack=severity >= 3,
        knockout=False,
    )


def g_money_bag(severity=0, clean=False):
    im, d = canvas_rgba()
    sack = (168, 118, 48, 255) if not clean else (86, 150, 52, 255)
    if severity == 1:
        sack = (196, 120, 36, 255)
    if severity >= 2:
        sack = (168, 48, 36, 255)
    d.ellipse((24, 42, 104, 116), fill=sack)
    d.ellipse((44, 28, 84, 54), fill=sack)
    d.rectangle((52, 22, 76, 40), fill=(110, 72, 28, 255))
    d.ellipse((50, 66, 86, 100), fill=(236, 196, 56, 255))
    d.ellipse((58, 74, 78, 94), fill=(196, 148, 28, 255))
    if not clean and severity >= 1:
        d.ellipse((92, 96, 114, 118), fill=(236, 196, 56, 255))
    if not clean and severity >= 2:
        d.ellipse((10, 98, 32, 120), fill=(236, 196, 56, 255))
        d.line((38, 72, 72, 112), fill=(40, 16, 8, 255), width=5)
    return finish_rgba(im)


def g_flag(severity=0):
    im, d = canvas_rgba()
    cloth = [(214, 176, 36), (214, 118, 28), (188, 36, 36), (96, 16, 20)][min(severity, 3)]
    d.rectangle((20, 8, 34, 118), fill=(96, 68, 36, 255))
    d.ellipse((16, 4, 38, 20), fill=(196, 160, 48, 255))
    d.polygon([(34, 14), (118, 26), (110, 42), (34, 50)], fill=(*cloth, 255))
    d.polygon([(34, 50), (108, 42), (100, 68), (34, 76)], fill=(max(cloth[0] - 30, 0), max(cloth[1] - 30, 0), max(cloth[2] - 20, 0), 255))
    d.polygon([(68, 28), (80, 28), (64, 50), (82, 76), (66, 76), (54, 50)], fill=(0, 0, 0, 255))
    if severity >= 2:
        d.polygon([(88, 32), (118, 26), (110, 42), (86, 46)], fill=(0, 0, 0, 255))
    return finish_rgba(im)


def g_flood_house(severity=0):
    im, d = canvas_rgba()
    water_y = 88 - severity * 11
    d.polygon([(22, 56), (64, 12), (106, 56)], fill=(92, 52, 28, 255))
    d.rectangle((28, 54, 100, 110), fill=(196, 156, 92, 255))
    d.rectangle((52, 78, 76, 110), fill=(72, 44, 20, 255))
    d.rectangle((36, 64, 50, 78), fill=(48, 88, 140, 255))
    d.rectangle((84, 24, 96, 54), fill=(92, 52, 28, 255))
    water = (36, 110, 196, 230)
    if severity >= 2:
        water = (28, 72, 160, 240)
    pts = [(x, water_y + int(math.sin(x * 0.2) * 6)) for x in range(4, 124, 3)]
    d.polygon(pts + [(124, 124), (4, 124)], fill=water)
    return finish_rgba(im)


def g_skull_bones(severity=0):
    """Skull over crossed bones — piracy."""
    im, d = canvas_rgba()
    bone = [(236, 220, 180), (220, 176, 112), (196, 88, 64), (128, 40, 32)][min(severity, 3)]
    dark = (16, 12, 10, 255)
    # bones behind
    d.polygon([(8, 28), (28, 16), (120, 100), (104, 116), (8, 28)], fill=(*bone, 255))
    d.polygon([(100, 16), (120, 28), (24, 116), (8, 100), (100, 16)], fill=(*bone, 255))
    d.ellipse((4, 12, 32, 36), fill=(*bone, 255))
    d.ellipse((96, 12, 124, 36), fill=(*bone, 255))
    d.ellipse((4, 92, 32, 116), fill=(*bone, 255))
    d.ellipse((96, 92, 124, 116), fill=(*bone, 255))
    # skull
    d.ellipse((30, 14, 98, 88), fill=(*bone, 255))
    d.ellipse((40, 40, 58, 64), fill=dark)
    d.ellipse((70, 40, 88, 64), fill=dark)
    d.polygon([(58, 60), (70, 60), (64, 76)], fill=dark)
    d.rectangle((44, 80, 84, 110), fill=(*bone, 255))
    for x in (48, 60, 72):
        d.rectangle((x, 84, x + 8, 106), fill=dark)
    return finish_rgba(im)


def g_barn():
    im, d = canvas_rgba()
    d.polygon([(14, 58), (64, 14), (114, 58)], fill=(72, 140, 48, 255))
    d.rectangle((20, 56, 108, 114), fill=(168, 124, 56, 255))
    d.rectangle((52, 78, 76, 114), fill=(72, 44, 16, 255))
    d.polygon([(72, 102), (90, 40), (102, 46), (88, 106)], fill=(220, 184, 48, 255))
    return finish_rgba(im)


def g_bread():
    im, d = canvas_rgba()
    d.ellipse((14, 46, 114, 110), fill=(176, 112, 40, 255))
    d.ellipse((20, 34, 108, 88), fill=(228, 176, 72, 255))
    d.arc((28, 26, 62, 68), 200, 340, fill=(248, 220, 140, 255), width=7)
    d.arc((58, 22, 98, 66), 200, 340, fill=(248, 220, 140, 255), width=7)
    return finish_rgba(im)


def g_terraces():
    """Rice paddies with green crop + water — irrigation."""
    im, d = canvas_rgba()
    steps = [(22, 16, 106, 46), (14, 48, 114, 80), (8, 82, 120, 118)]
    for i, (x0, y0, x1, y1) in enumerate(steps):
        d.rectangle((x0, y0, x1, y1), fill=(76, 140, 48, 255))
        d.rectangle((x0 + 8, y0 + 10, x1 - 6, y1 - 5), fill=(40, 112, 188, 255))
        for x in range(x0 + 12, x1 - 10, 14):
            d.ellipse((x, y0 + 2, x + 8, y0 + 10), fill=(168, 196, 56, 255))
    return finish_rgba(im)


def g_broken_canal():
    """Broken stone aqueduct — irrigation / silted canal."""
    return from_photo(ASSETS / "broken_aqueduct.png")


def g_river_junk():
    """Junk on a river — Yangtze navigation."""
    return from_photo(ASSETS / "river_junk.png")


def g_cracked_dike():
    """Cracked earthen dike — Yellow River dikes."""
    return from_photo(ASSETS / "cracked_dike.png")


def g_patchwork():
    """Imperial core + satellite regions — not a flat quilt."""
    im, d = canvas_rgba()
    d.ellipse((40, 40, 88, 88), fill=(220, 184, 48, 255))
    d.ellipse((50, 50, 78, 78), fill=(168, 40, 36, 255))
    # four mismatched provinces stuck to the core
    d.polygon([(18, 18), (56, 28), (48, 54), (14, 48)], fill=(196, 56, 48, 255))
    d.polygon([(78, 16), (114, 22), (110, 56), (76, 48)], fill=(48, 128, 72, 255))
    d.polygon([(12, 72), (48, 78), (44, 114), (10, 104)], fill=(48, 96, 176, 255))
    d.polygon([(80, 76), (116, 70), (118, 110), (78, 114)], fill=(148, 72, 168, 255))
    return finish_rgba(im)


def g_scroll():
    """Stacked papers + red stamp — bureaucracy, no stick (looked like an anchor)."""
    im, d = canvas_rgba()
    d.rounded_rectangle((22, 18, 108, 86), radius=4, fill=(196, 176, 120, 255))
    d.rounded_rectangle((16, 30, 102, 100), radius=4, fill=(220, 204, 148, 255))
    d.rounded_rectangle((10, 42, 96, 114), radius=4, fill=(236, 220, 168, 255))
    d.line((22, 60, 80, 60), fill=(120, 88, 40, 255), width=4)
    d.line((22, 74, 76, 74), fill=(120, 88, 40, 255), width=4)
    d.line((22, 88, 70, 88), fill=(120, 88, 40, 255), width=4)
    d.ellipse((68, 86, 92, 110), fill=(196, 40, 36, 255))
    return finish_rgba(im)


def g_tax():
    im, d = canvas_rgba()
    d.rounded_rectangle((12, 50, 86, 94), radius=4, fill=(72, 120, 56, 255))
    d.rounded_rectangle((28, 36, 104, 84), radius=4, fill=(88, 148, 64, 255))
    d.rounded_rectangle((40, 22, 118, 72), radius=4, fill=(210, 64, 56, 255))
    d.ellipse((72, 34, 102, 60), fill=(236, 196, 56, 255))
    d.rectangle((14, 6, 114, 20), fill=(236, 48, 40, 255))
    return finish_rgba(im)


def g_anchor(broken=False):
    im, d = canvas_rgba()
    col = (196, 48, 48, 255) if broken else (64, 72, 88, 255)
    d.rectangle((58, 16, 70, 88), fill=col)
    d.ellipse((48, 6, 80, 38), fill=col)
    d.ellipse((54, 12, 74, 32), fill=(0, 0, 0, 255))
    d.polygon([(16, 66), (64, 88), (64, 108), (10, 80)], fill=col)
    d.polygon([(112, 66), (64, 88), (64, 108), (118, 80)], fill=col)
    if broken:
        d.line((34, 16, 100, 108), fill=(20, 8, 8, 255), width=7)
    return finish_rgba(im)


def g_harbor_flag():
    im, d = canvas_rgba()
    d.rectangle((24, 12, 38, 110), fill=(96, 68, 36, 255))
    d.polygon([(38, 14), (114, 36), (38, 56)], fill=(64, 168, 64, 255))
    d.polygon([(10, 94), (118, 94), (106, 118), (22, 118)], fill=(48, 88, 140, 255))
    return finish_rgba(im)


def g_banner(torn=True):
    im, d = canvas_rgba()
    d.rectangle((14, 12, 114, 26), fill=(96, 68, 36, 255))
    d.polygon([(32, 26), (96, 26), (88, 116), (28, 104)], fill=(204, 112, 32, 255))
    if torn:
        d.polygon([(54, 26), (74, 26), (58, 78), (78, 116), (44, 104)], fill=(0, 0, 0, 255))
    return finish_rgba(im)


def g_hourglass():
    im, d = canvas_rgba()
    d.polygon([(32, 12), (96, 12), (70, 64), (96, 116), (32, 116), (58, 64)], fill=(196, 160, 64, 255))
    d.rectangle((28, 10, 100, 24), fill=(120, 84, 32, 255))
    d.rectangle((28, 104, 100, 118), fill=(120, 84, 32, 255))
    d.polygon([(48, 24), (80, 24), (64, 56)], fill=(236, 196, 80, 255))
    d.polygon([(46, 104), (82, 104), (64, 72)], fill=(176, 128, 40, 255))
    return finish_rgba(im)


def g_torch(lit=True, hue=(236, 140, 32)):
    im, d = canvas_rgba()
    d.polygon([(48, 58), (80, 58), (74, 118), (54, 118)], fill=(120, 76, 32, 255))
    d.rectangle((44, 52, 84, 66), fill=(168, 112, 40, 255))
    if lit:
        d.ellipse((36, 8, 92, 68), fill=(*hue, 255))
        d.polygon([(44, 40), (64, 2), (84, 40)], fill=(255, 220, 80, 255))
    return finish_rgba(im)


def g_seal():
    im, d = canvas_rgba()
    d.rounded_rectangle((18, 18, 110, 110), radius=10, fill=(168, 40, 36, 255))
    d.rounded_rectangle((30, 30, 98, 98), radius=4, fill=(40, 12, 10, 255))
    d.rectangle((44, 42, 84, 52), fill=(228, 196, 80, 255))
    d.rectangle((58, 42, 70, 86), fill=(228, 196, 80, 255))
    d.rectangle((44, 78, 84, 88), fill=(228, 196, 80, 255))
    return finish_rgba(im)


def g_cannon_ship():
    im, d = canvas_rgba()
    d.polygon([(8, 78), (120, 78), (108, 110), (20, 110)], fill=(64, 72, 56, 255))
    d.rectangle((26, 56, 88, 78), fill=(86, 140, 64, 255))
    d.rectangle((72, 46, 114, 62), fill=(48, 52, 40, 255))
    d.ellipse((88, 34, 120, 68), fill=(196, 196, 72, 255))
    return finish_rgba(im)


def _ramp(make, steps, protect_blue=False):
    last = max(steps - 1, 1)
    return [grade_toward_vanilla(make(i), i / last, protect_blue) for i in range(steps)]


def build_new_frames():
    # Same picture, tone walks from the original toward vanilla light-red.
    # Water/blue stays blue — no full recolor of the flood/dam.
    frames = [
        *_ramp(g_money_bag, 3), g_money_bag(0, clean=True),
        *_ramp(g_flag, 4),
        grade_toward_vanilla(g_empty_bowl(0), 0.00),
        grade_toward_vanilla(g_empty_bowl(0), 0.33),
        grade_toward_vanilla(g_empty_bowl(2), 0.66),
        grade_toward_vanilla(g_empty_bowl(2), 1.00),
        *_ramp(g_flood_house, 4, protect_blue=True),
        grade_toward_vanilla(g_crown(0), 0.00),
        grade_toward_vanilla(g_crown(0), 0.25),
        grade_toward_vanilla(g_crown(0), 0.50),
        grade_toward_vanilla(g_crown(3), 0.75),
        grade_toward_vanilla(g_crown(3), 1.00),
        *_ramp(g_skull_bones, 4),
        g_barn(), g_bread(), g_cannon_ship(),
        g_terraces(), g_broken_canal(),
        g_patchwork(), g_scroll(), g_tax(),
        g_anchor(True), g_harbor_flag(), g_banner(True),
        g_hourglass(), g_torch(True, (236, 140, 32)), g_torch(True, (204, 40, 36)),
        g_seal(),
        g_river_junk(), g_cracked_dike(),
    ]
    assert len(frames) == 42
    return frames


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


def main():
    van = Image.open(VANILLA).convert("RGBA")
    assert van.size == (640, 32), van.size
    new_frames = build_new_frames()
    total = 20 + len(new_frames)
    strip = Image.new("RGBA", (total * CELL, CELL), (0, 0, 0, 0))
    strip.paste(van, (0, 0))
    for i, fr in enumerate(new_frames):
        strip.paste(fr, ((20 + i) * CELL, 0), fr)
    OUT_DDS.parent.mkdir(parents=True, exist_ok=True)
    write_dds_bgra(strip, OUT_DDS)
    strip.save(OUT_TGA, format="TGA")
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    strip.resize((strip.size[0] * 3, strip.size[1] * 3), Image.Resampling.NEAREST).save(PREVIEW)
    rows = (len(new_frames) + 7) // 8
    sheet = Image.new("RGBA", (8 * 140, rows * 150), (16, 16, 16, 255))
    dr = ImageDraw.Draw(sheet)
    for n in range(len(new_frames)):
        r, c = divmod(n, 8)
        fr = strip.crop(((20 + n) * 32, 0, (21 + n) * 32, 32)).resize((128, 128), Image.Resampling.NEAREST)
        sheet.paste(fr, (c * 140 + 6, r * 150 + 6), fr)
        dr.text((c * 140 + 6, r * 150 + 134), str(21 + n), fill=(220, 220, 220))
    sheet.save(PREVIEW.parent / "new_sheet.png")
    print("frames", total, "size", strip.size)


if __name__ == "__main__":
    main()
