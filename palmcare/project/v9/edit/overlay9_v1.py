"""Video 6 graphics over base9.mov — the "citrus editorial" system (new for this film): cinematic letterbox bars that
slide away on the beat drop, elegant Cormorant serif headlines, frosted citrus chips that pop only on key words, the
tone trio stacking as it is named, hydration ingredients orbiting the real jar, a GlowShield cross-sell chip with the
real pack, and signature transitions (light-leak burst, whip-pan blur, citrus iris wipe) on the big cuts.
Usage: overlay9.py OUT.mp4 | overlay9.py SHEET.jpg t1,t2,..."""
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import tl9 as tl

W, H, FPS = 1080, 1920, 24
BASE = "base9.mov"
FD = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/fonts/"
GS_PACK = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v5/assets/glowshield_box_flat.png"
SERIF, SERIF_I, CAPS, CAPS_L = "Cormorant-SemiBold.ttf", "Cormorant-Italic.ttf", "Jost-Medium.ttf", "Jost-Light.ttf"
INK, ORANGE, DEEP, CREAM, WHITE = (52, 30, 16), (240, 128, 36), (196, 92, 18), (255, 246, 234), (255, 255, 255)
_fc = {}


def font(n, s):
    if (n, s) not in _fc:
        _fc[(n, s)] = ImageFont.truetype(FD + n, s)
    return _fc[(n, s)]


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def eob(x, c=2.2):
    x = c01(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def text_img(s, f, fill, tracking=0, pad=10):
    w = sum(f.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    a, d = f.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, a + d + 2 * pad), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = pad
    for c in s:
        dr.text((x, pad), c, font=f, fill=fill)
        x += f.getlength(c) + tracking
    return im


def citrus_fill(im, top=(255, 214, 140), bot=(236, 108, 26)):
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    a[..., :3] = np.array(top, np.float32) * (1 - g) + np.array(bot, np.float32) * g
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def shadowed(im, blur=10, alpha=0.55, dy=3, col=(30, 14, 4)):
    out = Image.new("RGBA", (im.width + 60, im.height + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, col + (0,))
    m = Image.new("L", out.size, 0)
    m.paste(im.split()[-1], (30, 30 + dy))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha)))
    out.alpha_composite(sh)
    out.alpha_composite(im, (30, 30))
    return out


def fade(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.split()[-1].point(lambda v: int(v * max(0.0, a))))
    return im


