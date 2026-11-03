"""Vitamin C ad (final concept): street stop -> real jar -> cream -> her review with the real box -> hero -> end card.
Professional cut: hook on the first word, punch-ins / push-ins inside takes, J-cut cutaway (her voice over the swatch),
whip-blur cuts, flash + shake on the drop, warm cinematic grade, punchy word-pop subtitles with gold key words,
ingredient pop-ups synced to her voice. Usage: edit14.py OUT.mp4 | edit14.py SHEET.jpg t1,t2,..."""
import json
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
V = D + "v14/"
W, H, FPS = 1080, 1920, 24
# (source, src_in, src_out, zoom0, zoom1, focus_x, focus_y [0..1 of frame], kind)
SHOTS = [(V + "src/D.mp4", 1.80, 5.62, 1.00, 1.12, 0.50, 0.42, "talk"),     # stranger stops her (hook)
         (V + "src/D.mp4", 6.30, 8.80, 1.38, 1.46, 0.52, 0.30, "talk"),     # punch-in: she names the product
         (V + "A_fixed.mp4", 5.50, 7.60, 1.00, 1.10, 0.47, 0.62, "prod"),   # DROP: real jar in the sun
         (V + "src/B.mp4", 0.20, 1.40, 1.05, 1.22, 0.50, 0.45, "broll"),    # cream swirl
         (V + "src/B.mp4", 7.00, 9.00, 1.00, 1.10, 0.55, 0.45, "broll"),    # fingertip lifts the cream
         (V + "box_fixed.mp4", 0.00, 3.90, 1.00, 1.06, 0.50, 0.50, "talk"), # review, medium: the four actives
         (V + "box_fixed.mp4", 3.90, 5.30, 1.08, 1.12, 0.50, 0.42, "talk"), # gentle push (chips stay clear of the box)
         (V + "src/C.mp4", 4.00, 6.30, 1.00, 1.12, 0.50, 0.50, "broll"),    # J-cut: swatch glows under her voice
         (V + "box_fixed.mp4", 7.60, 10.0, 1.45, 1.52, 0.50, 0.30, "talk"), # close-up: "Trust me, you need this!"
         (D + "v11/qa/C_P9.mp4", 5.00, 7.60, 1.00, 1.08, 0.50, 0.55, "prod"), # hero: real box + jar
         (D + "v9/EC9b.mp4", 0.00, 6.00, 1.00, 1.00, 0.50, 0.50, "ec")]     # end card
STARTS = list(np.cumsum([0] + [round((b - a) * FPS) / FPS for _, a, b, *_ in SHOTS]))
TOTAL = STARTS[-1]
DROP, HERO, EC = STARTS[2], STARTS[9], STARTS[10]
REVIEW = STARTS[5]
# subtitles: (start, end, text, gold?)  — timeline seconds, word-pop groups
def dw(t):
    return t - 1.80                     # D first take
def dw2(t):
    return STARTS[1] + (t - 6.30)       # D second take
def ew(t):
    return REVIEW + t                   # review audio runs continuously from the start of shot 5
SUBS = [(dw(2.06), dw(2.85), "WAIT…", False),
        (dw(3.32), dw(4.45), "YOUR SKIN IS", False), (dw(4.02), dw(4.70), "GLOWING!", True),
        (dw(4.86), dw(5.62), "WHAT DO YOU USE?", False),
        (dw2(6.48), dw2(7.40), "PALMCARE", True), (dw2(7.08), dw2(8.75), "VITAMIN C FACE MOISTURISER", True),
        (ew(5.38), ew(5.95), "BRIGHTER,", True), (ew(6.36), ew(6.80), "EVEN,", True), (ew(6.78), ew(7.85), "HYDRATED SKIN", True),
        (ew(8.34), ew(8.90), "TRUST ME,", False), (ew(9.02), ew(9.95), "YOU NEED THIS!", True)]
