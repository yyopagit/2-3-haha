import imagecodecs, struct, numpy as np
from PIL import Image

def load_dds_img(path):
    d=open(path,'rb').read()
    w,h=struct.unpack_from('<I',d,16)[0],struct.unpack_from('<I',d,12)[0]
    bpp=struct.unpack_from('<I',d,88)[0]
    if bpp==32:
        return Image.frombytes('RGBA',(w,h),d[128:],'raw','BGRA')
    return Image.frombytes('RGBA',(w,h),imagecodecs.dds_decode(d))

img8=load_dds_img(r'C:\Users\Антон\Desktop\BDSM_Mod-Victoria2-main\V2BDSM\mod\8\gfx\interface\province_bg.dds')
arr8=np.array(img8)
print(f"mod8 province_bg size: {img8.size}")

# Найти строки где есть иконки - x=5..50, alpha>150
in_icon=False
icon_starts=[]
for y in range(200, 640):
    alpha_mean=float(arr8[y, 5:55, 3].mean())
    if alpha_mean > 150 and not in_icon:
        in_icon=True
        icon_starts.append(y)
        print(f"Icon start y={y}")
    elif alpha_mean <= 150 and in_icon:
        in_icon=False
        print(f"Icon end   y={y-1} (height={y-icon_starts[-1]})")

# Также mod5 оригинал
img5=load_dds_img(r'C:\Games\Vic2LV2\Victoria 2\mod\5\gfx\interface\province_bg.dds')
arr5=np.array(img5)
print(f"\nmod5 province_bg (git) size: {img5.size}")

in_icon=False
icon_starts5=[]
for y in range(200, 615):
    alpha_mean=float(arr5[y, 5:55, 3].mean())
    if alpha_mean > 150 and not in_icon:
        in_icon=True
        icon_starts5.append(y)
        print(f"Mod5 Icon start y={y}")
    elif alpha_mean <= 150 and in_icon:
        in_icon=False
        print(f"Mod5 Icon end   y={y-1} (height={y-icon_starts5[-1]})")
