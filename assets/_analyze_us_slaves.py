#!/usr/bin/env python3
import re
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent
PROV_DIR = MOD / "history" / "provinces" / "North America"
POP = MOD / "history" / "pops" / "1836.1.1" / "United States.txt"

usa_csa = {}
for fp in PROV_DIR.glob("*.txt"):
    pid = fp.stem.split(" - ", 1)[0].strip()
    text = fp.read_text(encoding="cp1251", errors="replace")
    if "owner = USA" not in text:
        continue
    usa_csa[pid] = "add_core = CSA" in text

text = POP.read_text(encoding="cp1251", errors="replace")
prov_re = re.compile(r"(?m)^(\d+)\s*=\s*\{")
slave_re = re.compile(r"(?ms)\tslaves\s*=\s*\{.*?\n\t\}")
matches = list(prov_re.finditer(text))
for i, m in enumerate(matches):
    pid = m.group(1)
    start = m.start()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
    chunk = text[start:end]
    if not slave_re.search(chunk):
        continue
    csa = usa_csa.get(pid, False)
    print(pid, "CSA" if csa else "FREE", chunk[:80].splitlines()[0])

print("total usa provinces", len(usa_csa))
print("with slaves in pops", sum(1 for i, m in enumerate(matches) if slave_re.search(text[m.start(): (matches[i+1].start() if i+1 < len(matches) else len(text))])))
