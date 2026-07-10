"""Добавить (Г) к названиям регионов, где в history есть town_infrastructure > 0."""
from __future__ import annotations

import re
from pathlib import Path

MOD = Path(r"C:\Games\Vic2LV2\Victoria 2\mod\5")
LOC = MOD / "localisation" / "a.csv"
REGION = MOD / "map" / "region.txt"
PROV_DIR = MOD / "history" / "provinces"
MARK = " (Г)"
ENC = "cp1251"


def town_provinces() -> set[int]:
    out: set[int] = set()
    for path in PROV_DIR.rglob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"town_infrastructure\s*=\s*[1-9]\d*", text):
            continue
        m = re.match(r"^(\d+)", path.name)
        if m:
            out.add(int(m.group(1)))
    return out


def regions_with_towns(towns: set[int]) -> set[str]:
    text = REGION.read_text(encoding="utf-8", errors="replace")
    keys: set[str] = set()
    for m in re.finditer(r"^([A-Z]{3}_\d+)\s*=\s*\{([^}]*)\}", text, re.M):
        ids = {int(x) for x in re.findall(r"\d+", m.group(2))}
        if ids & towns:
            keys.add(m.group(1))
    return keys


def strip_mark(name: str) -> str:
    # убрать прежние варианты маркера
    name = re.sub(r"\s*\(Г\)\s*$", "", name)
    name = re.sub(r"\s*\(G\)\s*$", "", name, flags=re.I)
    return name.rstrip()


def patch_loc(town_regions: set[str]) -> tuple[int, int, list[str]]:
    lines = LOC.read_text(encoding=ENC, errors="replace").splitlines()
    added = 0
    cleared = 0
    missing: list[str] = []
    seen: set[str] = set()
    out: list[str] = []

    for line in lines:
        if not line.strip() or ";" not in line:
            out.append(line)
            continue
        parts = line.split(";")
        key = parts[0]
        if not re.fullmatch(r"[A-Z]{3}_\d+", key):
            out.append(line)
            continue

        name = parts[1] if len(parts) > 1 else ""
        base = strip_mark(name)
        if base != name:
            cleared += 1

        if key in town_regions:
            parts[1] = base + MARK
            if not name.endswith(MARK):
                added += 1
            seen.add(key)
        else:
            parts[1] = base

        # pad columns
        while len(parts) < 8:
            parts.append("X")
        out.append(";".join(parts[:8]))

    missing = sorted(town_regions - seen)
    LOC.write_text("\n".join(out) + "\n", encoding=ENC, errors="replace")
    return added, cleared, missing


def main() -> None:
    towns = town_provinces()
    regs = regions_with_towns(towns)
    added, cleared, missing = patch_loc(regs)
    print(f"town provinces: {len(towns)}")
    print(f"town regions: {len(regs)}")
    print(f"loc updated (+Г): {added}, stripped old marks: {cleared}")
    if missing:
        print(f"MISSING loc keys ({len(missing)}): {', '.join(missing)}")
    else:
        print("all region keys found in a.csv")


if __name__ == "__main__":
    main()
