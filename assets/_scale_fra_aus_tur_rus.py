# -*- coding: utf-8 -*-
"""Scale FRA / AUS / RUS / TUR European-core pops to historical 1836.

size = display / 4. Cultures and pop types unchanged.
Only provinces of those four tags (plus uncolonized Sakhalin).
Colonies, Turkey.txt (no figures), Iraq/Syria/Libya/Gulf left alone.
"""
from __future__ import print_function
import os, re, collections, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
POP_ROOT = os.path.join(MOD, "history", "pops")
PROV_DIR = os.path.join(MOD, "history", "provinces")

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)

OWNER_RE = re.compile(r"^\s*owner\s*=\s*([A-Z0-9]{3})\s*$", re.I)
PID_FILE = re.compile(r"^(\d+)\s+-")
CITY_CMT = re.compile(r"^#+\s*(.+?)\s*\(\s*(\d+)\s*/\s*(\d+)", re.I)
REG_CMT = re.compile(r"^#+\s*(.+?Region.*?)\s*\(\s*(\d+)", re.I)
ID_RE = re.compile(r"^(\d+)\s*=")

TUR_FILES = set([
    "Albania.txt", "Bosnia.txt", "Bulgaria.txt", "Cyprus.txt",
    "Greece.txt", "Macedonia.txt", "Romania.txt", "Serbia.txt",
    "Georgia.txt", "Montenegro.txt",
])
SAKHALIN = set([1086, 1087, 1088, 1089])
ARMENIA = set([1098, 1099, 1100, 1101])
# Bournoutian / Russian survey 1832 of the Armenian Oblast.
ARMENIA_DISPLAY = 164500


def load_owners():
    owners = {}
    for root, dirs, files in os.walk(PROV_DIR):
        for fn in files:
            m = PID_FILE.match(fn)
            if not m:
                continue
            pid = int(m.group(1))
            owner = None
            with open(os.path.join(root, fn), "r", encoding="latin-1", errors="replace") as f:
                for line in f:
                    mm = OWNER_RE.match(line.split("#", 1)[0])
                    if mm:
                        owner = mm.group(1).upper()
                        break
            owners[pid] = owner
    return owners


def in_scope(fn, pid, owner):
    if pid in SAKHALIN and fn == "Russia.txt":
        return True
    if owner == "FRA":
        return False
    if owner == "AUS":
        return True
    if owner == "RUS" and fn != "United States.txt":
        return True
    if owner == "TUR" and fn in TUR_FILES:
        return True
    return False


def parse_base(text):
    """pid -> (region, city, display_comment, size)."""
    region = ""
    pending_city = None
    pending_disp = None
    rows = {}
    pid = None
    size = 0
    city = None
    disp = None
    reg = ""
    for line in text.split("\n"):
        rm = REG_CMT.match(line.strip())
        if rm:
            region = rm.group(1).strip()
            continue
        cm = CITY_CMT.match(line.strip())
        if cm:
            pending_city = cm.group(1).strip()
            pending_disp = int(cm.group(2))
            continue
        im = ID_RE.match(line)
        if im:
            if pid is not None:
                rows[pid] = (reg, city, disp, size)
            pid = int(im.group(1))
            size = 0
            city = pending_city
            disp = pending_disp
            reg = region
            pending_city = None
            pending_disp = None
            continue
        sm = re.match(r"^\s*size\s*=\s*(\d+)", line, re.I)
        if sm:
            size += int(sm.group(1))
    if pid is not None:
        rows[pid] = (reg, city, disp, size)
    return rows


