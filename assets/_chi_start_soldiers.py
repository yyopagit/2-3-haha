# -*- coding: utf-8 -*-
"""Set CHI starting soldiers: ~0 in separatist regions, 1% elsewhere.

Does not touch poptype recruitment caps.
"""
from __future__ import print_function
import os
import re
import sys

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATES = ["1836.1.1", "1836.1.2", "1836.1.3", "1836.1.4"]
POP_ROOT = os.path.join(MOD, "history", "pops")
PROV_DIR = os.path.join(MOD, "history", "provinces")
REGION = os.path.join(MOD, "map", "region.txt")
WRAPPER = os.path.join(MOD, "assets", "_chi_crisis_wrapper1.py")

OWNER_RE = re.compile(r"^owner\s*=\s*(\w+)", re.M)
ID_LINE = re.compile(r"^(\d+)\s*=", re.M)
INNER_RE = re.compile(r"(?ms)^([ \t]+)([A-Za-z_]+)\s*=\s*\{(.*?)\}")
SIZE_RE = re.compile(r"(?im)(size\s*=\s*)(\d+)")
CULTURE_RE = re.compile(r"(?im)culture\s*=\s*(\w+)")
RELIGION_RE = re.compile(r"(?im)religion\s*=\s*(\w+)")
LEVELS_RE = re.compile(
    r'"CHI_(\d+)"\s*:\s*\(\s*(\d+)\s*,',
)
SKIP = {"CHI_1618"}


def read_text(path):
    raw = open(path, "rb").read()
    nl = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("latin-1"), nl


def write_text(path, text, nl):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if nl == "\r\n":
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("latin-1"))


def parse_chi_regions():
    text = open(REGION, "rb").read().decode("utf-8", "replace")
    out = {}
    for m in re.finditer(r"^(CHI_\d+)\s*=\s*\{([^}]*)\}", text, flags=re.M):
        key = m.group(1)
        ids = [int(x) for x in re.findall(r"\d+", m.group(2))]
        if key.startswith("CHI_corruption") or not ids:
            continue
        out[key] = ids
    return out


def separatist_pids():
    src = open(WRAPPER, "rb").read().decode("utf-8", "replace")
    sep = set()
    regions = parse_chi_regions()
    for m in LEVELS_RE.finditer(src):
        key = "CHI_" + m.group(1)
        if key in SKIP:
            continue
        if int(m.group(2)) <= 0:
            continue
        sep.update(regions.get(key, []))
    return sep


def chi_owners():
    owners = {}
    for root, _dirs, files in os.walk(PROV_DIR):
        for fn in files:
            if not fn.endswith(".txt"):
                continue
            fp = os.path.join(root, fn)
            text = open(fp, "rb").read().decode("cp1251", "replace")
            m = OWNER_RE.search(text)
            if not m:
                continue
            pid = fn.split(" - ", 1)[0].strip()
            if pid.isdigit():
                owners[int(pid)] = m.group(1)
    return owners


def province_ranges(text):
    matches = list(ID_LINE.finditer(text))
    out = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((int(m.group(1)), start, end))
    return out


def parse_pops(chunk):
    pops = []
    for m in INNER_RE.finditer(chunk):
        body = m.group(3)
        sm = SIZE_RE.search(body)
        if not sm:
            continue
        cm = CULTURE_RE.search(body)
        rm = RELIGION_RE.search(body)
        pops.append(
            {
                "start": m.start(),
                "end": m.end(),
                "indent": m.group(1),
                "ptype": m.group(2),
                "body": body,
                "size": int(sm.group(2)),
                "culture": cm.group(1) if cm else "",
                "religion": rm.group(1) if rm else "",
            }
        )
    return pops


def set_size_body(body, new_size):
    return SIZE_RE.sub(lambda m: m.group(1) + str(int(new_size)), body, count=1)


def add_to_rural(pops, culture, religion, amount):
    if amount == 0:
        return
    rural = [p for p in pops if p["ptype"] in ("farmers", "labourers") and p["size"] > 0]
    if not rural:
        return
    same = [
        p
        for p in rural
        if p["culture"] == culture and p["religion"] == religion
    ]
    pool = same if same else [p for p in rural if p["ptype"] == "farmers"] or rural
    target = max(pool, key=lambda p: p["size"])
    target["size"] += amount
    target["dirty"] = True


