# -*- coding: utf-8 -*-
"""Scale Korea and Central Asian tags to historical 1836.

size = display / 4. Cultures unchanged.
Korea: Kwon/Shin reconstruction of 1837 hogun x2.5.
AFG/KHI/BUK/KOK: larger 1830s estimates. CHI and uncolonized steppe left.
"""
from __future__ import print_function
import os, collections, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
POP_ROOT = os.path.join(MOD, "history", "pops")

KOREA_DISPLAY = 16772500  # 6,709,000 hogun 1837 x 2.5
AFG_DISPLAY = 5000000
KHI_DISPLAY = 800000
BUK_DISPLAY = 3000000
KOK_DISPLAY = 5500000  # Iranica: >5 mln, 3 + 2-2.5 nomads

CA_FILES = [
    "Afghanistan.txt", "Uzbekistan.txt", "Kazakhstan.txt",
    "Turkmenistan.txt", "Kirghizstan.txt", "Tajikistan.txt",
]
TAG_TARGET = {
    "KOR": KOREA_DISPLAY,
    "AFG": AFG_DISPLAY,
    "KHI": KHI_DISPLAY,
    "BUK": BUK_DISPLAY,
    "KOK": KOK_DISPLAY,
}

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)
spec2 = importlib.util.spec_from_file_location(
    "sc", os.path.join(MOD, "assets", "_scale_fra_aus_tur_rus.py"))
s = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(s)


def main():
    owners = s.load_owners()
    files = ["Korea.txt"] + CA_FILES
    pid_group = {}
    base = os.path.join(POP_ROOT, "1836.1.1")
    for fn in files:
        text, _ = sea.read_text(os.path.join(base, fn))
        for pid in sea.file_pid_sizes(text):
            tag = owners.get(pid)
            if tag in TAG_TARGET:
                pid_group[pid] = tag
    adults = {tag: int(round(disp / 4.0)) for tag, disp in TAG_TARGET.items()}

    share = collections.defaultdict(lambda: collections.defaultdict(int))
    for fn in files:
        text, _ = sea.read_text(os.path.join(base, fn))
        for pid, sz in sea.file_pid_sizes(text).items():
            tag = pid_group.get(pid)
            if tag:
                share[tag][fn] += sz
    tag_total = {t: sum(share[t].values()) for t in share}
    file_adults = collections.defaultdict(dict)
    for tag, fns in share.items():
        tgt = adults[tag]
        used = 0
        items = list(fns.items())
        for i, (fn, sz) in enumerate(items):
            if i == len(items) - 1:
                part = tgt - used
            else:
                part = int(round(tgt * (float(sz) / tag_total[tag])))
                used += part
            file_adults[fn][tag] = part

    report = ["targets screen mln:"]
    for tag in ["KOR", "AFG", "KHI", "BUK", "KOK"]:
        n = sum(1 for g in pid_group.values() if g == tag)
        report.append("  %s  pids %d  %.3f" % (tag, n, TAG_TARGET[tag] / 1e6))

    for date in DATES:
        for fn in files:
            path = os.path.join(POP_ROOT, date, fn)
            text, nl = sea.read_text(path)
            sizes = sea.file_pid_sizes(text)
            mapping = {p: g for p, g in pid_group.items() if p in sizes}
            if not mapping:
                continue
            targets = {g: file_adults[fn][g] for g in set(mapping.values())}
            new_text, new_by, fac = sea.scale_groups(text, mapping, targets)
            sea.write_text(path, new_text, nl)
            if date == "1836.1.1":
                got = sum(new_by.get(p, 0) for p in mapping)
                want = sum(targets.values())
                facs = {}
                for pid, g in mapping.items():
                    facs[g] = fac[pid]
                report.append("%s %s adults %s/%s  %s" % (
                    fn, ",".join(sorted(targets)), got, want,
                    " ".join("%sx%.2f" % (g, facs[g]) for g in sorted(facs))))
                if got != want:
                    report.append("WARN %s" % fn)

    tot = collections.defaultdict(int)
    for fn in files:
        text, _ = sea.read_text(os.path.join(POP_ROOT, "1836.1.1", fn))
        for pid, sz in sea.file_pid_sizes(text).items():
            tag = owners.get(pid)
            if tag in TAG_TARGET:
                tot[tag] += sz * 4
    report.append("tag totals screen mln:")
    for tag in ["KOR", "AFG", "KHI", "BUK", "KOK"]:
        report.append("  %s  %.3f  (target %.3f)" % (
            tag, tot[tag] / 1e6, TAG_TARGET[tag] / 1e6))
    print("\n".join(report))


if __name__ == "__main__":
    main()