ACTIVES = [(ew(0.0), "VITAMIN C"), (ew(1.26), "NIACINAMIDE"), (ew(2.56), "ALPHA ARBUTIN"), (ew(3.72), "TRANEXAMIC ACID")]
FD = D + "fonts/"
GOLD, WHITE, INK = (255, 196, 64), (255, 255, 255), (20, 12, 4)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.28 * np.clip(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H * 0.48) / (H * 0.62)) ** 2, 0, 1.4) ** 1.3)[..., None]
_x = np.linspace(0, 1, 256)
LUT = np.clip(255 * (_x - 0.05 * np.sin(2 * np.pi * _x)), 0, 255).astype(np.uint8)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eob(x, c=2.0):
    x = c01(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


_cache = {}


def word_img(text, gold, size=92):
    key = (text, gold, size)
    if key in _cache:
        return _cache[key]
    f = ImageFont.truetype(FD + "Montserrat-ExtraBold.ttf", size)
    w = int(f.getlength(text)) + 60
    while w > W - 60:
        size -= 6
        f = ImageFont.truetype(FD + "Montserrat-ExtraBold.ttf", size)
        w = int(f.getlength(text)) + 60
    a, d = f.getmetrics()
    im = Image.new("RGBA", (w, a + d + 50), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((30, 22), text, font=f, fill=(GOLD if gold else WHITE) + (255,), stroke_width=7, stroke_fill=INK + (255,))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.55)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 6))
    out.alpha_composite(im)
    _cache[key] = out
    return out


def chip(text):
    key = ("chip", text)
    if key in _cache:
        return _cache[key]
    f = ImageFont.truetype(FD + "Montserrat-ExtraBold.ttf", 46)
    tw = int(f.getlength(text))
    im = Image.new("RGBA", (tw + 150, 120), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((10, 14, tw + 140, 106), 46, fill=(255, 196, 64, 245))
    dr.ellipse((30, 38, 74, 82), fill=(255, 255, 255, 255))
    dr.text((44, 34), "✓" if False else "", font=f, fill=INK + (255,))
    dr.line((40, 60, 50, 71), fill=(232, 120, 20, 255), width=6)
    dr.line((50, 71, 66, 48), fill=(232, 120, 20, 255), width=6)
    dr.text((92, 30), text, font=f, fill=INK + (255,))
    _cache[key] = im
    return im


def paste(img, im, cx, cy, a=1.0, sc=1.0):
    if a <= 0.01 or sc <= 0.02:
        return
    if abs(sc - 1) > 0.01:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    if a < 0.99:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def reader(src, st, dur):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{st:.4f}", "-i", src, "-t", f"{dur + 0.25:.4f}", "-vf",
                          f"fps={FPS},scale={W}:{H}:flags=lanczos,cas=0.45", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         stdout=subprocess.PIPE)
    last = None
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            while True:
                yield last
        last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        yield last


