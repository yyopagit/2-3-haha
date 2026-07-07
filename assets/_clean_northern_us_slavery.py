#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove slaves from free (non-CSA) US states and CSA core from northern border states."""
import re
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent
PROV_DIR = MOD / "history" / "provinces" / "North America"
POPS_DIR = MOD / "history" / "pops"

# Border / mid-Atlantic states that should stay Union (also listed in USA civil war event)
NORTHERN_BORDER_CSA_CORE = {"217", "218", "219", "220", "221", "222"}

PROVINCE_RE = re.compile(r"(?m)^(\d+)\s*=\s*\{")
SLAVES_BLOCK_RE = re.compile(r"(?ms)\n\tslaves\s*=\s*\{.*?\n\t\}")


def load_usa_province_info() -> tuple[set[str], set[str]]:
    free_states: set[str] = set()
    csa_core: set[str] = set()
    for fp in PROV_DIR.glob("*.txt"):
        pid = fp.stem.split(" - ", 1)[0].strip()
        text = fp.read_text(encoding="cp1251", errors="replace")
        if "owner = USA" not in text:
            continue
        if "add_core = CSA" in text:
            csa_core.add(pid)
        else:
            free_states.add(pid)
    return free_states, csa_core


def province_ranges(text: str) -> list[tuple[str, int, int]]:
    matches = list(PROVINCE_RE.finditer(text))
    ranges: list[tuple[str, int, int]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        ranges.append((m.group(1), start, end))
    return ranges


def remove_slaves_from_pop_file(fp: Path, free_states: set[str]) -> int:
    text = fp.read_text(encoding="cp1251", errors="replace")
    original = text
    removed = 0
    for pid, start, end in reversed(province_ranges(text)):
        if pid not in free_states:
            continue
        chunk = text[start:end]
        new_chunk, n = SLAVES_BLOCK_RE.subn("", chunk)
        if n:
            removed += n
            text = text[:start] + new_chunk + text[end:]
    if text != original:
        fp.write_text(text, encoding="cp1251", errors="replace")
    return removed


def clean_province_files(free_states: set[str]) -> tuple[int, int]:
    slave_flag_removed = 0
    csa_core_removed = 0
    for fp in PROV_DIR.glob("*.txt"):
        pid = fp.stem.split(" - ", 1)[0].strip()
        text = fp.read_text(encoding="cp1251", errors="replace")
        if "owner = USA" not in text:
            continue
        new_text = text
        if pid in free_states:
            new2 = re.sub(r"(?m)^is_slave\s*=\s*yes\s*\r?\n", "", new_text)
            if new2 != new_text:
                slave_flag_removed += 1
                new_text = new2
        if pid in NORTHERN_BORDER_CSA_CORE:
            new2 = re.sub(r"(?m)^add_core\s*=\s*CSA\s*\r?\n", "", new_text)
            if new2 != new_text:
                csa_core_removed += 1
                new_text = new2
        if new_text != text:
            fp.write_text(new_text, encoding="cp1251", errors="replace")
    return slave_flag_removed, csa_core_removed


def main() -> None:
    free_states, csa_core = load_usa_province_info()
    print(f"USA free states (no CSA core): {len(free_states)}")
    print(f"USA CSA-core states: {len(csa_core)}")
    print(f"Northern border CSA cores to remove: {sorted(NORTHERN_BORDER_CSA_CORE)}")

    total_slave_blocks = 0
    for date_dir in sorted(POPS_DIR.glob("1836.1.*")):
        fp = date_dir / "United States.txt"
        if not fp.exists():
            continue
        n = remove_slaves_from_pop_file(fp, free_states)
        print(f"{date_dir.name}/United States.txt: removed {n} slave blocks")
        total_slave_blocks += n

    slave_flags, csa_removed = clean_province_files(free_states)
    print(f"Province is_slave flags removed: {slave_flags}")
    print(f"Province CSA cores removed (border north): {csa_removed}")
    print(f"TOTAL slave blocks removed: {total_slave_blocks}")


if __name__ == "__main__":
    main()