def paste(dst, im, cx, cy, a=1.0, sc=1.0):
    if a <= 0.003 or sc <= 0.02:
        return
    if abs(sc - 1) > 0.005:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    dst.alpha_composite(fade(im, a), (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


def life(t, s, e, fin=0.14, fout=0.25):
    if t < s or t >= e:
        return 0.0
    return c01((t - s) / fin) * (1 - c01((t - (e - fout)) / fout))


def pop(dst, im, cx, cy, t, s, e, dur=0.42):
    a = life(t, s, e)
    if a > 0:
        paste(dst, im, cx, cy, a, 0.75 + 0.25 * eob((t - s) / dur))


def scrim(dst, y0, y1, strength, a):
    if a <= 0:
        return
    h = y1 - y0
    m = (np.sin(np.pi * np.linspace(0, 1, h)) ** 0.8)[:, None] * np.ones((1, W)) * strength * a
    band = np.zeros((h, W, 4), np.uint8)
    band[..., :3] = (30, 14, 4)
    band[..., 3] = (m * 255).astype(np.uint8)
    dst.alpha_composite(Image.fromarray(band, "RGBA"), (0, y0))


_chips = {}


def chip(text, dot=True, size=34, dark=False):
    """Frosted citrus chip: soft cream glass pill, orange-slice dot, spaced Jost caps."""
    key = (text, dot, size, dark)
    if key in _chips:
        return _chips[key]
    ti = text_img(text, font(CAPS, size), (WHITE if dark else INK) + (255,), tracking=5, pad=0)
    h = int(size * 2.1)
    w = ti.width + (h + 30 if dot else 70)
    im = Image.new("RGBA", (w + 50, h + 50), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((25, 31, 25 + w, 31 + h), radius=h // 2, fill=95)
    sh = Image.new("RGBA", im.size, (60, 26, 4, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((25, 25, 25 + w, 25 + h), radius=h // 2,
                        fill=(44, 22, 8, 210) if dark else (255, 248, 240, 236), outline=(246, 168, 92, 255), width=2)
    if dot:                                               # an orange slice: rind ring + segments
        cx, cy, r = 25 + h // 2 + 2, 25 + h // 2, int(h * 0.30)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE + (255,))
        d.ellipse((cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78), fill=(255, 196, 96, 255))
        for k in range(6):
            a = k * math.pi / 3
            d.line((cx, cy, cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78), fill=(255, 240, 210, 255), width=2)
        x0 = 25 + h + 8
    else:
        x0 = 25 + 35
    im.alpha_composite(ti, (x0, 25 + (h - ti.height) // 2 - 1))
    _chips[key] = im
    return im


def serif(text, size, italic=False, fill="cream"):
    im = text_img(text, font(SERIF_I if italic else SERIF, size), WHITE + (255,), pad=10)
    if fill == "citrus":
        return citrus_fill(im)
    a = np.asarray(im).copy()
    a[..., :3] = CREAM if fill == "cream" else INK
    return Image.fromarray(a, "RGBA")


# ---------- letterbox bars ----------
def letterbox(img, t):
    for s, e in ((0.0, tl.DROP), (56.4, tl.EC_START)):
        if s <= t < e + 0.35:
            q = 1 - eio((t - e) / 0.35) if t >= e else eo((t - s) / 0.25) if s > 0 else 1.0
            hb = int(150 * q)
            if hb > 0:
                d = ImageDraw.Draw(img)
                d.rectangle((0, 0, W, hb), fill=(8, 5, 3, 255))
                d.rectangle((0, H - hb, W, H), fill=(8, 5, 3, 255))


# ---------- hook ----------
HK1 = shadowed(serif("Dull, tired mornings?", 92, True), 14, 0.6)
HK2a = shadowed(text_img("WAKE  UP  YOUR", font(CAPS_L, 44), CREAM + (255,), tracking=10, pad=6), 12, 0.6)
HK2b = shadowed(serif("glow.", 190, True, "citrus"), 18, 0.55)


def draw_hook(img, t):
    a = life(t, 0.3, 2.25, 0.18, 0.2)
    if a > 0:
        scrim(img, 1240, 1640, 0.35, a)
        u = t - 0.3
        paste(img, HK1, W / 2, 1440 - 14 * (1 - eo(u / 0.5)), a)
    a = life(t, 2.62, tl.DROP, 0.12, 0.15)
    if a > 0:
        u = t - 2.62
        scrim(img, 1280, 1700, 0.4, a)
        paste(img, HK2a, W / 2, 1390, a * c01(u / 0.25))
        paste(img, HK2b, W / 2, 1530, a * c01((u - 0.55) / 0.12), 0.7 + 0.3 * eob((u - 0.55) / 0.45, 2.6))


# ---------- the morning problem ----------
def draw_problem(img, t):
    pop(img, chip("LOSES MOISTURE"), W / 2, 1600, t, 6.47, 7.7)
    pop(img, chip("FLAT"), W / 2 - 150, 1600, t, 8.14, tl.REVEAL - 0.05)
    pop(img, chip("PATCHY"), W / 2 + 150, 1600, t, 9.45, tl.REVEAL - 0.05)


# ---------- the reveal lock-up ----------
RV1 = text_img("P A L M C A R E", font(CAPS, 30), INK + (255,), tracking=4, pad=4)
RV2 = serif("Vitamin C", 118, False, "ink")
RV3 = serif("Face Moisturiser", 70, True, "citrus")


def draw_reveal(img, t):
    s, e = 13.85, tl.STARTS[5]
    if not (s <= t < e):
        return
    a = 1 - c01((t - (e - 0.3)) / 0.3)
    u = t - s
    paste(img, RV1, W / 2, 150, a * c01(u / 0.3))
    paste(img, RV2, W / 2, 238, a * c01((u - 0.55) / 0.2), 0.88 + 0.12 * eob((u - 0.55) / 0.4))
    paste(img, RV3, W / 2, 335, a * c01((u - 1.4) / 0.3))


# ---------- vitamin C, the tone trio ----------
TRIO = [("NIACINAMIDE", 25.55), ("ALPHA ARBUTIN", 26.36), ("TRANEXAMIC ACID", 27.66)]


def draw_actives(img, t):
    a = life(t, 18.85, 22.2, 0.15, 0.25)
    if a > 0:
        paste(img, chip("STABILISED VITAMIN C"), W / 2, 330, a, 0.8 + 0.2 * eob((t - 18.85) / 0.4))
    a = life(t, 22.3, 25.4, 0.15, 0.25)
    if a > 0:
        paste(img, chip("BRIGHTENS  ·  REVIVES"), W / 2, 330, a, 0.8 + 0.2 * eob((t - 22.3) / 0.4))
    end = 32.25
    on_pack = tl.STARTS[7] <= t < tl.STARTS[8]               # over the box + jar cutaway the chips lift above the products
    for k, (name, s) in enumerate(TRIO):
        pop(img, chip(name, True, 32, True), W / 2, (150 if on_pack else 1520) + k * 92, t, s, end)
    pop(img, chip("DARK SPOTS  ·  UNEVEN TONE", True, 30), W / 2, 1520 - 100, t, 30.03, end)


# ---------- hydration complex around the real jar ----------
ORBIT = [("HYALURONIC ACID", 32.8, (W / 2, 390)), ("GLYCERIN", 33.91, (W / 2 - 200, 495)), ("SQUALANE", 34.83, (W / 2 + 200, 495))]


def draw_hydration(img, t):
    s, e = tl.STARTS[9], tl.STARTS[10]
    if s <= t < e:
        a = 1 - c01((t - (e - 0.25)) / 0.25)
        hd = serif("deep, lasting hydration", 76, True, "ink")
        paste(img, hd, W / 2, 230, a * c01((t - 35.99) / 0.3))
        for k, (name, ts, (x, y)) in enumerate(ORBIT):        # above the jar: never over its label
            u = t - ts
            if u > 0:
                paste(img, chip(name, True, 30), x, y + 6 * math.sin(t * 2 + k), a * c01(u / 0.12), 0.75 + 0.25 * eob(u / 0.4))
    pop(img, chip("SHEA BUTTER", True, 30, True), W / 2 - 200, 1560, t, 38.26, 41.9)
    pop(img, chip("LICORICE EXTRACT", True, 30, True), W / 2 + 190, 1560, t, 39.09, 41.9)
    pop(img, chip("STRONGER SKIN BARRIER", True, 34), W / 2, 1660, t, 40.63, 43.9)


# ---------- results, daily use, finale ----------
_gs = Image.open(GS_PACK).convert("RGBA")
GS = shadowed(_gs.resize((round(_gs.width * 340 / _gs.height), 340), Image.LANCZOS), 12, 0.5, 6)
FIN = [("Luminous.", 56.9), ("Supple.", 57.95), ("Yours.", 58.9)]


def draw_results(img, t):
    pop(img, chip("HEALTHY INGREDIENTS"), W / 2, 1600, t, 44.2, 45.7)
    pop(img, chip("LIGHTWEIGHT  ·  NON-GREASY"), W / 2, 1600, t, 45.75, 47.85)
    a = life(t, 47.95, tl.STARTS[12] - 0.05, 0.12, 0.25)
    if a > 0:
        scrim(img, 1340, 1760, 0.35, a)
        for k, (wd, s) in enumerate((("Soft.", 47.95), ("Smooth.", 48.32), ("Radiant.", 48.81))):
            u = t - s
            if u > 0:
                im = shadowed(serif(wd, 84, True, "citrus" if k == 2 else "cream"), 12, 0.6)
                paste(img, im, W / 2, 1450 + k * 92, a * c01(u / 0.1), 0.8 + 0.2 * eob(u / 0.35))
    pop(img, chip("MORNING  &  NIGHT"), W / 2, 1600, t, 51.0, 52.5)
    a = life(t, 52.55, tl.STARTS[13] - 0.05, 0.2, 0.25)
    if a > 0:
        u = t - 52.55
        paste(img, chip("BY DAY, FOLLOW WITH GLOWSHIELD SPF 50+", True, 28), W / 2, 1640, a * c01(u / 0.15), 0.8 + 0.2 * eob(u / 0.4))
        if t > 54.4:
            paste(img, GS, 165, 1330, a * c01((t - 54.4) / 0.2), 0.7 + 0.3 * eob((t - 54.4) / 0.4))


def draw_finale(img, t):
    a = life(t, 56.85, tl.EC_START, 0.1, 0.25)
    if a <= 0:
        return
    scrim(img, 1280, 1740, 0.45, a)
    for k, (wd, s) in enumerate(FIN):
        u = t - s
        if u > 0:
            im = shadowed(serif(wd, 108 if k < 2 else 140, True, "citrus" if k == 2 else "cream"), 14, 0.6)
            paste(img, im, W / 2, 1370 + k * 120, a * c01(u / 0.1), 0.7 + 0.3 * eob(u / 0.35, 2.6))


# ---------- transitions ----------
YY, XX = np.mgrid[0:H:4, 0:W:4].astype(np.float32)


def up(m):
    return cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)


def transitions(arr, t):
    # light-leak bursts (warm orange bloom sweeping across) on the drop, the reveal, the mirror "after" and the end card
    for c in (tl.DROP, tl.REVEAL, tl.STARTS[10], tl.EC_START):
        u = t - c
        if -0.15 < u < 0.45:
            k = math.exp(-((u - 0.03) / 0.14) ** 2)
            cx = W * (0.2 + 0.6 * c01((u + 0.15) / 0.6))
            g = np.exp(-(((XX - cx) / 520) ** 2 + ((YY - H * 0.45) / 900) ** 2)) * 0.95 + 0.2
            m = up(np.clip(g * k, 0, 1))
            arr = 255 - (255 - arr) * (1 - m[..., None] * np.array([1.0, 0.72, 0.38]))
    # whip-pan blur across the texture -> application cut and the walk -> finale cut
    for c in (tl.STARTS[6], tl.STARTS[12], tl.STARTS[13]):
        u = t - c
        if -0.09 < u < 0.09:
            s = 1 - abs(u) / 0.09
            ksz = int(4 + 80 * s) | 1
            kern = np.zeros((1, ksz), np.float32)
            kern[0, :] = 1.0 / ksz
            arr = cv2.filter2D(arr, -1, kern)
    # citrus iris wipe out of the hook burst into her eyes opening
    u = t - tl.STARTS[1]
    if -0.12 < u < 0.2:
        r = 60 + 1500 * c01((u + 0.12) / 0.32)
        ring = np.exp(-((np.sqrt((XX - W / 2) ** 2 + (YY - H * 0.42) ** 2) - r) / 40) ** 2)
        m = up(ring)
        arr = 255 - (255 - arr) * (1 - m[..., None] * np.array([1.0, 0.62, 0.22]) * 0.85)
    return arr


def compose(frame, t):
    arr = transitions(frame.astype(np.float32), t)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    if t < tl.EC_START:
        draw_hook(img, t)
        draw_problem(img, t)
        draw_reveal(img, t)
        draw_actives(img, t)
        draw_hydration(img, t)
        draw_results(img, t)
        draw_finale(img, t)
    letterbox(img, t)
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]
    if out.endswith((".jpg", ".png")):
        ts = [float(x) for x in sys.argv[2].split(",")]
        ims = []
        for t in ts:
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", BASE, "-frames:v", "1", "-f", "rawvideo",
                                 "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            ims.append(Image.fromarray(compose(np.frombuffer(fr, np.uint8).reshape(H, W, 3), t)))
        sheet = Image.new("RGB", (432 * len(ims), 768))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((432, 768), Image.LANCZOS), (432 * k, 0))
        sheet.save(out, quality=90)
        sys.exit()
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", BASE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", BASE, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "15", "-preset", "slow",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out],
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
