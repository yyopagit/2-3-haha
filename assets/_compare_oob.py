#!/usr/bin/env python3
import re
import subprocess
from pathlib import Path

REPL = b"\xef\xbf\xbd"


def analyze(path: Path, label: str) -> None:
    d = path.read_bytes()
    armies = re.findall(rb"(?m)^army\s*=\s*\{", d)
    leaders = re.findall(rb"(?m)^leader\s*=\s*\{", d)
    navies = re.findall(rb"(?m)^navy\s*=\s*\{", d)
    print(f"\n{label}: size={len(d)} repl={d.count(REPL)//3} armies={len(armies)} leaders={len(leaders)} navies={len(navies)}")
    for m in re.finditer(rb'(?m)^\s*name\s*=\s*"([^"]+)"', d):
        name = m.group(1)
        if REPL in name or any(b > 127 for b in name):
            print(" ", name.decode("cp1251", "replace"))


analyze(Path("history/units_backup_pass4/PRU_oob.txt"), "backup PRU")
analyze(Path("history/units/PRU_oob.txt"), "current PRU")
analyze(Path(r"C:\Games\Vic2LV2\Victoria 2\mod\Новая папка\6\history\units\NET_oob.txt"), "mod6 NET")
analyze(Path("history/units/NET_oob.txt"), "current NET")

head = subprocess.check_output(["git", "show", "60ce09b:history/units/NET_oob.txt"])
Path("assets/_tmp_net_60.bin").write_bytes(head)
analyze(Path("assets/_tmp_net_60.bin"), "60ce09b NET")
