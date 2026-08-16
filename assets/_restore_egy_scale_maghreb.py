# -*- coding: utf-8 -*-
"""Restore remaining EGY pops (Sudan/Eritrea/Crete) from pre-Africa commit;
scale Algeria/Morocco/Tunisia to historical 1830-60."""
from __future__ import print_function
import os, subprocess, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
OLD = "de57a9d"
POP_ROOT = os.path.join(MOD, "history", "pops")

MAGHREB = {
    "Algeria.txt": 3142556,   # OWID/Frankema 1860; French ~3.0 in 1830
    "Morocco.txt": 5000000,   # Noin / high 19th-c
    "Tunisia.txt": 1235541,   # 1860
}

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)
spec2 = importlib.util.spec_from_file_location(
    "sc", os.path.join(MOD, "assets", "_scale_fra_aus_tur_rus.py"))
s = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(s)


def git_text(rev, rel):
    raw = subprocess.check_output(
        ["git", "show", "%s:%s" % (rev, rel.replace("\\", "/"))],
        cwd=MOD,
    )
    return raw.decode("latin-1")


def restore_pids(date, fn, pids, report):
    rel = "history/pops/%s/%s" % (date, fn)
    path = os.path.join(MOD, rel.replace("/", os.sep))
    cur, nl = sea.read_text(path)
    old = git_text(OLD, rel)
    old_sz = sea.file_pid_sizes(old)
    cur_sz = sea.file_pid_sizes(cur)
    fac = {}
    want = {}
    for pid in pids:
        if pid not in cur_sz or pid not in old_sz:
            report.append("MISSING %s %s pid %s" % (date, fn, pid))
            continue
        if cur_sz[pid] <= 0:
            continue
        fac[pid] = float(old_sz[pid]) / cur_sz[pid]
        want[pid] = old_sz[pid]
    if not fac:
        return
    new_text, new_by = sea.apply_factors(cur, fac)
    for pid, tgt in want.items():
        delta = tgt - new_by.get(pid, 0)
        if delta:
            new_text = sea.add_remainder(new_text, pid, delta)
            new_by[pid] = new_by.get(pid, 0) + delta
    new_text = sea.update_comments(new_text, new_by, None)
    sea.write_text(path, new_text, nl)
    if date == "1836.1.1":
        before = sum(cur_sz[p] for p in fac) * 4
        after = sum(new_by[p] for p in fac) * 4
        report.append("%s %s  %.3f -> %.3f mln" % (fn, ",".join(str(p) for p in sorted(fac)[:3]) + "...", before / 1e6, after / 1e6))


def scale_file(date, fn, disp, report, old_disp):
    path = os.path.join(POP_ROOT, date, fn)
    text, nl = sea.read_text(path)
    sizes = sea.file_pid_sizes(text)
    adults = {"ALL": int(round(disp / 4.0))}
    mapping = {pid: "ALL" for pid in sizes}
    new_text, new_by, fac = sea.scale_groups(text, mapping, adults)
    sea.write_text(path, new_text, nl)
    if date == "1836.1.1":
        got = sum(new_by.values()) * 4
        report.append("%s  %.3f -> %.3f mln (target %.3f)" % (
            fn, old_disp[fn] / 1e6, got / 1e6, disp / 1e6))


def main():
    owners = s.load_owners()
    report = []
    egy_sudan = sorted(p for p, o in owners.items() if o == "EGY" and 1827 <= p <= 2564)
    # keep only pids that exist in Sudan
    sudan0, _ = sea.read_text(os.path.join(POP_ROOT, "1836.1.1", "Sudan.txt"))
    egy_sudan = [p for p in egy_sudan if p in sea.file_pid_sizes(sudan0)]
    ere0, _ = sea.read_text(os.path.join(POP_ROOT, "1836.1.1", "Eritrea.txt"))
    egy_eri = sorted(sea.file_pid_sizes(ere0))
    crete = [847, 848]

    report.append("Restore EGY from %s" % OLD)
    for date in DATES:
        restore_pids(date, "Sudan.txt", egy_sudan, report)
        restore_pids(date, "Eritrea.txt", egy_eri, report)
        restore_pids(date, "Greece.txt", crete, report)

    old_disp = {}
    for fn in MAGHREB:
        t, _ = sea.read_text(os.path.join(POP_ROOT, "1836.1.1", fn))
        old_disp[fn] = sum(sea.file_pid_sizes(t).values()) * 4
    report.append("Scale Maghreb historical")
    for date in DATES:
        for fn, disp in MAGHREB.items():
            scale_file(date, fn, disp, report, old_disp)

    # EGY tag check
    egy_files = [
        "Egypt.txt", "Sudan.txt", "Eritrea.txt", "Syria.txt",
        "Israel-Palestine.txt", "Jordan.txt", "Lebanon.txt",
        "Turkey.txt", "Greece.txt",
    ]
    report.append("EGY-owned screen by file:")
    tot = 0
    t0, _ = sea.read_text(os.path.join(POP_ROOT, "1836.1.1", "Egypt.txt"))
    # reuse owners
    for fn in egy_files:
        t, _ = sea.read_text(os.path.join(POP_ROOT, "1836.1.1", fn))
        sizes = sea.file_pid_sizes(t)
        sm = 0
        for pid, sz in sizes.items():
            if fn == "Egypt.txt" or owners.get(pid) == "EGY":
                if fn != "Egypt.txt" and owners.get(pid) != "EGY":
                    continue
                if fn in ("Turkey.txt", "Greece.txt", "Sudan.txt", "Syria.txt",
                          "Israel-Palestine.txt", "Jordan.txt", "Lebanon.txt",
                          "Eritrea.txt") and owners.get(pid) != "EGY":
                    continue
                sm += sz
        # Egypt.txt all pids are EGY
        if fn == "Egypt.txt":
            sm = sum(sizes.values())
        else:
            sm = sum(sz for pid, sz in sizes.items() if owners.get(pid) == "EGY")
        if sm:
            report.append("  %s  %.3f" % (fn, sm * 4 / 1e6))
            tot += sm
    report.append("EGY tag total %.3f mln" % (tot * 4 / 1e6))
    print("\n".join(report))


if __name__ == "__main__":
    main()
