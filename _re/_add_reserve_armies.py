# -*- coding: utf-8 -*-
"""Добавляет резервную армию (1 драгун + 4 пехоты + 4 артиллерии) в OOB.
Работает побайтово, не декодируя весь файл — некоторые OOB содержат
повреждённые (не cp1251) байты в старых именах лидеров, которые нельзя
декодировать, но которые не нужно трогать.
"""
import re
from pathlib import Path

MOD = Path(r"C:\Games\Vic2LV2\Victoria 2\mod\5")
OOB_DIR = MOD / "history" / "units"

QUALIFYING = ["PRU", "SPA", "SWE", "NET", "DEN", "POR", "SIC", "SAR", "GRE", "BEL", "PAP"]

TAG_CAPITAL = {
    "PRU": 549, "SPA": 487, "SWE": 322, "NET": 375,
    "DEN": 372, "POR": 521, "SIC": 754, "SAR": 720, "GRE": 834, "BEL": 387, "PAP": 749,
}


def regiment(name: str, rtype: str, home: int) -> str:
    return f'\tregiment = {{\n\t\tname = "{name}"\n\t\ttype = {rtype}\n\t\thome = {home}\n\t}}\n'


def main() -> None:
    for tag in QUALIFYING:
        fp = OOB_DIR / f"{tag}_oob.txt"
        data = fp.read_bytes()
        existing_armies = len(re.findall(rb"(?m)^army\s*=\s*\{", data))
        cap = TAG_CAPITAL[tag]
        army_num = existing_armies + 1

        parts = ["\narmy = {\n"]
        parts.append(f'\tname = "{army_num}-\u044f \u0440\u0435\u0437\u0435\u0440\u0432\u043d\u0430\u044f \u0430\u0440\u043c\u0438\u044f"\n')
        parts.append(f"\tlocation = {cap}\n\n")
        parts.append(regiment(f"{army_num}-\u0439 \u0434\u0440\u0430\u0433\u0443\u043d\u0441\u043a\u0438\u0439 \u043f\u043e\u043b\u043a", "dragoon", cap))
        for i in range(1, 5):
            parts.append(regiment(f"{army_num}-\u0439 \u043f\u0435\u0445\u043e\u0442\u043d\u044b\u0439 \u043f\u043e\u043b\u043a {i}", "infantry", cap))
        for i in range(1, 5):
            parts.append(regiment(f"{army_num}-\u0439 \u0430\u0440\u0442\u0438\u043b\u043b\u0435\u0440\u0438\u0439\u0441\u043a\u0438\u0439 \u043f\u043e\u043b\u043a {i}", "artillery", cap))
        parts.append("}\n")
        block = "".join(parts)
        block_bytes = block.encode("cp1251")

        new_data = data.rstrip(b"\r\n") + b"\n" + block_bytes
        fp.write_bytes(new_data)
        print(tag, "added army", army_num, "at capital", cap)


if __name__ == "__main__":
    main()
