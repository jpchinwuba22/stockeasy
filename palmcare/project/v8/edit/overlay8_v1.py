"""Video 5 graphics over base8.mov: the "sun badge" system (new for GlowShield; nothing shared with Video 4's kinetic type).
Unbounded headlines with a sunlit gradient, frosted info chips that pop only on key spoken words, an animated skin
diagram that explains UVB vs UVA, a 98 % counter, SPF 50+ / PA++++ shield badges, a shield checklist, the GlowShield
pack floating beside her while she applies it, and warm sun-flare flashes on the big cuts.
Usage: overlay8.py OUT.mp4 | overlay8.py SHEET.jpg t1,t2,..."""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import tl8 as tl

W, H, FPS = 1080, 1920, 24
BASE = "base8.mov"
FD = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/fonts/"
PACK = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v5/assets/glowshield_box_flat.png"
HEAD, CHIP, CHIP_M, SERIF_I = "Unbounded-ExtraBold.ttf", "Bricolage-ExtraBold.ttf", "Bricolage-Medium.ttf", "Cormorant-Italic.ttf"
INK, AMBER, GOLD, CREAM, WHITE = (46, 26, 12), (232, 140, 30), (250, 196, 92), (255, 246, 232), (255, 255, 255)
UVB_C, UVA_C = (255, 168, 40), (176, 120, 255)
_fc = {}


def font(n, s):
    if (n, s) not in _fc:
        _fc[(n, s)] = ImageFont.truetype(FD + n, s)
    return _fc[(n, s)]


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


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


def sun_fill(im, top=(255, 252, 240), bot=(255, 176, 64)):
    """Recolour an RGBA text image with a vertical sunlit gradient (white-gold top to amber)."""
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None] ** 1.3
    a[..., :3] = np.array(top, np.float32) * (1 - g) + np.array(bot, np.float32) * g
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def shadowed(im, blur=10, alpha=0.55, dy=4, col=(20, 10, 4)):
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
    """Opacity of an element that lives from s to e."""
    if t < s or t >= e:
        return 0.0
    return c01((t - s) / fin) * (1 - c01((t - (e - fout)) / fout))


def pop(dst, im, cx, cy, t, s, e, dur=0.45):
    a = life(t, s, e)
    if a > 0:
        paste(dst, im, cx, cy, a, 0.72 + 0.28 * eob((t - s) / dur))


def scrim(dst, y0, y1, strength, t_a):
    """A soft dark gradient band so light text reads on bright, sunlit frames."""
    if t_a <= 0:
        return
    h = y1 - y0
    m = np.zeros((h, W), np.float32)
    yy = np.linspace(0, 1, h)[:, None]
    m[:] = (np.sin(np.pi * yy) ** 0.8) * strength * t_a
    band = np.zeros((h, W, 4), np.uint8)
    band[..., :3] = (24, 12, 4)
    band[..., 3] = (m * 255).astype(np.uint8)
    dst.alpha_composite(Image.fromarray(band, "RGBA"), (0, y0))


def sun_icon(d, cx, cy, r, col):
    d.ellipse((cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45), fill=col)
    for k in range(8):
        a = k * math.pi / 4
        d.line((cx + math.cos(a) * r * 0.65, cy + math.sin(a) * r * 0.65, cx + math.cos(a) * r, cy + math.sin(a) * r), fill=col, width=max(2, int(r * 0.16)))


def check_icon(d, cx, cy, r, col):
    d.line((cx - r * 0.5, cy, cx - r * 0.12, cy + r * 0.4, cx + r * 0.55, cy - r * 0.45), fill=col, width=max(3, int(r * 0.22)), joint="curve")


_chips = {}


