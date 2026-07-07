#!/usr/bin/env python3
from pathlib import Path

REPL = b"\xef\xbf\xbd"
ROOT = Path(".")
EXTS = {".txt", ".csv", ".lua"}

rows = []
for p in sorted(ROOT.rglob("*")):
    if not p.is_file() or p.suffix.lower() not in EXTS:
        continue
    rel = p.relative_to(ROOT).as_posix()
    if rel.startswith("assets/") or rel.startswith(".git/"):
        continue
    data = p.read_bytes()
    n = data.count(REPL) // 3
    if n:
        rows.append((n, len(data), rel))

rows.sort(reverse=True)
print(f"Files with U+FFFD corruption: {len(rows)}")
for n, size, rel in rows:
    print(f"{n:5d}  {size:8d}  {rel}")
