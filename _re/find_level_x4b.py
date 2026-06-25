"""Broader search for factory level * 4 accumulation."""
from pathlib import Path
import re
try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
except ImportError:
    raise SystemExit('capstone required')

EXE = Path(r"C:\Games\Vic2LV2\Victoria 2\v2game.exe")
OUT = Path(__file__).resolve().parent / "_level_x4b.txt"
CODE_END = 8_947_200


def disasm(data, fo, before=96, after=200):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    s = max(0, fo - before)
    return "\n".join(
        f"{'>>>' if ins.address == fo else '   '} {ins.address:#010x}: {ins.mnemonic} {ins.op_str}"
        for ins in md.disasm(data[s : fo + after], s)
    )


def has_float(window: bytes) -> bool:
    return any(b in window for b in (b"\xD9", b"\xDC", b"\xDE", b"\xD8", b"\xDB"))


def main() -> None:
    data = EXE.read_bytes()
    hits: list[int] = []

    for i in range(CODE_END - 8):
        # shl reg, 2 after small load
        if data[i + 1] in range(0xC0, 0xC8) and data[i + 2] == 0x02 and data[i] in (0xC1, 0xD1):
            prev = data[max(0, i - 8) : i]
            if b"\x0F\xB6" in prev or b"\x0F\xB7" in prev or prev[-1] in range(0x8A, 0x8F):
                hits.append(i)

        # lea reg, [reg + reg*4] or [eax + ecx*4]
        if data[i] == 0x8D and i + 3 < CODE_END:
            modrm = data[i + 1]
            if (modrm & 0xC7) == 0x04:  # sib follows
                sib = data[i + 2]
                if (sib & 0x07) == 0x04 and (sib >> 6) == 0x02:  # *4 scale
                    hits.append(i)

    lines = [f"hits={len(hits)}"]
    shown = 0
    for fo in hits:
        w = data[fo : fo + 260]
        if not has_float(w):
            continue
        # filter noise: need add instruction nearby
        if b"\x01" not in w and b"\x03" not in w:
            continue
        lines.append(f"\n=== {fo:#x} ===")
        lines.append(disasm(data, fo))
        shown += 1
        if shown >= 40:
            break

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"hits={len(hits)} shown={shown} -> {OUT}")


if __name__ == "__main__":
    main()
