# -*- coding: utf-8 -*-
"""Raise tag RUS to VIII revision 1834/35. Finland untouched.

Display = size x 4. Cultures / pop types unchanged.
Target: Wikipedia VIII revision 59,132,955 (larger than Kabuzan
okladnaya 52.1). Covers owner=RUS: European Russia, Siberia,
Caucasus, Baltics, Ukraine, Belarus, Bessarabia, Kazakh steppe,
Alaska. Not FIN, not POL, not uncolonized Sakhalin, not Qing Amur.
"""
from __future__ import print_function
import os, collections, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
POP_ROOT = os.path.join(MOD, "history", "pops")
RUS_DISPLAY = 59132955  # VIII revision, both sexes
MOSCOW = 1008

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)
spec2 = importlib.util.spec_from_file_location(
    "sc", os.path.join(MOD, "assets", "_scale_fra_aus_tur_rus.py"))
s = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(s)


def rus_pids_in(text, owners):
    out = []
    for pid in sea.file_pid_sizes(text):
        if owners.get(pid) == "RUS":
            out.append(pid)
    return out


def main():
    owners = s.load_owners()
    target_adults = int(round(RUS_DISPLAY / 4.0))
    report = []
    report.append("RUS target %.3f mln  adults %d" % (
        target_adults * 4 / 1e6, target_adults))

    for date in DATES:
        pop = os.path.join(POP_ROOT, date)
        files = sorted(fn for fn in os.listdir(pop) if fn.endswith(".txt"))
        current = 0
        file_pids = {}
        for fn in files:
            path = os.path.join(pop, fn)
            text, _ = sea.read_text(path)
            sizes = sea.file_pid_sizes(text)
            pids = [p for p in sizes if owners.get(p) == "RUS"]
            if not pids:
                continue
            file_pids[fn] = pids
            current += sum(sizes[p] for p in pids)
        if current <= 0:
            report.append("WARN %s no RUS" % date)
            continue
        factor = float(target_adults) / current
        got = 0
        largest_pid = None
        largest_sz = -1
        largest_fn = None
        by_file = []
        for fn, pids in file_pids.items():
            path = os.path.join(pop, fn)
            text, nl = sea.read_text(path)
            facmap = {p: factor for p in pids}
            new_text, new_by = sea.apply_factors(text, facmap)
            rus_sum = sum(new_by.get(p, 0) for p in pids)
            got += rus_sum
            by_file.append((rus_sum, fn, rus_sum * 4 / 1e6))
            for p in pids:
                sz = new_by.get(p, 0)
                if sz > largest_sz:
                    largest_sz = sz
                    largest_pid = p
                    largest_fn = fn
            new_text = sea.update_comments(new_text, new_by, None)
            sea.write_text(path, new_text, nl)

        delta = target_adults - got
        if delta and largest_fn:
            path = os.path.join(pop, largest_fn)
            text, nl = sea.read_text(path)
            text = sea.add_remainder(text, largest_pid, delta)
            sizes = sea.file_pid_sizes(text)
            text = sea.update_comments(text, sizes, None)
            sea.write_text(path, text, nl)
            got += delta

        if date == "1836.1.1":
            report.append("factor x%.4f  remainder %d on pid %s in %s" % (
                factor, delta, largest_pid, largest_fn))
            by_file.sort(reverse=True)
            report.append("by file (screen mln):")
            for _, fn, mln in by_file:
                report.append("  %s  %.3f" % (fn, mln))
        report.append("%s RUS screen %.3f mln" % (date, got * 4 / 1e6))
        if got != target_adults:
            report.append("WARN adults %s != %s" % (got, target_adults))

        # Finland / Poland sanity
        fin = pol = 0
        for fn in files:
            text, _ = sea.read_text(os.path.join(pop, fn))
            for pid, sz in sea.file_pid_sizes(text).items():
                o = owners.get(pid)
                if o == "FIN":
                    fin += sz
                elif o == "POL":
                    pol += sz
        if date == "1836.1.1":
            report.append("FIN untouched %.3f mln  POL untouched %.3f mln" % (
                fin * 4 / 1e6, pol * 4 / 1e6))

    print("\n".join(report))


if __name__ == "__main__":
    main()
