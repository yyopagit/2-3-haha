# -*- coding: utf-8 -*-
"""Scale USA pops to 1836 census; then report Africa pops vs history."""
from __future__ import print_function
import os, re, collections, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)

SIZE_RE = re.compile(r"^\s*size\s*=\s*(\d+)", re.I)
ID_RE = re.compile(r"^(\d+)\s*=")
COMMENT_RE = re.compile(r"^#+\s*(.+?)\s*$")


def interp_jan1836(a1830, a1840):
    """June 1830 -> Jan 1836 = 67 months of 120."""
    return a1830 + (67.0 / 120.0) * (a1840 - a1830)


# Census 1830 / 1840. Maryland includes DC. Virginia includes future WV.
CENSUS = {
    "Maine Region": (399455, 501793),
    "New Hampshire Region": (269328, 284574),
    "Vermont Region": (280652, 291948),
    "Massachusetts Region": (610408, 737699),
    "Rhode Island Region": (97199, 108830),
    "Connecticut Region": (297675, 309978),
    "New York Region": (1918608, 2428921),
    "New Jersey Region": (320823, 373306),
    "Pennsylvania Region": (1348233, 1724033),
    "Delaware Region": (76748, 78085),
    "Maryland Region": (447040 + 30261, 470019 + 33745),
    "Virginia Region": (1220978, 1239792),
    "North Carolina Region": (737987, 753419),
    "South Carolina Region": (581185, 594398),
    "Georgia Region": (516823, 691392),
    "Florida Region": (34730, 54477),
    "Alabama Region": (309527, 590756),
    "Mississippi Region": (136621, 375651),
    "Louisiana Region": (215739, 352411),
    "Tennessee Region": (681904, 829210),
    "Kentucky Region": (687917, 779828),
    "Ohio Region": (937903, 1519467),
    "Indiana Region": (343031, 685866),
    "Illinois Region": (157445, 476183),
    "Missouri Region": (140455, 383702),
    "Arkansas Region": (30388, 97574),
    "Michigan Region": (28004, 212267),
    "Wisconsin Region": (3635, 30945),
    "Iowa Region": (0, 43112),
}

# Not in 1830/40 census (or only natives). Display totals.
FRONTIER_DISPLAY = {
    "Alaska Region": 40000,          # Russian America ~40k
    "Washington Region": 25000,      # OR+WA+ID high end of 40-80k = 80k
    "Oregon Region": 25000,
    "Idaho Region": 30000,
    "California Region": 60000,      # high end of 30-60k
    "Nevada Region": 12000,
    "Utah Region": 16000,
    "Arizona Region": 16000,         # NM+AZ high end of 50-70k = 70k
    "New Mexico Region": 54000,
    "Colorado Region": 20000,
    "Wyoming Region": 28000,
    "Montana Region": 32000,
    "North Dakota Region": 24000,
    "South Dakota Region": 24000,
    "Nebraska Region": 20000,
    "Kansas Region": 24000,
    "Oklahoma Region": 80000,        # high end of 40-80k
    "Texas Region": 80000,           # high end of 50-80k
    "Minnesota Region": 32000,
}


def pid_regions(text):
    pid = None
    size = 0
    region = ""
    cur_region = ""
    mapping = {}
    sizes = {}
    for line in text.split("\n"):
        cm = COMMENT_RE.match(line)
        if cm:
            txt = cm.group(1)
            if "Region" in txt:
                cur_region = txt.split("(")[0].strip()
            continue
        im = ID_RE.match(line)
        if im:
            if pid is not None:
                mapping[pid] = region
                sizes[pid] = size
            pid = int(im.group(1))
            region = cur_region
            size = 0
            continue
        sm = SIZE_RE.match(line)
        if sm:
            size += int(sm.group(1))
    if pid is not None:
        mapping[pid] = region
        sizes[pid] = size
    return mapping, sizes


