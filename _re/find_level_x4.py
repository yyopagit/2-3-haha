"""Find movzx word + shl 2 patterns (4 * factory level)."""
from pathlib import Path
import re
try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
except ImportError:
    raise SystemExit('capstone required')

EXE = Path(r"C:\Games\Vic2LV2\Victoria 2\v2game.exe")
OUT = Path(__file__).resolve().parent / "_level_x4.txt"
CODE_END = 8_947_200


def disasm(data, fo, before=80, after=160):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    s = max(0, fo-before)
    return '\n'.join(
        f"{'>>>' if ins.address==fo else '   '} {ins.address:#010x}: {ins.mnemonic} {ins.op_str}"
        for ins in md.disasm(data[s:fo+after], s)
    )


def main():
    data = EXE.read_bytes()
    hits = []
    # 0F B7 = movzx r16, r/m16
    for m in re.finditer(rb"\x0F\xB7", data[:CODE_END-8]):
        fo = m.start()
        nxt = data[fo+3:fo+6]
        if len(nxt) >= 2 and nxt[0] in range(0xC0, 0xC8) and nxt[1] == 0x02:  # shl eax..edi, 2
            hits.append(fo)
        if fo+4 < CODE_END and data[fo+3] == 0xC1 and fo+5 < CODE_END and data[fo+4] in range(0xC0,0xC8) and data[fo+5]==0x02:
            hits.append(fo)
    lines = [f'movzx+shl2 hits: {len(hits)}']
    for fo in hits:
        w = data[fo:fo+220]
        if b'\xD9' in w or b'\xDC' in w or b'\xDE' in w or b'\xD8' in w:
            lines.append(f'\n=== {fo:#x} ===')
            lines.append(disasm(data, fo))
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print('hits', len(hits), 'written', OUT)

if __name__ == '__main__':
    main()
