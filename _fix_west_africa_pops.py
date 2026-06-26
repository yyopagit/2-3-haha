# -*- coding: utf-8 -*-
"""Fix broken pop syntax from _transfer_sa_to_west_africa.py (province IDs used as pop types)."""
from __future__ import annotations

import re
from pathlib import Path

MOD = Path(__file__).resolve().parent
POPS_DIR = MOD / "history" / "pops"
FILES = ("Benin.txt", "Ghana.txt", "Togo.txt")
INVALID_POP = re.compile(r"^\t(\d{4})\s*=\s*\{\s*$")
POP_BLOCK_START = re.compile(r"^\t(\w+)\s*=\s*\{\s*$")


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("".join(lines), encoding="utf-8")


def parse_invalid_block(lines: list[str], start: int) -> tuple[str, str, int, int]:
    culture = religion = ""
    size = 0
    depth = 1
    j = start + 1
    while j < len(lines) and depth:
        line = lines[j]
        if m := re.search(r"culture\s*=\s*(\w+)", line):
            culture = m.group(1)
        if m := re.search(r"religion\s*=\s*(\w+)", line):
            religion = m.group(1)
        if m := re.search(r"size\s*=\s*(\d+)", line):
            size = int(m.group(1))
        depth += line.count("{") - line.count("}")
        j += 1
    return culture, religion, size, j


def find_farmers_size_line(prov_lines: list[str], base: int, culture: str, religion: str) -> int | None:
    i = 0
    while i < len(prov_lines):
        if re.match(r"^\tfarmers\s*=\s*\{\s*$", prov_lines[i]):
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


def append_farmers(lines: list[str], insert_at: int, culture: str, religion: str, size: int) -> None:
    block = [
        "\n\tfarmers = {\n",
        f"\t\tculture = {culture}\n",
        f"\t\treligion = {religion}\n",
        f"\t\tsize = {size}\n",
        "\t}\n",
    ]
    lines[insert_at:insert_at] = block


def fix_province_block(lines: list[str], start: int, end: int) -> int:
  fixed = 0
  merged: dict[tuple[str, str], int] = {}
  to_remove: list[tuple[int, int]] = []
  i = start + 1
  while i < end - 1:
    if INVALID_POP.match(lines[i]):
      culture, religion, size, j = parse_invalid_block(lines, i)
      if culture and religion and size > 0:
        merged[(culture, religion)] = merged.get((culture, religion), 0) + size
        to_remove.append((i, j))
        fixed += 1
      i = j
      continue
    i += 1

  if not merged:
    return 0

  for begin, stop in reversed(to_remove):
    del lines[begin:stop]
    end -= stop - begin

  for (culture, religion), amount in merged.items():
    size_line = find_farmers_size_line(lines[start:end], start, culture, religion)
    if size_line is not None:
      lines[size_line] = re.sub(
        r"size\s*=\s*(\d+)",
        lambda m, a=amount: f"size = {int(m.group(1)) + a}",
        lines[size_line],
      )
    else:
      append_farmers(lines, end - 1, culture, religion, amount)
      end += 5

  return fixed


def province_ranges(lines: list[str]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    i = 0
    while i < len(lines):
        if re.match(r"^(\d+)\s*=\s*\{\s*$", lines[i]):
            depth = 1
            j = i + 1
            while j < len(lines) and depth:
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
            ranges.append((i, j))
            i = j
            continue
        i += 1
    return ranges


def fix_file(path: Path) -> int:
    lines = read_lines(path)
    total = 0
    for start, end in reversed(province_ranges(lines)):
        total += fix_province_block(lines, start, end)
    if total:
        write_lines(path, lines)
    return total


def main() -> None:
  grand = 0
  for date_dir in sorted(POPS_DIR.iterdir()):
    if not date_dir.is_dir() or not date_dir.name.startswith("1836."):
      continue
    for fname in FILES:
      path = date_dir / fname
      if not path.exists():
        continue
      n = fix_file(path)
      if n:
        print(f"{date_dir.name}/{fname}: fixed {n} invalid blocks")
        grand += n
  print(f"Done. Total invalid blocks converted: {grand}")


if __name__ == "__main__":
  main()
