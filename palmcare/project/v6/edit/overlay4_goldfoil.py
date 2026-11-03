"""Video 2 (redo) graphics over baseR2b.mov: calm, editorial, sunlit. Nothing shared with Video 1 or the old V2 cut:
- captions: light Jost, the spoken word in full white and the rest of the phrase softly dimmed, rising gently
- product titles: large DM Serif lines that resolve letter by letter, a fine rule and a spaced tag
- benefit call-outs: frosted-glass capsules (the picture behind is blurred and brightened), small orange dot
- ingredient constellation: fine white hexagon outlines joined by drawn lines, spaced labels
- closing words in serif italic; a slow, soft light sweep across each product reveal (no flashes)
Usage: overlay2b.py OUT.mp4 | overlay2b.py SHEET.jpg t1,t2,..."""
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import tl6 as tl

W, H, FPS = 1080, 1920, 24
F = "../../fonts/"
ORANGE, CREAM, INK, WHITE = (238, 112, 22), (255, 236, 210), (52, 34, 20), (255, 255, 255)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = "base4.mov"


def font(n, s):
    return ImageFont.truetype(F + n, s)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def text_img(s, fnt, fill, tracking=0, pad=20):
    w = sum(fnt.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    asc, desc = fnt.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c in s:
        d.text((x, pad), c, font=fnt, fill=fill)
        x += fnt.getlength(c) + tracking
    return im


def shadow(im, blur=10, alpha=0.5, dy=3):
    sh = Image.new("RGBA", im.size, (20, 12, 6, 0))
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


def paste(dst, im, cx, cy, a=1.0):
    if a > 0.003:
        dst.alpha_composite(fade(im, a), (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


# ---------------- soft light sweep over the reveals ----------------
def sweep(arr, t):
    return arr          # the product shots carry their own light sweep
    for r in tl.REVEALS:
        p = (t - (r + 0.9)) / 1.6
        if 0 <= p <= 1:
            pos = -500 + eio(p) * (W + H * 0.45 + 1000)
            d = (XX + YY * 0.45) - pos
            band = np.exp(-(d / 150) ** 2) * math.sin(math.pi * p) * 46
            arr = 255 - (255 - arr) * (1 - band[..., None] / 255 * np.array([1.0, 0.94, 0.82]))
    return arr


# ---------------- captions ----------------
CAP_F = font("Jost-Medium.ttf", 52)
CAP_Y = 1610
CHUNKS = tl.caption_chunks()
WORD_SPANS = [(s, e) for _, s, e in tl.WORDS]
_cw = {}
_g = np.clip((np.arange(H) - 1380) / 420, 0, 1) ** 1.6 * 0.42
SCRIM = Image.fromarray(np.dstack([np.full((H, W), 25, np.uint8), np.full((H, W), 16, np.uint8), np.full((H, W), 8, np.uint8),
                                   np.repeat((_g * 255).astype(np.uint8)[:, None], W, 1)]), "RGBA")


def word_im(w, a):
    key = (w, a)
    if key not in _cw:
        _cw[key] = text_img(w, CAP_F, WHITE + (a,), tracking=1, pad=0)
    return _cw[key]


def draw_captions(img, t):
    if t >= tl.CAPTION_UNTIL or any(a <= t < b for a, b in tl.PRODUCT_SPANS) or any(s - 0.1 <= t < e for s, e in WORD_SPANS) or any(s - 0.1 <= t < e for *_, s, e in tl.TITLES):
        return
    for ci, ch in enumerate(CHUNKS):
        s, e = ch[0][1] - 0.12, ch[-1][2]
        nxt = CHUNKS[ci + 1][0][1] - 0.15 if ci + 1 < len(CHUNKS) else e + 0.9
        e_out = min(e + 0.7, nxt)
        if not (s <= t < e_out):
            continue
        a = eo((t - s) / 0.3) * (1 - c01((t - (e_out - 0.25)) / 0.25))
        dy = (1 - eo((t - s) / 0.45)) * 18
        words = [w for w, _, _ in ch]
        sp = CAP_F.getlength(" ") + 2
        ims = []
        for w, ws, we in ch:
            lit = 255 if t >= ws - 0.04 else 170
            ims.append(word_im(w, lit))
        total = sum(i.width for i in ims) + sp * (len(ims) - 1)
        asc, desc = CAP_F.getmetrics()
        layer = Image.new("RGBA", (int(total) + 60, asc + desc + 40), (0, 0, 0, 0))
        x = 30
        for im in ims:
            layer.alpha_composite(im, (int(x), 20))
            x += im.width + sp
        layer = shadow(shadow(layer, blur=14, alpha=0.55, dy=0), blur=4, alpha=0.5, dy=1)
        img.alpha_composite(fade(SCRIM, a))
        paste(img, layer, W / 2, CAP_Y + dy, a)
        _ = words


# ---------------- product titles ----------------
T_F = font("DMSerifDisplay.ttf", 116)
TAG_F = font("Jost-Bold.ttf", 28)


TITLE_Y = [150, 150]
TITLE_COL = [(INK, ORANGE, 0.0), (INK, ORANGE, 0.0)]      # light-on-scrim low, dark editorial on the bright prism set


def draw_titles(img, t):
    for (l1, l2, tag, s, e), ty, (tc, gc, sha) in zip(tl.TITLES, TITLE_Y, TITLE_COL):
        if not (s <= t < e):
            continue
        out = c01((t - (e - 0.45)) / 0.45)
        layer = Image.new("RGBA", (W, 520), (0, 0, 0, 0))
        y = 40
        for j, line in enumerate((l1, l2)):
            x = W / 2 - T_F.getlength(line) / 2
            for k, ch in enumerate(line):
                q = eo((t - s - 0.12 * j - 0.035 * k) / 0.5)
                if q > 0:
                    ci = text_img(ch, T_F, tc + (int(255 * q),), pad=0)
                    layer.alpha_composite(ci, (int(x), int(y + (1 - q) * 14)))
                x += T_F.getlength(ch)
            y += 122
        rp = eo((t - s - 0.5) / 0.6)
        if rp > 0:
            ImageDraw.Draw(layer).line((W / 2 - 120 * rp, y + 34, W / 2 + 120 * rp, y + 34), fill=tc + (220,), width=2)
        ta = eo((t - s - 0.7) / 0.5)
        if ta > 0:
            ti = text_img(tag, TAG_F, gc + (255,), tracking=7, pad=0)
            layer.alpha_composite(fade(ti, ta), (int(W / 2 - ti.width / 2), int(y + 62)))
        if ty > 1000:
            img.alpha_composite(fade(SCRIM, (1 - out) * eo((t - s) / 0.5)))
        img.alpha_composite(fade(shadow(layer, blur=16, alpha=sha, dy=3), 1 - out), (0, ty))


# ---------------- frosted benefit capsules ----------------
PILL_F = font("Jost-SemiBold.ttf", 38)
_pt = {}


def draw_pills(img, t):
    for kind, text, s, e, cy in tl.PILLS:
        if not (s <= t < e):
            continue
        if text not in _pt:
            _pt[text] = text_img(text, PILL_F, INK + (255,), tracking=1, pad=0)
        ti = _pt[text]
        w, h = ti.width + 120, 92
        a = eo((t - s) / 0.4) * (1 - c01((t - (e - 0.3)) / 0.3))
        dy = (1 - eo((t - s) / 0.5)) * 20
        x0, y0 = int(W / 2 - w / 2), int(cy - h / 2 + dy)
        bg = img.crop((x0 - 30, y0 - 30, x0 + w + 30, y0 + h + 30)).filter(ImageFilter.GaussianBlur(18))
        bg = Image.blend(bg.convert("RGB"), Image.new("RGB", bg.size, (255, 250, 244)), 0.62).convert("RGBA")
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=255)
        cap = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        cap.paste(bg.crop((30, 30, 30 + w, 30 + h)), (0, 0), m)
        d = ImageDraw.Draw(cap)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, outline=WHITE + (235,), width=2)
        d.ellipse((34, h / 2 - 9, 52, h / 2 + 9), fill=ORANGE + (255,))
        cap.alpha_composite(ti, (72, int(h / 2 - ti.height / 2 - 3)))
        lay = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
        sh = Image.new("RGBA", lay.size, (60, 40, 20, 0))
        sm = Image.new("L", lay.size, 0)
        ImageDraw.Draw(sm).rounded_rectangle((30, 36, 30 + w, 36 + h), radius=h // 2, fill=70)
        sh.putalpha(sm.filter(ImageFilter.GaussianBlur(14)))
        lay.alpha_composite(sh)
        lay.alpha_composite(cap, (30, 30))
        img.alpha_composite(fade(lay, a), (x0 - 30, y0 - 30))


# ---------------- ingredient constellation ----------------
MOL_F = font("Jost-SemiBold.ttf", 29)


def hexagon(cx, cy, r, rot=0.0):
    return [(cx + r * math.cos(math.radians(60 * k + 30) + rot), cy + r * math.sin(math.radians(60 * k + 30) + rot)) for k in range(7)]


def draw_molecule(img, t):
    nodes, t_end = tl.MOLECULE
    if not (nodes[0][1] <= t < t_end):
        return
    out = c01((t - (t_end - 0.4)) / 0.4)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    shown = [(lab, s, p) for lab, s, p in nodes if t >= s]
    g = np.asarray(img.convert("L"), np.float32)
    lum = np.mean([g[max(0, cy - 60):cy + 140, max(0, cx - 160):cx + 160].mean() for _, _, (cx, cy) in shown])
    C = INK if lum > 175 else WHITE
    for (_, _, pa), (_, sb, pb) in zip(shown[:-1], shown[1:]):
        q = eio((t - sb) / 0.6)
        d.line((pa[0], pa[1], pa[0] + (pb[0] - pa[0]) * q, pa[1] + (pb[1] - pa[1]) * q), fill=C + (170,), width=2)
    for lab, s, (cx, cy) in shown:
        u = t - s
        q = eo(u / 0.6)
        r = 40 + 8 * q
        d.line(hexagon(cx, cy, r, u * 0.25), fill=C + (int(240 * q),), width=3)
        d.line(hexagon(cx, cy, r * 0.62, -u * 0.25), fill=C + (int(130 * q),), width=2)
        rr = 7 + 2 * math.sin(u * 3)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=ORANGE + (int(255 * q),))
        pa = eo((u - 0.25) / 0.5)
        if pa > 0:
            ti = text_img(lab, MOL_F, C + (255,), tracking=5, pad=0)
            lx = min(max(cx - ti.width / 2, 40), W - 40 - ti.width)
            layer.alpha_composite(fade(ti, pa), (int(lx), int(cy + 72 + (1 - pa) * 12)))
    img.alpha_composite(fade(shadow(layer, blur=12, alpha=0.6 if C == WHITE else 0.0, dy=2), 1 - out))


# ---------------- closing words ----------------
WORD_F = font("DMSerifDisplay-Italic.ttf", 132)
_wi = {}


def draw_words(img, t):
    for text, s, e in tl.WORDS:
        if not (s - 0.05 <= t < e):
            continue
        if text not in _wi:
            _wi[text] = shadow(text_img(text, WORD_F, WHITE + (255,), pad=30), blur=18, alpha=0.55, dy=3)
        a = eo((t - s + 0.05) / 0.45) * (1 - c01((t - (e - 0.3)) / 0.3))
        paste(img, _wi[text], W / 2, 1470 + (1 - eo((t - s) / 0.6)) * 16, a)


# ---------------- energy: punch-in on every cut, bright flash on each reveal ----------------
def energy(arr, t):
    for c in tl.CUTS:
        p = (t - c) / 0.4
        if 0 <= p < 1 and c < tl.EC_START - 0.01:
            z = 1 + 0.055 * (1 - eo(p))
            h, w = arr.shape[:2]
            ch, cw = int(round(h / z)), int(round(w / z))
            y0, x0 = (h - ch) // 2, (w - cw) // 2
            arr = cv2.resize(arr[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_CUBIC)
            break
    for r in list(tl.REVEALS) + [tl.EC_START]:
        p = (t - r) / 0.32
        if 0 <= p < 1:
            arr = arr + (255 - arr) * 0.55 * (1 - p) ** 2
    return arr



# =====================================================================================================
#  WOW PASS: bold kinetic captions, solid benefit badges, slam words, light leaks, sparkle bursts, glow
# =====================================================================================================
HOT = (236, 168, 36)
DARK = (28, 14, 4)
BOLD = "Montserrat-ExtraBold.ttf"


def btext(s, size, fill, stroke=0, sfill=DARK, tracking=0):
    f = font(BOLD, size)
    pad = stroke + 6
    w = sum(f.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c in s:
        d.text((x, pad), c, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
        x += f.getlength(c) + tracking
    return im


def scaled(im, sc):
    if abs(sc - 1) < 0.01:
        return im
    return im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)


def eob(x, c=1.9):
    x = c01(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


# ---------- kinetic captions ----------
CS = 70
_ck = {}


def cword(w, col, a):
    k = (w, col, a)
    if k not in _ck:
        _ck[k] = btext(w.upper(), CS, col + (a,), stroke=7, sfill=DARK + (int(a * 0.85),))
    return _ck[k]


def draw_captions(img, t):
    return                      # no running captions: key-word pop-ups only
    if t >= tl.CAPTION_UNTIL or any(a <= t < b for a, b in tl.PRODUCT_SPANS) or any(s - 0.1 <= t < e for s, e in WORD_SPANS) \
            or any(s - 0.1 <= t < e for *_, s, e in tl.TITLES):
        return
    for ci, ch in enumerate(CHUNKS):
        s, e = ch[0][1] - 0.08, ch[-1][2]
        nxt = CHUNKS[ci + 1][0][1] - 0.1 if ci + 1 < len(CHUNKS) else e + 0.8
        e_out = min(e + 0.6, nxt)
        if not (s <= t < e_out):
            continue
        a = c01((t - s) / 0.08) * (1 - c01((t - (e_out - 0.15)) / 0.15))
        pop = 0.82 + 0.18 * eob((t - s) / 0.28)
        # active word = last word whose start has passed
        act = max([j for j, (_, ws, _) in enumerate(ch) if t >= ws - 0.03] or [0])
        ims, scs = [], []
        for j, (w, ws, we) in enumerate(ch):
            if j == act:
                im = cword(w, HOT, 255); sc = 1 + 0.22 * (1 - eo((t - (ws - 0.03)) / 0.18))
            elif t >= ws - 0.03:
                im = cword(w, WHITE, 255); sc = 1
            else:
                im = cword(w, WHITE, 120); sc = 1
            ims.append(im); scs.append(sc)
        sp = 18
        # wrap into lines no wider than 980
        lines, cur, cw = [], [], 0
        for im, sc in zip(ims, scs):
            if cur and cw + sp + im.width > 980:
                lines.append(cur); cur, cw = [], 0
            cur.append((im, sc)); cw += (sp if len(cur) > 1 else 0) + im.width
        lines.append(cur)
        lh = ims[0].height - 14
        y0 = 1590 - lh * (len(lines) - 1) / 2
        g = int(255 * 0.55 * a)
        img.alpha_composite(fade(SCRIM, a))
        for li, ln in enumerate(lines):
            tw = sum(im.width for im, _ in ln) + sp * (len(ln) - 1)
            x = W / 2 - tw * pop / 2
            for im, sc in ln:
                cx = x + im.width * pop / 2
                paste(img, scaled(im, sc * pop), cx, y0 + li * lh * pop, a)
                x += (im.width + sp) * pop
        _ = g


# ---------- solid benefit badges ----------
_bd = {}


def badge(text):
    if text not in _bd:
        ti = btext(text.upper(), 40, WHITE + (255,), tracking=2)
        w, h = ti.width + 110, 104
        im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
        sh = Image.new("L", im.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle((30, 40, 30 + w, 40 + h), radius=h // 2, fill=120)
        shl = Image.new("RGBA", im.size, (70, 40, 0, 0)); shl.putalpha(sh.filter(ImageFilter.GaussianBlur(14)))
        im.alpha_composite(shl)
        grad = np.zeros((h, w, 4), np.uint8)
        tcol = np.linspace(0, 1, w)[None, :, None]
        c0, c1 = np.array([248, 200, 84]), np.array([186, 120, 18])
        grad[..., :3] = (c0 * (1 - tcol) + c1 * tcol).astype(np.uint8)
        m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=255)
        grad[..., 3] = np.asarray(m)
        cap = Image.fromarray(grad, "RGBA")
        d = ImageDraw.Draw(cap)
        d.rounded_rectangle((3, 3, w - 4, h // 2), radius=h // 3, fill=(255, 255, 255, 38))     # gloss
        cx, cy, r = 52, h // 2, 15                                                                # white sparkle icon
        d.polygon([(cx, cy - r), (cx + r * 0.3, cy - r * 0.3), (cx + r, cy), (cx + r * 0.3, cy + r * 0.3), (cx, cy + r),
                   (cx - r * 0.3, cy + r * 0.3), (cx - r, cy), (cx - r * 0.3, cy - r * 0.3)], fill=WHITE + (255,))
        cap.alpha_composite(ti, (82, int(h / 2 - ti.height / 2)))
        im.alpha_composite(cap, (30, 30))
        _bd[text] = im
    return _bd[text]


def draw_pills(img, t):
    for k, (kind, text, s, e, cy) in enumerate(tl.PILLS):
        if not (s <= t < e):
            continue
        b = badge(text)
        sc = eob((t - s) / 0.35, 2.2) * (1 - 0.2 * c01((t - (e - 0.2)) / 0.2))
        a = c01((t - s) / 0.08) * (1 - c01((t - (e - 0.2)) / 0.2))
        # shine sweep across the badge
        q = (t - s - 0.3) / 0.5
        bb = b
        if 0 < q < 1:
            bb = b.copy(); arr = np.asarray(bb).astype(np.float32)
            xx = np.arange(arr.shape[1])[None, :]; yy = np.arange(arr.shape[0])[:, None]
            band = np.exp(-(((xx + yy * 0.5) - q * (arr.shape[1] + 200) + 100) / 30) ** 2) * 0.6
            arr[..., :3] = arr[..., :3] + (255 - arr[..., :3]) * band[..., None] * (arr[..., 3:4] > 200)
            bb = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
        paste(img, scaled(bb, max(0.05, sc)), W / 2, cy - 30, a)


# ---------- product titles: bold, letter drop ----------
TB_SIZE = 104


def draw_titles(img, t):
    for (l1, l2, tag, s, e) in tl.TITLES:
        if not (s <= t < e):
            continue
        out = c01((t - (e - 0.3)) / 0.3)
        layer = Image.new("RGBA", (W, 460), (0, 0, 0, 0))
        y = 20
        for j, line in enumerate((l1.upper(), l2.upper())):
            f = font(BOLD, TB_SIZE)
            tw = sum(f.getlength(c) for c in line) + 4 * (len(line) - 1)
            sc0 = min(1.0, 1000 / tw)
            fs = int(TB_SIZE * sc0)
            f = font(BOLD, fs)
            tw = sum(f.getlength(c) for c in line) + 4 * (len(line) - 1)
            x = W / 2 - tw / 2
            for k, ch in enumerate(line):
                q = (t - s - 0.1 * j - 0.03 * k) / 0.35
                if q > 0:
                    ci = btext(ch, fs, (DARK if j == 0 else HOT) + (255,), stroke=0)
                    sc = eob(q, 2.4)
                    layer.alpha_composite(fade(scaled(ci, max(0.05, sc)), c01(q * 3)),
                                          (int(x + f.getlength(ch) / 2 - ci.width * sc / 2), int(y + fs * 0.6 - ci.height * sc / 2 + 20)))
                x += f.getlength(ch) + 4
            y += int(fs * 1.12)
        ta = eob((t - s - 0.6) / 0.35)
        if ta > 0:
            ti = btext(tag, 30, WHITE + (255,), tracking=6)
            pw, ph = ti.width + 50, ti.height + 16
            pl = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            ImageDraw.Draw(pl).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=ph // 2, fill=DARK + (235,))
            pl.alpha_composite(ti, (25, 8))
            pl = scaled(pl, max(0.05, ta))
            layer.alpha_composite(pl, (int(W / 2 - pl.width / 2), int(y + 30)))
        lay = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        glw = Image.new("RGBA", layer.size, (255, 248, 236, 0))
        glw.putalpha(layer.split()[-1].filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.85)))
        lay.alpha_composite(glw); lay.alpha_composite(layer)
        img.alpha_composite(fade(lay, 1 - out), (0, 120))


# ---------- ingredient labels: bold dark tags ----------
def draw_molecule(img, t):
    nodes, t_end = tl.MOLECULE
    if not (nodes[0][1] <= t < t_end):
        return
    out = c01((t - (t_end - 0.3)) / 0.3)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    shown = [(lab, s, p) for lab, s, p in nodes if t >= s]
    for (_, _, pa), (_, sb, pb) in zip(shown[:-1], shown[1:]):
        q = eio((t - sb) / 0.4)
        d.line((pa[0], pa[1], pa[0] + (pb[0] - pa[0]) * q, pa[1] + (pb[1] - pa[1]) * q), fill=HOT + (230,), width=5)
    for lab, s, (cx, cy) in shown:
        u = t - s
        q = eob(u / 0.4, 2.2)
        r = 50 * q
        d.polygon(hexagon(cx, cy, r + 7, u * 0.4)[:6], fill=WHITE + (245,))
        d.polygon(hexagon(cx, cy, r, u * 0.4)[:6], fill=HOT + (255,))
        d.polygon(hexagon(cx, cy, r * 0.42, -u * 0.4)[:6], fill=WHITE + (255,))
        if u > 0.12:
            ti = btext(lab, 34, WHITE + (255,), tracking=3)
            pw, ph = ti.width + 40, ti.height + 14
            pl = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            ImageDraw.Draw(pl).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=14, fill=DARK + (235,))
            pl.alpha_composite(ti, (20, 7))
            pl = scaled(pl, max(0.05, eob((u - 0.12) / 0.3, 2.0)))
            lx = min(max(cx - pl.width / 2, 30), W - 30 - pl.width)
            layer.alpha_composite(pl, (int(lx), int(cy + 70)))
    sh = Image.new("RGBA", (W, H), (40, 20, 5, 0)); sh.putalpha(layer.split()[-1].filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.45)))
    sh.alpha_composite(layer)
    img.alpha_composite(fade(sh, 1 - out))


# ---------- closing words: slam ----------
def draw_words(img, t):
    for text, s, e in tl.WORDS:
        if not (s - 0.03 <= t < e):
            continue
        k = ("W", text)
        if k not in _wi:
            core = btext(text.upper(), 150 if len(text) < 10 else 112, WHITE + (255,), stroke=8, sfill=DARK + (200,), tracking=4)
            big = Image.new("RGBA", (core.width + 120, core.height + 120), (0, 0, 0, 0))
            gl = Image.new("RGBA", big.size, HOT + (0,))
            m = Image.new("L", big.size, 0); m.paste(core.split()[-1], (60, 60))
            gl.putalpha(m.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.9)))
            big.alpha_composite(gl); big.alpha_composite(core, (60, 60))
            _wi[k] = big
        u = t - s
        sc = 1.7 - 0.7 * eo(u / 0.18) + 0.04 * u
        a = c01(u / 0.06 + 0.5) * (1 - c01((t - (e - 0.15)) / 0.15))
        sc = min(sc, 1060 / _wi[k].width)
        paste(img, scaled(_wi[k], sc), W / 2, 1450, a)


