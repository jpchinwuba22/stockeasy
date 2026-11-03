"""Vitamin C ad, revision: gentle camera only (characters always in frame), soft cross-dissolves between every shot (a
white dip on the beat drop), smooth eased moves, rock-steady real labels, refined subtitles (clean semibold, soft
shadow, gold key words), small ingredient pop-ups below the box. Two passes: shots -> dissolves (base15.mp4) ->
overlays (OUT). Usage: edit15.py base | edit15.py OUT.mp4 | edit15.py SHEET.jpg t1,t2,..."""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
V = D + "v14/"
W, H, FPS = 1080, 1920, 24
XF = 0.35
# (source, src_in, src_out, zoom0, zoom1, focus_x, focus_y, kind)
SHOTS = [(V + "src/D.mp4", 1.80, 5.62, 1.00, 1.04, 0.50, 0.45, "talk"),        # stranger stops her (hook)
         (V + "src/D.mp4", 6.30, 8.80, 1.04, 1.08, 0.50, 0.42, "talk"),        # she names the product
         (V + "jar_hero.mp4", 0.30, 2.40, 1.00, 1.00, 0.50, 0.50, "prod"),     # DROP: real jar, seated on the pedestal
         (V + "src/B.mp4", 0.20, 1.40, 1.00, 1.06, 0.50, 0.45, "broll"),       # cream swirl
         (V + "src/B.mp4", 7.00, 9.00, 1.00, 1.05, 0.55, 0.45, "broll"),       # fingertip lifts the cream
         (V + "box_fixed.mp4", 0.00, 5.30, 1.00, 1.06, 0.50, 0.46, "talk"),    # review: the four actives (one smooth take)
         (V + "src/C.mp4", 4.00, 6.30, 1.00, 1.06, 0.50, 0.50, "broll"),       # her voice continues over the swatch
         (V + "box_fixed.mp4", 7.60, 10.0, 1.10, 1.15, 0.50, 0.40, "talk"),    # "Trust me, you need this!"
         (V + "hero_static.mp4", 0.10, 2.70, 1.00, 1.00, 0.50, 0.55, "prod"),    # hero: real box + jar, seated on a still set
         (D + "v9/EC9b.mp4", 0.00, 6.00, 1.00, 1.00, 0.50, 0.50, "ec")]        # end card
STARTS = list(np.cumsum([0] + [round((b - a) * FPS) / FPS for _, a, b, *_ in SHOTS]))
TOTAL = STARTS[-1]
DROP, HERO, EC, REVIEW = STARTS[2], STARTS[8], STARTS[9], STARTS[5]
TRANS = {2: "fadewhite"}                                       # transition INTO shot k (default: soft dissolve)


def dw(t):
    return t - 1.80


def dw2(t):
    return STARTS[1] + (t - 6.30)


def ew(t):
    return REVIEW + t


SUBS = [(dw(2.06), dw(2.85), [("Wait…", 0)]),
        (dw(3.32), dw(4.75), [("Your skin is ", 0), ("glowing!", 1)]),
        (dw(4.86), dw(5.62), [("What do you use?", 0)]),
        (dw2(6.48), dw2(8.75), [("PalmCare ", 1), ("Vitamin C Face Moisturiser", 1)]),
        (ew(5.38), ew(7.85), [("Brighter, even, ", 0), ("hydrated skin", 1)]),
        (ew(8.34), ew(9.95), [("Trust me, ", 0), ("you need this!", 1)])]
ACTIVES = [(ew(0.0), "VITAMIN C"), (ew(1.26), "NIACINAMIDE"), (ew(2.56), "ALPHA ARBUTIN"), (ew(3.72), "TRANEXAMIC ACID")]
FD = D + "fonts/"
GOLD, WHITE, INK = (255, 205, 96), (255, 255, 255), (24, 14, 6)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.22 * np.clip(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H * 0.48) / (H * 0.62)) ** 2, 0, 1.4) ** 1.3)[..., None]
_x = np.linspace(0, 1, 256)
LUT = np.clip(255 * (_x - 0.04 * np.sin(2 * np.pi * _x)), 0, 255).astype(np.uint8)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def ease(p):
    p = c01(p)
    return p * p * (3 - 2 * p)


