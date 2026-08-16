# -*- coding: utf-8 -*-
"""Scale China / Indochina pops to historical 1836 (display = size * 4). Verify Japan."""
from __future__ import print_function
import os, re, collections

MOD = r"c:\Games\Vic2LV2\Victoria 2\mod\5"
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
PROV_DIR = os.path.join(MOD, "history", "provinces")

SIZE_LINE = re.compile(r"^(\s*size\s*=\s*)(\d+)(\s*)$", re.I | re.M)
ID_LINE = re.compile(r"^(\d+)\s*=", re.M)
CITY_CMT = re.compile(
    r"^(#+)([^(\r\n]*?)\s*\(\s*\d+\s*/\s*\d+\s*POPS\)(.*)$",
    re.I | re.M,
)
REGION_CMT = re.compile(
    r"^(#+\s*.*?Region[^\(\r\n]*?)\(\s*\d+\s*\)(.*)$",
    re.I | re.M,
)

# Cao Shuji 1820 / 1851; interpolate to 1836 (16/31).
CAO = {
    "Jiangsu": (39435000, 44719000),
    "Zhejiang": (27335000, 30276000),
    "Jiangxi": (22346000, 24286000),
    "Anhui": (32068000, 37386000),
    "Shandong": (32326000, 35585000),
    "Henan": (27498000, 30771000),
    "Zhili": (23082000, 27055000),
    "Hubei": (19482000, 22187000),
    "Hunan": (18981000, 21809000),
    "Shanxi": (14339000, 15838000),
    "Sichuan": (23565000, 29465000),
    "Guangdong": (21405000, 23859000),
    "Fujian": (13779000, 16545000),
    "Guangxi": (9461000, 10962000),
    "Yunnan": (10299000, 12675000),
    "Guizhou": (7478000, 8794000),
    "Shaanxi": (12130000, 13269000),
    "Gansu": (17605000, 18990000),
    "Liaoning": (1757000, 2582000),
    "Jilin": (567000, 1238000),
    "Heilongjiang": (168000, 370000),
    "Mongolia": (2290000, 2656000),
    "Qinghai": (300000, 314000),
    "Xinjiang": (1105000, 1363000),
    "Tibet": (1190000, 1231000),
}