# ---------- frame FX: glow grade, light leaks on cuts, sparkle bursts on reveals ----------
RNG = np.random.default_rng(9)
BURSTS = [(tl.EC_START, 540, 1050)]          # the unveils carry their own spark burst; none over her face
PARTS = {b[0]: [(RNG.uniform(0, 2 * math.pi), RNG.uniform(380, 1100), RNG.uniform(5, 14), RNG.uniform(0.6, 1.3)) for _ in range(70)]
         for b in BURSTS}
LEAK_COL = [np.array(c, np.float32) for c in ((255, 150, 60), (255, 110, 120), (255, 200, 90))]


def fx(arr, t):
    # glow grade (skip the built product reveals so the bottle colours stay true)
    if not any(a <= t < b for a, b in tl.PRODUCT_SPANS) and t < tl.EC_START:
        small = cv2.resize(arr, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        hi = np.clip(small - 170, 0, None) * 1.6
        bloom = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 10), (W, H), interpolation=cv2.INTER_LINEAR)
        arr = 255 - (255 - arr) * (1 - np.clip(bloom, 0, 255) / 255 * 0.55)
        m = arr.mean(2, keepdims=True)
        arr = np.clip(m + (arr - m) * 1.12, 0, 255)                               # vibrance
    # light leak at every cut
    for k, c in enumerate(tl.CUTS):
        p = (t - c + 0.08) / 0.6
        if 0 <= p < 1 and c < tl.EC_START + 0.01:
            side = 1 if k % 2 else -1
            cx = W / 2 + side * (W * 0.75 - p * W * 0.5)
            cy = H * (0.3 + 0.4 * ((k * 37) % 10) / 10)
            sm_x = np.arange(0, W, 4, dtype=np.float32); sm_y = np.arange(0, H, 4, dtype=np.float32)
            d = ((sm_x[None, :] - cx) / (W * 0.55)) ** 2 + ((sm_y[:, None] - cy) / (H * 0.45)) ** 2
            g = np.exp(-d * 2.2) * math.sin(math.pi * p) * 0.75
            g = cv2.resize(g.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
            col = LEAK_COL[k % 3] / 255
            arr = 255 - (255 - arr) * (1 - g[..., None] * col)
    return arr


def sparkles(img, t):
    d = None
    for t0, cx, cy in BURSTS:
        u = t - t0
        if not (0 <= u < 1.4):
            continue
        d = d or ImageDraw.Draw(img)
        for ang, spd, sz, life in PARTS[t0]:
            if u > life:
                continue
            q = u / life
            r = spd * eo(u / 0.9) * 0.9
            flat = 0.22 if cy > 1300 else 1.15                 # word bursts: a flat band beside the words, never over her face
            if cy > 1300:
                r = min(r, 560)
            x, y = cx + math.cos(ang) * r, cy + math.sin(ang) * r * flat + (120 * u * u if cy <= 1300 else 0)
            s_ = sz * (1 - q * 0.6)
            al = int(255 * (1 - q) ** 1.3)
            col = (255, 236, 190, al) if int(ang * 10) % 3 else (255, 255, 255, al)
            d.polygon([(x, y - s_ * 2.2), (x + s_ * 0.35, y - s_ * 0.35), (x + s_ * 2.2, y), (x + s_ * 0.35, y + s_ * 0.35),
                       (x, y + s_ * 2.2), (x - s_ * 0.35, y + s_ * 0.35), (x - s_ * 2.2, y), (x - s_ * 0.35, y - s_ * 0.35)], fill=col)



# ---------- UV SHIELD: a shimmering golden dome forms around her; sunbeams glint off it ----------
SH_RNG = np.random.default_rng(21)
SH_GLINTS = [(SH_RNG.uniform(-1.15, -0.15) * math.pi, SH_RNG.uniform(0, 6.28)) for _ in range(9)]


def shield(arr, t):
    s0, s1 = tl.SHIELD
    if not (s0 - 0.05 <= t < s1):
        return arr
    u = t - s0
    grow = eo(u / 0.55)
    fade_out = 1 - c01((t - (s1 - 0.3)) / 0.3)
    cx, cy, rx, ry = W / 2, H * 0.56, 470 * (0.6 + 0.4 * grow), 900 * (0.6 + 0.4 * grow)
    sx, sy = np.arange(0, W, 2, dtype=np.float32), np.arange(0, H, 2, dtype=np.float32)
    X, Y = np.meshgrid(sx, sy)
    rr = np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2)
    ang = np.arctan2(Y - cy, X - cx)
    rim = np.exp(-((rr - 1) / 0.018) ** 2)                                         # thin bright rim
    inner = np.clip(1 - np.abs(rr - 0.93) / 0.12, 0, 1) ** 2 * 0.35                 # soft inner glow near the rim
    shimmer = 0.6 + 0.4 * np.sin(ang * 9 + u * 5) * np.sin(ang * 4 - u * 3)       # light travelling round the dome
    hexes = (np.abs(np.sin((X * 0.035) + (Y * 0.02))) * np.abs(np.sin((X * -0.035) + (Y * 0.02)))) > 0.92
    hexgrid = hexes * np.clip(1 - np.abs(rr - 0.9) / 0.15, 0, 1) * 0.25
    ripple = np.exp(-((rr - eo(u / 0.7) * 1.1) / 0.03) ** 2) * (1 - c01(u / 0.7)) * 0.9 # formation ripple
    a = (rim * 0.75 + inner + hexgrid) * shimmer * grow + ripple
    a = cv2.resize(a.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR) * fade_out
    col = np.array([255, 214, 120], np.float32) / 255
    arr = 255 - (255 - arr) * (1 - np.clip(a, 0, 1)[..., None] * col)
    return arr


