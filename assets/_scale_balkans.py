# -*- coding: utf-8 -*-
"""Scale Balkan pops to historical 1836.

size = display / 4. Cultures and pop types unchanged.
Greece / Montenegro / Moldavia: city comments (larger vanilla historical).
Wallachia: 1832 statistics 1,976,809 (larger than comments).
Crete (EGY): larger 1840 estimate 172,450.
Serbia, Ionian, Ottoman Balkans, Habsburg leftovers already ~comments.
"""
from __future__ import print_function
import os, re, collections, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
POP_ROOT = os.path.join(MOD, "history", "pops")

WAL_DISPLAY = 1976809  # 1832 Wallachian statistics
CRETE_DISPLAY = 172450  # larger 1840 range 152760-172450
CRETE_PIDS = set([847, 848])
WAL_PIDS = set([664, 665, 666, 667, 668, 669])
FILES = [
    "Albania.txt", "Bosnia.txt", "Bulgaria.txt", "Greece.txt",
    "Macedonia.txt", "Montenegro.txt", "Romania.txt", "Serbia.txt",
]
# Independent states + Ottoman Balkans in these files. Not AUS (already done).
COMMENT_OWNERS = set(["GRE", "MON", "MOL", "SER", "ION", "TUR"])

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)
spec2 = importlib.util.spec_from_file_location(
    "sc", os.path.join(MOD, "assets", "_scale_fra_aus_tur_rus.py"))
s = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(s)


def build_plan(owners):
    pid_group = {}
    group_disp = {}
    meta = {}
    base = os.path.join(POP_ROOT, "1836.1.1")
    for fn in FILES:
        text, _ = sea.read_text(os.path.join(base, fn))
        rows = s.parse_base(text)
        for pid, (reg, city, disp, sz) in rows.items():
            own = owners.get(pid)
            if pid in WAL_PIDS and own == "WAL":
                g = "Wallachia"
                pid_group[pid] = g
                group_disp[g] = WAL_DISPLAY
                meta[pid] = (fn, own, g, city, disp, sz)
                continue
            if pid in CRETE_PIDS and own == "EGY":
                g = "Crete"
                pid_group[pid] = g
                group_disp[g] = CRETE_DISPLAY
                meta[pid] = (fn, own, g, city, disp, sz)
                continue
            if own not in COMMENT_OWNERS:
                continue
            if not disp:
                continue
            # Always pin to 1.1 city comments so dates 1.2-1.4 catch leftover inflation.
            g = "%s:%s" % (fn, pid)
            pid_group[pid] = g
            group_disp[g] = disp
            meta[pid] = (fn, own, g, city, disp, sz)
    group_adults = {}
    for g, d in group_disp.items():
        group_adults[g] = int(round(d / 4.0))
    return pid_group, group_adults, meta


def main():
    owners = s.load_owners()
    pid_group, group_adults, meta = build_plan(owners)
    report = []
    report.append("plan pids=%d groups=%d" % (len(pid_group), len(group_adults)))
    by_tag = collections.defaultdict(lambda: [0, 0])
    changes = []
    grouped = collections.defaultdict(list)
    for pid, (fn, own, g, city, disp, sz) in meta.items():
        grouped[g].append(pid)
    for g, pids in grouped.items():
        old_d = sum(meta[p][5] for p in pids) * 4
        new_d = group_adults[g] * 4
        own = meta[pids[0]][1]
        city = ",".join(meta[p][3] or "?" for p in pids)
        fn = meta[pids[0]][0]
        fac = (new_d / float(old_d)) if old_d else 0
        by_tag[own][0] += old_d
        by_tag[own][1] += new_d
        if abs(fac - 1.0) >= 0.03:
            changes.append((abs(fac - 1), fn, own, g, city, old_d, new_d, fac, pids))
    changes.sort(reverse=True)
    report.append("1.1 notable (|x-1|>=3%):")
    for row in changes:
        report.append("  %s %s %s [%s]  %.3f -> %.3f mln  x%.2f  pids %s" % (
            row[1], row[2], row[4], row[3],
            row[5] / 1e6, row[6] / 1e6, row[7], row[8]))
    report.append("TAG scoped display mln:")
    for tag in ["GRE", "MON", "MOL", "WAL", "EGY", "SER", "ION", "TUR"]:
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
            targets = {}
            for g in set(mapping.values()):
                targets[g] = group_adults[g]
            new_text, new_by, fac = s.scale_no_comments(text, mapping, targets)
            new_text = s.update_city_only(new_text, new_by, set(mapping))
            new_text = s.update_regions_full(new_text, new_by, set(mapping))
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