def chip(text, icon="sun", dark=False, size=40):
    """Frosted pill: sun / check / clock icon in an amber disc + bold caps."""
    key = (text, icon, dark, size)
    if key in _chips:
        return _chips[key]
    f = font(CHIP, size)
    ti = text_img(text, f, (WHITE if dark else INK) + (255,), tracking=2, pad=0)
    h = int(size * 2.15)
    w = ti.width + h + 54
    im = Image.new("RGBA", (w + 50, h + 50), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((25, 31, 25 + w, 31 + h), radius=h // 2, fill=110)
    sh = Image.new("RGBA", im.size, (40, 20, 6, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((25, 25, 25 + w, 25 + h), radius=h // 2,
                        fill=(36, 20, 8, 215) if dark else (255, 250, 242, 238), outline=GOLD + (255,), width=3)
    cx, cy, r = 25 + h // 2 + 4, 25 + h // 2, int(h * 0.36)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=AMBER + (255,))
    if icon == "sun":
        sun_icon(d, cx, cy, r * 0.78, WHITE + (255,))
    elif icon == "check":
        check_icon(d, cx, cy, r * 0.8, WHITE + (255,))
    elif icon == "clock":
        d.ellipse((cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6), outline=WHITE + (255,), width=3)
        d.line((cx, cy, cx, cy - r * 0.42), fill=WHITE + (255,), width=3)
        d.line((cx, cy, cx + r * 0.32, cy + r * 0.1), fill=WHITE + (255,), width=3)
    im.alpha_composite(ti, (25 + h + 22, 25 + (h - ti.height) // 2 - 2))
    _chips[key] = im
    return im


def headline(text, size, fill="sun", tracking=4):
    im = text_img(text, font(HEAD, size), WHITE + (255,), tracking=tracking, pad=8)
    if fill == "sun":
        im = sun_fill(im)
    elif fill == "ink":
        a = np.asarray(im).copy()
        a[..., :3] = INK
        im = Image.fromarray(a, "RGBA")
    return im


def spaced(text, size, col, tracking=8, f=CHIP_M):
    return text_img(text, font(f, size), col + (255,), tracking=tracking, pad=4)


# ---------- A. hook ----------
LAGOS = shadowed(headline("LAGOS SUN", 100), 16, 0.6)
DOTS = shadowed(headline("...", 100), 16, 0.6)
MEET = shadowed(spaced("MEET  YOUR", 46, WHITE, tracking=14, f=CHIP), 12, 0.6)
MATCH = shadowed(headline("MATCH.", 150), 18, 0.6)


def draw_hook(img, t):
    a = life(t, 0.85, 3.95, 0.1, 0.2)
    if a > 0:
        scrim(img, 1040, 1460, 0.45, a)
        # heat-haze: the line ripples, settling as it lands
        u = t - 0.85
        amp = 9 * (1 - eo(u / 1.4))
        src = np.asarray(LAGOS)
        out = np.zeros_like(src)
        for y in range(src.shape[0]):
            out[y] = np.roll(src[y], int(amp * math.sin(y / 9 + t * 14)), axis=0)
        li = Image.fromarray(out, "RGBA")
        gx = W / 2 - (DOTS.width - 70) / 2
        paste(img, li, gx, 1250, a, 0.9 + 0.1 * eob(u / 0.5))
        paste(img, DOTS, gx + li.width / 2 + DOTS.width / 2 - 70, 1250, a * c01((u - 0.5) / 0.3))
    a = life(t, 4.45, 7.95, 0.1, 0.2)
    if a > 0:
        scrim(img, 1330, 1800, 0.5, a)
        u = t - 4.45
        paste(img, MEET, W / 2, 1460, a * c01(u / 0.2), 1.0)
        paste(img, MATCH, W / 2, 1585, a * c01((u - 0.25) / 0.12), 0.6 + 0.4 * eob((u - 0.25) / 0.4, 2.6))
        q = eo((u - 0.55) / 0.5)                          # gold shield underline draws out
        if q > 0:
            d = ImageDraw.Draw(img)
            d.line((W / 2 - 230 * q, 1680, W / 2 + 230 * q, 1680), fill=GOLD + (int(255 * a),), width=5)


# ---------- B. the UV explainer: skin diagram card ----------
CARD_X0, CARD_Y0, CARD_W, CARD_H = 70, 1240, 940, 520
L_SURF, L_DEEP = (CARD_Y0 + 290, CARD_Y0 + 350), (CARD_Y0 + 350, CARD_Y0 + 460)
UVB_X, UVA_X = 330, 720
T_B, T_UVB, T_UVA, T_CLOUD, T_MEL, T_SPOT, T_LINE, T_BEND = 8.35, 11.2, 13.15, 14.75, 16.5, 19.15, 20.4, 21.62
rng = np.random.default_rng(3)
MEL = [(rng.uniform(CARD_X0 + 470, CARD_X0 + CARD_W - 60), rng.uniform(L_DEEP[0] + 20, L_DEEP[1] - 20), rng.uniform(5, 11)) for _ in range(26)]
LBL_F = font(CHIP, 26)


def arrow(d, x, y0, y1, col, a, wv=1.0):
    """A wavy ray from y0 down to y1 with an arrow head."""
    pts = [(x + 14 * math.sin((y - y0) / 26 * wv), y) for y in np.linspace(y0, y1, 40)]
    d.line(pts, fill=col + (int(255 * a),), width=7, joint="curve")
    d.polygon([(x - 16, y1 - 18), (x + 16, y1 - 18), (x, y1 + 6)], fill=col + (int(255 * a),))


def draw_uv(img, t):
    a = life(t, T_B, T_BEND, 0.3, 0.3)
    if a <= 0:
        return
    u = t - T_B
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y_off = int((1 - eo(u / 0.6)) * 60)
    X0, Y0 = CARD_X0, CARD_Y0 + y_off
    d.rounded_rectangle((X0, Y0, X0 + CARD_W, Y0 + CARD_H), radius=34, fill=(28, 16, 6, 200), outline=GOLD + (200,), width=2)
    hdr = text_img("HOW THE SUN REACHES YOUR SKIN", font(CHIP, 27), GOLD + (255,), tracking=4, pad=0)
    layer.alpha_composite(hdr, (int(X0 + CARD_W / 2 - hdr.width / 2), Y0 + 26))
    s0, s1 = L_SURF[0] + y_off, L_SURF[1] + y_off
    e0, e1 = L_DEEP[0] + y_off, L_DEEP[1] + y_off
    d.rectangle((X0 + 30, s0, X0 + CARD_W - 30, s1), fill=(196, 132, 88, 255))         # surface layer
    d.rectangle((X0 + 30, e0, X0 + CARD_W - 30, e1), fill=(150, 92, 60, 255))          # deeper layer
    for k, (lab, y) in enumerate((("SURFACE", (s0 + s1) / 2), ("DEEPER LAYERS", (e0 + e1) / 2))):
        li = text_img(lab, font(CHIP, 22), CREAM + (230,), tracking=4, pad=0)
        layer.alpha_composite(li, (X0 + 50, int(y - li.height / 2)))
    top = Y0 + 130
    # UVB: short ray that stops (burns) at the surface
    q = eo((t - T_UVB) / 0.6)
    if q > 0:
        yb = top + (s0 + 4 - top) * q
        arrow(d, X0 + UVB_X, top, yb, UVB_C, 1.0)
        lb = text_img("UVB  ·  BURNS", LBL_F, UVB_C + (255,), tracking=3, pad=0)
        layer.alpha_composite(fade(lb, c01((t - T_UVB) / 0.25)), (int(X0 + UVB_X - lb.width / 2), top - 50))
        if q >= 1:
            r = 26 + 8 * math.sin(t * 9)
            d.ellipse((X0 + UVB_X - r, s0 - r * 0.45, X0 + UVB_X + r, s0 + r * 0.45), fill=(255, 120, 40, 150))
    # UVA: longer ray that passes the surface and reaches the deeper layer
    q = eo((t - T_UVA) / 0.9)
    if q > 0:
        ya = top + (e0 + 70 - top) * q
        arrow(d, X0 + UVA_X, top, ya, UVA_C, 1.0, 0.8)
        la = text_img("UVA  ·  GOES DEEPER", LBL_F, UVA_C + (255,), tracking=3, pad=0)
        layer.alpha_composite(fade(la, c01((t - T_UVA) / 0.25)), (int(X0 + UVA_X - la.width / 2), top - 50))
    # through clouds and glass: a small cloud + window the UVA ray passes through
    q = c01((t - T_CLOUD) / 0.3)
    if q > 0:
        cx, cy = X0 + UVA_X - 120, top + 70
        for dx, dy, r in ((-22, 4, 20), (0, -8, 26), (24, 4, 20)):
            d.ellipse((cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r), fill=(240, 240, 250, int(220 * q)))
        wx, wy = X0 + UVA_X + 90, top + 50
        d.rectangle((wx, wy, wx + 56, wy + 56), outline=(220, 235, 255, int(240 * q)), width=4)
        d.line((wx + 28, wy, wx + 28, wy + 56), fill=(220, 235, 255, int(240 * q)), width=3)
        d.line((wx, wy + 28, wx + 56, wy + 28), fill=(220, 235, 255, int(240 * q)), width=3)
        lc = text_img("THROUGH CLOUDS & GLASS", font(CHIP, 21), CREAM + (255,), tracking=2, pad=0)
        layer.alpha_composite(fade(lc, q), (int(X0 + UVA_X - lc.width / 2), top + 120))
    # melanin wakes: dots darken and grow in the deeper layer, then rise as dark spots on the surface
    q = eo((t - T_MEL) / 1.2)
    if q > 0:
        for k, (mx, my, r) in enumerate(MEL):
            rr = r * (0.4 + 0.6 * q) * (1 + 0.15 * math.sin(t * 5 + k))
            d.ellipse((mx - rr, my + y_off - rr, mx + rr, my + y_off + rr), fill=(62, 30, 14, int(235 * q)))
        lm = text_img("MELANIN  WAKES", LBL_F, CREAM + (255,), tracking=3, pad=0)
        layer.alpha_composite(fade(lm, c01((t - T_MEL) / 0.3)), (int(X0 + CARD_W - 50 - lm.width), int(e1 + 14)))
    q = eo((t - T_SPOT) / 0.6)
    if q > 0:
        for k, (sx, r) in enumerate(((X0 + 520, 15), (X0 + 600, 10), (X0 + 690, 18), (X0 + 800, 12))):
            d.ellipse((sx - r * q, (s0 + s1) / 2 - r * 0.6 * q, sx + r * q, (s0 + s1) / 2 + r * 0.6 * q), fill=(80, 40, 18, 240))
    img.alpha_composite(fade(layer, a))
    # key-word pop-ups above the card
    c1, c2 = chip("DARK SPOTS  ·  PATCHES", "sun", True, 28), chip("EARLY LINES", "sun", True, 28)
    gap = 14
    x1 = W / 2 - (c1.width + c2.width + gap - 100) / 2 + c1.width / 2 - 25
    pop(img, c1, x1, CARD_Y0 - 60, t, T_SPOT, T_BEND)
    pop(img, c2, x1 + c1.width / 2 + c2.width / 2 + gap - 50, CARD_Y0 - 60, t, T_LINE, T_BEND)


# ---------- C. reveal titles ----------
R0 = tl.REVEAL
PC_T = shadowed(spaced("P A L M C A R E", 30, CREAM, tracking=6, f=CHIP), 10, 0.55)
GS_T = shadowed(headline("GLOWSHIELD", 104), 16, 0.55)
SUB_T = shadowed(spaced("BROAD-SPECTRUM DAILY DEFENSE SUNSCREEN", 27, CREAM, tracking=5, f=CHIP), 10, 0.6)


def badge(top, bot):
    """Round sun-shield badge: amber ring, cream disc, big value, small label."""
    s = 168
    im = Image.new("RGBA", (s + 40, s + 40), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).ellipse((20, 26, 20 + s, 26 + s), fill=120)
    sh = Image.new("RGBA", im.size, (40, 20, 6, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(12)))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.ellipse((20, 20, 20 + s, 20 + s), fill=CREAM + (250,), outline=AMBER + (255,), width=8)
    d.ellipse((34, 34, 6 + s, 6 + s), outline=GOLD + (255,), width=2)
    a = text_img(top, font(HEAD, 32), INK + (255,), pad=0)
    b = text_img(bot, font(CHIP, 16), AMBER + (255,), tracking=3, pad=0)
    im.alpha_composite(a, (20 + s // 2 - a.width // 2, 20 + s // 2 - a.height // 2 - 14))
    im.alpha_composite(b, (20 + s // 2 - b.width // 2, 20 + s // 2 + 26))
    return im


B_SPF, B_PA = badge("SPF 50+", "UVB SHIELD"), badge("PA++++", "UVA SHIELD")


def draw_reveal(img, t):
    s, e = R0, tl.STARTS[6]
    if not (s <= t < e):
        return
    out = 1 - c01((t - (e - 0.3)) / 0.3)
    u = t - 23.5                                          # the name is spoken
    if u > 0:
        scrim(img, 120, 600, 0.35, out)
        paste(img, PC_T, W / 2, 210, out * c01(u / 0.3))
        paste(img, GS_T, W / 2, 310, out * c01((u - 0.1) / 0.15), 0.7 + 0.3 * eob((u - 0.1) / 0.45))
        paste(img, SUB_T, W / 2, 410, out * c01((u - 0.7) / 0.4))
    for k, (b, x) in enumerate(((B_SPF, 128), (B_PA, W - 128))):
        u = t - (27.1 + 0.75 * k)
        if u > 0:
            paste(img, b, x, 1080, out * c01(u / 0.12), 0.5 + 0.5 * eob(u / 0.45, 2.6))


# ---------- D. what SPF 50+ and PA++++ mean ----------
def draw_numbers(img, t):
    a = life(t, 30.15, 34.45, 0.15, 0.25)
    if a > 0:
        u = t - 30.15
        n = int(round(98 * eo(u / 1.6)))
        big = headline(f"{n}%", 190, "ink", 2)
        paste(img, big, W / 2, 360, a, 0.85 + 0.15 * eob(u / 0.4))
        lab = spaced("OF UVB FILTERED  ·  SPF 50+", 32, INK, tracking=6, f=CHIP)
        paste(img, lab, W / 2, 500, a * c01((u - 0.4) / 0.3))
    a = life(t, 34.75, 38.45, 0.15, 0.25)
    if a > 0:
        u = t - 34.75
        scrim(img, 1360, 1800, 0.5, a)
        pa = text_img("PA", font(HEAD, 120), WHITE + (255,), pad=8)
        lay = Image.new("RGBA", (60 + pa.width + 50 + 3 * 92 + 60, 200), (0, 0, 0, 0))
        lay.alpha_composite(sun_fill(pa), (60, 20))
        d = ImageDraw.Draw(lay)
        for k in range(4):                                # the four plus marks light up one by one
            q = c01((u - 0.3 - 0.28 * k) / 0.2)
            cx, cy = 60 + pa.width + 50 + k * 92, 105
            col = (255, 196, 80, int(255 * (0.25 + 0.75 * q)))
            d.rectangle((cx - 32, cy - 8, cx + 32, cy + 8), fill=col)
            d.rectangle((cx - 8, cy - 32, cx + 8, cy + 32), fill=col)
        paste(img, shadowed(lay, 14, 0.5), W / 2, 1500, a)
        paste(img, shadowed(spaced("THE HIGHEST UVA GRADE", 34, CREAM, tracking=8, f=CHIP), 10, 0.6), W / 2, 1650, a * c01((u - 1.4) / 0.3))
    pop(img, chip("GUARDS THE DEEPER LAYERS", "sun", True, 36), W / 2, 1620, t, 38.75, 41.4)


# ---------- E. texture + application pops, and the pack beside her ----------
POPS = [("LIGHTWEIGHT", "sun", 42.45, 43.85), ("HEALTHY INGREDIENTS", "sun", 43.9, 45.5), ("MELTS IN CLEAR", "sun", 45.6, 47.45),
        ("NO WHITE CAST", "check", 48.35, 49.7), ("NO GREASE", "check", 49.75, 50.95), ("INVISIBLE VEIL", "sun", 51.0, 52.75)]
_pack = Image.open(PACK).convert("RGBA")
PACK_S = _pack.resize((round(_pack.width * 500 / _pack.height), 500), Image.LANCZOS)
PACK_IN = shadowed(PACK_S, 16, 0.5, 8)


def draw_apply(img, t):
    for text, ic, s, e in POPS:
        pop(img, chip(text, ic, False, 40), W / 2, 1590, t, s, e)
    for s, e in ((30.0, 34.45), (47.6, 50.75)):           # the pack floats beside the cream on the fingertip shots
        a = life(t, s, e, 0.35, 0.3)
        if a > 0:
            u = t - s
            paste(img, PACK_IN, 210, 1030 + 8 * math.sin(u * 1.6) + (1 - eo(u / 0.6)) * 40, a)


# ---------- F. the shield checklist ----------
CHECKS = [("MELANIN KEPT CALM", 54.85), ("MARKS STOP SPREADING", 56.45), ("COLLAGEN PROTECTED", 58.4), ("NATURAL TONE, EVEN", 60.15)]


def draw_checks(img, t):
    a = life(t, 53.05, 62.2, 0.3, 0.3)
    if a <= 0:
        return
    scrim(img, 1180, 1820, 0.5, a)
    hd = shadowed(headline("YOUR SHIELD", 64), 12, 0.6)
    paste(img, hd, W / 2, 1270, a * c01((t - 53.05) / 0.3), 0.85 + 0.15 * eob((t - 53.05) / 0.4))
    for k, (text, s) in enumerate(CHECKS):
        u = t - s
        if u > 0:
            ci = chip(text, "check", False, 34)
            paste(img, ci, W / 2, 1385 + k * 100, a * c01(u / 0.12), 0.75 + 0.25 * eob(u / 0.4))


# ---------- G/H. daily use, sunrise to sunset ----------
def draw_daily(img, t):
    pop(img, chip("EACH MORNING  ·  RAIN OR SHINE", "sun", False, 36), W / 2, 1590, t, 62.6, 64.9)
    pop(img, chip("REAPPLY EVERY 2 HOURS", "clock", False, 40), W / 2, 1590, t, 64.95, 67.5)
    a = life(t, 68.0, 72.5, 0.3, 0.3)
    if a > 0:
        u = t - 68.0
        scrim(img, 1440, 1800, 0.45, a)
        d = ImageDraw.Draw(img)
        x0, x1, y = 170, W - 170, 1660
        pts = [(x0 + (x1 - x0) * k / 60, y - 110 * math.sin(math.pi * k / 60)) for k in range(61)]
        q = eo(u / 2.2)
        d.line(pts[: max(2, int(61 * q))], fill=GOLD + (int(230 * a),), width=4)
        px, py = pts[min(60, int(60 * q))]
        sun_icon(d, px, py, 26, (255, 210, 110, int(255 * a)))
        for lab, x in (("SUNRISE", x0), ("SUNSET", x1)):
            li = text_img(lab, font(CHIP, 26), CREAM + (255,), tracking=5, pad=0)
            img.alpha_composite(fade(li, a), (int(x - li.width / 2), y + 18))
        g = shadowed(text_img("your glow, protected", font(SERIF_I, 64), CREAM + (255,), pad=6), 10, 0.6)
        paste(img, g, W / 2, 1500, a * c01((u - 1.85) / 0.4))


# ---------- I. finale words ----------
FIN_W = [("PROTECTED.", 72.75), ("RADIANT.", 73.65), ("YOU.", 74.5)]


def draw_finale(img, t):
    a = life(t, 72.7, 75.55, 0.1, 0.3)
    if a <= 0:
        return
    scrim(img, 1300, 1820, 0.5, a)
    for k, (wd, s) in enumerate(FIN_W):
        u = t - s
        if u > 0:
            im = shadowed(headline(wd, 96 if k < 2 else 130), 14, 0.6)
            paste(img, im, W / 2, 1410 + k * 135, a * c01(u / 0.1), 0.6 + 0.4 * eob(u / 0.35, 2.6))


# ---------- J. warm sun-flare flashes on the big cuts ----------
YY, XX = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
FLARES = [tl.HOOK2, 13.0, tl.REVEAL, tl.SHIELD, tl.FIN, tl.EC_START]


def flare(arr, t):
    for c in FLARES:
        u = t - c
        if -0.12 < u < 0.4:
            k = math.exp(-((u - 0.02) / 0.12) ** 2)
            g = np.exp(-(((XX - W * 0.7) / 520) ** 2 + ((YY - H * 0.2) / 700) ** 2)) * 0.85 + 0.25
            streak = np.exp(-((YY - H * 0.2) / 14) ** 2) * 0.6
            m = np.clip((g + streak) * k, 0, 1)
            m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
            arr = 255 - (255 - arr) * (1 - m[..., None] * np.array([1.0, 0.86, 0.62]))
    return arr


def compose(frame, t):
    arr = flare(frame.astype(np.float32), t)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    if t < tl.EC_START:
        draw_hook(img, t)
        draw_uv(img, t)
        draw_reveal(img, t)
        draw_numbers(img, t)
        draw_apply(img, t)
        draw_checks(img, t)
        draw_daily(img, t)
        draw_finale(img, t)
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