def fill_bare_pops_comments(text, pid_new):
    """Also rewrite '#City (POPS)' comments that have no numbers."""
    lines = text.split("\n")
    pid_at = {}
    for i, line in enumerate(lines):
        m = re.match(r"^(\d+)\s*=", line)
        if m:
            pid_at[i] = int(m.group(1))
    for i, pid in pid_at.items():
        if pid not in pid_new:
            continue
        adults = pid_new[pid]
        display = adults * 4
        j = i - 1
        while j >= 0 and lines[j].strip() == "":
            j -= 1
        if j < 0:
            continue
        cm = re.match(r"^(#+)([^(\n]+?)\s*\(POPS\)(.*)$", lines[j], re.I)
        if cm:
            lines[j] = "%s%s (%d/%d POPS)%s" % (
                cm.group(1), cm.group(2).rstrip(), display, adults, cm.group(3))
    return "\n".join(lines)


def scale_usa():
    report = []
    targets_adults = {}
    for name, (a, b) in CENSUS.items():
        targets_adults[name] = int(round(interp_jan1836(a, b) / 4.0))
    for name, disp in FRONTIER_DISPLAY.items():
        targets_adults[name] = int(round(disp / 4.0))

    base = os.path.join(MOD, "history", "pops", "1836.1.1", "United States.txt")
    base_text, _ = sea.read_text(base)
    mapping_base, _ = pid_regions(base_text)
    if "" in mapping_base.values():
        raise SystemExit("empty region on 1836.1.1")

    for date in DATES:
        path = os.path.join(MOD, "history", "pops", date, "United States.txt")
        text, nl = sea.read_text(path)
        mapping = dict(mapping_base)
        unknown = sorted(set(mapping.values()) - set(targets_adults))
        if unknown:
            raise SystemExit("unknown regions %s in %s" % (unknown, date))
        new, newsizes, fac = sea.scale_groups(text, mapping, targets_adults)
        new = fill_bare_pops_comments(new, newsizes)
        sea.write_text(path, new, nl)
        if date == "1836.1.1":
            by = collections.defaultdict(int)
            for pid, g in mapping.items():
                by[g] += newsizes.get(pid, 0)
            report.append("=== USA %s after scale ===" % date)
            census_a = 0
            frontier_a = 0
            for g in sorted(by):
                a = by[g]
                tgt = targets_adults[g]
                kind = "CENSUS" if g in CENSUS else "FRONTIER"
                if g in CENSUS:
                    census_a += a
                else:
                    frontier_a += a
                report.append("  [%s] %s adults %d (tgt %d) display %.3f mln x%.3f" % (
                    kind, g, a, tgt, a * 4 / 1e6, fac.get(
                        next(p for p, gg in mapping.items() if gg == g), 1.0)))
            report.append("CENSUS USA adults %d display %.3f mln  hist ~15.21" % (
                census_a, census_a * 4 / 1e6))
            report.append("FRONTIER adults %d display %.3f mln" % (
                frontier_a, frontier_a * 4 / 1e6))
            report.append("FILE TOTAL display %.3f mln" % ((census_a + frontier_a) * 4 / 1e6))
    return report


AFRICA_FILES = {
    "North": [
        "Algeria.txt", "Morocco.txt", "Tunisia.txt", "Libya.txt", "West Sahara.txt",
    ],
    "Egypt": ["Egypt.txt"],
    "Ethiopia": ["Ethiopia.txt", "Eritrea.txt"],
    "South": [
        "South Africa.txt", "Namibia.txt", "Botswana.txt",
    ],
    "Central": [
        "Congo.txt", "Congo-Zaire.txt", "Central Africa.txt", "Cameroun.txt",
        "Chad.txt", "Gabon.txt", "Angola.txt",
    ],
}

