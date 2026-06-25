"""Scan v2game.exe for industrial score calculation patterns."""
from pathlib import Path
import struct
import re

EXE = Path(r"C:\Games\Vic2LV2\Victoria 2\v2game.exe")
OUT = Path(__file__).resolve().parent / "_ind_score_scan.txt"


def fo_to_va(data: bytes, fo: int) -> int:
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    ib = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    ns = struct.unpack_from("<H", data, pe + 6)[0]
    os = struct.unpack_from("<H", data, pe + 20)[0]
    so = pe + 24 + os
    for i in range(ns):
        o = so + i * 40
        vs, vaddr, _, raddr = struct.unpack_from("<IIII", data, o + 8)
        if raddr <= fo < raddr + vs:
            return ib + vaddr + (fo - raddr)
    return 0


def find_string_refs(data: bytes, text: bytes) -> list[int]:
    fo = data.find(text)
    if fo < 0:
        return []
    va = fo_to_va(data, fo)
    pat = struct.pack("<I", va)
    refs = []
    code_end = min(len(data), 9_000_000)
    i = 0
    while i < code_end - 4:
        if data[i : i + 4] == pat:
            refs.append(i)
        i += 1
    return refs


def main() -> None:
    data = EXE.read_bytes()
    lines: list[str] = [f"size={len(data)}"]

    for s in [b"investment_score_factor", b"industrial_score", b"INDUSTRIAL_SCORE"]:
        fo = data.find(s)
        lines.append(f"string {s!r} file_offset={fo:#x}")
        if fo >= 0:
            lines.append(f"  va={fo_to_va(data, fo):#x}")
            refs = find_string_refs(data, s)
            lines.append(f"  code_refs={len(refs)} {[hex(r) for r in refs[:12]]}")

    for val in (0.001, 0.0010, 0.005, 4.0, 2500.0):
        pat = struct.pack("<f", val)
        idxs = [m.start() for m in re.finditer(re.escape(pat), data)]
        lines.append(f"float {val}: {len(idxs)} hits, first={[hex(x) for x in idxs[:6]]}")

    # dword 2500
    pat_i = struct.pack("<I", 2500)
    idxs_i = [m.start() for m in re.finditer(re.escape(pat_i), data)]
    lines.append(f"int 2500: {len(idxs_i)} hits, first={[hex(x) for x in idxs_i[:10]]}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
