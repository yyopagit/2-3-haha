# -*- coding: utf-8 -*-
"""Scale Mexico, Central America, Canada, South Africa, South America (not Brazil)."""
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
REGION_HDR = re.compile(
    r"^(?P<name>.+?Region[s]?)\s*[\(:\-]\s*(?P<num>\d+)",
    re.I,
)
FILE_HDR = re.compile(
    r"^(?P<name>.+?)\s*[\(:]\s*(?P<num>\d+)\s*\)?\s*$",
)

FILES = [
    "Mexico.txt",
    "Guatemala.txt", "Salvador.txt", "Honduras.txt", "Nicaragua.txt",
    "Costa Rica.txt", "Panama.txt", "Belize.txt",
    "Canada.txt",
    "South Africa.txt", "Namibia.txt", "Botswana.txt",
    "Argentina.txt", "Chile.txt", "Peru.txt", "Bolivia.txt",
    "Colombia.txt", "Venezuela.txt", "Ecuador.txt",
    "Paraguay.txt", "Uruguay.txt",
    "Guyana.txt", "Surinam.txt", "French Guiana.txt", "Falkland Islands.txt",
]

# If sources disagree, always use the larger historical figure.
FILE_TOTAL = {
    "Mexico.txt": 7800000,         # INEGI conventional 1836 (McCaa new series ~6.8)
    "Guatemala.txt": 700000,       # Galindo 1836 > 1824 census 661k
    "Salvador.txt": 416000,        # vanilla comment > Galindo 350k
    "Honduras.txt": 352000,        # vanilla comment > Galindo 300k
    "Nicaragua.txt": 350000,       # Galindo 1836 > comment 292k
    "Costa Rica.txt": 150000,      # Galindo 1836 > 84k census-trajectory
    "Paraguay.txt": 652000,        # vanilla comments > 1846 census ~300k
    "Uruguay.txt": 200000,         # vanilla comment / populstat 1820 > ~100k
    "Bolivia.txt": 1236000,        # vanilla comments > census 1835 1.06
    "Colombia.txt": 1558000,       # NG 1835 1,687,109 minus Panama
    "Peru.txt": 1935000,           # 1791-1876 linear to 1836 > comments 1.62
    "Venezuela.txt": 1046760,      # Cajigal 1838 > Codazzi 945k / comments 950k
    "South Africa.txt": 3612000,   # Frankema South 1850 4.1 minus Nam/Bwa
    "Namibia.txt": 382000,
    "Botswana.txt": 107000,
}

REGION_OVERRIDE = {
    "Canada.txt": {
        "Nova Scotia": 202575,              # 1838 census > 1837 199,906
        "New Brunswick": 148000,            # vanilla comment > 1836 interp 132k
        "Prince Edward Island": 38000,      # 1836 interp > 1833 32k
        "Newfoundland": 84000,              # vanilla comment > 1836 census 75k
        "Ontario": 448000,                  # vanilla comment > UC census 374k
        "Quebec": 676000,                   # vanilla comment > LC interp ~603k
    },
}


def header_from_comment(txt):
    t = re.split(r"\s+#see\b", txt, 1)[0].strip()
    m = REGION_HDR.match(t)
    if m:
        return m.group("name").strip(), int(m.group("num"))
    m = FILE_HDR.match(t)
    if m:
        name = m.group("name").strip()
        if name.lower() in (
            "guyana", "surinam", "french guiana", "falkland islands",
        ) or name.lower().endswith("region"):
            return name, int(m.group("num"))
    return None, None


def pid_regions(text):
    pid = None
    size = 0
    region = ""
    cur_region = ""
    comments = {}
    mapping = {}
    sizes = {}
    for line in text.split("\n"):
        cm = COMMENT_RE.match(line)
        if cm:
            name, num = header_from_comment(cm.group(1))
            if name:
                cur_region = name
                comments[name] = num
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
    return mapping, sizes, comments


def fill_bare_pops_comments(text, pid_new):
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


