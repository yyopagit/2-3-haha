"""Добавить (Г) к названиям регионов, где в history есть terrain = urban."""
from __future__ import annotations

import re
from pathlib import Path

MOD = Path(r"C:\Games\Vic2LV2\Victoria 2\mod\5")
LOC = MOD / "localisation" / "a.csv"
REGION = MOD / "map" / "region.txt"
PROV_DIR = MOD / "history" / "provinces"
MARK = " (Г)"
ENC = "cp1251"


def urban_provinces() -> set[int]:
    out: set[int] = set()
    for path in PROV_DIR.rglob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"terrain\s*=\s*urban\b", text):
            continue
        m = re.match(r"^(\d+)", path.name)
        if m:
            out.add(int(m.group(1)))
    return out


def regions_with_urban(urban: set[int]) -> set[str]:
    text = REGION.read_text(encoding="utf-8", errors="replace")
    keys: set[str] = set()
    for m in re.finditer(r"^([A-Z]{3}_\d+)\s*=\s*\{([^}]*)\}", text, re.M):
        ids = {int(x) for x in re.findall(r"\d+", m.group(2))}
        if ids & urban:
            keys.add(m.group(1))
    return keys


def strip_mark(name: str) -> str:
    name = re.sub(r"\s*\(Г\)\s*$", "", name)
    name = re.sub(r"\s*\(G\)\s*$", "", name, flags=re.I)
    return name.rstrip()


def patch_loc(urban_regions: set[str]) -> tuple[int, int, int, list[str]]:
    raw = LOC.read_bytes()
    text = raw.decode(ENC)
    nl = "\r\n" if b"\r\n" in raw else "\n"
    lines = text.splitlines()
    added = 0
    stripped = 0
    kept = 0
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
        had_mark = base != name

        if key in urban_regions:
            parts[1] = base + MARK
            seen.add(key)
            if had_mark:
                kept += 1
            else:
                added += 1
        else:
            parts[1] = base
            if had_mark:
                stripped += 1

        while len(parts) < 8:
            parts.append("X")
        out.append(";".join(parts[:8]))

    missing = sorted(urban_regions - seen)
    LOC.write_bytes((nl.join(out) + nl).encode(ENC))
    return added, stripped, kept, missing


def main() -> None:
    urban = urban_provinces()
    regs = regions_with_urban(urban)
    added, stripped, kept, missing = patch_loc(regs)
    print(f"urban provinces: {len(urban)}")
    print(f"urban regions: {len(regs)}")
    print(f"loc + (Г): {added}")
    print(f"loc kept (Г): {kept}")
    print(f"loc stripped (Г) [town without urban]: {stripped}")
    if missing:
        print(f"MISSING loc keys ({len(missing)}): {', '.join(missing)}")
    else:
        print("all region keys found in a.csv")


if __name__ == "__main__":
    main()
