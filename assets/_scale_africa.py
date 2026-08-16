# -*- coding: utf-8 -*-
"""Scale African pop files to the larger 1830s-1860 estimate.

size = display / 4. Cultures / pop types unchanged.
North Africa: contemporary counts (1860 only if no earlier census).
SSA: max(OWID/Frankema 1836-1860, Manning 1850 where the region is 1:1).
South Africa / Namibia / Botswana already on Frankema 1850 high — kept.
"""
from __future__ import print_function
import os, importlib.util

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
POP_ROOT = os.path.join(MOD, "history", "pops")

# Display totals (historical people on screen).
FILE_TOTAL = {
    # Maghreb — исторические. Египет и Ливия оставлены раздутыми (откат).
    "Algeria.txt": 3142556,       # OWID/Frankema 1860; 1830 French high ~3.0
    "Morocco.txt": 5000000,       # Noin / high 19th-c; no census. OWID 3.14
    "Tunisia.txt": 1235541,       # 1860 (no 1830s census)
    # "Libya.txt": 1000000,
    "West Sahara.txt": 150000,    # nomads; OWID ~800 is the Spanish posts
    # "Egypt.txt": 5500000,
    # Northeast
    "Sudan.txt": 6557378,         # Manning Eastern Sudan 1850 > OWID SD+SS 6.11
    "Ethiopia.txt": 18434000,     # OWID 1850 (max in window)
    "Eritrea.txt": 684015,
    "Somalia.txt": 1510219,       # OWID Somalia + Djibouti (no file)
    # South — already Frankema 1850 high
    "South Africa.txt": 3612000,
    "Namibia.txt": 382000,
    "Botswana.txt": 107000,
    # Central
    "Congo.txt": 511829,
    "Congo-Zaire.txt": 8303530,   # OWID DRC 1860
    "Central Africa.txt": 949659,
    "Cameroun.txt": 2886130,
    "Chad.txt": 2442180,          # Manning 1850
    "Gabon.txt": 316484,
    "Angola.txt": 4015345,        # Manning 1850
    "Equatorial Guinea.txt": 115383,
    # West — Manning 1:1 or region scaled to Manning
    "Nigeria.txt": 14857000,      # Central Sudan split with Niger
    "Niger.txt": 1083700,
    "Ghana.txt": 3043167,         # Manning Gold Coast
    "Ivory Coast.txt": 1568935,   # Manning
    "Benin.txt": 840120,
    "Togo.txt": 542053,
    "Mali.txt": 2452700,          # Western Sudan split
    "Burkina.txt": 2874200,
    "Mauritania.txt": 496500,
    "Senegambia.txt": 2020997,    # Manning Senegambia (SN+GM)
    "Guinea.txt": 1574164,        # Upper Guinea split
    "Guinea Bissau.txt": 313112,
    "Sierra Leone.txt": 1172776,
    "Liberia.txt": 502700,
    # East
    "Kenya.txt": 3529609,
    "Tanzania.txt": 5406174,
    "Uganda.txt": 3130583,
    "Rwanda-Burundi.txt": 3006266,
    "Mozambique.txt": 8392608,    # Manning 1850
    "Madagascar.txt": 2816274,    # Manning 1850
    "Malawi.txt": 2150183,
    "Zambia.txt": 1597950,
    "Zimbabwe.txt": 836674,       # OWID 1836 is the window max
    # Islands
    "Comoros.txt": 64347,
    "Mauritius.txt": 313826,      # colonial count 1860
    "Reunion.txt": 163950,
    "Sao Tome.txt": 30227,
    "Cape Verde.txt": 87833,
}

spec = importlib.util.spec_from_file_location(
    "sea", os.path.join(MOD, "assets", "_scale_east_asia_pops.py"))
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)


def main():
    report = []
    old = {}
    path0 = os.path.join(POP_ROOT, "1836.1.1")
    for fn, disp in sorted(FILE_TOTAL.items()):
        p = os.path.join(path0, fn)
        if not os.path.isfile(p):
            report.append("MISSING %s" % fn)
            continue
        t, _ = sea.read_text(p)
        old[fn] = sum(sea.file_pid_sizes(t).values()) * 4

    for date in DATES:
        for fn, disp in FILE_TOTAL.items():
            path = os.path.join(POP_ROOT, date, fn)
            if not os.path.isfile(path):
                continue
            text, nl = sea.read_text(path)
            sizes = sea.file_pid_sizes(text)
            if not sizes:
                report.append("EMPTY %s %s" % (date, fn))
                continue
            adults = {"ALL": int(round(disp / 4.0))}
            mapping = {pid: "ALL" for pid in sizes}
            new_text, new_by, fac = sea.scale_groups(text, mapping, adults)
            sea.write_text(path, new_text, nl)
            got = sum(new_by.values())
            want = adults["ALL"]
            if date == "1836.1.1" and got != want:
                report.append("WARN %s adults %s != %s" % (fn, got, want))

    report.append("Africa file targets (screen mln):")
    tot_old = tot_new = 0
    rows = []
    for fn, disp in FILE_TOTAL.items():
        o = old.get(fn)
        if o is None:
            continue
        tot_old += o
        tot_new += disp
        rows.append((o, fn, disp, disp / float(o) if o else 0))
    rows.sort(reverse=True)
    for o, fn, disp, fac in rows:
        report.append("  %s  %.3f -> %.3f  x%.2f" % (
            fn, o / 1e6, disp / 1e6, fac))
    report.append("SUM  %.3f -> %.3f mln" % (tot_old / 1e6, tot_new / 1e6))

    for date in DATES:
        s = 0
        for fn in FILE_TOTAL:
            path = os.path.join(POP_ROOT, date, fn)
            if not os.path.isfile(path):
                continue
            t, _ = sea.read_text(path)
            s += sum(sea.file_pid_sizes(t).values())
        report.append("%s Africa listed %.3f mln" % (date, s * 4 / 1e6))

    print("\n".join(report))


if __name__ == "__main__":
    main()