def update_flex_region_comments(text, mapping, pid_new):
    lines = text.split("\n")
    pid_at = {}
    for i, line in enumerate(lines):
        m = re.match(r"^(\d+)\s*=", line)
        if m:
            pid_at[i] = int(m.group(1))
    region_idx = []
    for i, line in enumerate(lines):
        cm = COMMENT_RE.match(line)
        if not cm:
            continue
        name, _ = header_from_comment(cm.group(1))
        if name:
            region_idx.append((i, name))
    by = collections.defaultdict(int)
    for pid, g in mapping.items():
        by[g] += pid_new.get(pid, 0)
    for k, (i, name) in enumerate(region_idx):
        display = by.get(name, 0) * 4
        # replace last integer on the header line
        lines[i] = re.sub(r"(\d+)(?!.*\d)", str(display), lines[i], count=1)
    return "\n".join(lines)


def targets_for_file(fn, comments, mapping):
    used = set(mapping.values())
    if "" in used:
        raise SystemExit("empty region in %s" % fn)
    comment_sum = 0
    for g in used:
        if g not in comments:
            raise SystemExit("region %r in %s has no comment total" % (g, fn))
        comment_sum += comments[g]
    file_total = FILE_TOTAL.get(fn)
    ov = REGION_OVERRIDE.get(fn, {})
    out = {}
    for g in used:
        disp = comments[g]
        if file_total and comment_sum:
            disp = int(round(file_total * (float(comments[g]) / comment_sum)))
        for key, val in ov.items():
            if key.lower() in g.lower():
                disp = val
                break
        out[g] = int(round(disp / 4.0))
    # remainder so file_total matches exactly when no region overrides leftover
    if file_total and not ov:
        delta = int(round(file_total / 4.0)) - sum(out.values())
        if delta:
            biggest = max(out, key=lambda k: out[k])
            out[biggest] += delta
    return out


def scale_file(fn, report):
    base = os.path.join(MOD, "history", "pops", "1836.1.1", fn)
    base_text, _ = sea.read_text(base)
    mapping, old_sizes, comments = pid_regions(base_text)
    targets = targets_for_file(fn, comments, mapping)
    old_by = collections.defaultdict(int)
    for pid, g in mapping.items():
        old_by[g] += old_sizes.get(pid, 0)
    report.append("=== %s ===" % fn)
    for g in sorted(old_by):
        old_d = old_by[g] * 4
        new_d = targets[g] * 4
        report.append("  %s  %.3f -> %.3f mln  x%.3f" % (
            g, old_d / 1e6, new_d / 1e6,
            (new_d / old_d) if old_d else 0))
    old_tot = sum(old_by.values()) * 4
    new_tot = sum(targets.values()) * 4
    report.append("  FILE  %.3f -> %.3f mln" % (old_tot / 1e6, new_tot / 1e6))

    for date in DATES:
        path = os.path.join(MOD, "history", "pops", date, fn)
        if not os.path.isfile(path):
            report.append("  MISSING %s" % date)
            continue
        text, nl = sea.read_text(path)
        pids = set(sea.file_pid_sizes(text))
        extra = pids - set(mapping)
        missing = set(mapping) - pids
        if extra or missing:
            raise SystemExit("%s %s extra=%s missing=%s" % (
                date, fn, sorted(extra)[:8], sorted(missing)[:8]))
        new, newsizes, _fac = sea.scale_groups(text, mapping, targets)
        new = fill_bare_pops_comments(new, newsizes)
        new = update_flex_region_comments(new, mapping, newsizes)
        sea.write_text(path, new, nl)
        if date != "1836.1.1":
            got = sum(newsizes.values()) * 4
            if got != new_tot:
                report.append("  WARN %s display %d != %d" % (date, got, new_tot))
    return new_tot, old_tot


def main():
    report = []
    grand_old = grand_new = 0
    for fn in FILES:
        path = os.path.join(MOD, "history", "pops", "1836.1.1", fn)
        if not os.path.isfile(path):
            report.append("MISSING FILE %s" % fn)
            continue
        n, o = scale_file(fn, report)
        grand_old += o
        grand_new += n
    report.append("GRAND %.3f -> %.3f mln (Brazil not included)" % (
        grand_old / 1e6, grand_new / 1e6))
    print("\n".join(report))


if __name__ == "__main__":
    main()
