# -*- coding: utf-8 -*-
import os

loc = r"c:\Games\Vic2LV2\Victoria 2\mod\5\localisation"
for name in os.listdir(loc):
    if not name.endswith(".csv"):
        continue
    path = os.path.join(loc, name)
    lines = []
    changed = False
    for line in open(path, encoding="cp1251", errors="replace"):
        raw = line.rstrip("\n").rstrip("\r")
        if raw.startswith("noloc;"):
            changed = True
            continue
        if name == "mod.csv" and raw.startswith("ZZZ_LOC_PAD_mod"):
            lines.append("noloc;-;X;X;X;X;X;X")
            changed = True
        lines.append(raw)
    if changed:
        with open(path, "w", encoding="cp1251", newline="") as f:
            for raw in lines:
                f.write(raw + "\r\n")
        print("updated", name)
print("done")
