"""
Госпитали в городе: province_hospital_strip.dds + иконка уровня 0 в province_bg.
Источник: hospital_levels_source.png (6 уровней, даунскейл как town).
"""
from __future__ import annotations

import os
import shutil
import struct
import subprocess
import sys

import imagecodecs
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from _dds_tools import FRAME_H, FRAME_W, get_frame
from _patch_strips import (
    apply_fort_alpha_mask,
    downscale_art,
    empty_frame_from_fort,
    fit_art_in_frame,
    write_bgra32,
)

DIGIT_X, DIGIT_Y = 28, 15

ASSETS = os.path.dirname(__file__)
MOD = os.path.dirname(ASSETS)
MOD_GFX = os.path.join(MOD, "gfx", "interface")
BASE_GFX = os.path.join(os.path.dirname(MOD), "gfx", "interface")
SOURCE = os.path.join(ASSETS, "hospital_levels_source.png")

ICON_X = 23
ROW_H = 34  # высота строки здания в province_bg (между разделителями)
TOWN_ICON_Y = 496
HOSPITAL_ROW_Y = 529  # сразу под городом; в git здесь начинался военный блок
ICON_Y = HOSPITAL_ROW_Y + 1  # как у остальных: row_y + 1
TOWN_LEVEL0_SRC = os.path.join(ASSETS, "city_town_level1.png")


def load_dds_rgba_bytes(data: bytes) -> Image.Image:
    w = struct.unpack_from("<I", data, 16)[0]
    h = struct.unpack_from("<I", data, 12)[0]
    bpp = struct.unpack_from("<I", data, 88)[0]
    if bpp == 32:
        return Image.frombytes("RGBA", (w, h), data[128:], "raw", "BGRA")
    pw = -(-w // 4) * 4
    ph = -(-h // 4) * 4
    fmt = 1 if data[84:88] == b"DXT1" else 3
    arr = imagecodecs.bcn_decode(data[128:], format=fmt, shape=(ph, pw, 4))
    return Image.fromarray(arr[:h, :w, :], "RGBA")


def slice_source_levels() -> list[Image.Image]:
    """6 панелей из горизонтального исходника."""
    src = Image.open(SOURCE).convert("RGBA")
    w, h = src.size
    panel_w = w // 6
    levels: list[Image.Image] = []
    for i in range(6):
        panel = src.crop((i * panel_w, 0, (i + 1) * panel_w, h))
        levels.append(panel)
        panel.save(os.path.join(ASSETS, f"hospital_source_lvl{i + 1}.png"))
    return levels


def draw_digit(frame: Image.Image, digit: str) -> Image.Image:
    """Цифра без erase_old_number — иначе копируется кусок здания под цифру."""
    out = frame.copy()
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/timesbd.ttf", 14)
    except OSError:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 14)
        except OSError:
            font = ImageFont.load_default()
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        draw.text((DIGIT_X + dx, DIGIT_Y + dy), digit, fill=(0, 0, 0, 255), font=font)
    draw.text((DIGIT_X, DIGIT_Y), digit, fill=(255, 255, 255, 255), font=font)
    return out


def panel_to_frame(panel: Image.Image, digit: str | None) -> Image.Image:
    art = downscale_art(panel)
    art = ImageEnhance.Color(art).enhance(1.12)
    art = ImageEnhance.Contrast(art).enhance(1.06)
    frame = fit_art_in_frame(art)
    frame = apply_fort_alpha_mask(frame)
    if digit is not None:
        frame = draw_digit(frame, digit)
    return frame


def level0_from_panel(panel: Image.Image) -> Image.Image:
    """Уровень 0 на фоне — тот же пайплайн и позиция (2,4), что у уровня 1 в стрипе."""
    return panel_to_frame(panel, "0")


def town_level0_frame() -> Image.Image:
    """Город ур.0 на province_bg — как town_strip f1, но city_town_level1 и цифра 0."""
    if not os.path.exists(TOWN_LEVEL0_SRC):
        raise FileNotFoundError(TOWN_LEVEL0_SRC)
    art = downscale_art(Image.open(TOWN_LEVEL0_SRC).convert("RGBA"))
    frame = apply_fort_alpha_mask(fit_art_in_frame(art))
    return draw_digit(frame, "0")


def build_hospital_strip() -> None:
    if not os.path.exists(SOURCE):
        raise FileNotFoundError(f"Нет исходника: {SOURCE}")

    panels = slice_source_levels()
    empty = empty_frame_from_fort()
    frames = [empty]
    for i, panel in enumerate(panels, start=1):
        frames.append(panel_to_frame(panel, str(i)))

    strip = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * FRAME_W, 0), fr)

    out = os.path.join(MOD_GFX, "province_hospital_strip.dds")
    os.makedirs(MOD_GFX, exist_ok=True)
    write_bgra32(out, strip)
    shutil.copy2(out, os.path.join(BASE_GFX, "province_hospital_strip.dds"))

    strip.save(os.path.join(ASSETS, "province_hospital_strip_preview.png"))
    for i in range(7):
        get_frame(strip, i).save(os.path.join(ASSETS, f"hospital_f{i}.png"))
    print(f"province_hospital_strip.dds: {strip.size}, 7 frames")


