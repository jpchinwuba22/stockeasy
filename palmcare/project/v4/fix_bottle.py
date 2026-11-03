"""Straighten a dropper-bottle cutout and make its silhouette perfectly symmetric by mirroring the
clean left profile about the bottle's centre line (fixes squared/flapped shoulders and clipped edges).
Usage: fix_bottle.py IN.png OUT.png ROTATE_DEG"""
import sys

import numpy as np
from PIL import Image

src, dst, rot = sys.argv[1], sys.argv[2], float(sys.argv[3])
im = Image.open(src).convert("RGBA")
im = im.crop(im.split()[-1].getbbox())
pad = Image.new("RGBA", (im.width + 80, im.height + 20), (0, 0, 0, 0))
pad.paste(im, (40, 10))
r = pad.rotate(rot, Image.BICUBIC, expand=True)
a = np.asarray(r).astype(np.float32)
al = a[..., 3]
H, Wd = al.shape
rows = np.arange(H)
has = (al > 128).any(axis=1)
L = np.array([np.argmax(al[y] > 128) if has[y] else -1 for y in rows])
R = np.array([Wd - 1 - np.argmax(al[y, ::-1] > 128) if has[y] else -1 for y in rows])
width = np.where(has, R - L, 0)
body = rows[width > 0.9 * width.max()]
y0, y1 = body[0] + 30, body[-1] - 30
# centre line from the body's left edge + median body width (robust to a clipped/flapped right edge)
Wb = float(np.median(width[y0:y1]))
lfit = np.poly1d(np.polyfit(rows[y0:y1], L[y0:y1], 1))
cx = lambda y: lfit(y) + Wb / 2
xs = np.arange(Wd, dtype=np.float32)
for y in rows[has]:
    c = cx(y)
    half = c - L[y]                       # mirror the left profile
    lx, rx = c - half, c + half
    new = np.clip(xs - lx + 0.5, 0, 1) * np.clip(rx - xs + 0.5, 0, 1) * 255
    # keep the original soft alpha on the left, mirrored edge softness on the right
    al[y] = np.minimum(np.maximum(new, 0), 255)
    last = int(min(R[y], rx) - 3)
    if rx > R[y] - 1 and last > L[y] + 6:
        a[y, last:, :3] = a[y, last - 5:last, :3].mean(axis=0)
a[..., 3] = al
out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
out = out.crop(out.split()[-1].getbbox())
out.save(dst)
print(out.size, round(Wb, 1))
