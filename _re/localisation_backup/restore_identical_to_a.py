# -*- coding: utf-8 -*-
"""Restore only vanilla-identical keys into localisation/a.csv."""
import os

BACKUP = os.path.dirname(os.path.abspath(__file__))
MOD_LOC = os.path.abspath(os.path.join(BACKUP, "..", "..", "localisation"))
GAME_LOC = os.path.abspath(os.path.join(BACKUP, "..", "..", "..", "..", "localisation"))
SRC = os.path.join(BACKUP, "vanilla_identical.csv.bak")
KEEP = os.path.join(MOD_LOC, "vanilla_keep.csv")
OUT_A = os.path.join(MOD_LOC, "a.csv")
OUT_C = os.path.join(GAME_LOC, "c.csv")

HEADER = (
    "#CODE;ENGLISH;FRENCH;GERMAN;POLISH;SPANISH;ITALIAN;"
    "SWEDISH;CZECH;HUNGARIAN;DUTCH;PORTUGESE;RUSSIAN;FINNISH;x"
)


def load_rows(path):
    rows = []
    seen = set()
    for line in open(path, encoding="cp1251", errors="replace"):
        raw = line.rstrip("\n").rstrip("\r")
        if not raw.strip() or raw.startswith("#"):
            continue
        key = raw.split(";", 1)[0]
        if key.startswith("ZZZ_LOC_PAD_"):
            continue
        if key and key not in seen:
            seen.add(key)
            rows.append(raw)
    return rows, seen


def write_csv(path, rows, pad_key):
    with open(path, "w", encoding="cp1251", newline="") as f:
        f.write(HEADER + "\r\n")
        for raw in rows:
            f.write(raw + "\r\n")
        f.write("%s;x;X;X;X;X;X;X\r\n" % pad_key)


ident_rows, ident_keys = load_rows(SRC)
write_csv(OUT_A, ident_rows, "ZZZ_LOC_PAD_a")

keep_rows, _ = load_rows(KEEP)
keep_only = [raw for raw in keep_rows if raw.split(";", 1)[0] not in ident_keys]
write_csv(KEEP, keep_only, "ZZZ_LOC_PAD_vanilla_keep")

os.makedirs(GAME_LOC, exist_ok=True)
with open(OUT_C, "w", encoding="cp1251", newline="") as f:
    f.write(HEADER + "\r\n")
    f.write("ZZZ_LOC_PAD_c;x;X;X;X;X;X;X\r\n")

print("a.csv keys", len(ident_rows))
print("vanilla_keep leftover", len(keep_only))
print("wrote stub", OUT_C)
