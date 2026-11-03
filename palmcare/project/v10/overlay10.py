"""Video 7 graphics over base10.mov — "gold editorial" (new for this film): a gold hairline lower-third that names each
product as it is spoken (spaced PALMCARE caps + Cormorant italic name), gold serif tag lines on the benefit phrases,
and a soft gold light sweep on every beat cut. Pop-ups on key words only, no running captions.
Usage: overlay10.py OUT.mp4 | overlay10.py SHEET.jpg t1,t2,..."""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from build10 import STARTS

W, H, FPS = 1080, 1920, 24
BASE = "base10.mov"
FD = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/fonts/"
GOLD, CREAM, INK = (214, 172, 96), (255, 246, 232), (40, 24, 10)
_f = {}


def font(n, s):
    if (n, s) not in _f:
        _f[(n, s)] = ImageFont.truetype(FD + n, s)
    return _f[(n, s)]


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def text(s, f, fill, tracking=0, shadow=True):
    w = int(sum(f.getlength(c) for c in s) + tracking * max(0, len(s) - 1)) + 40
    a, d = f.getmetrics()
    im = Image.new("RGBA", (w, a + d + 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = 20
    for c in s:
        dr.text((x, 20), c, font=f, fill=fill + (255,))
        x += f.getlength(c) + tracking
    if shadow:
        sh = Image.new("RGBA", im.size, (20, 10, 2, 0))
        sh.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.65)))
        out = Image.new("RGBA", im.size, (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 3))
        out.alpha_composite(im)
        return out
    return im


def paste(dst, im, cx, cy, a=1.0):
    if a <= 0.003:
        return
    if a < 1:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    dst.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def life(t, s, e, fin=0.25, fout=0.3):
    if t < s or t >= e:
        return 0.0
    return c01((t - s) / fin) * (1 - c01((t - (e - fout)) / fout))


CAPS = text("P A L M C A R E", font("Jost-Medium.ttf", 30), GOLD, 6)
# (start, end, line1, line2)
NAMES = [(7.2, 10.8, "Milky Hydro-Glow", "Moisturising Body Wash"),
         (10.8, 16.05, "Cacao & Collagen", "Body Lotion"),
         (16.4, 19.7, "Citrus Vitamin Glow Infusion", "Body Wash"),
         (19.7, 25.3, "Molecular Glow", "Body Lotion"),
         (25.6, 29.95, "Advanced Tropical Glow", "Exfoliating Lightening Body Wash"),
         (29.95, 34.55, "Dermalight", "Body Lotion"),
         (35.95, 38.0, "Vita C+ Serum", ""),
         (38.3, 41.45, "N10 Niacinamide Serum", ""),
         (41.5, 44.95, "DermaLuxe Pro", "Hydrating Night Repair Serum"),
         (45.3, 51.85, "GlowShield", "Broad-Spectrum Daily Defense Sunscreen"),
         (52.3, 57.6, "Vitamin C", "Face Moisturiser")]
NAME_IM = []
for s, e, l1, l2 in NAMES:
    a = text(l1, font("Cormorant-SemiBold.ttf", 80), CREAM)
    b = text(l2, font("Cormorant-Italic.ttf", 54), GOLD) if l2 else None
    NAME_IM.append((s, e, a, b))
TAGS = [(14.05, 16.05, "softness you can feel."), (22.55, 25.3, "radiance, unlocked."), (32.45, 34.55, "a luminous, even tone."),
        (34.8, 35.95, "for your face")]
TAG_IM = [(s, e, text(x, font("Cormorant-Italic.ttf", 92), CREAM)) for s, e, x in TAGS]
SPF = text("SPF 50+   ·   PA++++", font("Jost-Medium.ttf", 44), GOLD, 4)
HEALTHY = text("HEALTHY  INGREDIENTS", font("Jost-Medium.ttf", 40), INK, 6, shadow=False)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
SCRIM = np.clip((YY[:, :1] - 1380) / 420, 0, 1) ** 1.4                       # bottom darkening for the lower-third


def lower_third(img, arr_a, t):
    for s, e, a, b in NAME_IM:
        k = life(t, s, e)
        if k <= 0:
            continue
        arr_a[0] = max(arr_a[0], k)
        u = t - s
        y = 1625
        paste(img, CAPS, W / 2, y - 95, k * c01(u / 0.3))
        rp = eo(u / 0.5)
        ImageDraw.Draw(img).line((W / 2 - 170 * rp, y - 62, W / 2 + 170 * rp, y - 62), fill=GOLD + (int(255 * k),), width=2)
        paste(img, a, W / 2, y + 2 + 16 * (1 - eo(u / 0.45)), k)
        if b is not None:
            paste(img, b, W / 2, y + 82 + 16 * (1 - eo((u - 0.12) / 0.45)), k * c01((u - 0.12) / 0.3))


def tags(img, t):
    for s, e, im in TAG_IM:
        k = life(t, s, e)
        if k > 0:
            paste(img, im, W / 2, 300 + 14 * (1 - eo((t - s) / 0.5)), k)
    k = life(t, 49.1, 51.85)
    if k > 0:
        paste(img, SPF, W / 2, 300, k)
    k = life(t, 57.95, 61.7)
    if k > 0:                                                   # end card: gold pill above the lineup
        u = t - 57.95
        pill = Image.new("RGBA", (HEALTHY.width + 40, 110), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((20, 20, pill.width - 20, 90), 35, fill=GOLD + (240,))
        pill.alpha_composite(HEALTHY, (20, (110 - HEALTHY.height) // 2))
        paste(img, pill, W / 2, 400 + 10 * (1 - eo(u / 0.4)), k)


def sweep(arr, t):
    for c in STARTS[1:-1]:
        u = t - c
        if -0.1 < u < 0.42:
            k = math.exp(-((u - 0.03) / 0.14) ** 2)
            cx = W * (0.15 + 0.7 * c01((u + 0.1) / 0.52))
            g = np.exp(-(((XX[::4, ::4] - cx) / 380) ** 2)) * 0.85 * k
            m = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
            arr = 255 - (255 - arr) * (1 - m[..., None] * np.array([1.0, 0.82, 0.5]))
    return arr


def compose(frame, t):
    arr = sweep(frame.astype(np.float32), t)
    lt = [0.0]
    img0 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lower_third(img0, lt, t)
    if lt[0] > 0:
        arr = arr * (1 - SCRIM[..., None] * 0.62 * lt[0])
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    img.alpha_composite(img0)
    tags(img, t)
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]
    if out.endswith((".jpg", ".png")):
        ims = []
        for t in [float(x) for x in sys.argv[2].split(",")]:
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", BASE, "-frames:v", "1", "-f", "rawvideo",
                                 "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            ims.append(Image.fromarray(compose(np.frombuffer(fr, np.uint8).reshape(H, W, 3), t)))
        sheet = Image.new("RGB", (360 * len(ims), 640))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((360, 640), Image.LANCZOS), (360 * k, 0))
        sheet.save(out, quality=90)
        sys.exit()
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", BASE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", out],
                          stdin=subprocess.PIPE)
    i = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        wr.stdin.write(compose(np.frombuffer(buf, np.uint8).reshape(H, W, 3), i / FPS).tobytes())
        i += 1
    wr.stdin.close()
    wr.wait()
    print("frames", i)