NAME_TO_QING = {
    "Anqing": "Anhui", "Chizhou": "Anhui", "Fengyang": "Anhui", "Huizhou": "Anhui",
    "Luzhou": "Anhui", "Ningguo": "Anhui", "Sizhou": "Anhui", "Taiping": "Anhui",
    "Yingzhou": "Anhui",
    "Mukden": "Liaoning", "Jinzhou": "Liaoning", "Port Arthur": "Liaoning",
    "Fuzhou": "Fujian", "Jianning": "Fujian", "Quanzhou": "Fujian",
    "Tingzhou": "Fujian", "Zhangzhou": "Fujian",
    "Gansu": "Gansu", "Gongchang": "Gansu", "Lanzhou": "Gansu",
    "Ningxia": "Gansu", "Pingliang": "Gansu",
    "Canton": "Guangdong", "Chaozhou": "Guangdong", "Gauzhou": "Guangdong",
    "Hong Kong": "Guangdong", "Waizao": "Guangdong", "Hainan": "Guangdong",
    "Shaozhou": "Guangdong", "Zhaoqing": "Guangdong", "Macao": "Guangdong",
    "Nanning": "Guangxi", "Guilin": "Guangxi", "Pingle": "Guangxi",
    "Guiyang": "Guizhou", "Anshun": "Guizhou", "Zhenyuan": "Guizhou",
    "Kaifeng": "Henan", "Guide": "Henan", "Henan": "Henan", "Huaiqing": "Henan",
    "Chenzhou": "Henan", "Nanyang": "Henan", "Runing": "Henan", "Weihui": "Henan",
    "Hanyang": "Hubei", "Dean": "Hubei", "Huangzhou": "Hubei", "Anlu": "Hubei",
    "Jingzhou": "Hubei", "Shinan": "Hubei", "Wuchang": "Hubei", "Xiangyang": "Hubei",
    "Changsha": "Hunan", "Changde": "Hunan", "Baoqing": "Hunan", "Hengzhou": "Hunan",
    "Yuezhou": "Hunan", "Yongshun": "Hunan", "Yongzhou": "Hunan",
    "Guihua Tumed": "Inner Mongolia", "Jirim Chuulgan": "Inner Mongolia",
    "Ulaan Chab Chuulghan": "Inner Mongolia", "Yeke Juu Chuulghan": "Inner Mongolia",
    "Nanjing": "Jiangsu", "Huaian": "Jiangsu", "Changzhou": "Jiangsu",
    "Shanghai": "Jiangsu", "Suzhou": "Jiangsu", "Taicangzhou": "Jiangsu",
    "Tongzhou": "Jiangsu", "Xuzhou": "Jiangsu", "Yangzhou": "Jiangsu",
    "Zhenjiang": "Jiangsu",
    "Nanchang": "Jiangxi", "Guangxin": "Jiangxi", "Jian": "Jiangxi",
    "Jianchang": "Jiangxi", "Jiujiang": "Jiangxi", "Ganzhou": "Jiangxi",
    "Raozhou": "Jiangxi",
    "Qiqihar": "Heilongjiang", "Aigun": "Heilongjiang", "Manzhouli": "Heilongjiang",
    "Ninguta": "Jilin", "Jilin": "Jilin",
    "Makhai": "Qinghai", "Balekungomi": "Qinghai", "Kegudo": "Qinghai",
    "Xian": "Shaanxi", "Yenan": "Shaanxi", "Hanzhong": "Shaanxi", "Shangzhou": "Shaanxi",
    "Jinan": "Shandong", "Caozhou": "Shandong", "Laizhou": "Shandong",
    "Qingdao": "Shandong", "Qingzhou": "Shandong", "Taian": "Shandong",
    "Weihaiwei": "Shandong", "Wuding": "Shandong", "Yizhou": "Shandong",
    "Taiyuan": "Shanxi", "Datong": "Shanxi", "Fenzhou": "Shanxi",
    "Luan": "Shanxi", "Pingyang": "Shanxi",
    "Chengdu": "Sichuan", "Chongqing": "Sichuan", "Kuizhou": "Sichuan",
    "Jiading": "Sichuan", "Longan": "Sichuan", "Yibin": "Sichuan",
    "Tongchuan": "Sichuan", "Yazhou": "Sichuan", "Shunqing": "Sichuan",
    "Baotung": "Sichuan",
    "Kunming": "Yunnan", "Dali": "Yunnan", "Puer": "Yunnan",
    "Hangzhou": "Zhejiang", "Ningbo": "Zhejiang", "Jinhua": "Zhejiang",
    "Taizhou": "Zhejiang", "Shaoxing": "Zhejiang", "Huzhou": "Zhejiang",
    "Jiaxing": "Zhejiang", "Wenzhou": "Zhejiang",
    "Beijing": "Zhili", "Tianjin": "Zhili", "Chengde": "Zhili",
    "Shuntian": "Zhili", "Daming": "Zhili", "Zhongding": "Zhili",
    "Jizhou": "Zhili",
}


def interp1836(a, b):
    return a + (16.0 / 31.0) * (b - a)


def cao_display(name):
    a, b = CAO[name]
    return interp1836(a, b)


def load_id_name():
    m = {}
    for dirpath, _, files in os.walk(PROV_DIR):
        for fn in files:
            if not fn.endswith(".txt") or " - " not in fn:
                continue
            base = fn[:-4]
            pid_s, name = base.split(" - ", 1)
            if pid_s.isdigit():
                m[int(pid_s)] = name
    return m


def read_text(path):
    raw = open(path, "rb").read()
    nl = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("latin-1"), nl


def write_text(path, text, nl):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if nl == "\r\n":
        out = text.replace("\n", "\r\n")
    else:
        out = text
    open(path, "wb").write(out.encode("latin-1"))


