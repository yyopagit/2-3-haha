"""Анализ позиции цифр уровня в province strips."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _dds_tools import FRAME_W, get_frame, load_dds

MOD = os.path.dirname(os.path.dirname(__file__))


def analyze_path(path: str, label: str) -> None:
    img, fmt, _ = load_dds(path)
    print(f"{label}: {img.size} {fmt}, frames={img.size[0] // FRAME_W}")
    for i in range(img.size[0] // FRAME_W):
        fr = get_frame(img, i)
        whites = [
            (x, y)
            for y in range(32)
            for x in range(40)
            if fr.getpixel((x, y))[0] > 200 and fr.getpixel((x, y))[3] > 200
        ]
        if whites:
            xs, ys = zip(*whites)
            print(f"  f{i}: white x={min(xs)}-{max(xs)} y={min(ys)}-{max(ys)}")
        else:
            print(f"  f{i}: (no white digit pixels)")


def main() -> None:
    for fname in [
        "province_town_strip.dds",
        "province_fort_strip.dds",
        "province_infra_strip.dds",
    ]:
        tmp = os.path.join(os.path.dirname(__file__), f"_tmp_{fname}")
        r = subprocess.run(
            ["git", "-C", MOD, "show", f"HEAD:gfx/interface/{fname}"],
            capture_output=True,
            check=True,
        )
        open(tmp, "wb").write(r.stdout)
        analyze_path(tmp, f"git {fname}")

    analyze_path(
        os.path.join(MOD, "gfx", "interface", "province_town_strip.dds"),
        "current town",
    )


if __name__ == "__main__":
    main()