def scale_no_comments(text, pid_to_group, group_target_adults):
    sizes = sea.file_pid_sizes(text)
    group_current = collections.defaultdict(int)
    for pid, sz in sizes.items():
        g = pid_to_group.get(pid)
        if g:
            group_current[g] += sz
    pid_factor = {}
    for pid, g in pid_to_group.items():
        if pid not in sizes:
            continue
        cur = group_current.get(g, 0)
        tgt = group_target_adults[g]
        pid_factor[pid] = (float(tgt) / cur) if cur else 1.0
    new_text, new_by_pid = sea.apply_factors(text, pid_factor)
    group_new = collections.defaultdict(int)
    group_largest = {}
    for pid, sz in new_by_pid.items():
        g = pid_to_group.get(pid)
        if not g:
            continue
        group_new[g] += sz
        if g not in group_largest or sz > new_by_pid.get(group_largest[g], 0):
            group_largest[g] = pid
    for g, tgt in group_target_adults.items():
        delta = tgt - group_new.get(g, 0)
        if delta and g in group_largest:
            new_text = sea.add_remainder(new_text, group_largest[g], delta)
            new_by_pid[group_largest[g]] = new_by_pid.get(group_largest[g], 0) + delta
    return new_text, new_by_pid, pid_factor


def update_city_only(text, pid_new, scaled):
    lines = text.split("\n")
    pid_at = {}
    for i, line in enumerate(lines):
        m = re.match(r"^(\d+)\s*=", line)
        if m:
            pid_at[i] = int(m.group(1))
    for i, pid in pid_at.items():
        if pid not in scaled:
            continue
        adults = pid_new[pid]
        display = adults * 4
        j = i - 1
        while j >= 0 and lines[j].strip() == "":
            j -= 1
        if j < 0:
            continue
        cm = re.match(
            r"^(#+)([^(\n]*?)\s*\(\s*\d+\s*/\s*\d+\s*POPS\)(.*)$",
            lines[j], re.I)
        if cm:
            name = cm.group(2).rstrip()
            lines[j] = "%s%s (%d/%d POPS)%s" % (
                cm.group(1), name, display, adults, cm.group(3))
    return "\n".join(lines)


def update_regions_full(text, pid_new, scaled):
    lines = text.split("\n")
    pid_at = {}
    for i, line in enumerate(lines):
        m = re.match(r"^(\d+)\s*=", line)
        if m:
            pid_at[i] = int(m.group(1))
    region_idx = []
    for i, line in enumerate(lines):
        if re.search(r"Region", line, re.I) and line.lstrip().startswith("#"):
            region_idx.append(i)
    for k, i in enumerate(region_idx):
        end = region_idx[k + 1] if k + 1 < len(region_idx) else len(lines)
        block_pids = []
        for li in range(i, end):
            if li in pid_at:
                block_pids.append(pid_at[li])
        if not any(p in scaled for p in block_pids):
            continue
        total = 0
        for p in block_pids:
            total += pid_new.get(p, 0)
        display = total * 4
        rm = re.match(r"^(#+\s*.*?Region[^\(\n]*?)\(\s*\d+\s*\)(.*)$", lines[i], re.I)
        if rm:
            lines[i] = "%s(%d)%s" % (rm.group(1), display, rm.group(2))
    return "\n".join(lines)


def build_plan(owners):
    pid_group = {}
    group_disp = {}
    meta = {}
    base = os.path.join(POP_ROOT, "1836.1.1")
    for fn in os.listdir(base):
        if not fn.lower().endswith(".txt"):
            continue
        text, _ = sea.read_text(os.path.join(base, fn))
        rows = parse_base(text)
        for pid, (reg, city, disp, sz) in rows.items():
            own = owners.get(pid)
            if not in_scope(fn, pid, own):
                continue
            tag = own or "NONE"
            if pid in ARMENIA:
                g = "Armenia"
                pid_group[pid] = g
                group_disp[g] = ARMENIA_DISPLAY
                meta[pid] = (fn, tag, g, city, disp, sz)
                continue
            if not disp:
                continue
            actual_d = sz * 4
            if pid not in SAKHALIN:
                if actual_d <= 0:
                    continue
                if abs(actual_d / float(disp) - 1.0) < 0.12:
                    continue
            g = "%s:%s" % (fn, pid)
            pid_group[pid] = g
            group_disp[g] = disp
            meta[pid] = (fn, tag, g, city, disp, sz)
    group_adults = {}
    for g, d in group_disp.items():
        group_adults[g] = int(round(d / 4.0))
    # exact remainder on Armenia
    if "Armenia" in group_adults:
        group_adults["Armenia"] = int(round(ARMENIA_DISPLAY / 4.0))
    return pid_group, group_adults, meta