def parse_blocks(text):
    """List of (pid, start, end) char spans for each province block."""
    matches = list(ID_LINE.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((int(m.group(1)), start, end))
    return blocks


def block_size_sum(text, start, end):
    total = 0
    for m in SIZE_LINE.finditer(text[start:end]):
        total += int(m.group(2))
    return total


def apply_factors(text, pid_factor, skip_pids=None):
    skip_pids = skip_pids or set()
    blocks = parse_blocks(text)
    # scale each block independently; collect (start,end,new_chunk)
    pieces = []
    last = 0
    new_by_pid = {}
    for pid, start, end in blocks:
        chunk = text[start:end]
        if pid in skip_pids or pid not in pid_factor:
            pieces.append(text[last:end])
            last = end
            new_by_pid[pid] = block_size_sum(text, start, end)
            continue
        fac = pid_factor[pid]
        sizes = []

        def repl(m):
            old = int(m.group(2))
            if old <= 0:
                new = 0
            else:
                new = int(round(old * fac))
                if new < 1:
                    new = 1
            sizes.append(new)
            return m.group(1) + str(new) + m.group(3)

        new_chunk = SIZE_LINE.sub(repl, chunk)
        new_by_pid[pid] = sum(sizes)
        pieces.append(text[last:start] + new_chunk)
        last = end
    pieces.append(text[last:])
    return "".join(pieces), new_by_pid


def add_remainder(text, pid, delta):
    """Add delta to the largest size= in that province."""
    if delta == 0:
        return text
    blocks = parse_blocks(text)
    for bpid, start, end in blocks:
        if bpid != pid:
            continue
        chunk = text[start:end]
        best = None
        best_val = -1
        for m in SIZE_LINE.finditer(chunk):
            val = int(m.group(2))
            if val > best_val:
                best_val = val
                best = m
        if best is None:
            return text
        new_val = max(1, best_val + delta)
        new_chunk = chunk[:best.start()] + best.group(1) + str(new_val) + best.group(3) + chunk[best.end():]
        return text[:start] + new_chunk + text[end:]
    return text


def update_comments(text, pid_new, pid_city_span):
    """Update (display/adults POPS) comments immediately above each pid."""
    # Work from the original text: for each pid, find the last # comment before the id line.
    out = text
    # Safer: line-based.
    lines = out.split("\n")
    pid_at_line = {}
    for i, line in enumerate(lines):
        m = re.match(r"^(\d+)\s*=", line)
        if m:
            pid_at_line[i] = int(m.group(1))
    for i, pid in pid_at_line.items():
        if pid not in pid_new:
            continue
        adults = pid_new[pid]
        display = adults * 4
        # walk up over blank lines to a city comment
        j = i - 1
        while j >= 0 and lines[j].strip() == "":
            j -= 1
        if j < 0:
            continue
        cm = re.match(
            r"^(#+)([^(\n]*?)\s*\(\s*\d+\s*/\s*\d+\s*POPS\)(.*)$",
            lines[j],
            re.I,
        )
        if cm:
            name = cm.group(2).rstrip()
            lines[j] = "%s%s (%d/%d POPS)%s" % (
                cm.group(1), name, display, adults, cm.group(3),
            )
    # region comments: sum pids that follow until next Region comment
    region_idx = []
    for i, line in enumerate(lines):
        if re.search(r"Region", line, re.I) and line.lstrip().startswith("#"):
            region_idx.append(i)
    for k, i in enumerate(region_idx):
        end = region_idx[k + 1] if k + 1 < len(region_idx) else len(lines)
        total = 0
        for li in range(i, end):
            if li in pid_at_line:
                total += pid_new.get(pid_at_line[li], 0)
        display = total * 4
        rm = re.match(r"^(#+\s*.*?Region[^\(\n]*?)\(\s*\d+\s*\)(.*)$", lines[i], re.I)
        if rm:
            lines[i] = "%s(%d)%s" % (rm.group(1), display, rm.group(2))
        else:
            rm2 = re.match(r"^(#+\s*.*?Region\s*)(.*)$", lines[i], re.I)
            # leave if no number
    return "\n".join(lines)


def file_pid_sizes(text):
    d = {}
    for pid, start, end in parse_blocks(text):
        d[pid] = block_size_sum(text, start, end)
    return d


def scale_groups(text, pid_to_group, group_target_adults, skip_pids=None):
    skip_pids = skip_pids or set()
    sizes = file_pid_sizes(text)
    group_current = collections.defaultdict(int)
    for pid, sz in sizes.items():
        if pid in skip_pids:
            continue
        g = pid_to_group.get(pid)
        if g:
            group_current[g] += sz
    pid_factor = {}
    for pid, g in pid_to_group.items():
        if pid in skip_pids:
            continue
        cur = group_current.get(g, 0)
        tgt = group_target_adults[g]
        pid_factor[pid] = (float(tgt) / cur) if cur else 1.0
    new_text, new_by_pid = apply_factors(text, pid_factor, skip_pids=skip_pids)
    # remainder per group onto largest pid
    group_new = collections.defaultdict(int)
    group_largest = {}
    for pid, sz in new_by_pid.items():
        if pid in skip_pids:
            continue
        g = pid_to_group.get(pid)
        if not g:
            continue
        group_new[g] += sz
        if g not in group_largest or sz > new_by_pid.get(group_largest[g], 0):
            group_largest[g] = pid
    for g, tgt in group_target_adults.items():
        delta = tgt - group_new.get(g, 0)
        if delta and g in group_largest:
            new_text = add_remainder(new_text, group_largest[g], delta)
            new_by_pid[group_largest[g]] = new_by_pid.get(group_largest[g], 0) + delta
    new_text = update_comments(new_text, new_by_pid, None)
    return new_text, new_by_pid, pid_factor


def verify_japan():
    path = os.path.join(MOD, "history", "pops", "1836.1.1", "Japan.txt")
    text, _ = read_text(path)
    sizes = file_pid_sizes(text)
    total = sum(sizes.values())
    # Ryukyu 1672 Okinawa, 1673 Amami — check IDs from file
    lines = []
    region = None
    by_reg = collections.OrderedDict()
    pending_region = None
    for line in text.split("\n"):
        if "Region" in line and line.lstrip().startswith("#"):
            pending_region = line.split("(")[0].replace("#", "").strip()
        m = re.match(r"^(\d+)\s*=", line)
        if m:
            region = pending_region
            pid = int(m.group(1))
            by_reg.setdefault(region, 0)
            by_reg[region] += sizes.get(pid, 0)
    # Kito 32.5m without Ryukyu
    ryukyu = 0
    home = 0
    for r, a in by_reg.items():
        if r and "Ryukyu" in r:
            ryukyu += a
        else:
            home += a
    return {
        "adults": total,
        "display": total * 4,
        "home_display": home * 4,
        "ryukyu_display": ryukyu * 4,
        "by_reg": {r: (a, a * 4) for r, a in by_reg.items()},
    }


def main():
    id_name = load_id_name()
    report = []

    jap = verify_japan()
    report.append("=== JAPAN 1836.1.1 ===")
    report.append("adults %d  display %.3f mln" % (jap["adults"], jap["display"] / 1e6))
    report.append("home (no Ryukyu) display %.3f mln  target 32.50  ratio %.4f" % (
        jap["home_display"] / 1e6, jap["home_display"] / 32.5e6))
    report.append("Ryukyu display %.3f mln  target 0.25  ratio %.4f" % (
        jap["ryukyu_display"] / 1e6, jap["ryukyu_display"] / 0.25e6 if jap["ryukyu_display"] else 0))
    for r, (a, d) in jap["by_reg"].items():
        report.append("  %s adults %d display %.3f" % (r, a, d / 1e6))

    # China mapping
    china_ids = {}
    # discover from 1836.1.1 China.txt
    ch_text, _ = read_text(os.path.join(MOD, "history", "pops", "1836.1.1", "China.txt"))
    unmapped = []
    for pid in file_pid_sizes(ch_text):
        name = id_name.get(pid, "")
        q = NAME_TO_QING.get(name)
        if not q:
            unmapped.append((pid, name))
        else:
            china_ids[pid] = q
    report.append("UNMAPPED China.txt: %s" % unmapped)

    # Taiwan pids
    tw_text, _ = read_text(os.path.join(MOD, "history", "pops", "1836.1.1", "Taiwan.txt"))
    taiwan_ids = {pid: "Taiwan" for pid in file_pid_sizes(tw_text)}

    xj_text, _ = read_text(os.path.join(MOD, "history", "pops", "1836.1.1", "Xinjiang.txt"))
    xj_ids = {pid: "Xinjiang" for pid in file_pid_sizes(xj_text)}

    mg_text, _ = read_text(os.path.join(MOD, "history", "pops", "1836.1.1", "Mongolia.txt"))
    mg_ids = {pid: "Outer Mongolia" for pid in file_pid_sizes(mg_text)}

    tb_text, _ = read_text(os.path.join(MOD, "history", "pops", "1836.1.1", "Tibet.txt"))
    TAWANG = 1593
    tb_ids = {}
    for pid in file_pid_sizes(tb_text):
        if pid != TAWANG:
            tb_ids[pid] = "Tibet"

    # Inner Mongolia current vs Outer — combined Cao
    inner_pids = [p for p, q in china_ids.items() if q == "Inner Mongolia"]

    # Fujian mainland target = Cao Fujian minus Taiwan Han 1811-93 interp
    taiwan_han = 1944737 + (25.0 / 82.0) * (2545731 - 1944737)
    fujian_cao = cao_display("Fujian")
    fujian_mainland = fujian_cao - taiwan_han
    taiwan_display = taiwan_han + 150000  # indigenous ~150k

    # Split Cao Mongolia between inner (China.txt) and outer (Mongolia.txt)
    inner_cur = sum(file_pid_sizes(ch_text).get(p, 0) for p in inner_pids) * 4
    outer_cur = sum(file_pid_sizes(mg_text).values()) * 4
    mon_tgt = cao_display("Mongolia")
    inner_tgt = mon_tgt * (inner_cur / (inner_cur + outer_cur)) if (inner_cur + outer_cur) else mon_tgt * 0.5
    outer_tgt = mon_tgt - inner_tgt

    china_targets = {}
    for name in CAO:
        if name in ("Fujian", "Mongolia", "Xinjiang", "Tibet"):
            continue
        china_targets[name] = int(round(cao_display(name) / 4.0))
    china_targets["Fujian"] = int(round(fujian_mainland / 4.0))
    china_targets["Inner Mongolia"] = int(round(inner_tgt / 4.0))
    china_targets["Qinghai"] = int(round(cao_display("Qinghai") / 4.0))

    report.append("China adult targets:")
    for k in sorted(china_targets, key=lambda x: -china_targets[x]):
        report.append("  %s %d (display %.2f mln)" % (k, china_targets[k], china_targets[k] * 4 / 1e6))
    report.append("Taiwan display tgt %.3f  Fujian mainland %.3f  Cao Fujian %.3f" % (
        taiwan_display / 1e6, fujian_mainland / 1e6, fujian_cao / 1e6))
    report.append("Mongolia inner tgt %.3f outer tgt %.3f cao %.3f" % (
        inner_tgt / 1e6, outer_tgt / 1e6, mon_tgt / 1e6))

    if unmapped:
        raise SystemExit("unmapped china pids, abort")

    VN_TONKIN = {1369, 1370, 1371, 1372, 1373, 1374}
    VN_ANNAM = {1375, 1376, 1377, 1378, 1379}
    VN_COCHIN = {1380, 1381, 1382, 1383}

    for date in DATES:
        popdir = os.path.join(MOD, "history", "pops", date)
        report.append("\n==== %s ====" % date)

        # China.txt
        path = os.path.join(popdir, "China.txt")
        text, nl = read_text(path)
        new, newsizes, fac = scale_groups(text, china_ids, china_targets)
        write_text(path, new, nl)
        # factor sample
        facs = {}
        for pid, q in china_ids.items():
            facs.setdefault(q, fac[pid])
        report.append("China.txt written. sample factors:")
        for q in sorted(facs):
            report.append("  %s x%.4f" % (q, facs[q]))

        # Taiwan
        path = os.path.join(popdir, "Taiwan.txt")
        text, nl = read_text(path)
        tgt = {"Taiwan": int(round(taiwan_display / 4.0))}
        new, _, _ = scale_groups(text, taiwan_ids, tgt)
        write_text(path, new, nl)

        # Xinjiang
        path = os.path.join(popdir, "Xinjiang.txt")
        text, nl = read_text(path)
        tgt = {"Xinjiang": int(round(cao_display("Xinjiang") / 4.0))}
        new, _, _ = scale_groups(text, xj_ids, tgt)
        write_text(path, new, nl)

        # Mongolia
        path = os.path.join(popdir, "Mongolia.txt")
        text, nl = read_text(path)
        tgt = {"Outer Mongolia": int(round(outer_tgt / 4.0))}
        new, _, _ = scale_groups(text, mg_ids, tgt)
        write_text(path, new, nl)

        # Tibet except Tawang
        path = os.path.join(popdir, "Tibet.txt")
        text, nl = read_text(path)
        tgt = {"Tibet": int(round(cao_display("Tibet") / 4.0))}
        new, _, _ = scale_groups(text, tb_ids, tgt, skip_pids={TAWANG})
        write_text(path, new, nl)

        # Vietnam
        path = os.path.join(popdir, "Vietnam.txt")
        text, nl = read_text(path)
        vn_map = {}
        for pid in VN_TONKIN:
            vn_map[pid] = "Tonkin"
        for pid in VN_ANNAM:
            vn_map[pid] = "Annam"
        for pid in VN_COCHIN:
            vn_map[pid] = "Cochinchina"
        vn_tgt = {
            "Tonkin": 1312500,       # 5.25 mln; wiki 10.5 > Goscha 8.0
            "Annam": 787500,         # 3.15
            "Cochinchina": 525000,   # 2.10
        }
        new, _, _ = scale_groups(text, vn_map, vn_tgt)
        write_text(path, new, nl)

        # Cambodia 0.90 mln
        path = os.path.join(popdir, "Cambodia.txt")
        text, nl = read_text(path)
        pids = {pid: "Cambodia" for pid in file_pid_sizes(text)}
        new, _, _ = scale_groups(text, pids, {"Cambodia": 225000})
        write_text(path, new, nl)

        # Laos 0.50 mln
        path = os.path.join(popdir, "Laos.txt")
        text, nl = read_text(path)
        pids = {pid: "Laos" for pid in file_pid_sizes(text)}
        new, _, _ = scale_groups(text, pids, {"Laos": 125000})
        write_text(path, new, nl)

        # Thailand 5.00 mln (modern territory)
        path = os.path.join(popdir, "Thailand.txt")
        text, nl = read_text(path)
        pids = {pid: "Siam" for pid in file_pid_sizes(text)}
        new, _, _ = scale_groups(text, pids, {"Siam": 1250000})
        write_text(path, new, nl)

        # Burma 4.50 mln
        path = os.path.join(popdir, "Burma.txt")
        text, nl = read_text(path)
        pids = {pid: "Burma" for pid in file_pid_sizes(text)}
        new, _, _ = scale_groups(text, pids, {"Burma": 1125000})
        write_text(path, new, nl)

    # verify 1836.1.1 totals
    report.append("\n=== VERIFY 1836.1.1 ===")

    def sum_file(fn):
        t, _ = read_text(os.path.join(MOD, "history", "pops", "1836.1.1", fn))
        return sum(file_pid_sizes(t).values())

    ch = sum_file("China.txt")
    tw = sum_file("Taiwan.txt")
    xj = sum_file("Xinjiang.txt")
    mg = sum_file("Mongolia.txt")
    tb = sum_file("Tibet.txt")
    report.append("China.txt adults %d display %.2f mln" % (ch, ch * 4 / 1e6))
    report.append("Taiwan adults %d display %.3f mln" % (tw, tw * 4 / 1e6))
    report.append("Xinjiang adults %d display %.3f mln" % (xj, xj * 4 / 1e6))
    report.append("Mongolia adults %d display %.3f mln" % (mg, mg * 4 / 1e6))
    report.append("Tibet adults %d display %.3f mln (incl Tawang)" % (tb, tb * 4 / 1e6))
    report.append("Vietnam adults %d display %.3f mln" % (sum_file("Vietnam.txt"), sum_file("Vietnam.txt") * 4 / 1e6))
    report.append("Cambodia adults %d display %.3f mln" % (sum_file("Cambodia.txt"), sum_file("Cambodia.txt") * 4 / 1e6))
    report.append("Laos adults %d display %.3f mln" % (sum_file("Laos.txt"), sum_file("Laos.txt") * 4 / 1e6))
    report.append("Thailand adults %d display %.3f mln" % (sum_file("Thailand.txt"), sum_file("Thailand.txt") * 4 / 1e6))
    report.append("Burma adults %d display %.3f mln" % (sum_file("Burma.txt"), sum_file("Burma.txt") * 4 / 1e6))

    outp = os.path.join(MOD, "assets", "_scale_east_asia_report.txt")
    open(outp, "w", encoding="utf-8").write("\n".join(report) + "\n")
    print("\n".join(report))
    print("wrote", outp)


if __name__ == "__main__":
    main()