def shield_glints(img, t):
    s0, s1 = tl.SHIELD
    if not (s0 + 0.3 <= t < s1 - 0.2):
        return
    u = t - s0
    d = ImageDraw.Draw(img)
    cx, cy, rx, ry = W / 2, H * 0.56, 470, 900
    for k, (ang, ph) in enumerate(SH_GLINTS):
        q = (u * 1.3 + ph / 6.28) % 1.0                       # each glint pulses once per ~0.8 s
        if q > 0.45:
            continue
        al = math.sin(math.pi * q / 0.45)
        x, y = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        # incoming sunbeam from the top-right, stopped at the shield
        sxx, syy = x + 260, y - 520
        d.line((sxx, syy, x, y), fill=(255, 236, 170, int(120 * al)), width=3)
        s_ = 22 * al
        d.polygon([(x, y - s_ * 2.2), (x + s_ * 0.3, y - s_ * 0.3), (x + s_ * 2.2, y), (x + s_ * 0.3, y + s_ * 0.3),
                   (x, y + s_ * 2.2), (x - s_ * 0.3, y + s_ * 0.3), (x - s_ * 2.2, y), (x - s_ * 0.3, y - s_ * 0.3)], fill=(255, 250, 225, int(255 * al)))



# =====================================================================================================
#  GOLD-FOIL PASS (V3 correction): elegant metallic serif lettering that shimmers in, replacing the bold
#  sans badges and slams. Foil = vertical metal gradient + bevel + travelling specular shine.
# =====================================================================================================
FOIL_STOPS = [(0.0, (255, 246, 220)), (0.30, (246, 210, 128)), (0.52, (184, 122, 28)), (0.66, (238, 196, 112)),
              (0.82, (255, 236, 176)), (1.0, (150, 96, 20))]
