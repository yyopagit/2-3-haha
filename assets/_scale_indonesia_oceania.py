# -*- coding: utf-8 -*-
"""Scale Indonesia / Malaysia / Australia / NZ / Philippines / Melanesia
to the larger 1830s estimate. size = display / 4. Cultures unchanged.
"""
from __future__ import print_function
import os, re, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
POP_ROOT = os.path.join(MOD, "history", "pops")

# Display totals (people on screen). Larger of comment / contemporary high.
# Java island still 12.70 mln (Peper ~10 in 1800 -> Boomgaard 14 in 1850),
# but split by Vic2 province. Shares: Koloniaal Verslag 1850 residencies
# (OCR 8->3 on Batavia, Japara, Yogyakarta, Pasuruan, Madura so the table
# sums ~9.67 mln), mapped onto the nine Java/Madura pids, then scaled up
# to 12.70. Outer islands: comment plus inland undercount.

JAVA_1850_RAW = {
    1413: 944315,    # Batavia: Bantam + Batavia + Krawang
    1414: 1019362,   # Bogor: Buitenzorg + Preanger
    1415: 830666,    # Cirebon: Cheribon + Tegal
    1416: 1629614,   # Yogyakarta: Yogya + Bagelen + Banyumas + Kedu
    1417: 1727325,   # Semarang: Semarang + Japara + Rembang + Pekalongan
    1418: 1555160,   # Surabaya: Surabaya + Madiun + Kediri + Pacitan
    1419: 603769,    # Surakarta
    1420: 1045755,   # Probolinggo: Pasuruan + Besuki + Banyuwangi
    1421: 345171,    # Madura
}
JAVA_TOTAL = 12700000
JAVA_CITY = {
    1413: "Batavia", 1414: "Bogor", 1415: "Cirebon",
    1416: "Yogyakarta", 1417: "Semarang", 1418: "Surabaya",
    1419: "Surakarta", 1420: "Probolinggo", 1421: "Madura",
}


def java_display_targets(total=JAVA_TOTAL):
    s = float(sum(JAVA_1850_RAW.values()))
    rounded = {pid: int(round(v / s * total)) for pid, v in JAVA_1850_RAW.items()}
    rounded[max(rounded, key=rounded.get)] += total - sum(rounded.values())
    return rounded


INDONESIA_GROUPS = {
    "East Sumatra Region": 1200000,
    "Riau Region": 91000,
    "Siak Region": 500000,
    "Aceh Region": 1000000,
    "Minangkabau Region": 1200000,
    "Eastern Borneo Region": 900000,
    "Western Borneo Region": 650000,
    "Celebes Region": 1500000,
    "Sunda Region": 2000000,
    "Moluccas Region": 400000,
    "Wests Papua": 550000,
}

MALAYSIA_GROUPS = {
    "Malaya Region": 1000000,
    "Northern Borneo Region": 400000,
}

PHIL_GROUPS = {
    "Luzon Region": 2400000,
    "Visayas Region": 1200000,
    "Mindanao Region": 800000,
}

FILE_TOTAL = {
    "Australia.txt": 690000,
    "New Zealand.txt": 100000,
    "Fiji.txt": 200000,
    "Papua New Guinea.txt": 1500000,
    "Vanuatu.txt": 100000,
    "New Caledonia.txt": 50000,
}

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)

ID_RE = re.compile(r"^(\d+)\s*=")


def parse_region_pids(text):
    """Region header -> list of pids until the next Region/Papua/Melanesia header."""
    lines = text.splitlines()
    blocks = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("#"):
            continue
        if re.search(r"Region|Papua|Melanesia", s, re.I):
            name = re.sub(r"[\d(),:\-]+", " ", s.lstrip("#")).strip()
            name = re.sub(r"\s+", " ", name)
            # drop trailing junk
            name = name.replace(" POPS", "").replace("see Vanuatu.txt for balance of region", "").strip()
            name = name.replace("#see New Caledonia.txt for balance of region", "").strip()
            blocks.append((name, i))
    pid_line = {}
    for i, line in enumerate(lines):
        m = ID_RE.match(line)
        if m:
            pid_line[i] = int(m.group(1))
    out = {}
    for k, (name, start) in enumerate(blocks):
        end = blocks[k + 1][1] if k + 1 < len(blocks) else len(lines)
        pids = []
        for i in range(start, end):
            if i in pid_line:
                pids.append(pid_line[i])
        # normalize names
        key = name
        if key.startswith("Visayas"):
            key = "Visayas Region"
        if key.startswith("Southern Melanesia"):
            key = "Southern Melanesia"
        out.setdefault(key, [])
        out[key].extend(pids)
    return out


