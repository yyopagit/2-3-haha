#!/usr/bin/env python3
"""Восстановление повреждённых OOB из чистых источников + резервные армии."""
import re
import shutil
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent
OOB_DIR = MOD / "history" / "units"
PRU_SRC = MOD / "history" / "units_backup_pass4" / "PRU_oob.txt"
NET_SRC = Path(r"C:\Games\Vic2LV2\Victoria 2\mod\Новая папка\6\history\units\NET_oob.txt")

TAG_CAPITAL = {
    "PRU": 549,
    "NET": 375,
}


def regiment(name: str, rtype: str, home: int) -> str:
    return (
        f'\tregiment = {{\n\t\tname = "{name}"\n\t\ttype = {rtype}\n\t\thome = {home}\n\t}}\n'
    )


def reserve_army_block(army_num: int, capital: int) -> bytes:
    parts = ["\narmy = {\n"]
    parts.append(f'\tname = "{army_num}-я резервная армия"\n')
    parts.append(f"\tlocation = {capital}\n\n")
    parts.append(regiment(f"{army_num}-й драгунский полк", "dragoon", capital))
    for i in range(1, 5):
        parts.append(regiment(f"{army_num}-й пехотный полк {i}", "infantry", capital))
    for i in range(1, 5):
        parts.append(
            regiment(f"{army_num}-й артиллерийский полк {i}", "artillery", capital)
        )
    parts.append("}\n")
    return "".join(parts).encode("cp1251")


def add_reserve(tag: str) -> None:
    fp = OOB_DIR / f"{tag}_oob.txt"
    data = fp.read_bytes()
    armies = len(re.findall(rb"(?m)^army\s*=\s*\{", data))
    if b"\xd0\xb5\xd0\xb7\xd0\xb5\xd1\x80\xd0\xb2\xd0\xbd\xd0\xb0\xd1\x8f" in data:
        print(f"{tag}: reserve army already present, skip append")
        return
    if "резервная армия".encode("cp1251") in data:
        print(f"{tag}: reserve army already present, skip append")
        return
    army_num = armies + 1
    block = reserve_army_block(army_num, TAG_CAPITAL[tag])
    fp.write_bytes(data.rstrip(b"\r\n") + b"\n" + block)
    print(f"{tag}: added reserve army #{army_num}")


def verify(tag: str) -> None:
    fp = OOB_DIR / f"{tag}_oob.txt"
    data = fp.read_bytes()
    repl = data.count(b"\xef\xbf\xbd") // 3
    bad98 = data.count(b"\x98\x98\x98")
    print(f"{tag}: size={len(data)} repl={repl} bad0x98={bad98}")


def main() -> None:
    shutil.copy2(PRU_SRC, OOB_DIR / "PRU_oob.txt")
    print("PRU restored from backup_pass4")
    shutil.copy2(NET_SRC, OOB_DIR / "NET_oob.txt")
    print("NET restored from mod/6")

    add_reserve("PRU")
    add_reserve("NET")

    verify("PRU")
    verify("NET")


if __name__ == "__main__":
    main()