_foil = {}


def _grad(h):
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3), np.float32)
    for (a, ca), (b, cb) in zip(FOIL_STOPS[:-1], FOIL_STOPS[1:]):
        m = (ys >= a) & (ys <= b)
        q = ((ys[m] - a) / (b - a))[:, None]
        out[m] = np.array(ca) * (1 - q) + np.array(cb) * q
    return out


def foil(text, fname, size, tracking=0, shadow_a=0.9):
    """Gold-foil text as float RGBA arrays (colour, alpha) with a soft dark halo for legibility on bright shots."""
    k = (text, fname, size, tracking)
    if k in _foil:
        return _foil[k]
    f = font(fname, size)
    pad = int(size * 0.45)
    w = int(sum(f.getlength(c) for c in text) + tracking * max(0, len(text) - 1)) + 2 * pad
    asc, desc = f.getmetrics()
    h = asc + desc + 2 * pad
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    x = pad
    for c in text:
        d.text((x, pad), c, font=f, fill=255)
        x += f.getlength(c) + tracking
    A = np.asarray(m, np.float32) / 255
    rows = np.nonzero(A.max(1) > 0.1)[0]
    g = np.zeros((h, 3), np.float32)
    g[rows[0]:rows[-1] + 1] = _grad(rows[-1] - rows[0] + 1)
    col = np.repeat(g[:, None, :], w, 1)
    bl = cv2.GaussianBlur(A, (0, 0), max(1.0, size / 60))
    gy = np.gradient(bl, axis=0)
    col = col + (gy < 0)[..., None] * (-gy)[..., None] * 900 * np.array([1.0, 0.97, 0.9]) - (gy > 0)[..., None] * gy[..., None] * 520
    edge = np.clip(cv2.dilate(A, np.ones((3, 3), np.uint8)) - A, 0, 1)                     # fine bronze keyline
    halo = np.clip(cv2.GaussianBlur(cv2.dilate(A, np.ones((5, 5), np.uint8)), (0, 0), size / 8) * 1.6, 0, 1) * shadow_a
    out_a = np.clip(A + edge + halo * (1 - A), 0, 1)
    rgb = np.where(A[..., None] > 0, col, np.array(DARK, np.float32))
    rgb = rgb * (1 - edge[..., None] * (1 - A[..., None])) + np.array([110, 66, 10], np.float32) * edge[..., None] * (1 - A[..., None])
    rgb = np.where((A + edge)[..., None] > 0.02, rgb, np.array([30, 16, 4], np.float32))
    _foil[k] = (np.clip(rgb, 0, 255), out_a, A)
    return _foil[k]


