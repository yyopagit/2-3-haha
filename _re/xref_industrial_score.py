"""Find industrial score calculation via investment_score_factor xref."""
from pathlib import Path
import struct

EXE = Path(r"C:\Games\Vic2LV2\Victoria 2\v2game.exe")
OUT = Path(__file__).resolve().parent / "_ind_score_xref.txt"
CODE_END = 8_947_200


def pe_info(data: bytes):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    ib = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    return pe, ib


def fo_to_va(data: bytes, fo: int) -> int:
    pe, ib = pe_info(data)
    ns = struct.unpack_from("<H", data, pe + 6)[0]
    os = struct.unpack_from("<H", data, pe + 20)[0]
    so = pe + 24 + os
    for i in range(ns):
        o = so + i * 40
        vs, vaddr, _, raddr = struct.unpack_from("<IIII", data, o + 8)
        if raddr <= fo < raddr + vs:
            return ib + vaddr + (fo - raddr)
    return 0


def va_to_fo(data: bytes, va: int) -> int | None:
    pe, ib = pe_info(data)
    rva = va - ib
    ns = struct.unpack_from("<H", data, pe + 6)[0]
    os = struct.unpack_from("<H", data, pe + 20)[0]
    so = pe + 24 + os
    for i in range(ns):
        o = so + i * 40
        vs, vaddr, _, raddr = struct.unpack_from("<IIII", data, o + 8)
        if vaddr <= rva < vaddr + vs:
            return raddr + (rva - vaddr)
    return None


def disasm_window(data: bytes, fo: int, before: int = 80, after: int = 160) -> str:
  try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
  except ImportError:
    return "(capstone not installed)"
  md = Cs(CS_ARCH_X86, CS_MODE_32)
  start = max(0, fo - before)
  chunk = data[start : fo + after]
  lines = []
  for ins in md.disasm(chunk, start):
    mark = ">>>" if ins.address == fo else "   "
    lines.append(f"{mark} {ins.address:#010x}: {ins.mnemonic} {ins.op_str}")
  return "\n".join(lines)


def find_mov_imm_refs(data: bytes, imm: int) -> list[int]:
    pat4 = struct.pack("<I", imm)
    refs = []
    for i in range(CODE_END - 6):
        # mov reg, imm32
        if data[i] in (0xB8, 0xB9, 0xBA, 0xBB, 0xBD, 0xBE, 0xBF) and data[i + 1 : i + 5] == pat4:
            refs.append(i)
        # push imm32
        if data[i] == 0x68 and data[i + 1 : i + 5] == pat4:
            refs.append(i)
    return refs


def main() -> None:
    data = EXE.read_bytes()
    lines: list[str] = []

    # defines table floats
    for label, fo in [("0.001", 0xA43F9C), ("0.005", 0xA43FA0)]:
        va = fo_to_va(data, fo)
        lines.append(f"{label} data fo={fo:#x} va={va:#x}")
        pat = struct.pack("<I", va)
        refs = [i for i in range(CODE_END - 4) if data[i : i + 4] == pat]
        lines.append(f"  dword ptr refs: {len(refs)} {[hex(r) for r in refs[:20]]}")
        for r in refs[:5]:
            lines.append(disasm_window(data, r))
            lines.append("")

    # search investment string variants
    for s in [b"INVESTMENT_SCORE", b"investment_score", b"Investment"]:
        fo = data.find(s)
        if fo >= 0:
            lines.append(f"string {s!r} at {fo:#x} va={fo_to_va(data, fo):#x}")

    # imul / shl by 4 near fdiv sequences - heuristic
    hits = []
    for i in range(CODE_END - 3):
        if data[i] in (0xC1, 0xD1) and data[i + 1] in range(0xE0, 0xE8) and data[i + 2] == 0x02:
            hits.append(i)  # shl/shr reg, 2
    lines.append(f"shl/shr by 2 count: {len(hits)}")

    # look for fild + fdiv pattern clusters
    fdiv_fos = [i for i in range(CODE_END) if data[i] == 0xDE and data[i + 1] in (0xF1, 0xF9)]
    lines.append(f"fdivp/fdivr count: {len(fdiv_fos)}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
