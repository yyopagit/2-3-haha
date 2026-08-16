# -*- coding: utf-8 -*-
"""Scale TUR provinces in Turkey.txt to 1844, not 1831.

1831 counted males, missed the east, and undercounted the periphery
(Kars, Trabzon, Adana). 1844 is the first fuller count: Doğanay puts
Anatolia at 10.5 mln. Ubicini 1844 has no eyalet split, so regional
shares come from the 1914 census (same geography, complete vilayets),
scaled down to the 1844 Anatolia total.

Kars / Ardahan left the empire in 1878 — 1914 has no row. Kars uses
the high reconstruction of the sancak through 1877 (80-100k). Cildir
uses 1831 males x2 with 1844 completeness (10.5/7.5).

Istanbul: Ubicini 1844. East Thrace: same 3 pids as before (Edirne
vilayet later includes Greece.txt).

EGY pids (Marash, Antep, Antioch) left alone.
Cultures / pop types unchanged. size = display / 4.
"""
from __future__ import print_function
import os, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
POP_ROOT = os.path.join(MOD, "history", "pops")

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)

# Doğanay / 1844 census geography: Anatolia 10.5 mln (larger than 1831 7.5).
ANATOLIA_1844 = 10500000

GROUPS = {
    "Istanbul": [860, 861],
    "Thrace": [828, 858, 859],
    "Anadolu": [
        862, 863, 864, 865, 866, 867, 868, 869, 870, 871, 872,
        876, 880, 881, 883,
    ],
    "Karaman": [873, 874, 875],
    "Sivas": [877, 878, 879],
    "Adana": [894, 895],
    "Trabzon": [882, 884],
    "Kars": [885],
    "Cildir": [886],
    "East": [887, 888, 889, 890, 891, 892, 893, 899],
}

# 1914 official totals (Karpat / Memalik-i Osmaniye 1330). Independent
# sanjaks listed separately so Hudavendigar is Bursa remainder.
W1914 = {
    "Anadolu": (
        325153 +   # Izmit
        609160 +   # Hudavendigar (Bursa)
        472970 +   # Karesi (Balikesir)
        165815 +   # Kale-i Sultaniye (Canakkale)
        285820 +   # Karahisar-i Sahip (Afyon)
        316894 +   # Kutahya
        152726 +   # Eskisehir
        1608742 +  # Aydin (Izmir / Manisa / Denizli)
        210874 +   # Mentese (Mugla)
        953817 +   # Ankara
        767227 +   # Kastamonu (incl. Sinop)
        408648     # Bolu
    ),
    "Karaman": (
        789308 +   # Konya
        249686 +   # Antalya
        291117     # Nigde (Konya basin; game Konya pid)
    ),
    "Sivas": (
        1169443 +  # Sivas (incl. Amasya / Tokat)
        263074     # Kayseri
    ),
    "Adana": (
        411023 +   # Adana
        105194     # Icel / Mersin
    ),
    "Trabzon": (
        1122947 +  # Trabzon (incl. Giresun)
        393302     # Canik / Samsun — no own pid, Pontic coast
    ),
    "East": (
        815432 +   # Erzurum (incl. Erzincan)
        259141 +   # Van (incl. Hakkari)
        437479 +   # Bitlis
        538227 +   # Mamuret-ul-Aziz (Malatya / Harput)
        619825 +   # Diyarbekir
        170988     # Urfa
    ),
}

# Pre-1878. Kars paper: sancak 80-100k through 1877. Cildir: 1831
# males 78360 x2 x (10.5/7.5).
KARS_1844 = 100000
CILDIR_1844 = int(round(78360 * 2.0 * (ANATOLIA_1844 / 7500000.0)))

mapped = sum(W1914.values())
rest = ANATOLIA_1844 - KARS_1844 - CILDIR_1844
scale = rest / float(mapped)

DISPLAY = {
    "Istanbul": 891000,   # Ubicini 1844
    "Thrace": 700000,     # Edirne + Kirklareli + Gallipoli; later vilayet includes Greece.txt
    "Kars": KARS_1844,
    "Cildir": CILDIR_1844,
}
for name, raw in W1914.items():
    DISPLAY[name] = raw * scale

EGY_SKIP = set([896, 898, 900])

ORDER = [
    "Istanbul", "Thrace", "Anadolu", "Karaman", "Sivas",
    "Adana", "Trabzon", "Kars", "Cildir", "East",
]


def main():
    pid_group = {}
    for g, pids in GROUPS.items():
        for pid in pids:
            pid_group[pid] = g
    adults = {}
    for g, disp in DISPLAY.items():
        adults[g] = int(round(disp / 4.0))

    report = []
    report.append("Anatolia 1844 target %.3f mln  1914-share scale x%.4f" % (
        ANATOLIA_1844 / 1e6, scale))
    report.append("1914 mapped %.3f mln  Kars+Cildir %.3f" % (
        mapped / 1e6, (KARS_1844 + CILDIR_1844) / 1e6))
    report.append("group display targets:")
    tot = 0
    for g in ORDER:
        report.append("  %s  %.3f mln  adults %d" % (
            g, adults[g] * 4 / 1e6, adults[g]))
        tot += adults[g] * 4
    report.append("TUR Turkey.txt target %.3f mln" % (tot / 1e6))

    for date in DATES:
        path = os.path.join(POP_ROOT, date, "Turkey.txt")
        text, nl = sea.read_text(path)
        sizes = sea.file_pid_sizes(text)
        mapping = {p: g for p, g in pid_group.items() if p in sizes}
        missing = set(pid_group) - set(sizes)
        if missing:
            report.append("WARN %s missing %s" % (date, sorted(missing)))
        extra_egy = [p for p in EGY_SKIP if p in sizes]
        new_text, new_by, fac = sea.scale_groups(text, mapping, adults)
        sea.write_text(path, new_text, nl)
        got = sum(new_by.get(p, 0) for p in mapping)
        want = sum(adults[g] for g in set(mapping.values()))
        egy = sum(new_by.get(p, 0) for p in extra_egy)
        if date == "1836.1.1":
            report.append("factors vs current file:")
            seen = {}
            for pid, g in mapping.items():
                if g not in seen:
                    seen[g] = fac[pid]
            for g in ORDER:
                if g in seen:
                    report.append("  %s x%.3f" % (g, seen[g]))
            report.append("TUR screen %.3f mln  EGY leftover %.3f mln" % (
                got * 4 / 1e6, egy * 4 / 1e6))
            if got != want:
                report.append("WARN adults %s != %s" % (got, want))
        else:
            if got != want:
                report.append("WARN %s adults %s != %s" % (date, got, want))

    print("\n".join(report))


if __name__ == "__main__":
    main()
