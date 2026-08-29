# -*- coding: utf-8 -*-
path = r"c:\Games\Vic2LV2\Victoria 2\mod\5\localisation\mod.csv"
lines = []
for line in open(path, encoding="cp1251", errors="replace"):
    raw = line.rstrip("\n").rstrip("\r")
    if raw.startswith("noloc;"):
        continue
    if raw.startswith("ZZZ_LOC_PAD_mod"):
        lines.append("noloc; ;X;X;X;X;X;X")
    lines.append(raw)
with open(path, "w", encoding="cp1251", newline="") as f:
    for raw in lines:
        f.write(raw + "\r\n")
print("ok", len(lines))
