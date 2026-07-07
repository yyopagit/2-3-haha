#!/usr/bin/env python3
import re
import subprocess
from pathlib import Path

REPL = b"\xef\xbf\xbd"


def inspect(path: Path, label: str) -> None:
    data = path.read_bytes() if path.exists() else subprocess.check_output(
        ["git", "show", f"HEAD:{path.as_posix()}"]
    )
    print(f"\n=== {label} ({path}) size={len(data)} repl={data.count(REPL)//3} ===")
    for m in re.finditer(rb'name = "([^"]+)"', data):
        name = m.group(1)
        if REPL in name or any(b > 127 for b in name):
            print("bytes:", name[:80])
            print("cp1251:", name.decode("cp1251", errors="replace")[:80])


inspect(Path("history/units/PRU_oob.txt"), "WORKING PRU")
inspect(Path("history/units/NET_oob.txt"), "WORKING NET")

# HEAD versions via temp
for tag in ("PRU", "NET"):
    data = subprocess.check_output(["git", "show", f"HEAD:history/units/{tag}_oob.txt"])
    tmp = Path(f"assets/_tmp_{tag}_head.bin")
    tmp.write_bytes(data)
    inspect(tmp, f"HEAD {tag}")
    tmp.unlink()

# scan all oob for repl
print("\n=== ALL OOB with replacement chars ===")
for p in sorted(Path("history/units").glob("*_oob.txt")):
    d = p.read_bytes()
    n = d.count(REPL) // 3
    if n:
        print(f"{p.name}: {n}")