def load_git_province_bg() -> Image.Image:
    """Чистый province_bg из git (до кривой вставки госпиталя)."""
    mod_root = MOD
    data = subprocess.run(
        ["git", "-C", mod_root, "show", "HEAD:gfx/interface/province_bg.dds"],
        capture_output=True,
        check=True,
    ).stdout
    return load_dds_rgba_bytes(data).convert("RGBA")


def make_empty_building_row(bg: Image.Image, template_row_y: int = 495) -> Image.Image:
    """Фон строки здания без иконки — копия town-ряда с пустым слотом 40x32."""
    row = bg.crop((0, template_row_y, bg.width, template_row_y + ROW_H)).copy()
    slot_fill = row.crop((ICON_X + FRAME_W, 0, ICON_X + FRAME_W + FRAME_W, ROW_H))
    slot_fill = slot_fill.resize((FRAME_W, ROW_H), Image.Resampling.NEAREST)
    row.paste(slot_fill, (ICON_X, 0))
    return row


def extend_province_bg_for_hospital(bg_git: Image.Image) -> Image.Image:
    """Вставить строку госпиталя между городом и военным блоком (+34 px)."""
    w, h = bg_git.size
    mil_top = HOSPITAL_ROW_Y
    out_h = h + ROW_H
    out = Image.new("RGBA", (w, out_h), (0, 0, 0, 0))
    out.paste(bg_git.crop((0, 0, w, mil_top)), (0, 0))
    out.paste(make_empty_building_row(bg_git), (0, mil_top))
    out.paste(bg_git.crop((0, mil_top, w, h)), (0, mil_top + ROW_H))
    return out


def update_bg_hospital_icon() -> None:
    """Расширить province_bg из git и вставить иконку госпиталя в правильную строку."""
    path = os.path.join(MOD_GFX, "province_bg.dds")
    bg_git = load_git_province_bg()
    bg = extend_province_bg_for_hospital(bg_git)

    panels = slice_source_levels()
    town_icon = town_level0_frame()
    hospital_icon = level0_from_panel(panels[0])
    bg.paste(town_icon, (ICON_X, TOWN_ICON_Y), town_icon)
    bg.paste(hospital_icon, (ICON_X, ICON_Y), hospital_icon)

    write_bgra32(path, bg)
    shutil.copy2(path, os.path.join(BASE_GFX, "province_bg.dds"))

    bg.crop((0, 480, 280, 600)).save(os.path.join(ASSETS, "_preview_province_bg_hospital.png"))
    town_icon.save(os.path.join(ASSETS, "town_bg_lvl0.png"))
    hospital_icon.save(os.path.join(ASSETS, "hospital_bg_lvl0.png"))
    print(f"province_bg: {bg.size}, town @ ({ICON_X},{TOWN_ICON_Y}), hospital @ ({ICON_X},{ICON_Y})")


def main() -> None:
    os.makedirs(MOD_GFX, exist_ok=True)
    os.makedirs(BASE_GFX, exist_ok=True)
    build_hospital_strip()
    update_bg_hospital_icon()
    print("done")


if __name__ == "__main__":
    main()
