# -*- coding: utf-8 -*-
"""Split localisation/a.csv into logical fragments. Full dump and vanilla-identical
keys go to this folder as .csv.bak so the game never loads them."""
import collections
import os
import re
import shutil

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOC = os.path.join(MOD, "localisation")
SRC = os.path.join(LOC, "a.csv")
VANILLA = os.path.join(MOD, "..", "..", "localisation", "c.csv")
BACKUP = os.path.dirname(os.path.abspath(__file__))

JAPAN = (
    "meiji", "iwakura", "hokkaido", "sakhalin", "sakoku", "ryk_", "ryukyu",
    "japanese", "japan_", "tokio", "kioto", "tokugawa", "satsuma", "choshu",
    "edo_", "shogun", "form_japanese", "civilize_korea", "smz", "bakufu",
    "daimyo", "honshu", "kyushu", "shikoku", "yedo", "yokohama", "nagasaki",
    "tsushima",
)

FILES = [
    ("japan.csv", "Japan / SMZ"),
    ("china.csv", "China (CHI_)"),
    ("events.csv", "Events (EVT*)"),
    ("provinces.csv", "Provinces (PROV)"),
    ("countries.csv", "Country tags and parties"),
    ("regions.csv", "State/region names (TAG_id)"),
    ("decisions.csv", "Decisions / inventions title+desc"),
    ("ui.csv", "Interface strings"),
    ("tutorial.csv", "Tutorial"),
    ("gameplay.csv", "Techs, goods, pops, modifiers"),
    ("mod.csv", "Custom leftover keys"),
]


def load_key_lines(path):
    d = {}
    for line in open(path, encoding="cp1251", errors="replace"):
        raw = line.rstrip("\n").rstrip("\r")
        if not raw.strip() or raw.startswith("#"):
            continue
        key = raw.split(";", 1)[0]
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


def write_csv(path, comment, rows):
    pad_key = "ZZZ_LOC_PAD_" + os.path.splitext(os.path.basename(path))[0]
    with open(path, "w", encoding="cp1251", newline="") as f:
        f.write("# %s;x;X;X;X;X;X\r\n" % comment)
        for raw in rows:
            f.write(raw + "\r\n")
        f.write("%s;x;X;X;X;X;X\r\n" % pad_key)


def main():
    os.makedirs(BACKUP, exist_ok=True)
    a = load_key_lines(SRC)
    vanilla = load_key_lines(VANILLA) if os.path.isfile(VANILLA) else {}
    identical_keys = sorted(k for k in a if k in vanilla and a[k] == vanilla[k])

    dest = os.path.join(BACKUP, "a.csv.bak")
    shutil.copy2(SRC, dest)

    buckets = collections.OrderedDict((name, []) for name, _ in FILES)
    identical_rows = []
    for key, raw in a.items():
        if key in vanilla and raw == vanilla[key]:
            identical_rows.append(raw)
            continue
        buckets[classify(key)].append(raw)

    write_csv(
        os.path.join(BACKUP, "vanilla_identical.csv.bak"),
        "Exact copies of vanilla c.csv — unused backup",
        identical_rows,
    )

    for name, comment in FILES:
        write_csv(os.path.join(LOC, name), comment, buckets[name])

    # verify
    loaded = {}
    for name, _ in FILES:
        part = load_key_lines(os.path.join(LOC, name))
        for k, raw in part.items():
            if k.startswith("ZZZ_LOC_PAD_"):
                continue
            if k in loaded:
                raise SystemExit("duplicate key in fragments: %s" % k)
            loaded[k] = raw

    bak_ident = load_key_lines(os.path.join(BACKUP, "vanilla_identical.csv.bak"))
    bak_ident = {k: v for k, v in bak_ident.items() if not k.startswith("ZZZ_LOC_PAD_")}
    expected_active = {k: a[k] for k in a if k not in set(identical_keys)}
    if set(loaded) != set(expected_active):
        missing = set(expected_active) - set(loaded)
        extra = set(loaded) - set(expected_active)
        raise SystemExit("key set mismatch missing=%d extra=%d" % (len(missing), len(extra)))
    for k, raw in loaded.items():
        if raw != a[k]:
            raise SystemExit("line changed for key %s" % k)
    if set(bak_ident) != set(identical_keys):
        raise SystemExit("identical backup key mismatch")

    os.remove(SRC)

    for name in os.listdir(LOC):
        if name == "a.csv" or (name.startswith("a.csv.bak")):
            src = os.path.join(LOC, name)
            if os.path.isfile(src):
                shutil.move(src, os.path.join(BACKUP, name))

    csvs = [n for n in os.listdir(LOC) if n.lower().endswith(".csv")]
    report = []
    report.append("source keys: %d" % len(a))
    report.append("vanilla-identical (backup only): %d" % len(identical_keys))
    report.append("active keys: %d" % len(loaded))
    report.append("active csv in localisation/: %s" % ", ".join(sorted(csvs)))
    for name, _ in FILES:
        report.append("  %s: %d" % (name, len(buckets[name])))
    report.append("backup: %s" % BACKUP)
    text = "\n".join(report) + "\n"
    with open(os.path.join(BACKUP, "MANIFEST.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
