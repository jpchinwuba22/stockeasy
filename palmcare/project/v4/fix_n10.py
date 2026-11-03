"""Straighten the Vita C+ cutout and rebuild a clean, symmetric cylinder silhouette (the photo's right edge was clipped)."""
import numpy as np
from PIL import Image

im = Image.open("v4/n10_cut.png").convert("RGBA")
im = im.crop(im.split()[-1].getbbox())
pad = Image.new("RGBA", (im.width + 60, im.height), (0, 0, 0, 0))
pad.paste(im, (10, 0))
r = pad.rotate(-3.1, Image.BICUBIC, expand=True)
a = np.asarray(r).astype(np.float32)
al = a[..., 3]
rows = np.arange(al.shape[0])
L = np.array([np.argmax(al[y] > 128) if (al[y] > 128).any() else -1 for y in rows])
R = np.array([al.shape[1] - 1 - np.argmax(al[y, ::-1] > 128) if (al[y] > 128).any() else -1 for y in rows])
body = [y for y in rows if L[y] >= 0 and R[y] - L[y] > 280]
y0, y1 = body[0] + 18, body[-1]
# rows where both edges are genuine (right edge not at the old crop border)
good = [y for y in range(y0, y1) if R[y] < R[y0:y1].max() - 3]
W = float(np.median(R[good] - L[good]))
Lfit = np.poly1d(np.polyfit(np.arange(y0, y1 - 60), L[y0:y1 - 60], 1))
xs = np.arange(al.shape[1], dtype=np.float32)
for y in range(y0, al.shape[0]):
    if L[y] < 0:
        continue
    # mirror the genuine left profile (incl. the rounded foot) onto the right side
    dl = max(0.0, L[y] - Lfit(y)) if y > y1 - 80 else 0.0
    lx = Lfit(y) + dl
    rx = Lfit(y) + W - dl
    new = np.clip(xs - lx + 0.5, 0, 1) * np.clip(rx - xs + 0.5, 0, 1) * 255
    al[y] = new
    # extend colour past the old clipped right border by replicating the last solid column
    last = int(min(R[y], rx) - 4)
    if last > 8:
        a[y, last:, :3] = a[y, last - 6:last, :3].mean(axis=0)
a[..., 3] = al
out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
out = out.crop(out.split()[-1].getbbox())
out.save("v4/n10_fix.png")
print(out.size, W, y0, y1)
