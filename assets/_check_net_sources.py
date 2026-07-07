#!/usr/bin/env python3
from pathlib import Path

REPL = b"\xef\xbf\xbd"
paths = [
    Path(r"C:\Games\Vic2LV2\Victoria 2\mod\5\history\units\NET_oob.txt"),
    Path(r"C:\Games\Vic2LV2\Victoria 2\mod\Новая папка\6\history\units\NET_oob.txt"),
    Path(r"C:\Games\Vic2LV2\Victoria 2\history\units\NET_oob.txt"),
]

for p in paths:
    if not p.exists():
        print("MISSING", p)
        continue
    d = p.read_bytes()
    print(f"\n{p}")
    print("size", len(d), "repl", d.count(REPL) // 3)
    import re

    for m in re.finditer(rb'name = "([^"]+)"', d):
        name = m.group(1)
        if any(b > 127 for b in name):
            print(" ", name.decode("cp1251", "replace"))
