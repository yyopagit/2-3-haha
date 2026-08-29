# -*- coding: utf-8 -*-
import os

def load_map(path):
    d = {}
    for line in open(path, encoding="cp1251", errors="replace"):
        raw = line.rstrip("\n").rstrip("\r")
        if not raw.strip() or raw.startswith("#"):
            continue
        key = raw.split(";", 1)[0]
        if key.startswith("ZZZ_LOC_PAD_"):
            continue
        if key and key not in d:
            d[key] = raw
    return d

mod_bak = os.path.dirname(os.path.abspath(__file__))
mod_loc = os.path.abspath(os.path.join(mod_bak, "..", "..", "localisation"))
c_bak = os.path.join(mod_bak, "c.csv.bak")

c = load_map(c_bak)
mod = {}
for n in os.listdir(mod_loc):
    if n.endswith(".csv") and n != "vanilla_keep.csv":
        mod.update(load_map(os.path.join(mod_loc, n)))
ident = load_map(os.path.join(mod_bak, "vanilla_identical.csv.bak"))

rows = []
seen = set()
for key in list(ident) + sorted(set(c) - set(mod) - set(ident)):
    if key in c and key not in seen:
        seen.add(key)
        rows.append(c[key])

out = os.path.join(mod_loc, "vanilla_keep.csv")
with open(out, "w", encoding="cp1251", newline="") as f:
    f.write("# Keys only in vanilla c.csv or identical copies;x;X;X;X;X;X\r\n")
    for raw in rows:
        f.write(raw + "\r\n")
    f.write("ZZZ_LOC_PAD_vanilla_keep;x;X;X;X;X;X\r\n")

print("wrote", len(rows), "lines to", out)
print("size", os.path.getsize(out))
