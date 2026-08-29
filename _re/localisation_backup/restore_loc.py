# -*- coding: utf-8 -*-
"""Rebuild localisation fragments from a.csv.bak with the Vic2 header."""
import collections
import os
import re

BACKUP = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(BACKUP, "..", ".."))
LOC = os.path.join(MOD, "localisation")
SRC = os.path.join(BACKUP, "a.csv.bak")
VANILLA = os.path.join(BACKUP, "c.csv.bak")

HEADER = (
    "#CODE;ENGLISH;FRENCH;GERMAN;POLISH;SPANISH;ITALIAN;"
    "SWEDISH;CZECH;HUNGARIAN;DUTCH;PORTUGESE;RUSSIAN;FINNISH;x"
)

JAPAN = (
    "meiji", "iwakura", "hokkaido", "sakhalin", "sakoku", "ryk_", "ryukyu",
    "japanese", "japan_", "tokio", "kioto", "tokugawa", "satsuma", "choshu",
    "edo_", "shogun", "form_japanese", "civilize_korea", "smz", "bakufu",
    "daimyo", "honshu", "kyushu", "shikoku", "yedo", "yokohama", "nagasaki",
    "tsushima",
)

FILES = [
    "japan.csv",
    "china.csv",
    "events.csv",
    "provinces.csv",
    "countries.csv",
    "regions.csv",
    "decisions.csv",
    "ui.csv",
    "tutorial.csv",
    "gameplay.csv",
    "mod.csv",
]


def load_key_lines(path):
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


def classify(key):
    kl = key.lower()
    if any(n in kl for n in JAPAN):
        return "japan.csv"
    if key.startswith("CHI_") or key.startswith("chi_"):
        return "china.csv"
    if (
        key.startswith("EVT")
        or key.startswith("evt")
        or "EvtDesc" in key
        or "EvtOpt" in key
        or "EvtName" in key
        or key.endswith("_EvtDesc")
    ):
        return "events.csv"
    if re.match(r"^PROV\d+$", key):
        return "provinces.csv"
    if kl.startswith("tut_") or kl.startswith("remove_tut"):
        return "tutorial.csv"
    if key.startswith("COUNTRYALERT") or key.startswith("REMOVE_"):
        return "ui.csv"
    if re.match(r"^[A-Z]{3}_\d+$", key):
        return "regions.csv"
    if re.match(r"^[A-Z]{3}$", key) or re.match(r"^[A-Z]{3}_ADJ$", key):
        return "countries.csv"
    if re.match(
        r"^[A-Z]{3}_(conservative|liberal|reactionary|communist|"
        r"anarcho_liberal|socialist|fascist|absolute_monarchy|"
        r"proletarian_dictatorship|prussian_constitutionalism|"
        r"hms_government|democracy|presidential_dictatorship|"
        r"bourgeois_dictatorship|fascist_dictatorship)",
        key,
    ):
        return "countries.csv"
    if key.endswith("_title") or key.endswith("_desc"):
        return "decisions.csv"
    if key == key.upper() and re.search(r"[A-Z]", key):
        return "ui.csv"
    if re.match(r"^\d", key) or key.startswith("dino") or key.startswith("Exchange"):
        return "mod.csv"
    return "gameplay.csv"


def write_csv(path, rows):
    pad_key = "ZZZ_LOC_PAD_" + os.path.splitext(os.path.basename(path))[0]
    with open(path, "w", encoding="cp1251", newline="") as f:
        f.write(HEADER + "\r\n")
        for raw in rows:
            f.write(raw + "\r\n")
        f.write("%s;x;X;X;X;X;X\r\n" % pad_key)


def main():
    a = load_key_lines(SRC)
    vanilla = load_key_lines(VANILLA) if os.path.isfile(VANILLA) else {}

    buckets = collections.OrderedDict((name, []) for name in FILES)
    identical = []
    for key, raw in a.items():
        if key in vanilla and raw == vanilla[key]:
            identical.append(raw)
            continue
        buckets[classify(key)].append(raw)

    if "noloc" not in a:
        buckets["mod.csv"].append("noloc; ;X;X;X;X;X;X")

    only_c = []
    seen_ident = set()
    for raw in identical:
        seen_ident.add(raw.split(";", 1)[0])
    for key, raw in vanilla.items():
        if key not in a:
            only_c.append(raw)

    write_csv(os.path.join(LOC, "vanilla_keep.csv"), identical + only_c)
    for name in FILES:
        write_csv(os.path.join(LOC, name), buckets[name])

    loaded = {}
    for name in FILES:
        part = load_key_lines(os.path.join(LOC, name))
        for k, raw in part.items():
            if k.startswith("ZZZ_LOC_PAD_"):
                continue
            loaded[k] = raw
    expected = {k: a[k] for k in a if k not in seen_ident}
    if "noloc" in loaded and "noloc" not in expected:
        expected["noloc"] = loaded["noloc"]
    missing = set(expected) - set(loaded)
    extra = set(loaded) - set(expected)
    if missing or extra:
        raise SystemExit("mismatch missing=%d extra=%d" % (len(missing), extra and len(extra)))

    print("restored keys", len(loaded), "vanilla_keep", len(identical) + len(only_c))
    for name in FILES + ["vanilla_keep.csv"]:
        print(" ", name, os.path.getsize(os.path.join(LOC, name)))


if __name__ == "__main__":
    main()
