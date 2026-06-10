import os
import struct
import subprocess

from PIL import Image

MOD = r"C:\Games\Vic2LV2\Victoria 2\mod\5"
GFX = os.path.join(MOD, "gfx", "interface")
ASSETS = os.path.join(MOD, "assets")


def stats(img: Image.Image, label: str) -> None:
    px = list(img.convert("RGBA").getdata())
    visible = [p for p in px if p[3] > 0 and (p[0] > 30 or p[1] > 30 or p[2] > 30)]
    print(
        f"{label}: size={img.size} visible={len(visible)}/400 "
        f"max_rgb={max((max(p[:3]) for p in px if p[3]>0), default=0)}"
    )
    if visible:
        print(f"  sample={visible[:3]}")


def load_dds_bytes(data: bytes) -> Image.Image:
    w, h = struct.unpack_from("<I", data, 16)[0], struct.unpack_from("<I", data, 12)[0]
    return Image.frombytes("RGBA", (w, h), data[128 : 128 + w * h * 4], "raw", "BGRA")


def main() -> None:
    for name in ("button_speedup", "button_speeddown"):
        for ext in (".dds", ".tga"):
            path = os.path.join(GFX, name + ext)
            if not os.path.exists(path):
                print("MISSING", path)
                continue
            if ext == ".dds":
                data = open(path, "rb").read()
                img = load_dds_bytes(data)
                print(
                    path,
                    "fourcc",
                    data[84:88],
                    "bpp",
                    struct.unpack_from("<I", data, 88)[0],
                )
            else:
                img = Image.open(path).convert("RGBA")
                print(path, "TGA", img.size)
            stats(img, name + ext)
            img.save(os.path.join(ASSETS, f"_check_{name}{ext.replace('.', '_')}.png"))

        git = subprocess.run(
            ["git", "-C", MOD, "show", f"HEAD:gfx/interface/{name}.dds"],
            capture_output=True,
            check=True,
        ).stdout
        stats(load_dds_bytes(git), f"git {name}.dds")

    base = r"C:\Games\Vic2LV2\Victoria 2\gfx\interface"
    for name in ("button_speedup", "button_speeddown"):
        path = os.path.join(base, name + ".dds")
        if os.path.exists(path):
            data = open(path, "rb").read()
            stats(load_dds_bytes(data) if struct.unpack_from("<I", data, 88)[0] == 32 else Image.open(path), f"vanilla {name}")


if __name__ == "__main__":
    main()
