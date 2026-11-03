"""Straighten PalmCare product cutouts: remove the camera lean and the keystone taper from the source photos so the
bottle sides are parallel and dead vertical (the real square bottles and cylindrical serums have straight sides).
Lean -> per-row shift so the body's centre line is vertical; taper -> per-row horizontal scale about that centre so
the body width matches its width at the top of the body (caps and pumps above the body are only re-centred).
Usage: straighten.py IN.png OUT.png [BODY_TOP_FRAC BODY_BOT_FRAC]"""
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def edges(a, y0, y1):
    ys, ls, rs = [], [], []
    for y in range(int(y0), int(y1), 2):
        c = np.where(a[y] > 128)[0]
        if len(c) > 10:
            ys.append(y)
            ls.append(c.min())
            rs.append(c.max())
    ys, ls, rs = map(np.array, (ys, ls, rs))
    return np.polyfit(ys, ls, 1), np.polyfit(ys, rs, 1)


def straighten(im, top=0.45, bot=0.92):
    im = im.convert("RGBA")
    im = im.crop(im.split()[-1].getbbox())
    pad = 40
    big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    big.paste(im, (pad, pad))
    arr = np.asarray(big).astype(np.float32)
    a = arr[..., 3]
    ys = np.where(a.max(axis=1) > 128)[0]
    yt, yb = ys.min(), ys.max()
    h = yb - yt
    b0, b1 = yt + top * h, yt + bot * h
    (la, lb), (ra, rb) = edges(a, b0, b1)   # polyfit returns (slope, intercept)
    L = lambda y: la * y + lb
    R = lambda y: ra * y + rb
    c_line = lambda y: (L(y) + R(y)) / 2
    w_at = lambda y: R(y) - L(y)
    c0 = c_line(b0)
    w0 = w_at(b0)
    H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    yc = np.clip(yy, b0, b1)                       # taper scale only inside the body, constant above/below
    s = w_at(yc) / w0                               # source width / target width (<1 where the photo is narrower)
    src_x = c_line(yy) + (xx - c0) * s              # lean: follow the fitted centre line along the whole height
    out = np.zeros_like(arr)
    for ch in range(4):
        out[..., ch] = map_coordinates(arr[..., ch], [yy, src_x], order=3, mode="constant", cval=0.0)
    out = np.clip(out, 0, 255).astype(np.uint8)
    res = Image.fromarray(out, "RGBA")
    return res.crop(res.split()[-1].getbbox())


def measure(im, top=0.45, bot=0.92):
    a = np.asarray(im.convert("RGBA"))[..., 3].astype(np.float32)
    ys = np.where(a.max(axis=1) > 128)[0]
    yt, yb = ys.min(), ys.max()
    h = yb - yt
    (la, _), (ra, _) = edges(a, yt + top * h, yt + bot * h)
    return np.degrees(np.arctan(la)), np.degrees(np.arctan(ra))


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    top = float(sys.argv[3]) if len(sys.argv) > 3 else 0.45
    bot = float(sys.argv[4]) if len(sys.argv) > 4 else 0.92
    im = Image.open(src)
    before = measure(im, top, bot)
    out = straighten(im, top, bot)
    out.save(dst)
    after = measure(out, top, bot)
    print(f"{src}: left {before[0]:+.2f} right {before[1]:+.2f}  ->  left {after[0]:+.2f} right {after[1]:+.2f}  size {out.size}")
