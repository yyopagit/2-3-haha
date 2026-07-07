#!/usr/bin/env python3
"""Scan mod files for encoding corruption patterns."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTS = {".txt", ".csv", ".lua"}
REPL = b"\xef\xbf\xbd"
BOM = b"\xef\xbb\xbf"

results = []

for p in sorted(ROOT.rglob("*")):
    if not p.is_file() or p.suffix.lower() not in EXTS:
        continue
    rel = p.relative_to(ROOT).as_posix()
    try:
        data = p.read_bytes()
    except OSError as e:
        results.append((rel, "read_error", str(e), 0))
        continue

    issues = []
    if REPL in data:
        issues.append(f"replacement_chars={data.count(REPL) // 3}")
    if BOM in data:
        issues.append("utf8_bom")

    utf8_cyr = sum(
        1
        for i in range(len(data) - 1)
        if data[i] in (0xD0, 0xD1) and 0x80 <= data[i + 1] <= 0xBF
    )
    if utf8_cyr > 5:
        issues.append(f"utf8_cyrillic_bytes={utf8_cyr}")

    if issues:
        results.append((rel, data[:8].hex(), "; ".join(issues), len(data)))

print(f"CORRUPTED/SUSPECT FILES: {len(results)}")
for rel, head, issues, size in results:
    print(f"{rel}\t{head}\t{issues}\t{size}")
