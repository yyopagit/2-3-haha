# -*- coding: utf-8 -*-
"""Transfer 35% population from ENG South Africa to Ashanti, Yauri, Togo."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

MOD = Path(__file__).resolve().parent
POPS_DIR = MOD / "history" / "pops"
FRACTION = 0.35

SOURCE_PROVINCES = {
    2087, 2088, 2089, 2090, 2091,
    2092, 2093, 2558, 2096, 2097, 2098, 2099, 2100, 2104,
}

TARGET_BY_FILE: dict[str, set[int]] = {
    "Ghana.txt": {1910, 1911, 1912, 1913},
    "Benin.txt": {1919, 1920, 1921, 1922},
    "Togo.txt": {1914, 1917, 1918},
}

TARGET_PROVINCES = sorted({p for ids in TARGET_BY_FILE.values() for p in ids})
PROV_TO_FILE = {p: fn for fn, ids in TARGET_BY_FILE.items() for p in ids}


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("".join(lines), encoding="utf-8")


def find_province_range(lines: list[str], prov_id: int) -> tuple[int, int] | None:
    pat = re.compile(rf"^\s*{prov_id}\s*=\s*\{{\s*$")
    for i, line in enumerate(lines):
        if pat.match(line.rstrip("\r\n")):
            depth = 1
            j = i + 1
            while j < len(lines) and depth:
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
            return i, j
    return None


def parse_pop_blocks(lines: list[str], base: int) -> list[dict]:
    blocks: list[dict] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^\s*(\w+)\s*=\s*\{\s*$", lines[i])
        if not m:
            i += 1
            continue
        poptype = m.group(1)
        depth = 1
        j = i + 1
        culture = religion = None
        size = 0
        size_rel = None
        while j < len(lines) and depth:
            line = lines[j]
            cm = re.search(r"culture\s*=\s*(\w+)", line)
            rm = re.search(r"religion\s*=\s*(\w+)", line)
            sm = re.search(r"size\s*=\s*(\d+)", line)
            if cm:
                culture = cm.group(1)
            if rm:
                religion = rm.group(1)
            if sm:
                size = int(sm.group(1))
                size_rel = j
            depth += line.count("{") - line.count("}")
            j += 1
        if culture and religion and size_rel is not None:
            blocks.append(
                {
                    "poptype": poptype,
                    "culture": culture,
                    "religion": religion,
                    "size": size,
                    "size_line": base + size_rel,
                }
            )
        i = j
    return blocks


def pop_key(block: dict) -> tuple[str, str, str]:
    return block["poptype"], block["culture"], block["religion"]


def apply_transfer_to_sources(sa_lines: list[str]) -> dict[tuple[str, str, str], int]:
    removed_total: dict[tuple[str, str, str], int] = defaultdict(int)
    for prov_id in sorted(SOURCE_PROVINCES):
        rng = find_province_range(sa_lines, prov_id)
        if not rng:
            print(f"  WARN: province {prov_id} not in South Africa.txt")
            continue
        start, end = rng
        blocks = parse_pop_blocks(sa_lines[start:end], start)
        for block in blocks:
            old = block["size"]
            if old <= 0:
                continue
            removed = int(old * FRACTION)
            if removed <= 0 and old > 1:
                removed = 1
            if old > 1:
                removed = min(removed, old - 1)
            else:
                removed = 0
            new_size = old - removed
            if removed:
                removed_total[pop_key(block)] += removed
            sa_lines[block["size_line"]] = re.sub(
                r"size\s*=\s*\d+",
                f"size = {new_size}",
                sa_lines[block["size_line"]],
            )
    return removed_total


def find_matching_size_line(prov_lines: list[str], base: int, key: tuple[str, str, str]) -> int | None:
    poptype, culture, religion = key
    i = 0
    while i < len(prov_lines):
        if re.match(rf"^\s*{poptype}\s*=\s*\{{\s*$", prov_lines[i]):
            depth = 1
            j = i + 1
            has_c = has_r = False
            size_rel = None
            while j < len(prov_lines) and depth:
                line = prov_lines[j]
                if re.search(rf"culture\s*=\s*{culture}\b", line):
                    has_c = True
                if re.search(rf"religion\s*=\s*{religion}\b", line):
                    has_r = True
                if "size =" in line:
                    size_rel = j
                depth += line.count("{") - line.count("}")
                j += 1
            if has_c and has_r and size_rel is not None:
                return base + size_rel
        i += 1
    return None


def append_pop_block(lines: list[str], prov_end: int, key: tuple[str, str, str], amount: int) -> None:
    poptype, culture, religion = key
    insert_at = prov_end - 1
    block = [
        f"\n\t{poptype} = {{\n",
        f"\t\tculture = {culture}\n",
        f"\t\treligion = {religion}\n",
        f"\t\tsize = {amount}\n",
        "\t}\n",
    ]
    lines[insert_at:insert_at] = block


def distribute_to_targets(date_dir: Path, removed_total: dict[tuple[str, str, str], int]) -> None:
    n_targets = len(TARGET_PROVINCES)
    per_target: dict[tuple[str, str, str], list[int]] = {}
    for key, total in removed_total.items():
        base_share = total // n_targets
        rem = total % n_targets
        per_target[key] = [base_share + (1 if i < rem else 0) for i in range(n_targets)]

    file_cache: dict[str, list[str]] = {fn: read_lines(date_dir / fn) for fn in TARGET_BY_FILE}

    for idx, prov_id in enumerate(TARGET_PROVINCES):
        fn = PROV_TO_FILE[prov_id]
        lines = file_cache[fn]
        rng = find_province_range(lines, prov_id)
        if not rng:
            print(f"  WARN: target {prov_id} missing in {fn}")
            continue
        start, end = rng
        for key, shares in per_target.items():
            add = shares[idx]
            if add <= 0:
                continue
            size_line = find_matching_size_line(lines[start:end], start, key)
            if size_line is not None:
                lines[size_line] = re.sub(
                    r"size\s*=\s*(\d+)",
                    lambda m: f"size = {int(m.group(1)) + add}",
                    lines[size_line],
                )
            else:
                append_pop_block(lines, end, key, add)
                end += 5
        file_cache[fn] = lines

    for fn, lines in file_cache.items():
        write_lines(date_dir / fn, lines)


def process_date(date_name: str) -> None:
    date_dir = POPS_DIR / date_name
    sa_path = date_dir / "South Africa.txt"
    if not sa_path.exists():
        print(f"Skip {date_name}: no South Africa.txt")
        return
    sa_lines = read_lines(sa_path)
    removed = apply_transfer_to_sources(sa_lines)
    write_lines(sa_path, sa_lines)
    total_removed = sum(removed.values())
    distribute_to_targets(date_dir, removed)
    print(f"{date_name}: transferred {total_removed} pops (35% from {len(SOURCE_PROVINCES)} ENG SA provinces)")


def main() -> None:
    for date_dir in sorted(POPS_DIR.iterdir()):
        if date_dir.is_dir() and date_dir.name.startswith("1836."):
            process_date(date_dir.name)


if __name__ == "__main__":
    main()