def zoom(fr, z, fx, fy):
    if z <= 1.001:
        return fr
    cw, ch = W / z, H / z
    cx = min(max(fx * W, cw / 2), W - cw / 2)
    cy = min(max(fy * H, ch / 2), H - ch / 2)
    M = np.float32([[z, 0, -(cx - cw / 2) * z], [0, z, -(cy - ch / 2) * z]])
    return cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def grade(fr, kind):
    if kind == "ec":
        return fr.astype(np.float32)
    x = cv2.LUT(fr, LUT).astype(np.float32)
    g = x.mean(2, keepdims=True)
    x = g + (x - g) * 1.08
    x *= np.array([0.975, 1.0, 1.04], np.float32)            # warm (BGR)
    hi = np.clip(x - 185, 0, 255)
    bl = cv2.resize(cv2.GaussianBlur(cv2.resize(hi, (W // 6, H // 6)), (0, 0), 6), (W, H))
    x = 255 - (255 - x) * (1 - bl / 255 * 0.45)
    return x * VIG


def fx(x, t):
    for c in STARTS[1:-1]:                                  # whip blur through every cut
        u = t - c
        if -0.06 < u < 0.06 and c not in (STARTS[8],):
            k = int(4 + 60 * (1 - abs(u) / 0.06)) | 1
            x = cv2.filter2D(x, -1, np.full((1, k), 1.0 / k, np.float32))
    for c, s in ((DROP, 0.6), (HERO, 0.45), (EC, 0.35)):    # flash + shake on the big hits
        u = t - c
        if 0 <= u < 0.32:
            x = x + (255 - x) * s * (1 - u / 0.32) ** 2
        if 0 <= u < 0.18:
            k = (1 - u / 0.18) ** 2
            M = np.float32([[1.03, 0, -W * 0.015 + 14 * k * math.sin(u * 90)], [0, 1.03, -H * 0.015 + 10 * k * math.cos(u * 70)]])
            x = cv2.warpAffine(x, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return x


def overlays(img, t):
    for s, e, text, gold in SUBS:                           # word-pop subtitles
        if s <= t < e:
            u = t - s
            paste(img, word_img(text, gold), W / 2, 1530, 1.0, 0.7 + 0.3 * eob(u / 0.18, 2.6))
    for k, (s, text) in enumerate(ACTIVES):                 # the four actives stack in as she names them
        end = STARTS[7] - 0.05
        if s <= t < end:
            u = t - s
            a = 1 - c01((t - (end - 0.2)) / 0.2)
            cx, cy = (W * 0.29, 1600) if k % 2 == 0 else (W * 0.71, 1600)        # below the box, never over her face
            cy += (k // 2) * 118
            paste(img, chip(text), cx - 50 * (1 - eo(u / 0.25)), cy, a, 0.72 * (0.8 + 0.2 * eob(u / 0.3, 2.4)))
    if DROP <= t < STARTS[3] - 0.05:                        # title on the jar
        u = t - DROP
        paste(img, word_img("THE GLOW SECRET", True, 100), W / 2, 330, c01(u / 0.15), 0.75 + 0.25 * eob(u / 0.3, 2.6))
    if HERO <= t < EC - 0.05:
        u = t - HERO
        paste(img, word_img("PALMCARE", False, 110), W / 2, 300, c01(u / 0.15), 0.75 + 0.25 * eob(u / 0.3))
        paste(img, word_img("VITAMIN C FACE MOISTURISER", True, 64), W / 2, 420, c01((u - 0.15) / 0.15), 0.8 + 0.2 * eob((u - 0.15) / 0.3))


def render(want=None):
    for k, (src, a, b, z0, z1, fxp, fyp, kind) in enumerate(SHOTS):
        i0, i1 = int(round(STARTS[k] * FPS)), int(round(STARTS[k + 1] * FPS))
        if want is not None and not any(i0 <= w < i1 for w in want):
            continue
        rd = reader(src, a, b - a)
        for i in range(i0, i1):
            fr = next(rd)
            if want is not None and i not in want:
                continue
            t = i / FPS
            p = (i - i0) / max(1, i1 - i0 - 1)
            z = z0 + (z1 - z0) * (p * p * (3 - 2 * p))
            x = fx(grade(zoom(fr, z, fxp, fyp), kind), t)
            img = Image.fromarray(cv2.cvtColor(np.clip(x, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)).convert("RGBA")
            overlays(img, t)
            yield i, np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]
    if out.endswith(".jpg"):
        ts = [float(x) for x in sys.argv[2].split(",")]
        got = dict(render({int(round(t * FPS)) for t in ts}))
        ims = [Image.fromarray(got[int(round(t * FPS))]).resize((270, 480)) for t in ts]
        sheet = Image.new("RGB", (270 * len(ims), 480))
        for j, im in enumerate(ims):
            sheet.paste(im, (270 * j, 0))
        sheet.save(out, quality=88)
        sys.exit()
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = 0
    for i, rgb in render():
        wr.stdin.write(rgb.tobytes()); n += 1
    wr.stdin.close(); wr.wait()
    print("frames", n, "TOTAL", TOTAL, "DROP", DROP, "HERO", HERO, "EC", EC)
