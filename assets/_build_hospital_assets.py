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
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from _dds_tools import FRAME_H, FRAME_W, get_frame
from _patch_strips import (
    apply_fort_alpha_mask,
    downscale_art,
    empty_frame_from_fort,
    fit_art_in_frame,
    fort_f0_dim,
    naval_f0_from_bg,
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
# Позиция вставки кадра 40x32: bg_Y_paste = 358 + 35*i
# town  (i=4): 358+140=498; hospital (i=5): 358+175=533
TOWN_ICON_Y = 498
HOSPITAL_ROW_Y = 529  # сразу под городом; в git здесь начинался военный блок
ICON_Y = 533  # = 358 + 35*5
TOWN_LEVEL0_SRC = os.path.join(ASSETS, "city_town_level2.png")  # тот же арт что и strip f1 → плавный переход


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


def trim_panel_borders(panel: Image.Image, rgb_threshold: int = 28, sep_threshold: int = 10) -> Image.Image:
    """Убрать чёрные поля, разделители и тёмный хвост с краёв панели.

    Сначала находит bounding box по пикселям ярче rgb_threshold.
    Затем срезает «тёмный хвост» со всех сторон — колонки/строки, где среднее
    значение по всем пикселям ниже sep_threshold (≈чёрный разделитель).
    """
    arr = np.array(panel.convert("RGBA"))
    alpha = arr[:, :, 3]
    rgb_max = arr[:, :, :3].max(axis=2)
    mask = (alpha > 64) & (rgb_max > rgb_threshold)
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return panel
    x1, x2 = int(xs.min()), int(xs.max()) + 1
    y1, y2 = int(ys.min()), int(ys.max()) + 1

    col_avg = arr[:, :, :3].mean(axis=2).mean(axis=0)
    row_avg = arr[:, :, :3].mean(axis=2).mean(axis=1)

    # Срезаем с правого края — тёмный хвост (разделитель + виньетка)
    while x2 > x1 + 10 and col_avg[x2 - 1] < sep_threshold:
        x2 -= 1
    # Срезаем с левого края
    while x1 < x2 - 10 and col_avg[x1] < sep_threshold:
        x1 += 1
    # Срезаем снизу
    while y2 > y1 + 10 and row_avg[y2 - 1] < sep_threshold:
        y2 -= 1
    # Срезаем сверху
    while y1 < y2 - 10 and row_avg[y1] < sep_threshold:
        y1 += 1

    return panel.crop((x1, y1, x2, y2))


def find_content_regions(arr: np.ndarray, sep_threshold: int = 8) -> list[tuple[int, int]]:
    """Найти x-диапазоны контента в исходнике, разделённые чёрными полосами."""
    col_avg = arr[:, :, :3].mean(axis=2).mean(axis=0)
    W = arr.shape[1]
    in_sep = False
    seps: list[tuple[int, int]] = []
    for x in range(W):
        if col_avg[x] < sep_threshold:
            if not in_sep:
                in_sep = True
                sep_start = x
        else:
            if in_sep:
                in_sep = False
                seps.append((sep_start, x - 1))
    if in_sep:
        seps.append((sep_start, W - 1))
    regions: list[tuple[int, int]] = []
    prev_end = 0
    for s, e in seps:
        if s > prev_end:
            regions.append((prev_end, s - 1))
        prev_end = e + 1
    if prev_end < W:
        regions.append((prev_end, W - 1))
    return regions


def slice_source_levels() -> list[Image.Image]:
    """6 панелей из горизонтального исходника, извлечённых по позициям чёрных разделителей."""
    src = Image.open(SOURCE).convert("RGBA")
    arr = np.array(src)
    h = src.height
    regions = find_content_regions(arr)
    if len(regions) != 6:
        raise ValueError(f"Ожидалось 6 контент-регионов, найдено {len(regions)}: {regions}")
    levels: list[Image.Image] = []
    for i, (x1, x2) in enumerate(regions):
        raw = src.crop((x1, 0, x2 + 1, h))
        panel = trim_panel_borders(raw)
        levels.append(panel)
        panel.save(os.path.join(ASSETS, f"hospital_source_lvl{i + 1}.png"))
    return levels


def apply_strip_frame_mask(frame: Image.Image) -> Image.Image:
    """Прозрачные края кадра 40x32 — верх/низ как у форта, бока без чёрной рамки."""
    out = apply_fort_alpha_mask(frame)
    px = out.load()
    for y in range(FRAME_H):
        px[0, y] = (0, 0, 0, 0)
        px[FRAME_W - 1, y] = (0, 0, 0, 0)
    return out


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
    frame = apply_strip_frame_mask(frame)
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
    frame = apply_strip_frame_mask(fit_art_in_frame(art))
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
    if h != 615:
        # Уже расширенный фон (649+) — не дублировать строку
        return bg_git.copy()
    mil_top = HOSPITAL_ROW_Y
    out_h = h + ROW_H
    out = Image.new("RGBA", (w, out_h), (0, 0, 0, 0))
    out.paste(bg_git.crop((0, 0, w, mil_top)), (0, 0))
    out.paste(make_empty_building_row(bg_git), (0, mil_top))
    out.paste(bg_git.crop((0, mil_top, w, h)), (0, mil_top + ROW_H))
    return out


FORT_ROW_Y = 463   # строка i=3: 358+35*3
NAVAL_ROW_Y = 393  # строка i=1: 358+35*1


def update_bg_hospital_icon() -> None:
    """Расширить province_bg из git и вставить иконки нулевого уровня."""
    path = os.path.join(MOD_GFX, "province_bg.dds")
    bg_git = load_git_province_bg()
    bg = extend_province_bg_for_hospital(bg_git)

    panels = slice_source_levels()
    town_icon = town_level0_frame()
    hospital_icon = level0_from_panel(panels[0])
    fort_icon = fort_f0_dim()          # dim (50%) версия f1 → плавный переход 0→1
    naval_icon = naval_f0_from_bg()    # оригинальный маяк из base game

    bg.paste(naval_icon, (ICON_X, NAVAL_ROW_Y), naval_icon)
    bg.paste(fort_icon, (ICON_X, FORT_ROW_Y), fort_icon)
    bg.paste(town_icon, (ICON_X, TOWN_ICON_Y), town_icon)
    bg.paste(hospital_icon, (ICON_X, ICON_Y), hospital_icon)

    write_bgra32(path, bg)
    shutil.copy2(path, os.path.join(BASE_GFX, "province_bg.dds"))

    bg.crop((0, 360, 280, 580)).save(os.path.join(ASSETS, "_preview_province_bg_buildings.png"))
    town_icon.save(os.path.join(ASSETS, "town_bg_lvl0.png"))
    hospital_icon.save(os.path.join(ASSETS, "hospital_bg_lvl0.png"))
    fort_icon.save(os.path.join(ASSETS, "fort_bg_lvl0.png"))
    print(f"province_bg: {bg.size}, naval@{NAVAL_ROW_Y} fort@{FORT_ROW_Y} town@{TOWN_ICON_Y} hosp@{ICON_Y}")


def main() -> None:
    os.makedirs(MOD_GFX, exist_ok=True)
    os.makedirs(BASE_GFX, exist_ok=True)
    build_hospital_strip()
    update_bg_hospital_icon()
    print("done")


if __name__ == "__main__":
    main()
