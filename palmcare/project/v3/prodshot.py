"""Product hero shot built ONLY from the real, straight product photo (no AI bottle): the cutout is moved by uniform
scale + vertical translation only (never rotated, sheared or warped), so it stays a perfect, straight rectangle with
the exact label. Background: one of the Flow texture clips, heavily defocused into warm bokeh.
Usage: prodshot.py OUT(.mp4|.jpg) CONFIG   (CONFIG: citrus | molecular)"""
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter

W, H, FPS = 1080, 1920, 24
OUT, CFG = sys.argv[1], sys.argv[2]
C = {
    "citrus": dict(bottle="assets/citrus_cut.png", h=1120, bg="src/N1.mp4", bg_t0=0.5, bg_speed=0.55,
                   blur=26, tint=(255, 196, 120), glow=(255, 170, 60), dur=4.5, cy=1130, spark=(255, 214, 140)),
    "molecular": dict(bottle="assets/molecular_cut.png", h=1120, bg="src/N5.mp4", bg_t0=2.0, bg_speed=0.6,
                      blur=24, tint=(255, 226, 205), glow=(255, 205, 170), dur=4.5, cy=1130, spark=(255, 240, 225)),
}[CFG]
N = int(C["dur"] * FPS)
rng = np.random.default_rng(4)


def eo(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def eio(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# ---------- the real bottle (premultiplied float, exact) ----------
b = Image.open(C["bottle"]).convert("RGBA")
b = b.crop(b.getbbox())
B = np.asarray(b).astype(np.float32) / 255.0
# clean product whites: gentle levels on the bottle colours only (white point 0.93, slight gamma), alpha untouched
pass   # studio-clean product photos: colours used exactly as photographed
print("bottle", b.size)


def bottle_at(scale):
    """Uniformly scaled bottle (premultiplied rgb, alpha). Area resampling keeps the print crisp."""
    h = C["h"] * scale
    w = h * B.shape[1] / B.shape[0]
    pm = np.dstack([B[..., :3] * B[..., 3:4], B[..., 3]])
    r = cv2.resize(pm, (max(1, round(w)), max(1, round(h))), interpolation=cv2.INTER_AREA)
    return r[..., :3], r[..., 3]


# ---------- background frames from the texture clip ----------
cap = cv2.VideoCapture(C["bg"])
BG = []
for i in range(N):
    t = C["bg_t0"] + i / FPS * C["bg_speed"]
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * 24))
    f = cap.read()[1]
    f = cv2.resize(f, (W, H), interpolation=cv2.INTER_CUBIC)
    f = cv2.GaussianBlur(f, (0, 0), C["blur"])
    BG.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
vign = np.clip(1 - 0.18 * (((XX - W / 2) / (W * 0.75)) ** 2 + ((YY - H * 0.48) / (H * 0.62)) ** 2), 0.8, 1)[..., None]
tint = np.array(C["tint"], np.float32) / 255

# drifting sparkles (bokeh dots)
SP = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(6, 22), rng.uniform(-40, -12), rng.uniform(0, 6.28)) for _ in range(38)]
glow_c = np.array(C["glow"], np.float32) / 255
spark_c = np.array(C["spark"], np.float32) / 255


def frame(i):
    t = i / FPS
    bg = BG[i] * 0.62 + tint * 0.38
    bg = 1 - (1 - bg) * 0.82                              # lift: airy, sunlit
    bg = bg * vign
    out = bg.copy()
    # bokeh sparkles
    for x, y, r, vy, ph in SP:
        yy = (y + vy * t) % H
        a = 0.10 + 0.10 * math.sin(ph + t * 1.7)
        x0, x1, y0, y1 = int(max(0, x - 3 * r)), int(min(W, x + 3 * r)), int(max(0, yy - 3 * r)), int(min(H, yy + 3 * r))
        if x1 > x0 and y1 > y0:
            d = np.exp(-(((XX[y0:y1, x0:x1] - x) ** 2 + (YY[y0:y1, x0:x1] - yy) ** 2) / (2 * r * r)))[..., None]
            out[y0:y1, x0:x1] = 1 - (1 - out[y0:y1, x0:x1]) * (1 - d * a * spark_c)
    # bottle: rises in (0-0.7 s), then a slow uniform push-in
    rise = eo(t / 0.75)
    sc = 0.94 + 0.06 * eio(t / C["dur"])
    rgb, al = bottle_at(sc)
    bh, bw = al.shape
    cx, cy = W / 2, C["cy"] + (1 - rise) * 320
    x0, y0 = int(round(cx - bw / 2)), int(round(cy - bh / 2))
    # warm glow behind the bottle
    g = np.zeros((H, W), np.float32)
    ys, xs = max(0, y0), max(0, x0)
    g[ys:min(H, y0 + bh), xs:min(W, x0 + bw)] = al[ys - y0:min(H, y0 + bh) - y0, xs - x0:min(W, x0 + bw) - x0]
    g = cv2.GaussianBlur(g, (0, 0), 70) * 0.55 * rise
    out = 1 - (1 - out) * (1 - g[..., None] * glow_c)
    # soft floor shadow under the bottle
    pool = np.exp(-(((XX - cx) / (bw * 0.9)) ** 2 + ((YY - (y0 + bh)) / 60) ** 2)) * 0.45 * rise
    out = 1 - (1 - out) * (1 - pool[..., None] * glow_c)
    # composite the bottle (premultiplied)
    y1c, x1c = min(H, y0 + bh), min(W, x0 + bw)
    sub = out[ys:y1c, xs:x1c]
    a = al[ys - y0:y1c - y0, xs - x0:x1c - x0, None] * min(1.0, rise * 1.4)
    p = rgb[ys - y0:y1c - y0, xs - x0:x1c - x0] * min(1.0, rise * 1.4)
    out[ys:y1c, xs:x1c] = p + sub * (1 - a)
    # specular light sweep across the bottle only (1.0-2.2 s)
    q = (t - 1.0) / 1.2
    if 0 < q < 1:
        pos = -400 + eio(q) * (bw + bh * 0.5 + 800)
        band = np.exp(-((((XX[ys:y1c, xs:x1c] - x0) + (YY[ys:y1c, xs:x1c] - y0) * 0.5) - pos) / 70) ** 2) * math.sin(math.pi * q)
        out[ys:y1c, xs:x1c] = 1 - (1 - out[ys:y1c, xs:x1c]) * (1 - band[..., None] * a * 0.55)
    return np.clip(out * 255, 0, 255).astype(np.uint8)


if OUT.endswith(".jpg"):
    ims = [Image.fromarray(frame(int(t * FPS))) for t in (0.2, 0.5, 1.0, 1.6, 2.4, 4.4)]
    sheet = Image.new("RGB", (360 * len(ims), 640))
    for k, im in enumerate(ims):
        sheet.paste(im.resize((360, 640), Image.LANCZOS), (360 * k, 0))
    sheet.save(OUT, quality=92)
    Image.fromarray(frame(int(2.6 * FPS))).save(OUT.replace(".jpg", "_full.png"))
else:
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    for i in range(N):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close()
    p.wait()
    print("frames", N)
