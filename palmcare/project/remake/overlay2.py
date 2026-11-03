"""Video 2 graphics + transitions over baseR2.mov ("Sunlit" identity; nothing shared with Video 1):
- LIGHTNING UNVEILS: blackout breath -> double lightning strike (procedural bolts, flash, RGB split) -> lights come up
  with a specular sweep across the product
- transitions on the beat: sun-flare wipe, whip pan, liquid ripple
- captions: Bricolage phrases with a sliding orange highlighter on the spoken word
- unveil titles in colour blocks (Unbounded), rotating citrus seal, pill call-outs, molecule ingredient diagram,
  rooftop word slams, and the end card (sun glow, serif logo, slogan, bottle tags, contact bar)
Usage: overlay2.py OUT.mp4 | overlay2.py SHEET.jpg t1,t2,..."""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, ".")
import importlib  # noqa: E402
tl = importlib.import_module(os.environ.get("TLMOD", "tl2"))

W, H, FPS = 1080, 1920, 24
F = "../fonts/"
ORANGE, ORANGE2, INK, WHITE, CREAM = (255, 122, 26), (255, 168, 64), (16, 38, 41), (255, 255, 255), (255, 244, 228)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
RNG = np.random.default_rng(11)


def font(n, s):
    return ImageFont.truetype(F + n, s)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def eob(x, c=1.7):
    x = c01(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def text_img(s, fnt, fill, tracking=0, pad=24, stroke=0, stroke_fill=None):
    w = sum(fnt.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    asc, desc = fnt.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c in s:
        d.text((x, pad), c, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += fnt.getlength(c) + tracking
    return im


def shadow(im, blur=10, alpha=0.6, dy=4, col=(0, 0, 0)):
    sh = Image.new("RGBA", im.size, col + (0,))
    sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, dy))
    out.alpha_composite(im)
    return out


def fade(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.split()[-1].point(lambda v: int(v * max(0, a))))
    return im


def paste(dst, im, cx, cy, a=1.0, sc=1.0):
    if im is None or a <= 0.003:
        return
    if abs(sc - 1) > 0.003:
        im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.BICUBIC)
    dst.alpha_composite(fade(im, a), (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


# ======================= frame-level effects (numpy) =======================

def screen(arr, add):
    return 255 - (255 - arr) * (1 - np.clip(add / 255, 0, 1))


def bolt_points(x0, y0, x1, y1, rough, depth):
    pts = [(x0, y0), (x1, y1)]
    for _ in range(depth):
        new = [pts[0]]
        for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
            mx, my = (a + c) / 2, (b + d) / 2
            L = math.hypot(c - a, d - b)
            nx, ny = -(d - b) / (L + 1e-6), (c - a) / (L + 1e-6)
            off = RNG.normal(0, rough * L)
            new += [(mx + nx * off, my + ny * off), (c, d)]
        pts = new
    return pts


def make_bolts(seed, n=2):
    """A layer (H, W) of glowing lightning bolts with a few branches."""
    rng = np.random.default_rng(seed)
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for k in range(n):
        x0 = rng.uniform(150, 930)
        x1 = x0 + rng.uniform(-260, 260)
        main = bolt_points(x0, -20, x1, rng.uniform(1100, 1500), 0.22, 7)
        d.line(main, fill=255, width=5)
        for _ in range(4):
            j = rng.integers(len(main) // 5, len(main) * 3 // 4)
            bx, by = main[j]
            br = bolt_points(bx, by, bx + rng.uniform(-300, 300), by + rng.uniform(150, 420), 0.25, 5)
            d.line(br, fill=190, width=3)
    core = np.asarray(img).astype(np.float32)
    glow = cv2.GaussianBlur(core, (0, 0), 14) * 2.2 + cv2.GaussianBlur(core, (0, 0), 45) * 1.6
    return core, glow


BOLTS = [make_bolts(s) for s in (5, 17, 29)]


def unveil_fx(arr, t):
    for k, u in enumerate(tl.UNVEILS):
        dt = t - u
        if -0.30 <= dt < 0:                                   # the breath: everything sinks into darkness
            arr = arr * (1 - 0.92 * eio((dt + 0.30) / 0.30))
        elif 0 <= dt < 1.6:
            core, glow = BOLTS[k]
            # exposure: flash -> dip -> lights come up
            if dt < 0.08:
                expo = 0.25
            elif dt < 0.35:
                expo = 0.18 + 0.4 * eio((dt - 0.08) / 0.27)
            else:
                expo = 0.58 + 0.42 * eio((dt - 0.35) / 1.0)
            arr = arr * expo
            # double strike: bolts visible on frames 0-2 and 4-5
            fi = int(round(dt * FPS))
            strike = {0: 1.0, 1: 0.85, 2: 0.45, 4: 0.9, 5: 0.5}.get(fi, 0.0)
            if strike:
                col = np.array([215, 230, 255], np.float32)
                add = (glow[..., None] * col / 255) * strike + (core[..., None] * 1.4) * strike
                flash = np.exp(-dt / 0.06) * 210
                arr = screen(arr, add + flash)
                # RGB split on the strike
                sh = int(10 * strike)
                arr[..., 0] = np.roll(arr[..., 0], sh, 1)
                arr[..., 2] = np.roll(arr[..., 2], -sh, 1)
            # specular sweep across the product as the lights come up
            sp = (dt - 0.45) / 0.9
            if 0 < sp < 1:
                bx = -300 + (W + 600) * eio(sp)
                band = np.exp(-(((XX - bx) - (YY - 960) * 0.35) / 70) ** 2)
                arr = screen(arr, band[..., None] * np.array([255, 236, 210]) * 0.55)
    return arr


def flare_wipe(arr, s, p):
    """Sun-flare wipe: a warm anamorphic band crossing the frame (screen blend)."""
    cx = -200 + (W + 400) * p
    cy = 700 + 300 * p
    d = np.abs((XX - cx) * 0.9 + (YY - cy) * 0.45)
    band = np.exp(-(d / 160) ** 2)
    streak = np.exp(-((YY - cy) / 26) ** 2) * np.exp(-((XX - cx) / 900) ** 2)
    core = np.exp(-(((XX - cx) / 120) ** 2 + ((YY - cy) / 120) ** 2))
    add = band[..., None] * np.array([255, 170, 70]) * 0.9 + streak[..., None] * np.array([255, 220, 170]) * 0.9 + \
        core[..., None] * np.array([255, 245, 230]) * 1.2
    return screen(arr, add * s)


def whip(arr, s, direction):
    """Horizontal whip: offset + directional motion blur."""
    if s <= 0.01:
        return arr
    shift = int(direction * s * W * 0.35)
    arr = np.roll(arr, shift, 1)
    k = max(3, int(s * 90) | 1)
    return cv2.blur(arr, (k, 1))


def ripple(arr, s, phase):
    if s <= 0.01:
        return arr
    cx, cy = W / 2, H * 0.45
    r = np.hypot(XX - cx, YY - cy)
    disp = np.sin(r / 38 - phase * 9) * 14 * s
    mx = (XX + disp * (XX - cx) / (r + 1)).astype(np.float32)
    my = (YY + disp * (YY - cy) / (r + 1)).astype(np.float32)
    out = cv2.remap(arr.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out * (1 + 0.08 * s)


def transitions(arr, t):
    for k, cut in enumerate(tl.CUTS, start=1):
        kind = tl.TRANS.get(k)
        if not kind:
            continue
        dt = t - cut
        if kind == "flare" and abs(dt) < 0.32:
            arr = flare_wipe(arr, (1 - abs(dt) / 0.32) ** 1.2, c01((dt + 0.32) / 0.64))
        elif kind == "whip" and abs(dt) < 0.13:
            s = (1 - abs(dt) / 0.13) ** 1.5
            arr = whip(arr, s, -1 if dt < 0 else 1)
        elif kind == "ripple" and abs(dt) < 0.25:
            arr = ripple(arr, (1 - abs(dt) / 0.25), c01((dt + 0.25) / 0.5))
    return arr


# ======================= captions =======================
CAP_F = font("Bricolage-ExtraBold.ttf", 60)
CAP_Y = 1610
CHUNKS = tl.caption_chunks()
_cw = {}


def word_im(w, col):
    key = (w, col)
    if key not in _cw:
        _cw[key] = text_img(w, CAP_F, col, pad=0)
    return _cw[key]


def chunk_geom(ci):
    words = [w[0] for w in CHUNKS[ci]]
    sp = CAP_F.getlength(" ")
    ws = [CAP_F.getlength(w) for w in words]
    total = sum(ws) + sp * (len(words) - 1)
    sc = min(1.0, 960 / total)
    x = W / 2 - total * sc / 2
    xs = []
    for wv in ws:
        xs.append((x, x + wv * sc))
        x += (wv + sp) * sc
    return words, xs, sc


def draw_captions(img, t):
    if t >= tl.CAPTION_UNTIL:
        return
    if tl.SLAMS[0][1] - 0.05 <= t < tl.SLAMS[-1][2]:        # the word slams carry these words themselves
        return
    for ci, ch in enumerate(CHUNKS):
        s, e = ch[0][1] - 0.06, ch[-1][2]
        nxt = CHUNKS[ci + 1][0][1] - 0.08 if ci + 1 < len(CHUNKS) else e + 0.6
        e_out = min(e + 0.45, nxt)
        cut = next((c for c in tl.CUTS if e < c < e_out), None)
        if cut is not None:
            e_out = cut - 0.01
        if not (s <= t < e_out):
            continue
        words, xs, sc = chunk_geom(ci)
        a = eo((t - s) / 0.14) * (1 - c01((t - (e_out - 0.12)) / 0.12))
        dy = (1 - eo((t - s) / 0.2)) * 22
        bb = CAP_F.getbbox("Hxgy")                       # ink box of a cap + descender line
        ink_top, ink_bot = bb[1] * sc, bb[3] * sc
        h = int(ink_bot - ink_top) + 24
        # active word -> sliding highlighter
        k = 0
        for j, (_, ws_, we_) in enumerate(ch):
            if t >= ws_ - 0.05:
                k = j
        p = eo((t - (ch[k][1] - 0.05)) / 0.12)
        prev = xs[max(0, k - 1)] if k > 0 else xs[0]
        x0 = prev[0] + (xs[k][0] - prev[0]) * p
        x1 = prev[1] + (xs[k][1] - prev[1]) * p
        layer = Image.new("RGBA", (W, h + 60), (0, 0, 0, 0))
        dd = ImageDraw.Draw(layer)
        dd.rounded_rectangle((x0 - 14, 30, x1 + 14, 30 + h), radius=14, fill=ORANGE + (235,))
        txt = Image.new("RGBA", (W, h + 60), (0, 0, 0, 0))
        for j, (w, (a0, a1)) in enumerate(zip(words, xs)):
            im = word_im(w, WHITE)
            if sc < 0.999:
                im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
            txt.alpha_composite(im, (int(a0), int(30 + 12 - ink_top * 0.35)))
        layer.alpha_composite(shadow(txt, blur=8, alpha=0.75, dy=3))
        img.alpha_composite(fade(layer, a), (0, int(CAP_Y - h / 2 - 30 + dy)))


# ======================= unveil titles (colour blocks) =======================
TB = font("Unbounded-ExtraBold.ttf", 104)
TAG_F = font("Bricolage-Bold.ttf", 28)


def draw_unveil_titles(img, t):
    for lines, tag, s, e in tl.UNVEIL_TITLES:
        if not (s <= t < e):
            continue
        u = t - s
        out = c01((t - (e - 0.35)) / 0.35)
        y = 120
        for j, line in enumerate(lines):
            last = j == len(lines) - 1
            size = 104
            f = TB
            while f.getlength(line) > 820:
                size -= 4
                f = font("Unbounded-ExtraBold.ttf", size)
            tw = f.getlength(line)
            asc, desc = f.getmetrics()
            bh = asc + desc - 6
            pj = eo((u - j * 0.11) / 0.4)
            if pj <= 0:
                y += bh + 14
                continue
            bw = (tw + 56) * pj
            x0 = 64 - out * 40
            col = INK if last else ORANGE
            dd = ImageDraw.Draw(img)
            dd.rectangle((x0, y, x0 + bw, y + bh), fill=col + (int(240 * (1 - out)),))
            # text rises inside its block
            tp = eo((u - j * 0.11 - 0.12) / 0.4)
            if tp > 0:
                ti = text_img(line, f, ORANGE2 if last else WHITE, pad=0)
                clip = Image.new("RGBA", (int(bw) + 1, bh), (0, 0, 0, 0))
                clip.alpha_composite(ti, (28, int(-desc * 0.2 + (1 - tp) * bh)))
                img.alpha_composite(fade(clip, 1 - out), (int(x0), int(y)))
            y += bh + 14
        pt = eo((u - 0.5) / 0.4)
        if pt > 0:
            ti = text_img(tag, TAG_F, WHITE, tracking=5, pad=0)
            w = ti.width + 40
            pill = Image.new("RGBA", (w, 54), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle((0, 0, w - 1, 53), radius=27, fill=INK + (225,))
            pill.alpha_composite(ti, (20, (54 - ti.height) // 2 - 2))
            img.alpha_composite(fade(pill, pt * (1 - out)), (int(64 + (1 - pt) * -30 - out * 40), int(y + 8)))


# ======================= citrus seal =======================
_seal = {}


def seal_img(rot):
    key = round(rot) % 360
    if key in _seal:
        return _seal[key]
    ring_text, a, b = tl.SEAL[:3]
    R = 150
    im = Image.new("RGBA", (2 * R + 20, 2 * R + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = R + 10
    d.ellipse((c - R, c - R, c + R, c + R), fill=ORANGE + (245,))
    d.ellipse((c - R + 8, c - R + 8, c + R - 8, c + R - 8), outline=WHITE + (200,), width=2)
    d.ellipse((c - 82, c - 82, c + 82, c + 82), fill=WHITE + (255,))
    f = font("Bricolage-Bold.ttf", 25)
    txt = (ring_text + "  •  ") * 2
    n = len(txt)
    for k, ch in enumerate(txt):
        ang = math.radians(key + k * 360 / n)
        ci = text_img(ch, f, WHITE, pad=2).rotate(-math.degrees(ang) - 90, resample=Image.BICUBIC, expand=True)
        x = c + math.cos(ang) * (R - 34)
        y = c + math.sin(ang) * (R - 34)
        im.alpha_composite(ci, (int(x - ci.width / 2), int(y - ci.height / 2)))
    t1 = text_img(a, font("Unbounded-ExtraBold.ttf", 40), INK, pad=0)
    t2 = text_img(b, font("Unbounded-ExtraBold.ttf", 76), ORANGE, pad=0)
    im.alpha_composite(t1, (int(c - t1.width / 2), int(c - 62)))
    im.alpha_composite(t2, (int(c - t2.width / 2), int(c - 22)))
    _seal[key] = shadow(im, blur=16, alpha=0.45, dy=8)
    return _seal[key]


def draw_seal(img, t):
    _, _, _, s, e, (cx, cy) = tl.SEAL
    if not (s <= t < e):
        return
    u = t - s
    out = c01((t - (e - 0.25)) / 0.25)
    sc = eob(u / 0.45) * (1 - 0.3 * out)
    paste(img, seal_img(u * 40), cx, cy, 1 - out, max(0.05, sc))


# ======================= pill call-outs =======================

def icon(kind, r=30):
    im = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=ORANGE + (255,))
    c = r
    if kind == "drop":
        pts = [(c + 12 * math.sin(a) * (1 - math.cos(a)) / 1.4, c + 3 - 14 * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 40)]
        d.polygon(pts, fill=WHITE)
    elif kind == "leaf":
        ca, sa = math.cos(math.radians(-40)), math.sin(math.radians(-40))
        pts = [(-17 + 34 * q, 10 * math.sin(math.pi * q)) for q in np.linspace(0, 1, 18)] + \
              [(17 - 34 * q, -10 * math.sin(math.pi * q)) for q in np.linspace(0, 1, 18)]
        d.polygon([(c + x * ca - y * sa, c + x * sa + y * ca) for x, y in pts], fill=WHITE)
    elif kind == "spark":
        for (sx, sy, rr) in ((c - 3, c + 2, 15), (c + 11, c - 10, 6)):
            d.polygon([(sx, sy - rr), (sx + rr * 0.25, sy - rr * 0.25), (sx + rr, sy), (sx + rr * 0.25, sy + rr * 0.25),
                       (sx, sy + rr), (sx - rr * 0.25, sy + rr * 0.25), (sx - rr, sy), (sx - rr * 0.25, sy - rr * 0.25)], fill=WHITE)
    elif kind == "shield":
        d.polygon([(c, c - 15), (c + 13, c - 9), (c + 11, c + 6), (c, c + 15), (c - 11, c + 6), (c - 13, c - 9)], fill=WHITE)
        d.line([(c - 6, c), (c - 1, c + 5), (c + 7, c - 5)], fill=ORANGE, width=3)
    return im


PILL_F = font("Bricolage-ExtraBold.ttf", 36)
_pill = {}


def draw_pills(img, t):
    for kind, text, s, e, (cx, cy) in tl.PILLS:
        if not (s <= t < e):
            continue
        if text not in _pill:
            ti = text_img(text, PILL_F, WHITE, tracking=2, pad=0)
            ic = icon(kind)
            w, h = ti.width + ic.width + 70, 84
            im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=INK + (225,))
            im.alpha_composite(ic, (12, (h - ic.height) // 2))
            im.alpha_composite(ti, (ic.width + 36, (h - ti.height) // 2 - 3))
            _pill[text] = shadow(im, blur=12, alpha=0.45, dy=6)
        u = t - s
        out = c01((t - (e - 0.25)) / 0.25)
        sc = eob(u / 0.38) * (1 - 0.15 * out)
        # sun-burst ring pulse behind the pill
        rp = c01(u / 0.6)
        if 0 < rp < 1:
            d = ImageDraw.Draw(img)
            R = 60 + 260 * eo(rp)
            d.ellipse((cx - R, cy - R * 0.35, cx + R, cy + R * 0.35), outline=ORANGE2 + (int(160 * (1 - rp)),), width=3)
        paste(img, _pill[text], cx, cy, 1 - out, max(0.05, sc))


# ======================= molecule diagram =======================
MOL_F = font("Unbounded-Medium.ttf", 27)


def hexagon(cx, cy, r):
    return [(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]


def draw_molecule(img, t):
    nodes, t_end = tl.MOLECULE
    if not (nodes[0][1] <= t < t_end):
        return
    out = c01((t - (t_end - 0.3)) / 0.3)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    shown = [(lab, s, p) for lab, s, p in nodes if t >= s]
    # bonds draw from the previous node to the new one
    for (la, sa, pa), (lb, sb, pb) in zip(shown[:-1], shown[1:]):
        q = eo((t - sb) / 0.35)
        x = pa[0] + (pb[0] - pa[0]) * q
        y = pa[1] + (pb[1] - pa[1]) * q
        d.line((pa[0], pa[1], x, y), fill=WHITE + (200,), width=4)
        d.line((pa[0], pa[1] + 10, x, y + 10), fill=ORANGE + (150,), width=2)
    for lab, s, (cx, cy) in shown:
        u = t - s
        r = 46 * eob(u / 0.4)
        d.polygon(hexagon(cx, cy, r + 6), fill=WHITE + (235,))
        d.polygon(hexagon(cx, cy, r), fill=ORANGE + (255,))
        d.polygon(hexagon(cx, cy, r * 0.45), fill=WHITE + (255,))
        # orbiting electron
        ang = u * 4.0
        ex, ey = cx + math.cos(ang) * (r + 24), cy + math.sin(ang) * (r + 24) * 0.6
        d.ellipse((ex - 6, ey - 6, ex + 6, ey + 6), fill=ORANGE2 + (255,))
        pa = eo((u - 0.15) / 0.35)
        if pa > 0:
            ti = text_img(lab, MOL_F, WHITE, tracking=2, pad=0)
            w, h = ti.width + 36, ti.height + 22
            lbl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(lbl).rounded_rectangle((0, 0, w - 1, h - 1), radius=10, fill=INK + (225,))
            lbl.alpha_composite(ti, (18, 9))
            lx = cx - w / 2
            lx = min(max(lx, 30), W - 30 - w)
            layer.alpha_composite(fade(lbl, pa), (int(lx), int(cy + 70 + (1 - pa) * 16)))
    img.alpha_composite(fade(shadow(layer, blur=10, alpha=0.35, dy=4), 1 - out))


# ======================= rooftop slams =======================
SLAM_F = font("Unbounded-ExtraBold.ttf", 150)
_slam = {}


def draw_slams(img, t):
    for word, s, e in tl.SLAMS:
        if not (s - 0.02 <= t < e):
            continue
        if word not in _slam:
            f = SLAM_F
            size = 150
            while f.getlength(word) > 960:
                size -= 6
                f = font("Unbounded-ExtraBold.ttf", size)
            im = text_img(word, f, ORANGE, pad=30, stroke=4, stroke_fill=WHITE)
            _slam[word] = shadow(im, blur=18, alpha=0.5, dy=8)
        u = t - s
        out = c01((t - (e - 0.12)) / 0.12)
        sc = 1.35 - 0.35 * eo(u / 0.16)
        jx = (RNG.uniform(-6, 6) if u < 0.12 else 0)
        paste(img, _slam[word], W / 2 + jx, 360, (1 - out) * c01(u / 0.05 + 0.3), sc)


# ======================= end card =======================
LOGO = None


def build_logo():
    f = font("DMSerifDisplay.ttf", 150)
    im = text_img("PalmCare", f, WHITE, pad=30)
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    a[..., :3] = np.array(ORANGE2, np.float32) * (1 - g) + np.array((214, 92, 14), np.float32) * g
    logo = Image.fromarray(a.astype(np.uint8), "RGBA")
    r = text_img("®", font("DMSerifDisplay.ttf", 54), ORANGE, pad=0)
    out = Image.new("RGBA", (logo.width + r.width, logo.height), (0, 0, 0, 0))
    out.alpha_composite(logo, (0, 0))
    out.alpha_composite(r, (logo.width - 40, 52))
    return shadow(out, blur=22, alpha=0.55, dy=6, col=(255, 250, 240))


SL1 = text_img("Pamper your skin", font("Bricolage-Bold.ttf", 66), INK, pad=16)
SL2 = text_img("with PalmCare.", font("DMSerifDisplay-Italic.ttf", 92), (226, 96, 10), pad=16)
SUB = text_img("ADVANCED  SKIN  CARE", font("Unbounded-Light.ttf", 22), INK, tracking=8, pad=6)
PH_F = font("Bricolage-ExtraBold.ttf", 42)
AD_F = font("Bricolage-Medium.ttf", 27)
NM_F = font("Unbounded-Medium.ttf", 22)
SB_F = font("Bricolage-Medium.ttf", 24)


def phone_icon(r=26):
    im = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=ORANGE + (255,))
    d.rounded_rectangle((r - 9, r - 15, r + 9, r + 15), radius=4, outline=WHITE, width=3)
    d.line((r - 3, r + 10, r + 3, r + 10), fill=WHITE, width=2)
    return im


def pin_icon(r=26):
    im = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=ORANGE + (255,))
    d.ellipse((r - 10, r - 15, r + 10, r + 5), fill=WHITE)
    d.polygon([(r - 8, r), (r + 8, r), (r, r + 15)], fill=WHITE)
    d.ellipse((r - 4, r - 9, r + 4, r - 1), fill=ORANGE)
    return im


def draw_endcard(img, t):
    global LOGO
    s = tl.EC_START
    if t < s:
        return
    u = t - s
    if LOGO is None:
        LOGO = build_logo()
    # warm sky wash + rising sun glow behind the logo (top third is open sky in the packshot)
    a = eo((u - 0.9) / 1.2)
    if a > 0:
        sun_y = 300 - 40 * eo((u - 0.9) / 3)
        g = np.exp(-(((XX[:760] - W / 2) / 420) ** 2 + ((YY[:760] - sun_y) / 300) ** 2))
        wash = np.clip((700 - YY[:760]) / 700, 0, 1) ** 1.4 * 0.55
        layer = np.zeros((760, W, 4), np.uint8)
        layer[..., :3] = (255, 236, 205)
        layer[..., 3] = (np.clip(g * 0.85 + wash, 0, 1) * 255 * a).astype(np.uint8)
        img.alpha_composite(Image.fromarray(layer, "RGBA"))
    pl = eo((u - 1.1) / 0.6)
    paste(img, LOGO, W / 2, 190 + (1 - pl) * 24, pl)
    paste(img, SUB, W / 2, 300, eo((u - 1.4) / 0.5))
    # slogan with the voice (53.30)
    vo = 53.30
    a1 = eo((t - (vo - 0.15)) / 0.4)
    paste(img, SL1, W / 2, 392 + (1 - a1) * 18, a1)
    a2 = eo((t - (vo + 0.55)) / 0.45)
    paste(img, SL2, W / 2, 478 + (1 - a2) * 18, a2)
    # bottle name tags with fine leader lines
    d = ImageDraw.Draw(img)
    for k, (nm, sub, (ax, ay), (lx, ly)) in enumerate(tl.EC_TAGS):
        p = eo((u - 2.4 - 0.25 * k) / 0.5)
        if p <= 0:
            continue
        n1 = text_img(nm, NM_F, INK, tracking=3, pad=0)
        n2 = text_img(sub, SB_F, INK, pad=0)
        w = max(n1.width, n2.width) + 36
        hh = n1.height + n2.height + 30
        card = Image.new("RGBA", (w, hh), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle((0, 0, w - 1, hh - 1), radius=14, fill=(255, 250, 242, 235))
        ImageDraw.Draw(card).rectangle((0, 10, 5, hh - 10), fill=ORANGE + (255,))
        card.alpha_composite(n1, (18, 12))
        card.alpha_composite(n2, (18, 18 + n1.height))
        x0 = min(max(lx - w / 2, 36), W - 36 - w)
        y0 = ly - hh / 2
        ex = x0 + w / 2
        ey = y0 + hh if ay > ly else y0
        qx, qy = ex + (ax - ex) * p, ey + (ay - ey) * p
        d.line((ex, ey, qx, qy), fill=WHITE + (230,), width=3)
        d.ellipse((ax - 7, ay - 7, ax + 7, ay + 7), fill=ORANGE + (int(255 * p),), outline=WHITE + (int(255 * p),), width=2)
        img.alpha_composite(fade(shadow(card, blur=10, alpha=0.35, dy=4), p), (int(x0), int(y0 + (1 - p) * 14)))
    # contact bar
    pc = eo((u - 3.2) / 0.6)
    if pc > 0:
        x0, y0, x1, y1 = 52, 1672, W - 52, 1874
        bar = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bar)
        bd.rounded_rectangle((0, 0, bar.width - 1, bar.height - 1), radius=34, fill=INK + (232,))
        bd.rounded_rectangle((0, 0, bar.width - 1, bar.height - 1), radius=34, outline=ORANGE + (255,), width=3)
        ph = text_img("0903 055 5424   ·   0809 361 2901", PH_F, WHITE, pad=0)
        ad1 = text_img("Shop A67, Kogi Plaza, BBA Market,", AD_F, CREAM, pad=0)
        ad2 = text_img("Trade Fair Complex, Lagos", AD_F, CREAM, pad=0)
        pi1, pi2 = phone_icon(), pin_icon()
        bar.alpha_composite(pi1, (30, 22))
        bar.alpha_composite(ph, (100, 26))
        bar.alpha_composite(pi2, (30, 112))
        bar.alpha_composite(ad1, (100, 104))
        bar.alpha_composite(ad2, (100, 104 + ad1.height + 6))
        lab = text_img("ORDER NOW", font("Unbounded-ExtraBold.ttf", 22), WHITE, tracking=4, pad=0)
        pw, phh = lab.width + 40, 46
        pill = Image.new("RGBA", (pw, phh), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, pw - 1, phh - 1), radius=23, fill=ORANGE + (255,))
        pill.alpha_composite(lab, (20, (phh - lab.height) // 2 - 1))
        bar.alpha_composite(pill, (bar.width - pw - 26, 112 + 20))
        img.alpha_composite(fade(shadow(bar, blur=16, alpha=0.4, dy=8), pc), (x0, int(y0 + (1 - pc) * 40)))
    # sparkle glints on the two pumps once the lights are up
    for k, (gx, gy) in enumerate(getattr(tl, "EC_GLINTS", [])):
        gp = (u - 1.6 - 0.9 * k) % 3.0
        if gp < 0.5:
            r = 34 * math.sin(math.pi * gp / 0.5)
            d.polygon([(gx, gy - r), (gx + r * 0.16, gy - r * 0.16), (gx + r, gy), (gx + r * 0.16, gy + r * 0.16), (gx, gy + r),
                       (gx - r * 0.16, gy + r * 0.16), (gx - r, gy), (gx - r * 0.16, gy - r * 0.16)], fill=(255, 255, 255, 230))


def compose(frame, t):
    arr = frame.astype(np.float32)
    arr = transitions(arr, t)
    arr = unveil_fx(arr, t)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    draw_unveil_titles(img, t)
    draw_seal(img, t)
    draw_pills(img, t)
    draw_molecule(img, t)
    draw_slams(img, t)
    draw_captions(img, t)
    draw_endcard(img, t)
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]
    BASE = os.environ.get("BASE", f"baseR{tl.V}.mov")
    if out.endswith(".jpg") or out.endswith(".png"):
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
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", BASE, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "15", "-preset", "slow",
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
