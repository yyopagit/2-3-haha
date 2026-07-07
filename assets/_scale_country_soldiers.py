#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multiply soldiers pop size for selected countries in all pop start dates."""
import re
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent
PROV_DIR = MOD / "history" / "provinces"
POPS_DIR = MOD / "history" / "pops"

MULTIPLIERS = {
    "PRU": 1.3,
    "AUS": 1.5,
    "POR": 2.0,
    "NET": 3.0,
    "SWE": 1.4,
    "RUS": 1.5,
    "TUR": 1.8,
    "SPA": 1.5,
    "ARA": 1.5,
    "NEJ": 1.5,
    "OMA": 1.5,
    "YEM": 1.5,
    "ABU": 1.5,
    "HDJ": 1.5,
}

OWNER_RE = re.compile(r"^owner\s*=\s*(\w+)", re.MULTILINE)
PROVINCE_RE = re.compile(r"(?m)^(\d+)\s*=\s*\{")
SOLDIERS_BLOCK_RE = re.compile(
    r"(?ms)(\tsoldiers\s*=\s*\{.*?\n\t\tsize\s*=\s*)(\d+(?:\.\d+)?)"
)


def build_owner_map() -> dict[str, str]:
    owners: dict[str, str] = {}
    for fp in PROV_DIR.rglob("*.txt"):
        text = fp.read_text(encoding="cp1251", errors="replace")
        m = OWNER_RE.search(text)
        if not m:
            continue
        prov_id = fp.stem.split(" - ", 1)[0].strip()
        owners[prov_id] = m.group(1)
    return owners


def province_ranges(text: str) -> list[tuple[str, int, int]]:
    matches = list(PROVINCE_RE.finditer(text))
    ranges: list[tuple[str, int, int]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        ranges.append((m.group(1), start, end))
    return ranges


def scale_soldiers_in_file(
    fp: Path, owners: dict[str, str], multipliers: dict[str, float] | None = None
) -> tuple[int, int]:
    if multipliers is None:
        multipliers = MULTIPLIERS
    text = fp.read_text(encoding="cp1251", errors="replace")
    original = text
    ranges = province_ranges(text)
    if not ranges:
        return 0, 0

    # Process from end to keep offsets valid
    changed_blocks = 0
    for prov_id, start, end in reversed(ranges):
        tag = owners.get(prov_id)
        if tag not in multipliers:
            continue
        chunk = text[start:end]
        mult = multipliers[tag]

        def repl(match: re.Match[str]) -> str:
            nonlocal changed_blocks
            prefix, num = match.group(1), match.group(2)
            if "." in num:
                new_val = round(float(num) * mult, 2)
                if new_val.is_integer():
                    new_num = str(int(new_val))
                else:
                    new_num = str(new_val)
            else:
                new_num = str(int(round(int(num) * mult)))
            changed_blocks += 1
            return f"{prefix}{new_num}"

        new_chunk = SOLDIERS_BLOCK_RE.sub(repl, chunk)
        if new_chunk != chunk:
            text = text[:start] + new_chunk + text[end:]

    if text != original:
        fp.write_text(text, encoding="cp1251", errors="replace")
    return changed_blocks, sum(1 for pid, _, _ in ranges if owners.get(pid) in multipliers)


def main() -> None:
    import sys

    active = MULTIPLIERS
    if len(sys.argv) > 1:
        only = {tag.upper() for tag in sys.argv[1:]}
        active = {k: v for k, v in MULTIPLIERS.items() if k in only}
        if not active:
            raise SystemExit(f"No matching tags in {sorted(MULTIPLIERS)}")

    owners = build_owner_map()
    print("Province owners loaded:", len(owners))
    for tag in active:
        count = sum(1 for o in owners.values() if o == tag)
        print(f"  {tag}: {count} provinces x{active[tag]}")

    total_blocks = 0
    total_files = 0
    for date_dir in sorted(POPS_DIR.glob("1836.1.*")):
        file_blocks = 0
        file_count = 0
        for fp in sorted(date_dir.glob("*.txt")):
            blocks, _ = scale_soldiers_in_file(fp, owners, active)
            if blocks:
                file_count += 1
                file_blocks += blocks
        print(f"{date_dir.name}: {file_blocks} soldier blocks in {file_count} files")
        total_blocks += file_blocks
        total_files += file_count

    print(f"TOTAL: {total_blocks} soldier blocks updated across {total_files} file-date pairs")


if __name__ == "__main__":
    main()
