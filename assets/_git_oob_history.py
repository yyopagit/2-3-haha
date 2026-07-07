#!/usr/bin/env python3
import subprocess

REPL = b"\xef\xbf\xbd"
MARK = b'name = "'


def sample_name(data: bytes) -> bytes:
    i = data.find(MARK)
    if i < 0:
        return b""
    j = data.find(b'"', i + len(MARK))
    return data[i + len(MARK) : j][:50]


for commit in ["f06e7ab", "60ce09b", "8515b83", "de57a9d", "HEAD"]:
    for tag in ["PRU", "NET"]:
        try:
            data = subprocess.check_output(
                ["git", "show", f"{commit}:history/units/{tag}_oob.txt"]
            )
        except subprocess.CalledProcessError as e:
            print(commit, tag, "MISSING")
            continue
        name = sample_name(data)
        print(
            f"{commit} {tag}: size={len(data)} repl={data.count(REPL)//3} "
            f"name_bytes={name!r} cp1251={name.decode('cp1251','replace')!r}"
        )