def scale_mapped(path, mapping, group_disp, report, date):
    text, nl = sea.read_text(path)
    sizes = sea.file_pid_sizes(text)
    adults = {}
    used = {}
    for pid, g in mapping.items():
        if pid not in sizes:
            continue
        used[pid] = g
        adults[g] = int(round(group_disp[g] / 4.0))
    leftover = [pid for pid in sizes if pid not in used]
    if leftover:
        report.append("LEFTOVER %s %s %s" % (date, os.path.basename(path), leftover))
    missing = [g for g in group_disp if g not in adults]
    if missing:
        report.append("NO PIDS %s %s %s" % (date, os.path.basename(path), missing))
        return
    old = sum(sizes.get(p, 0) for p in used) * 4
    new_text, new_by, fac = sea.scale_groups(text, used, adults)
    if os.path.basename(path) == "Indonesia.txt":
        new_text = re.sub(
            r"(#Java Region)[^\n]*",
            r"\1 (%d)" % JAVA_TOTAL,
            new_text,
            count=1,
        )
    sea.write_text(path, new_text, nl)
    got = sum(new_by.get(p, 0) for p in used) * 4
    report.append("%s %s  %.3f -> %.3f mln" % (
        date, os.path.basename(path), old / 1e6, got / 1e6))
    if os.path.basename(path) == "Indonesia.txt" and date == "1836.1.1":
        jsum = 0
        for pid, city in JAVA_CITY.items():
            d = new_by.get(pid, 0) * 4
            jsum += d
            report.append("  Java %s %s  %.3f mln" % (pid, city, d / 1e6))
        report.append("  Java total  %.3f mln" % (jsum / 1e6))


def main():
    report = []
    base = os.path.join(POP_ROOT, "1836.1.1")
    maps = {}
    for fn, groups in [
        ("Indonesia.txt", INDONESIA_GROUPS),
        ("Malaysia.txt", MALAYSIA_GROUPS),
        ("Philippines.txt", PHIL_GROUPS),
    ]:
        t, _ = sea.read_text(os.path.join(base, fn))
        regions = parse_region_pids(t)
        mapping = {}
        groups = dict(groups)
        for g in list(groups):
            pids = regions.get(g)
            if not pids:
                for rn, rp in regions.items():
                    if rn.startswith(g) or g.startswith(rn.split()[0]):
                        pids = rp
                        break
            if not pids:
                report.append("BASE MAP FAIL %s %s have %s" % (fn, g, list(regions)))
                continue
            for pid in pids:
                mapping[pid] = g
        if fn == "Indonesia.txt":
            for pid, disp in java_display_targets().items():
                g = "Java " + JAVA_CITY[pid]
                groups[g] = disp
                mapping[pid] = g
        maps[fn] = (mapping, groups)

    for date in DATES:
        for fn, (mapping, groups) in maps.items():
            scale_mapped(
                os.path.join(POP_ROOT, date, fn),
                mapping, groups, report, date)
        for fn, disp in FILE_TOTAL.items():
            p = os.path.join(POP_ROOT, date, fn)
            if os.path.isfile(p):
                scale_file_total(p, disp, report, date)
    print("\n".join(report))


def scale_file_total(path, disp, report, date):
    text, nl = sea.read_text(path)
    sizes = sea.file_pid_sizes(text)
    if not sizes:
        report.append("EMPTY %s %s" % (date, path))
        return
    adults = {"ALL": int(round(disp / 4.0))}
    mapping = {pid: "ALL" for pid in sizes}
    old = sum(sizes.values()) * 4
    new_text, new_by, fac = sea.scale_groups(text, mapping, adults)
    sea.write_text(path, new_text, nl)
    got = sum(new_by.values()) * 4
    report.append("%s %s  %.3f -> %.3f mln (tgt %.3f)" % (
        date, os.path.basename(path), old / 1e6, got / 1e6, disp / 1e6))


if __name__ == "__main__":
    main()