# Rest of continent for the total
AFRICA_ALL = [
    "Algeria.txt", "Morocco.txt", "Tunisia.txt", "Libya.txt", "West Sahara.txt",
    "Egypt.txt", "Sudan.txt", "Ethiopia.txt", "Eritrea.txt", "Somalia.txt",
    "South Africa.txt", "Namibia.txt", "Botswana.txt",
    "Congo.txt", "Congo-Zaire.txt", "Central Africa.txt", "Cameroun.txt",
    "Chad.txt", "Gabon.txt", "Angola.txt",
    "Nigeria.txt", "Ghana.txt", "Mali.txt", "Senegambia.txt", "Guinea.txt",
    "Guinea Bissau.txt", "Sierra Leone.txt", "Ivory Coast.txt", "Burkina.txt",
    "Niger.txt", "Benin.txt", "Togo.txt", "Mauritania.txt",
    "Kenya.txt", "Tanzania.txt", "Uganda.txt", "Rwanda-Burundi.txt",
    "Mozambique.txt", "Madagascar.txt", "Malawi.txt", "Zambia.txt", "Zimbabwe.txt",
    "Comoros.txt", "Mauritius.txt", "Reunion.txt", "Sao Tome.txt",
    "Saint Helena.txt", "Liberia.txt", "Equatorial Guinea.txt", "Cape Verde.txt",
]


def sum_file(path):
    if not os.path.isfile(path):
        return None
    text, _ = sea.read_text(path)
    return sum(sea.file_pid_sizes(text).values())


def africa_report():
    lines = []
    popdir = os.path.join(MOD, "history", "pops", "1836.1.1")
    lines.append("\n=== AFRICA 1836.1.1 (actual size, display=x4) ===")
    continent = 0
    missing = []
    file_rows = []
    for fn in AFRICA_ALL:
        a = sum_file(os.path.join(popdir, fn))
        if a is None:
            missing.append(fn)
            continue
        continent += a
        file_rows.append((fn, a))
    lines.append("CONTINENT files listed adults %d display %.2f mln" % (
        continent, continent * 4 / 1e6))

    def grp(name, files):
        tot = 0
        parts = []
        for fn in files:
            a = sum_file(os.path.join(popdir, fn))
            if a is None:
                parts.append((fn, None))
                continue
            tot += a
            parts.append((fn, a))
        lines.append("\n-- %s adults %d display %.2f mln --" % (name, tot, tot * 4 / 1e6))
        for fn, a in parts:
            if a is None:
                lines.append("  MISSING %s" % fn)
            else:
                lines.append("  %s adults %d display %.3f mln" % (fn, a, a * 4 / 1e6))
        return tot

    n = grp("North (Maghreb+Libya, without Egypt)", AFRICA_FILES["North"])
    e = grp("Egypt", AFRICA_FILES["Egypt"])
    eth = grp("Ethiopia+Eritrea", AFRICA_FILES["Ethiopia"])
    s = grp("South (SA+Namibia+Botswana)", AFRICA_FILES["South"])
    c = grp("Central (Congo basin+Cameroon+Chad+Gabon+Angola)", AFRICA_FILES["Central"])
    lines.append("\nNorth including Egypt display %.2f mln" % ((n + e) * 4 / 1e6))
    if missing:
        lines.append("MISSING: %s" % missing)
    lines.append("\nAll listed African files:")
    for fn, a in sorted(file_rows, key=lambda x: -x[1]):
        lines.append("  %s display %.3f mln" % (fn, a * 4 / 1e6))
    return lines


def main():
    rep = scale_usa()
    # verify all dates same census total
    for date in DATES:
        path = os.path.join(MOD, "history", "pops", date, "United States.txt")
        text, _ = sea.read_text(path)
        tot = sum(sea.file_pid_sizes(text).values())
        rep.append("%s USA file adults %d display %.3f mln" % (date, tot, tot * 4 / 1e6))
    rep.extend(africa_report())
    out = os.path.join(MOD, "assets", "_usa_africa_report.txt")
    open(out, "w", encoding="utf-8").write("\n".join(rep) + "\n")
    print("\n".join(rep))
    print("wrote", out)


if __name__ == "__main__":
    main()
