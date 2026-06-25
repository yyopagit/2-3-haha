"""Find imul-by-4 sites and disassemble nearby for industrial score hunt."""
from pathlib import Path
import re

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
except ImportError:
    raise SystemExit("pip install capstone")

EXE = Path(r"C:\Games\Vic2LV2\Victoria 2\v2game.exe")
OUT = Path(__file__).resolve().parent / "_imul4_sites.txt"
CODE_END = 8_947_200


def disasm(data: bytes, fo: int, before=48, after=96) -> str:
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    start = max(0, fo - before)
    chunk = data[start : fo + after]
    lines = []
    for ins in md.disasm(chunk, start):
        mark = ">>>" if ins.address == fo else "   "
        lines.append(f"{mark} {ins.address:#010x}: {ins.mnemonic} {ins.op_str}")
    return "\n".join(lines)


def main() -> None:
    data = EXE.read_bytes()
    lines: list[str] = []

    # imul r32, r32, 4  => 6B ?? 04
    imul4 = [m.start() for m in re.finditer(rb"\x6B[\xC0-\xFF]\x04", data[:CODE_END])]
    lines.append(f"imul reg, imm8(4): {len(imul4)}")

    # shl reg, 2
    shl2 = [i for i in range(CODE_END - 3) if data[i] in (0xC1, 0xD1) and data[i + 1] in range(0xE0, 0xE8) and data[i + 2] == 0x02]
    lines.append(f"shl reg, 2: {len(shl2)}")

  # score sites: imul4 that have fdiv within 120 bytes after
    scored = []
    for fo in imul4:
        window = data[fo : fo + 160]
        if b"\xDE" in window or b"\xDC" in window or b"\xD8" in window:
            scored.append(fo)
    lines.append(f"imul4 with float div/mul within 160b: {len(scored)}")
    for fo in scored[:30]:
        lines.append(f"\n=== site {fo:#x} ===")
        lines.append(disasm(data, fo))

    # also check mov reg, 2500
    import struct
    pat = struct.pack("<I", 2500)
    for fo in [m.start() for m in re.finditer(re.escape(pat), data[:CODE_END])]:
        lines.append(f"\n=== mov 2500 at {fo:#x} ===")
        lines.append(disasm(data, fo))

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}, imul4={len(imul4)}, scored={len(scored)}")


if __name__ == "__main__":
    main()
