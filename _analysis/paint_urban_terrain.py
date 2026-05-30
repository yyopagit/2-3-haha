# -*- coding: utf-8 -*-
"""Paint terrain.bmp index 56 (RGB 156,139,228) for provinces with terrain = urban."""
import re
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image

MOD = Path(r"c:\Games\Vic2LV2\Victoria 2\mod\5")
MAP = MOD / "map"
HISTORY = MOD / "history" / "provinces"
URBAN_INDEX = 56
TARGET_RGB = (156, 139, 228)


def collect_urban_ids():
    ids = set()
    for f in HISTORY.rglob("*.txt"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        if "terrain = urban" not in text:
            continue
        m = re.match(r"^(\d+)\s*-", f.name)
        if m:
            ids.add(int(m.group(1)))
    return ids


def load_province_colors():
    colors = {}
    for line in (MAP / "definition.csv").read_text(encoding="latin-1").splitlines():
        if not line or line.startswith("province"):
            continue
        parts = line.split(";")
        if len(parts) < 4:
            continue
        try:
            pid = int(parts[0])
            rgb = (int(parts[1]), int(parts[2]), int(parts[3]))
        except ValueError:
            continue
        colors[pid] = rgb
    return colors


def main():
    urban_ids = collect_urban_ids()
    prov_colors = load_province_colors()
    missing = sorted(urban_ids - prov_colors.keys())
    if missing:
        print("WARNING: no definition.csv color for provinces:", missing[:20], "...")

    urban_rgbs = {prov_colors[pid] for pid in urban_ids if pid in prov_colors}
    print(f"Urban provinces: {len(urban_ids)}, colors: {len(urban_rgbs)}")

    provinces = Image.open(MAP / "provinces.bmp").convert("RGB")
    terrain = Image.open(MAP / "terrain.bmp")

    pal = terrain.getpalette()
    if pal:
        actual = tuple(pal[URBAN_INDEX * 3 : URBAN_INDEX * 3 + 3])
        print(f"Palette index {URBAN_INDEX}: {actual} (expected {TARGET_RGB})")
        if actual != TARGET_RGB:
            print("WARNING: palette mismatch — check terrain.bmp / text_56")

    if provinces.size != terrain.size:
        raise SystemExit(f"Size mismatch: provinces {provinces.size} vs terrain {terrain.size}")

    if terrain.mode != "P":
        terrain = terrain.convert("P")

    backup = MAP / f"terrain.bmp.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}_urban56"
    shutil.copy2(MAP / "terrain.bmp", backup)
    print(f"Backup: {backup}")

    terrain = terrain.copy()
    prov_px = provinces.load()
    terr_px = terrain.load()
    w, h = provinces.size
    painted_px = 0
    provinces_hit = set()

    for y in range(h):
        for x in range(w):
            if prov_px[x, y] in urban_rgbs:
                terr_px[x, y] = URBAN_INDEX
                painted_px += 1

    # count which provinces got pixels
    rgb_to_pid = {v: k for k, v in prov_colors.items()}
    for rgb in urban_rgbs:
        if rgb in rgb_to_pid:
            provinces_hit.add(rgb_to_pid[rgb])

    terrain.save(MAP / "terrain.bmp")
    print(f"Pixels painted: {painted_px}")
    print(f"Provinces with pixels on map: {len(provinces_hit)} / {len(urban_ids)}")
    not_on_map = sorted(urban_ids - provinces_hit)
    if not_on_map:
        print(f"No pixels (check provinces.bmp): {not_on_map[:30]} ... ({len(not_on_map)} total)")


if __name__ == "__main__":
    main()
