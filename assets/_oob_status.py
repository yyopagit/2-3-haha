#!/usr/bin/env python3
import re
import subprocess
from pathlib import Path

REPL = b"\xef\xbf\xbd"
TAGS = ["PRU", "SPA", "SWE", "NET", "DEN", "POR", "SIC", "SAR", "GRE", "BEL", "PAP", "AUS", "ENG", "FRA"]
OOB = Path("history/units")


def stats(data: bytes) -> tuple[int, int]:
    return data.count(REPL) // 3, len(re.findall(rb"(?m)^army\s*=\s*\{", data))


print("=== CURRENT OOB (14 tags from f06e7ab) ===")
for tag in TAGS:
    p = OOB / f"{tag}_oob.txt"
    d = p.read_bytes()
    r, a = stats(d)
    flag = "CORRUPT" if r else ("0x98" if b"\x98\x98" in d else "OK")
    print(f"{tag}: armies={a} repl={r} status={flag} size={len(d)}")

print("\n=== backup_pass4 PRU ===")
d = Path("history/units_backup_pass4/PRU_oob.txt").read_bytes()
r, a = stats(d)
print(f"armies={a} repl={r} size={len(d)}")

print("\n=== 8515b83 PRU ===")
d = subprocess.check_output(["git", "show", "8515b83:history/units/PRU_oob.txt"])
r, a = stats(d)
print(f"armies={a} repl={r} size={len(d)}")

print("\n=== 60ce09b NET (before f06e7ab armies) ===")
d = subprocess.check_output(["git", "show", "60ce09b:history/units/NET_oob.txt"])
r, a = stats(d)
print(f"armies={a} repl={r} size={len(d)}")
# show corrupted army names count
import re as re2
names = re2.findall(rb'name = "([^"]+)"', d)
bad = [n.decode("cp1251", "replace") for n in names if REPL in n]
print("bad names:", len(bad), bad[:5])
