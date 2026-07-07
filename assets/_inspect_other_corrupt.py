#!/usr/bin/env python3
import subprocess
from pathlib import Path

REPL = b"\xef\xbf\xbd"
files = [
    "events/PRU.txt",
    "events/MULTI.txt",
    "map/adjacencies.csv",
    "events/HND.txt",
    "decisions/GRE.txt",
]

for rel in files:
    data = Path(rel).read_bytes()
    print(f"\n=== {rel} ({data.count(REPL)//3} repl) ===")
    pos = 0
    shown = 0
    while shown < 3:
        idx = data.find(REPL, pos)
        if idx < 0:
            break
        start = max(0, idx - 40)
        end = min(len(data), idx + 80)
        snippet = data[start:end]
        print(f"  offset {idx}: {snippet!r}")
        pos = idx + 3
        shown += 1

# mod6 sources?
mod6 = Path(r"C:\Games\Vic2LV2\Victoria 2\mod\Новая папка\6")
for rel in files:
    p = mod6 / rel
    if p.exists():
        d = p.read_bytes()
        print(f"mod6 {rel}: repl={d.count(REPL)//3}")