def take_from_rural(pops, culture, religion, amount):
    if amount <= 0:
        return 0
    taken = 0
    rural = [p for p in pops if p["ptype"] in ("farmers", "labourers")]
    same = [
        p
        for p in rural
        if p["culture"] == culture and p["religion"] == religion and p["size"] > 1
    ]
    pool = same if same else [p for p in rural if p["size"] > 1]
    pool.sort(key=lambda p: p["size"], reverse=True)
    need = amount
    for p in pool:
        can = p["size"] - 1
        if can <= 0:
            continue
        grab = min(can, need)
        p["size"] -= grab
        p["dirty"] = True
        taken += grab
        need -= grab
        if need <= 0:
            break
    return taken


def apply_pops(chunk, pops):
    parts = []
    last = 0
    for p in pops:
        if p.get("drop"):
            start = p["start"]
            if start > last and chunk[last:start].strip() == "":
                # keep one newline before the next remaining block
                pass
            parts.append(chunk[last:start])
            last = p["end"]
            # eat following extra blank line
            if last < len(chunk) and chunk[last : last + 2] in ("\n\n", "\r\n"):
                if chunk[last] == "\r":
                    last += 2
                else:
                    last += 1
            continue
        if p.get("dirty"):
            new_block = "%s%s = {%s}" % (
                p["indent"],
                p["ptype"],
                set_size_body(p["body"], p["size"]),
            )
            parts.append(chunk[last : p["start"]] + new_block)
            last = p["end"]
        else:
            parts.append(chunk[last : p["end"]])
            last = p["end"]
    parts.append(chunk[last:])
    return "".join(parts)


def zero_soldiers(pops):
    soldiers = [p for p in pops if p["ptype"] == "soldiers" and p["size"] > 0]
    if not soldiers:
        return 0
    old = sum(p["size"] for p in soldiers)
    keep = max(soldiers, key=lambda p: p["size"])
    for p in soldiers:
        if p is keep:
            extra = p["size"] - 1
            p["size"] = 1
            p["dirty"] = True
            add_to_rural(pops, p["culture"], p["religion"], extra)
        else:
            add_to_rural(pops, p["culture"], p["religion"], p["size"])
            p["drop"] = True
    return old - 1


def scale_to_share(pops, share):
    total = sum(p["size"] for p in pops)
    if total <= 0:
        return 0
    soldiers = [p for p in pops if p["ptype"] == "soldiers"]
    old = sum(p["size"] for p in soldiers)
    target = int(round(total * share))
    if target < 0:
        target = 0
    if old == target:
        return 0
    if old == 0:
        if target <= 0:
            return 0
        rural = [p for p in pops if p["ptype"] in ("farmers", "labourers") and p["size"] > 1]
        if not rural:
            return 0
        src = max(rural, key=lambda p: p["size"])
        got = take_from_rural(pops, src["culture"], src["religion"], target)
        if got <= 0:
            return 0
        pops.append(
            {
                "start": src["end"],
                "end": src["end"],
                "indent": src["indent"],
                "ptype": "soldiers",
                "body": "\n%sculture = %s\n%sreligion = %s\n%ssize = %s\n%s"
                % (
                    src["indent"] + src["indent"][:1].replace("\t", "\t").ljust(len(src["indent"])),
                    src["culture"],
                    src["indent"] + ("\t" if "\t" in src["indent"] else "    "),
                    src["religion"],
                    got,
                    src["indent"],
                ),
                "size": got,
                "culture": src["culture"],
                "religion": src["religion"],
                "dirty": True,
            }
        )
        # inserting at src.end with start==end is messy; skip create-from-zero
        pops.pop()
        src["size"] += got
        src["dirty"] = True
        return 0
    # proportional scale, largest remainder
    sizes = [p["size"] for p in soldiers]
    if old > 0:
        raw = [s * target / float(old) for s in sizes]
        base = [int(x) for x in raw]
        rem = target - sum(base)
        order = sorted(range(len(soldiers)), key=lambda i: raw[i] - base[i], reverse=True)
        for i in order:
            if rem == 0:
                break
            if rem > 0:
                base[i] += 1
                rem -= 1
            elif base[i] > 0:
                base[i] -= 1
                rem += 1
    for p, new in zip(soldiers, base):
        delta = p["size"] - new
        if delta > 0:
            add_to_rural(pops, p["culture"], p["religion"], delta)
            p["size"] = new
            p["dirty"] = True
            if new <= 0:
                p["drop"] = True
        elif delta < 0:
            got = take_from_rural(pops, p["culture"], p["religion"], -delta)
            p["size"] = p["size"] + got
            p["dirty"] = True
    return old - sum(p["size"] for p in soldiers if not p.get("drop"))


