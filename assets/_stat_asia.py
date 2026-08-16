# -*- coding: utf-8 -*-
"""Inventory: Central Asia, Korea, India, Persia, China subregions."""
from __future__ import print_function
import os, re, collections, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
POP = os.path.join(MOD, "history", "pops", "1836.1.1")

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)
spec2 = importlib.util.spec_from_file_location(
    "sc", os.path.join(MOD, "assets", "_scale_fra_aus_tur_rus.py"))
s = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(s)

TAG_NAME = {}
with open(os.path.join(MOD, "common", "countries.txt"), "r", encoding="latin-1") as f:
    for line in f:
        m = re.match(r"^([A-Z0-9]{3})\s*=\s*\"countries/([^\"]+)\"", line.strip())
        if m:
            TAG_NAME[m.group(1)] = m.group(2).replace(".txt", "")

owners = s.load_owners()
id_name = sea.load_id_name()

FILES = {
    "korea": ["Korea.txt"],
    "persia": ["Iran.txt"],
    "india": ["India.txt", "Ceylon.txt", "Nepal.txt", "Bhutan.txt"],
    "casia": [
        "Afghanistan.txt", "Uzbekistan.txt", "Kazakhstan.txt",
        "Turkmenistan.txt", "Kirghizstan.txt", "Tajikistan.txt",
        "Xinjiang.txt",
    ],
    "china_sub": [
        "China.txt", "Mongolia.txt", "Tibet.txt", "Xinjiang.txt", "Taiwan.txt",
    ],
}


def scan_files(fns):
    by_tag = collections.defaultdict(lambda: [0, 0, 0])  # actual, comment, pids
    by_file_tag = collections.defaultdict(lambda: [0, 0, 0])
    outliers = []
    for fn in fns:
        path = os.path.join(POP, fn)
        if not os.path.isfile(path):
            print("MISSING", fn)
            continue
        text, _ = sea.read_text(path)
        rows = s.parse_base(text)
        for pid, (reg, city, disp, sz) in rows.items():
            own = owners.get(pid) or "NONE"
            ad = sz * 4
            by_tag[own][0] += ad
            by_tag[own][1] += disp or 0
            by_tag[own][2] += 1
            by_file_tag[(fn, own)][0] += ad
            by_file_tag[(fn, own)][1] += disp or 0
            by_file_tag[(fn, own)][2] += 1
            if disp and ad and abs(ad / float(disp) - 1.0) >= 0.12:
                outliers.append((fn, pid, own, city or id_name.get(pid, ""), disp, ad, ad / float(disp)))
    return by_tag, by_file_tag, outliers


def print_tags(title, by_tag):
    print("\n=== %s ===" % title)
    print("tag\tname\tpids\tactual_mln\tcomment_mln\tratio")
    tot_a = tot_c = 0
    for tag, (ad, cd, n) in sorted(by_tag.items(), key=lambda x: -x[1][0]):
        name = TAG_NAME.get(tag, tag)
        r = (ad / float(cd)) if cd else 0
        print("%s\t%s\t%d\t%.3f\t%.3f\tx%.2f" % (tag, name, n, ad / 1e6, cd / 1e6, r))
        tot_a += ad
        tot_c += cd
    r = (tot_a / float(tot_c)) if tot_c else 0
    print("TOTAL\t\t\t%.3f\t%.3f\tx%.2f" % (tot_a / 1e6, tot_c / 1e6, r))


for key, fns in [("korea", FILES["korea"]), ("persia", FILES["persia"]),
                 ("india", FILES["india"]), ("casia", FILES["casia"])]:
    by_tag, by_ft, outliers = scan_files(fns)
    print_tags(key, by_tag)
    print("outliers |x-1|>=12 percent: %d" % len(outliers))
    outliers.sort(key=lambda x: -abs(x[6] - 1))
    for row in outliers[:25]:
        print("  %s pid %s %s %s  cmt %.0f act %.0f x%.2f" % (
            row[0], row[1], row[2], row[3], row[4], row[5], row[6]))

# China subregions via NAME_TO_QING
print("\n=== china subregions ===")
ch_text, _ = sea.read_text(os.path.join(POP, "China.txt"))
ch_rows = s.parse_base(ch_text)
by_qing = collections.defaultdict(lambda: [0, 0, 0])
unmapped = []
for pid, (reg, city, disp, sz) in ch_rows.items():
    name = id_name.get(pid, city or "")
    q = sea.NAME_TO_QING.get(name)
    if not q:
        unmapped.append((pid, name))
        q = "UNMAPPED"
    ad = sz * 4
    by_qing[q][0] += ad
    by_qing[q][1] += disp or 0
    by_qing[q][2] += 1

for fn, label in [("Mongolia.txt", "Outer Mongolia"),
                  ("Tibet.txt", "Tibet file"),
                  ("Xinjiang.txt", "Xinjiang"),
                  ("Taiwan.txt", "Taiwan")]:
    text, _ = sea.read_text(os.path.join(POP, fn))
    rows = s.parse_base(text)
    for pid, (reg, city, disp, sz) in rows.items():
        ad = sz * 4
        by_qing[label][0] += ad
        by_qing[label][1] += disp or 0
        by_qing[label][2] += 1
        own = owners.get(pid)
        if fn == "Tibet.txt":
            by_qing["Tibet:%s" % own][0] += ad
            by_qing["Tibet:%s" % own][1] += disp or 0
            by_qing["Tibet:%s" % own][2] += 1

print("region\tpids\tactual_mln\tcomment_mln\tratio\tcao1836_mln")
manch = ["Liaoning", "Jilin", "Heilongjiang"]
man_a = man_c = 0
for q, (ad, cd, n) in sorted(by_qing.items(), key=lambda x: -x[1][0]):
    cao = ""
    if q in sea.CAO:
        cao = "%.3f" % (sea.cao_display(q) / 1e6)
    elif q == "Outer Mongolia":
        cao = "part of Mongolia %.3f" % (sea.cao_display("Mongolia") / 1e6)
    elif q == "Inner Mongolia":
        cao = "part of Mongolia %.3f" % (sea.cao_display("Mongolia") / 1e6)
    r = (ad / float(cd)) if cd else 0
    print("%s\t%d\t%.3f\t%.3f\tx%.2f\t%s" % (q, n, ad / 1e6, cd / 1e6, r, cao))
    if q in manch:
        man_a += ad
        man_c += cd

print("MANCHURIA (Liao+Ji+Hei)\t\t%.3f\t%.3f\tx%.2f\tcao %.3f" % (
    man_a / 1e6, man_c / 1e6,
    (man_a / float(man_c)) if man_c else 0,
    (sea.cao_display("Liaoning") + sea.cao_display("Jilin") + sea.cao_display("Heilongjiang")) / 1e6))
inner = by_qing["Inner Mongolia"][0]
outer = by_qing["Outer Mongolia"][0]
print("MONGOLIA inner+outer\t\t%.3f\tcao %.3f" % (
    (inner + outer) / 1e6, sea.cao_display("Mongolia") / 1e6))
print("UNMAPPED China.txt", unmapped)

# owners of china sub files
print("\n=== china sub files by owner ===")
for fn in FILES["china_sub"]:
    by_tag, _, _ = scan_files([fn])
    bits = []
    for tag, (ad, cd, n) in sorted(by_tag.items(), key=lambda x: -x[1][0]):
        bits.append("%s %.3f" % (tag, ad / 1e6))
    print(fn, " | ".join(bits))