def main():
    owners = load_owners()
    pid_group, group_adults, meta = build_plan(owners)
    by_tag = collections.defaultdict(lambda: [0, 0])
    report = []
    report.append("plan pids=%d groups=%d" % (len(pid_group), len(group_adults)))
    changes = []
    for pid, (fn, own, g, city, disp, sz) in meta.items():
        tgt = group_adults[g]
        # for multi-pid groups, show later
        if g.startswith(fn):
            old_d = sz * 4
            new_d = tgt * 4
            if old_d:
                fac = new_d / float(old_d)
            else:
                fac = 0
            by_tag[own][0] += old_d
            by_tag[own][1] += new_d
            if abs(fac - 1.0) >= 0.03:
                changes.append((abs(fac - 1), fn, pid, own, city, old_d, new_d, fac))
    # Armenia group
    arm_old = sum(meta[p][5] for p in ARMENIA if p in meta) * 4
    arm_new = ARMENIA_DISPLAY
    by_tag["RUS"][0] += arm_old
    by_tag["RUS"][1] += arm_new
    sak_old = sak_new = 0
    for pid in SAKHALIN:
        if pid in meta:
            sak_old += meta[pid][5] * 4
            sak_new += group_adults[pid_group[pid]] * 4

    changes.sort(reverse=True)
    report.append("notable (|x-1|>=3%):")
    for row in changes[:80]:
        report.append("  %s pid %s %s %s  %.3f -> %.3f mln  x%.2f" % (
            row[1], row[2], row[3], row[4],
            row[5] / 1e6, row[6] / 1e6, row[7]))
    report.append("Armenia  %.3f -> %.3f mln" % (arm_old / 1e6, arm_new / 1e6))
    report.append("Sakhalin %.3f -> %.3f mln" % (sak_old / 1e6, sak_new / 1e6))
    report.append("TAG totals (scoped, display mln):")
    for tag in ["FRA", "AUS", "RUS", "TUR", "NONE"]:
        o, n = by_tag[tag]
        if o:
            report.append("  %s  %.3f -> %.3f  x%.3f" % (
                tag, o / 1e6, n / 1e6, n / float(o)))

    files = sorted(set(meta[p][0] for p in pid_group))
    for date in DATES:
        for fn in files:
            path = os.path.join(POP_ROOT, date, fn)
            if not os.path.isfile(path):
                report.append("MISSING %s %s" % (date, fn))
                continue
            text, nl = sea.read_text(path)
            sizes = sea.file_pid_sizes(text)
            mapping = {p: g for p, g in pid_group.items() if p in sizes}
            if not mapping:
                continue
            extra = set(mapping) - set(sizes)
            if extra:
                report.append("WARN %s %s missing pids %s" % (
                    date, fn, sorted(extra)[:6]))
            targets = {}
            for g in set(mapping.values()):
                targets[g] = group_adults[g]
            new_text, new_by, fac = scale_no_comments(text, mapping, targets)
            new_text = update_city_only(new_text, new_by, set(mapping))
            new_text = update_regions_full(new_text, new_by, set(mapping))
            sea.write_text(path, new_text, nl)
            if date == "1836.1.1":
                got = sum(new_by.get(p, 0) for p in mapping)
                want = sum(targets[g] for g in set(mapping.values()))
                if got != want:
                    report.append("WARN %s %s adults %s != %s" % (
                        date, fn, got, want))

    print("\n".join(report))


if __name__ == "__main__":
    main()