def process_file(path, sep_pids, chi_pids, apply):
    text, nl = read_text(path)
    ranges = province_ranges(text)
    if not ranges:
        return None
    pieces = []
    last = 0
    changed = False
    stats = {
        "sep_old": 0,
        "sep_new": 0,
        "oth_old": 0,
        "oth_new": 0,
        "sep_n": 0,
        "oth_n": 0,
        "total_old": 0,
        "total_new": 0,
    }
    for pid, start, end in ranges:
        chunk = text[start:end]
        pops = parse_pops(chunk)
        if not pops:
            pieces.append(text[last:end])
            last = end
            continue
        total = sum(p["size"] for p in pops)
        sold = sum(p["size"] for p in pops if p["ptype"] == "soldiers")
        stats["total_old"] += total
        if pid in sep_pids and pid in chi_pids:
            stats["sep_n"] += 1
            stats["sep_old"] += sold
            zero_soldiers(pops)
            new_sold = sum(p["size"] for p in pops if p["ptype"] == "soldiers" and not p.get("drop"))
            stats["sep_new"] += new_sold
            new_chunk = apply_pops(chunk, pops)
            if new_chunk != chunk:
                changed = True
            pieces.append(text[last:start] + new_chunk)
        elif pid in chi_pids:
            stats["oth_n"] += 1
            stats["oth_old"] += sold
            scale_to_share(pops, 0.01)
            new_sold = sum(p["size"] for p in pops if p["ptype"] == "soldiers" and not p.get("drop"))
            stats["oth_new"] += new_sold
            new_chunk = apply_pops(chunk, pops)
            if new_chunk != chunk:
                changed = True
            pieces.append(text[last:start] + new_chunk)
        else:
            stats["total_new"] += total
            pieces.append(text[last:end])
            last = end
            continue
        stats["total_new"] += sum(p["size"] for p in pops if not p.get("drop"))
        last = end
    pieces.append(text[last:])
    if apply and changed:
        write_text(path, "".join(pieces), nl)
    stats["changed"] = changed
    stats["file"] = os.path.relpath(path, MOD)
    return stats


def main():
    apply = "--apply" in sys.argv
    sep = separatist_pids()
    owners = chi_owners()
    chi = {pid for pid, tag in owners.items() if tag == "CHI"}
    print("separatist pids", len(sep), "CHI-owned", len(chi), "CHI+sep", len(sep & chi))
    print("sep not CHI", sorted(sep - chi)[:30], "count", len(sep - chi))
    totals = {
        "sep_old": 0,
        "sep_new": 0,
        "oth_old": 0,
        "oth_new": 0,
        "sep_n": 0,
        "oth_n": 0,
        "files": 0,
    }
    for date in DATES:
        d = os.path.join(POP_ROOT, date)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".txt"):
                continue
            st = process_file(os.path.join(d, fn), sep, chi, apply)
            if not st or (st["sep_n"] == 0 and st["oth_n"] == 0):
                continue
            totals["files"] += 1
            for k in ("sep_old", "sep_new", "oth_old", "oth_new", "sep_n", "oth_n"):
                totals[k] += st[k]
            if date == DATES[0] and st["changed"]:
                print(
                    st["file"],
                    "sep",
                    st["sep_n"],
                    st["sep_old"],
                    "->",
                    st["sep_new"],
                    "oth",
                    st["oth_n"],
                    st["oth_old"],
                    "->",
                    st["oth_new"],
                )
    print("APPLY" if apply else "DRY", totals)


if __name__ == "__main__":
    main()
