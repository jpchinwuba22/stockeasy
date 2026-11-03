"""Side-by-side crops (source vs fixed) at chosen frames. Usage: cropsheet.py SRC FIX x0,y0,x1,y1 OUT f1,f2,..."""
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "labelfix")
from fixclip2 import read_frames
src, fix, box, out, fr = sys.argv[1], sys.argv[2], [int(v) for v in sys.argv[3].split(",")], sys.argv[4], [int(v) for v in sys.argv[5].split(",")]
A, B = read_frames(src), read_frames(fix)
x0, y0, x1, y1 = box
w, h = x1 - x0, y1 - y0
sc = min(1.0, 300 / w)
tw, th = int(w * sc), int(h * sc)
sheet = Image.new("RGB", (tw * len(fr), th * 2 + 20), "black")
d = ImageDraw.Draw(sheet)
for k, i in enumerate(fr):
    for r, F in enumerate((A, B)):
        im = Image.fromarray(F[min(i, len(F) - 1)][y0:y1, x0:x1]).resize((tw, th), Image.LANCZOS)
        g = ImageDraw.Draw(im)
        for yy in range(0, th, 40):   # fixed grid to judge motion
            g.line((0, yy, tw, yy), fill=(0, 255, 0), width=1)
        sheet.paste(im, (k * tw, r * (th + 20)))
    d.text((k * tw + 4, th + 4), f"f{i}", fill="white")
sheet.save(out, quality=90)