def put_foil(img, fo, cx, cy, t0, t, alpha=1.0, wipe=0.55, scale=1.0, shine_every=2.2):
    """Shimmer reveal: a soft left-to-right wipe, a bright specular band that follows it and re-crosses every few s."""
    rgb, a, core = fo
    h, w = a.shape
    u = t - t0
    p = c01(u / wipe)
    xs = np.arange(w, dtype=np.float32)[None, :]
    ys = np.arange(h, dtype=np.float32)[:, None]
    reveal = np.clip((p * (w + 160) - xs) / 160, 0, 1)
    al = a * reveal * alpha
    sp = (u % shine_every) / 0.7 if u > wipe else u / wipe
    band = np.exp(-(((xs + ys * 0.35) - (sp * (w + 300) - 150)) / (w * 0.05 + 18)) ** 2) * (sp <= 1)
    col = rgb + (255 - rgb) * (band * core * 0.85)[..., None]
    arr = np.dstack([col, al * 255]).astype(np.uint8)
    im = Image.fromarray(arr, "RGBA")
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BICUBIC)
    img.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))
    return im.width


def hairline(img, cx, y, half, a, col=(246, 214, 140)):
    if half < 1 or a <= 0:
        return
    lay = Image.new("RGBA", (int(2 * half) + 40, 9), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k in range(int(2 * half)):
        e = 1 - abs(k - half) / half
        d.point((20 + k, 4), fill=col + (int(255 * a * e ** 0.6),))
    img.alpha_composite(lay, (int(cx - half - 20), int(y - 4)))


def glint(d, x, y, s_, al):
    d.polygon([(x, y - s_ * 2.2), (x + s_ * 0.3, y - s_ * 0.3), (x + s_ * 2.2, y), (x + s_ * 0.3, y + s_ * 0.3),
               (x, y + s_ * 2.2), (x - s_ * 0.3, y + s_ * 0.3), (x - s_ * 2.2, y), (x - s_ * 0.3, y - s_ * 0.3)], fill=(255, 248, 222, int(255 * al)))


SERIF, SERIF_I, CAPS = "Playfair-Medium.ttf", "Playfair-Italic.ttf", "Jost-Medium.ttf"


# ---------- key-word pop-ups: gold italic line with hairlines ----------
def draw_pills(img, t):
    for kind, text, s, e, cy in tl.PILLS:
        if not (s <= t < e):
            continue
        a = c01((t - s) / 0.15) * (1 - c01((t - (e - 0.25)) / 0.25))
        fo = foil(text, SERIF_I, 76 if len(text) < 22 else 66)
        dy = (1 - eo((t - s) / 0.5)) * 14
        wv = put_foil(img, fo, W / 2, cy + dy, s, t, a, wipe=0.5)
        half = (wv * 0.42) * eo((t - s - 0.15) / 0.5)
        hairline(img, W / 2, cy + dy - fo[1].shape[0] * 0.30, half, a)
        hairline(img, W / 2, cy + dy + fo[1].shape[0] * 0.33, half, a)
        q = (t - s - 0.35) / 0.6
        if 0 < q < 1:
            glint(ImageDraw.Draw(img), W / 2 + wv * 0.40, cy + dy - fo[1].shape[0] * 0.18, 13 * math.sin(math.pi * q), math.sin(math.pi * q))


# ---------- product titles: italic kicker + foil serif name + spaced tag ----------
def draw_titles(img, t):
    for (l1, l2, tag, s, e) in tl.TITLES:
        if not (s <= t < e):
            continue
        a = 1 - c01((t - (e - 0.35)) / 0.35)
        y = 250
        put_foil(img, foil(l1, SERIF_I, 74), W / 2, y, s, t, a * c01((t - s) / 0.2), wipe=0.45)
        fo = foil(l2, "DMSerifDisplay.ttf" if any(ch.isdigit() for ch in l2) else SERIF, 128 if len(l2) < 12 else 116, tracking=2)   # lining figures for "N10"
        wv = put_foil(img, fo, W / 2, y + 118, s + 0.18, t, a * c01((t - s - 0.18) / 0.2), wipe=0.7, scale=1.04 - 0.04 * eo((t - s - 0.18) / 0.8))
        hairline(img, W / 2, y + 205, 170 * eo((t - s - 0.6) / 0.6), a)
        ta = eo((t - s - 0.8) / 0.5) * a
        if ta > 0:
            lum = np.asarray(img.convert("L").crop((140, y + 225, 940, y + 275)), np.float32).mean()
            if lum > 150:            # light set: deep bronze letters read cleanly
                ti = text_img(tag, font("Jost-SemiBold.ttf", 27), (112, 72, 12, 255), tracking=8, pad=14)
            else:
                ti = shadow(shadow(text_img(tag, font(CAPS, 27), (255, 240, 212, 255), tracking=8, pad=14), blur=12, alpha=0.9, dy=0), blur=4, alpha=0.9, dy=1)
            paste(img, ti, W / 2, y + 250, ta)


# ---------- ingredients at work: a stacked foil list, each active with its job ----------
CARD_X, CARD_Y0, CARD_DY = 80, 1330, 145


def draw_molecule(img, t):
    hs, he = tl.HEALTHY[1], tl.CARDS[-1][3] if tl.CARDS else tl.HEALTHY[2]
    if not (hs <= t < he):
        return
    out = 1 - c01((t - (he - 0.35)) / 0.35)
    # soft dark scrim on the left so the gold reads over the bright pour / skin
    sc = np.clip(1 - XX[::4, ::4] / (W * 0.95), 0, 1) ** 1.4 * np.clip((YY[::4, ::4] - 980) / 260, 0, 1) * np.clip((1880 - YY[::4, ::4]) / 160, 0, 1)
    sc = cv2.resize(sc.astype(np.float32), (W, H)) * 0.5 * out * eo((t - hs) / 0.5)
    img.alpha_composite(Image.fromarray(np.dstack([np.full((H, W, 3), (24, 12, 3), np.uint8), (sc * 255).astype(np.uint8)]), "RGBA"))
    fo = foil(tl.HEALTHY[0], SERIF_I, 70)
    put_foil(img, fo, CARD_X + fo[1].shape[1] / 2 - 30, CARD_Y0 - 120, hs, t, out, wipe=0.6)
    d = ImageDraw.Draw(img)
    for k, (name, job, s, e) in enumerate(tl.CARDS):
        if t < s:
            continue
        u = t - s
        y = CARD_Y0 + k * CARD_DY
        dx = (1 - eo(u / 0.5)) * -40
        r = 9 * eob(u / 0.4, 2.0)
        d.ellipse((CARD_X + dx - r, y - r, CARD_X + dx + r, y + r), fill=(250, 214, 130, int(255 * out)))
        if k:
            q = eio(u / 0.4)
            d.line((CARD_X, y - CARD_DY + 14, CARD_X, y - CARD_DY + 14 + (CARD_DY - 28) * q), fill=(246, 210, 128, int(200 * out)), width=2)
        ti = text_img(name, font(CAPS, 25), (255, 240, 212, 255), tracking=4, pad=12)
        ti = shadow(ti, blur=8, alpha=0.75, dy=1)
        img.alpha_composite(fade(ti, c01(u / 0.3) * out), (int(CARD_X + 34 + dx), int(y - 46)))
        jo = foil(job, SERIF_I, 50 if len(job) > 26 else 56)
        put_foil(img, jo, CARD_X + 34 + jo[1].shape[1] / 2 - 26 + dx, y + 30, s + 0.12, t, out, wipe=0.55)


# ---------- big words: foil serif, gentle scale-settle and shine (no slam) ----------
def draw_words(img, t):
    for text, s, e in tl.WORDS:
        if not (s - 0.03 <= t < e):
            continue
        u = t - s
        a = c01(u / 0.12 + 0.3) * (1 - c01((t - (e - 0.2)) / 0.2))
        fo = foil(text, SERIF_I if " " in text else SERIF, 150 if len(text) < 10 else 120, tracking=3)
        sc = 1.10 - 0.10 * eo(u / 0.5)
        put_foil(img, fo, W / 2, 1450, s, t, a, wipe=0.35, scale=min(sc, 1000 / fo[1].shape[1]))



# ---------- label call-outs on the unveils: dot on the bottle edge, a gold line drawing out, two lines of spaced caps ----------
import json as _json
_BOXES = [_json.load(open(p))["boxes"] for p in tl.PS_JSON]
_CUTS = ["../assets/tropical_cut.png", "../assets/dermalight_cut.png"]
_EDGE = {}


def _edge(pi, f):
    """Left / right body edge (as a fraction of the cut's width) at a fraction f down the bottle."""
    if (pi, f) not in _EDGE:
        im = Image.open(_CUTS[pi]).convert("RGBA")
        im = im.crop(im.getbbox())
        a = np.asarray(im)[..., 3]
        row = a[int(f * (a.shape[0] - 1))]
        xs = np.nonzero(row > 128)[0]
        _EDGE[(pi, f)] = (xs[0] / a.shape[1], xs[-1] / a.shape[1])
    return _EDGE[(pi, f)]


CO_F1, CO_F2 = font("Jost-SemiBold.ttf", 23), font("Jost-Medium.ttf", 18)


def draw_callouts(img, t):
    for pi, (s0, s1) in enumerate(tl.PRODUCT_SPANS):
        if not (s0 <= t < s1):
            continue
        fi = min(len(_BOXES[pi]) - 1, int(round((t - s0) * FPS)))
        x0, y0, w, h, _ = _BOXES[pi][fi]
        out = 1 - c01((t - (s1 - 0.3)) / 0.3)
        d = ImageDraw.Draw(img)
        for (p, f, side, l1, l2, off) in tl.CALLOUTS:
            if p != pi:
                continue
            u = t - s0 - off
            if u <= 0:
                continue
            el, er = _edge(pi, f)
            ex = x0 + w * (el if side < 0 else er) + side * 4
            ey = y0 + h * f
            end = 46 if side < 0 else W - 46
            q = eio(u / 0.4)
            xe = ex + (end - ex) * q
            r = 7 * eob(u / 0.3, 2.0)
            col = (250, 218, 140)
            d.line((ex, ey, xe, ey), fill=col + (int(235 * out),), width=2)
            d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=col + (int(255 * out),))
            d.ellipse((ex - r - 5, ey - r - 5, ex + r + 5, ey + r + 5), outline=col + (int(120 * out),), width=2)
            ta = c01((u - 0.3) / 0.35) * out
            if ta > 0:
                for k, (txt, fnt, tc) in enumerate(((l1, CO_F1, (255, 240, 210)), (l2, CO_F2, (246, 214, 140)))):
                    ti = shadow(shadow(text_img(txt, fnt, tc + (255,), tracking=3, pad=10), blur=10, alpha=0.95, dy=0), blur=3, alpha=0.9, dy=1)
                    ty = ey - 18 - (2 - k) * 30
                    tx = min(26, ex - 30 - ti.width) if side < 0 else max(W - 26 - ti.width, ex + 30)
                    img.alpha_composite(fade(ti, ta), (int(tx + side * -12 * (1 - ta)), int(ty)))


def compose(frame, t):
    arr = shield(fx(sweep(energy(frame.astype(np.float32), t), t), t), t)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    sparkles(img, t)
    shield_glints(img, t)
    draw_titles(img, t)
    draw_pills(img, t)
    draw_molecule(img, t)
    draw_callouts(img, t)
    draw_words(img, t)
    draw_captions(img, t)
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