# ---------- pass 1: shots -> dissolves ----------
def reader(src, st, dur):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{st:.4f}", "-i", src, "-t", f"{dur + 0.3:.4f}", "-vf",
                          f"fps={FPS},scale={W}:{H}:flags=lanczos,cas=0.35", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
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
        return fr
    x = cv2.LUT(fr, LUT).astype(np.float32)
    g = x.mean(2, keepdims=True)
    x = g + (x - g) * 1.06
    x *= np.array([0.98, 1.0, 1.035], np.float32)
    hi = np.clip(x - 190, 0, 255)
    bl = cv2.resize(cv2.GaussianBlur(cv2.resize(hi, (W // 6, H // 6)), (0, 0), 6), (W, H))
    x = 255 - (255 - x) * (1 - bl / 255 * 0.4)
    return np.clip(x * VIG, 0, 255).astype(np.uint8)


def build_base():
    os.makedirs("seg15", exist_ok=True)
    files = []
    for k, (src, a, b, z0, z1, fx, fy, kind) in enumerate(SHOTS):
        dur = STARTS[k + 1] - STARTS[k]
        tail = XF if k < len(SHOTS) - 1 else 0
        n = int(round((dur + tail) * FPS))
        nmain = int(round(dur * FPS))
        out = f"seg15/{k:02d}.mp4"
        wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                               "-i", "-", "-c:v", "libx264", "-crf", "11", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        rd = reader(src, a, dur + tail)
        for i in range(n):
            p = min(1.0, i / max(1, nmain - 1))
            z = z0 + (z1 - z0) * ease(p) + (z1 - z0) / max(1, nmain) * max(0, i - nmain)   # keep drifting through the tail
            wr.stdin.write(grade(zoom(next(rd), z, fx, fy), kind).tobytes())
        wr.stdin.close(); wr.wait()
        files.append(out)
    chain, cur = [], "[0:v]"
    for k in range(1, len(files)):
        tr = TRANS.get(k, "fade")
        d = 0.30 if tr == "fadewhite" else XF
        lab = f"[x{k}]"
        chain.append(f"{cur}[{k}:v]xfade=transition={tr}:duration={d}:offset={STARTS[k]:.4f}{lab}")
        cur = lab
    chain.append(f"{cur}trim=0:{TOTAL},format=yuv420p[v]")
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for f in files:
        cmd += ["-i", f]
    cmd += ["-filter_complex", ";".join(chain), "-map", "[v]", "-c:v", "libx264", "-crf", "12", "-preset", "medium", "base15.mp4"]
    subprocess.run(cmd, check=True)


# ---------- pass 2: overlays ----------
_cache = {}


def sub_img(parts):
    key = tuple(parts)
    if key in _cache:
        return _cache[key]
    f = ImageFont.truetype(FD + "Montserrat-SemiBold.ttf", 58)
    fb = ImageFont.truetype(FD + "Montserrat-Bold.ttf", 58)
    widths = [(fb if g else f).getlength(t) for t, g in parts]
    w = int(sum(widths)) + 60
    while w > W - 80:
        f = ImageFont.truetype(FD + "Montserrat-SemiBold.ttf", int(f.size * 0.9))
        fb = ImageFont.truetype(FD + "Montserrat-Bold.ttf", int(fb.size * 0.9))
        widths = [(fb if g else f).getlength(t) for t, g in parts]
        w = int(sum(widths)) + 60
    a, d = f.getmetrics()
    im = Image.new("RGBA", (w, a + d + 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = 30
    for (t, g), wd in zip(parts, widths):
        dr.text((x, 18), t, font=fb if g else f, fill=(GOLD if g else WHITE) + (255,), stroke_width=2, stroke_fill=(30, 18, 8, 160))
        x += wd
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.7)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 3))
    out.alpha_composite(im)
    _cache[key] = out
    return out


def chip(text):
    key = ("chip", text)
    if key in _cache:
        return _cache[key]
    f = ImageFont.truetype(FD + "Montserrat-SemiBold.ttf", 30)
    tw = int(f.getlength(text))
    im = Image.new("RGBA", (tw + 96, 76), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((6, 10, tw + 90, 66), 28, fill=(255, 250, 240, 235), outline=(232, 160, 60, 255), width=2)
    dr.ellipse((20, 26, 44, 50), fill=(240, 140, 30, 255))
    dr.line((26, 38, 31, 44), fill=(255, 255, 255, 255), width=3)
    dr.line((31, 44, 39, 32), fill=(255, 255, 255, 255), width=3)
    dr.text((56, 20), text, font=f, fill=INK + (255,))
    _cache[key] = im
    return im


def title(text, size, gold=True, track=6):
    key = ("t", text, size, gold)
    if key in _cache:
        return _cache[key]
    f = ImageFont.truetype(FD + "Montserrat-SemiBold.ttf", size)
    w = int(sum(f.getlength(c) for c in text) + track * len(text)) + 60
    a, d = f.getmetrics()
    im = Image.new("RGBA", (w, a + d + 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = 30
    for c in text:
        dr.text((x, 18), c, font=f, fill=(GOLD if gold else WHITE) + (255,))
        x += f.getlength(c) + track
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.75)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 3))
    out.alpha_composite(im)
    _cache[key] = out
    return out


def paste(img, im, cx, cy, a=1.0):
    if a <= 0.01:
        return
    if a < 0.99:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def overlays(img, t):
    for s, e, parts in SUBS:                                 # refined subtitles: fade + small rise
        if s <= t < e:
            u = t - s
            a = c01(u / 0.12) * (1 - c01((t - (e - 0.12)) / 0.12))
            paste(img, sub_img(parts), W / 2, 1655 + 14 * (1 - eo(u / 0.25)), a)
    end = STARTS[6] - 0.1
    for k, (s, text) in enumerate(ACTIVES):                  # actives: small chips, two rows below the box
        if s <= t < end:
            u = t - s
            a = c01(u / 0.18) * (1 - c01((t - (end - 0.25)) / 0.25))
            cx = W * (0.30 if k % 2 == 0 else 0.70)
            cy = 1640 + (k // 2) * 84
            paste(img, chip(text), cx, cy + 18 * (1 - eo(u / 0.3)), a)
    if DROP + 0.15 <= t < STARTS[3] - 0.1:
        u = t - DROP - 0.15
        paste(img, title("THE GLOW SECRET", 62, False), W / 2, 330 + 12 * (1 - eo(u / 0.4)), c01(u / 0.25))
    if HERO + 0.1 <= t < EC - 0.1:
        u = t - HERO - 0.1
        paste(img, title("PALMCARE", 70, False, 14), W / 2, 290 + 12 * (1 - eo(u / 0.4)), c01(u / 0.25))
        paste(img, title("VITAMIN C FACE MOISTURISER", 40, True, 4), W / 2, 380, c01((u - 0.2) / 0.25))


def render_overlays(want=None):
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", "base15.mp4", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    i = 0
    while True:
        b = rd.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            return
        if want is None or i in want:
            img = Image.fromarray(np.frombuffer(b, np.uint8).reshape(H, W, 3)).convert("RGBA")
            overlays(img, i / FPS)
            yield i, np.asarray(img.convert("RGB"))
        i += 1


if __name__ == "__main__":
    out = sys.argv[1]
    if out == "base":
        build_base(); sys.exit()
    if out.endswith(".jpg"):
        ts = [float(x) for x in sys.argv[2].split(",")]
        got = dict(render_overlays({int(round(t * FPS)) for t in ts}))
        ims = [Image.fromarray(got[int(round(t * FPS))]).resize((270, 480)) for t in ts]
        sheet = Image.new("RGB", (270 * len(ims), 480))
        for j, im in enumerate(ims):
            sheet.paste(im, (270 * j, 0))
        sheet.save(out, quality=88)
        sys.exit()
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = 0
    for i, rgb in render_overlays():
        wr.stdin.write(rgb.tobytes()); n += 1
    wr.stdin.close(); wr.wait()
    print("frames", n, "TOTAL", TOTAL)
