"""Analyze shl-by-2 sites with float math nearby."""
from pathlib import Path
try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
except ImportError:
    raise SystemExit("need capstone")

EXE = Path(r"C:\Games\Vic2LV2\Victoria 2\v2game.exe")
OUT = Path(__file__).resolve().parent / "_shl2_sites.txt"
CODE_END = 8_947_200


def disasm(data, fo, before=64, after=128):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    start = max(0, fo - before)
    return "\n".join(
        f"{'>>>' if ins.address==fo else '   '} {ins.address:#010x}: {ins.mnemonic} {ins.op_str}"
        for ins in md.disasm(data[start:fo+after], start)
    )


def main():
    data = EXE.read_bytes()
    shl2 = [i for i in range(CODE_END-3)
            if data[i] in (0xC1,0xD1) and 0xE0 <= data[i+1] <= 0xE7 and data[i+2]==0x02]
    lines = [f"shl2 count={len(shl2)}"]
    hits = []
    for fo in shl2:
        w = data[fo:fo+200]
        if any(x in w for x in (b'\xDE', b'\xDC', b'\xD8', b'\xD9')):
            hits.append(fo)
    lines.append(f"with float ops in 200b: {len(hits)}")
    for fo in hits:
        lines.append(f"\n=== {fo:#x} ===")
        lines.append(disasm(data, fo))
    OUT.write_text("\n".join(lines), encoding='utf-8')
    print('hits', len(hits), '->', OUT)

if __name__ == '__main__':
    main()
