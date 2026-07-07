#!/usr/bin/env python3
import subprocess
from pathlib import Path

REPL = b"\xef\xbf\xbd"

files = [
    Path("history/units/PRU_oob.txt"),
    Path("history/units_backup_pass4/PRU_oob.txt"),
    Path("history/units/NET_oob.txt"),
    Path("history/units_backup_pass4/NET_oob.txt"),
]

for p in files:
    if not p.exists():
        continue
    d = p.read_bytes()
    print(f"\n=== {p} size={len(d)} repl={d.count(REPL)//3} ===")
    # first cyrillic name
    idx = d.find(b'name = "')
    while idx != -1:
        end = d.find(b'"', idx + 8)
        name = d[idx + 8 : end]
        if any(b > 127 for b in name):
            print("raw:", name[:60])
            for enc in ("cp1251", "cp866", "koi8-r", "utf-8"):
                try:
                    print(f"  {enc}: {name.decode(enc)}")
                except Exception as e:
                    print(f"  {enc}: ERR {e}")
            break
        idx = d.find(b'name = "', idx + 1)

# HEAD commit
head = subprocess.check_output(["git", "show", "HEAD:history/units/PRU_oob.txt"])
print(f"\n=== HEAD PRU size={len(head)} repl={head.count(REPL)//3} ===")
idx = head.find(b'name = "')
end = head.find(b'"', idx + 8)
name = head[idx + 8 : end]
print("raw:", name)
for enc in ("cp1251", "cp866", "koi8-r"):
    print(f"  {enc}: {name.decode(enc, errors='replace')}")
