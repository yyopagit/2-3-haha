"""Утилиты DDS: DXT1/DXT5 и 32bpp BGRA для province strips."""
import struct
import numpy as np
from PIL import Image

FRAME_W, FRAME_H = 40, 32


def read_header(data):
    if data[:4] != b"DDS ":
        raise ValueError("not DDS")
    h = struct.unpack_from("<I", data, 12)[0]
    w = struct.unpack_from("<I", data, 16)[0]
    fourcc = data[84:88]
    bpp = struct.unpack_from("<I", data, 88)[0]
    return w, h, fourcc, bpp


def unpack_rgb565(c):
    r = ((c >> 11) & 0x1F) * 255 // 31
    g = ((c >> 5) & 0x3F) * 255 // 63
    b = (c & 0x1F) * 255 // 31
    return r, g, b


def decode_dxt1_block(block):
    c0, c1 = struct.unpack_from("<HH", block, 0)
    colors = [unpack_rgb565(c0), unpack_rgb565(c1)]
    if c0 > c1:
        for i in range(1, 4):
            colors.append(
                tuple(
                    max(0, min(255, (colors[0][j] * (4 - i) + colors[1][j] * i) // 3))
                    for j in range(3)
                )
            )
    else:
        for i in range(1, 3):
            colors.append(
                tuple(
                    max(0, min(255, (colors[0][j] + colors[1][j]) // 2)) for j in range(3)
                )
            )
        colors.append((0, 0, 0))
    idx = struct.unpack_from("<I", block, 4)[0]
    out = []
    for y in range(4):
        row = []
        for x in range(4):
            i = (idx >> (2 * (y * 4 + x))) & 3
            row.append(colors[i] + (255,))
        out.append(row)
    return out


def decode_dxt1(data, w, h, offset=128):
    blocks_x = (w + 3) // 4
    blocks_y = (h + 3) // 4
    img = np.zeros((h, w, 4), dtype=np.uint8)
    pos = offset
    for by in range(blocks_y):
        for bx in range(blocks_x):
            block = decode_dxt1_block(data[pos : pos + 8])
            pos += 8
            for y in range(4):
                for x in range(4):
                    px, py = bx * 4 + x, by * 4 + y
                    if px < w and py < h:
                        img[py, px] = block[y][x]
    return Image.fromarray(img, "RGBA")


def encode_dxt1_block(pixels):
    flat = [pixels[y][x][:3] for y in range(4) for x in range(4)]
    c0 = flat[0]
    c1 = flat[-1]
    c0h = ((c0[0] * 31 // 255) << 11) | ((c0[1] * 63 // 255) << 5) | (c0[2] * 31 // 255)
    c1h = ((c1[0] * 31 // 255) << 11) | ((c1[1] * 63 // 255) << 5) | (c1[2] * 31 // 255)
    idx = 0
    for i in range(16):
        idx |= (0 if flat[i] == c0 else 1) << (2 * i)
    return struct.pack("<HHI", c0h, c1h, idx)


def encode_dxt1(img):
    w, h = img.size
    rgba = img.convert("RGBA")
    blocks_x = (w + 3) // 4
    blocks_y = (h + 3) // 4
    canvas = Image.new("RGBA", (blocks_x * 4, blocks_y * 4), (0, 0, 0, 0))
    canvas.paste(rgba, (0, 0))
    out = bytearray()
    px = canvas.load()
    for by in range(blocks_y):
        for bx in range(blocks_x):
            block = [[px[bx * 4 + x, by * 4 + y] for x in range(4)] for y in range(4)]
            out += encode_dxt1_block(block)
    return bytes(out)


def load_dds(path):
    data = open(path, "rb").read()
    w, h, fourcc, bpp = read_header(data)
    if fourcc == b"DXT1":
        img = decode_dxt1(data, w, h)
        return img, "DXT1", bytes(data[:128])
    if fourcc == b"DXT5":
        raise NotImplementedError("DXT5 decode not implemented")
    if bpp == 32:
        img = Image.frombytes("RGBA", (w, h), data[128 : 128 + w * h * 4], "raw", "BGRA")
        return img, "BGRA32", bytes(data[:128])
    raise ValueError(f"unsupported {path} {fourcc!r} bpp={bpp}")


def load_dds_image(path):
    img, _, _ = load_dds(path)
    return img


def save_dds(path, img, fmt, header_template=None):
    w, h = img.size
    if fmt == "BGRA32":
        header = bytearray(header_template or bytearray(128))
        header[0:4] = b"DDS "
        struct.pack_into("<I", header, 4, 124)
        struct.pack_into("<I", header, 12, h)
        struct.pack_into("<I", header, 16, w)
        struct.pack_into("<I", header, 20, w * 4)
        struct.pack_into("<I", header, 76, 32)
        struct.pack_into("<I", header, 80, 0x41)
        struct.pack_into("<I", header, 88, 32)
        struct.pack_into("<I", header, 92, 0x00FF0000)
        struct.pack_into("<I", header, 96, 0x0000FF00)
        struct.pack_into("<I", header, 100, 0x000000FF)
        struct.pack_into("<I", header, 104, 0xFF000000)
        struct.pack_into("<I", header, 108, 0x1000)
        bgra = img.convert("RGBA").tobytes("raw", "BGRA")
        with open(path, "wb") as f:
            f.write(header)
            f.write(bgra)
        return
    if fmt == "DXT1":
        header = bytearray(header_template or bytearray(128))
        header[0:4] = b"DDS "
        struct.pack_into("<I", header, 4, 124)
        struct.pack_into("<I", header, 12, h)
        struct.pack_into("<I", header, 16, w)
        struct.pack_into("<I", header, 76, 4)
        struct.pack_into("<I", header, 80, 0x04)
        header[84:88] = b"DXT1"
        struct.pack_into("<I", header, 88, 0)
        struct.pack_into("<I", header, 108, 0x1000)
        payload = encode_dxt1(img)
        with open(path, "wb") as f:
            f.write(header)
            f.write(payload)
        return
    raise ValueError(fmt)


def frame_count(img):
    return img.width // FRAME_W


def get_frame(img, i):
    return img.crop((i * FRAME_W, 0, (i + 1) * FRAME_W, FRAME_H))


def set_frame(strip, i, frame):
    strip.paste(frame.resize((FRAME_W, FRAME_H), Image.Resampling.NEAREST), (i * FRAME_W, 0))


def copy_empty_f0(target_strip, empty_f0):
    set_frame(target_strip, 0, empty_f0)


def build_strip(frames):
    strip = Image.new("RGBA", (FRAME_W * len(frames), FRAME_H), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        set_frame(strip, i, fr)
    return strip
