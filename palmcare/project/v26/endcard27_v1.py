"""Bright, high-design PalmCare end card (1080x1920): luminous cream-peach set with soft light beams and gold bokeh,
the REAL group photo as a framed card (white border, rounded corners, shadow, floor reflection) that springs in, and
the slogan in bold display serif - chocolate words + polished-gold 'PalmCare.' - each word popping in with a spring,
a gold shimmer pass and star-glint pops. Import: end_frame(f) -> float BGR 0..1"""
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
W, H = 1080, 1920
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def ease(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def spring(x, k=7.0, z=0.42):
    """0 -> 1 with a lively overshoot"""
    if x <= 0: return 0.0
    return 1 - math.exp(-z * k * x) * math.cos(k * math.sqrt(1 - z * z) * x)


# ---------- background ----------
t = np.linspace(0, 1, H)[:, None, None]
BG = np.array([0.90, 0.95, 1.00], np.float32) * (1 - t) + np.array([0.74, 0.85, 0.96], np.float32) * t       # cream -> peach
glow = np.exp(-(((XX - 540) / 700) ** 2 + ((YY - 760) / 820) ** 2))[..., None]
BG = BG * (1 - glow * 0.5) + np.array([0.97, 0.99, 1.0], np.float32) * glow * 0.5
VIG = (1 - 0.16 * np.clip(((XX - 540) / 760) ** 2 + ((YY - 960) / 1250) ** 2, 0, 1.5))[..., None]
rng = np.random.default_rng(27)
BOKEH = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(4, 16), rng.uniform(25, 70), rng.uniform(0, 6.3), rng.uniform(0.25, 0.7))
         for _ in range(46)]

# ---------- group photo card ----------
G = cv2.imread(R + 'v26/group_enh.png').astype(np.float32) / 255
CW = 1000; CH = int(round(CW * G.shape[0] / G.shape[1])); BORD = 7; RAD = 34
img = cv2.resize(G, (CW, CH), interpolation=cv2.INTER_AREA)
_gy = np.linspace(0, 1, CH + 2 * BORD)[:, None, None]
card = (np.array([0.42, 0.78, 0.96], np.float32) * (1 - _gy) + np.array([0.16, 0.46, 0.72], np.float32) * _gy) * np.ones((1, CW + 2 * BORD, 1), np.float32)
card[BORD:BORD + CH, BORD:BORD + CW] = img
def rrect(h, w, r):
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r, h), 255, -1); cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 0.8)
CARD_A = rrect(*card.shape[:2], RAD)
inner = rrect(CH, CW, RAD - 8); card[BORD:BORD + CH, BORD:BORD + CW] = card[BORD:BORD + CH, BORD:BORD + CW] * inner[..., None] + \
    card[BORD:BORD + CH, BORD:BORD + CW] * (1 - inner[..., None])
CARD_CY = 1300


# ---------- slogan sprites ----------
FD = R + 'fonts/'
F_IT = ImageFont.truetype(FD + 'DMSerifDisplay-Italic.ttf', 124)
F_RG = ImageFont.truetype(FD + 'DMSerifDisplay.ttf', 150)
CHOC = np.array([0.10, 0.15, 0.25], np.float32)          # deep chocolate (BGR)


def sprite(text, font, gold):
    S = 2
    f2 = ImageFont.truetype(font.path, font.size * S)
    w = int(f2.getlength(text)) + 60 * S; h = int(font.size * S * 1.5)
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).text((30 * S, 10 * S), text, font=f2, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    a = cv2.resize(a, (w // S, h // S), interpolation=cv2.INTER_AREA)
    hh, ww = a.shape
    if gold:
        g = np.linspace(0, 1, hh)[:, None]
        top, mid, bot = np.array([0.16, 0.52, 0.84]), np.array([0.42, 0.80, 0.98]), np.array([0.04, 0.30, 0.58])
        col = np.where(g[..., None] < 0.5, top + (mid - top) * (g[..., None] / 0.5), mid + (bot - mid) * ((g[..., None] - 0.5) / 0.5))
        col = np.broadcast_to(col, (hh, ww, 3)).astype(np.float32)
        edge = cv2.dilate(a, np.ones((5, 5), np.uint8)) - a                         # thin dark-gold keyline
        rgb = col * (1 - np.clip(edge, 0, 1)[..., None]) + np.array([0.03, 0.14, 0.27], np.float32) * np.clip(edge, 0, 1)[..., None]
        a = np.clip(a + edge, 0, 1)
    else:
        rgb = np.broadcast_to(CHOC, (hh, ww, 3)).astype(np.float32).copy()
    return rgb, a


LINES = [[('Pamper', F_IT, False), ('your', F_IT, False), ('skin', F_IT, False)],
         [('with', F_IT, False), ('PalmCare.', F_RG, True)]]
LINE_Y = [520, 690]
WORDS = []                                               # (rgb, alpha, centre x, centre y, start frame)
k = 0
for li, line in enumerate(LINES):
    sps = [sprite(t_, f_, g_) for t_, f_, g_ in line]
    gap = -28
    total = sum(a.shape[1] for _, a in sps) + gap * (len(sps) - 1)
    x = (W - total) / 2
    for (rgb, a), (t_, f_, g_) in zip(sps, line):
        WORDS.append((rgb, a, x + a.shape[1] / 2, LINE_Y[li], 12 + 6 * k, g_)); x += a.shape[1] + gap; k += 1


def place(dst, rgb, a, cx, cy, sc, alpha, rise=0.0):
    hh, ww = a.shape
    M = np.float32([[sc, 0, cx - sc * ww / 2], [0, sc, cy + rise - sc * hh / 2]])
    A = cv2.warpAffine(a, M, (W, H)) * alpha
    C = cv2.warpAffine(rgb, M, (W, H))
    return dst * (1 - A[..., None]) + C * A[..., None], A


def glint(fr, x, y, s, a):
    st = np.exp(-(((XX - x) / 2.2) ** 2 + ((YY - y) / (46 * s + 1)) ** 2)) + np.exp(-(((XX - x) / (46 * s + 1)) ** 2 + ((YY - y) / 2.2) ** 2))
    st += np.exp(-((XX - x) ** 2 + (YY - y) ** 2) / (2 * (9 * s + 1) ** 2)) * 0.9
    col = np.array([0.80, 0.95, 1.0], np.float32)
    return 1 - (1 - fr) * (1 - np.clip(st, 0, 1)[..., None] * col * a)


GLINTS = [(930, 660, 58), (150, 470, 70), (985, 1610, 84), (95, 1000, 96), (800, 560, 108)]


def end_frame(f, n=135):
    tt = f / 30.0
    fr = BG.copy()
    for i, sx in enumerate((0.15, 0.48, 0.80)):                              # soft light beams, slowly drifting
        cx = W * sx + 70 * math.sin(tt * 0.6 + i)
        beam = np.exp(-(((XX - cx) - (YY - 0) * 0.42) / 85) ** 2) * np.clip(1 - YY / 1500, 0, 1)
        fr = 1 - (1 - fr) * (1 - beam[..., None] * 0.18)
    ov = np.zeros((H, W), np.float32)                                        # gold bokeh drifting up
    for x0, y0, r, sp, ph, al in BOKEH:
        cv2.circle(ov, (int(x0 + 14 * math.sin(tt + ph)), int((y0 - sp * tt) % H)), int(r), al * (0.6 + 0.4 * math.sin(tt * 2 + ph)), -1, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 3)[..., None]
    fr = fr * (1 - ov * 0.55) + np.array([0.52, 0.82, 0.98], np.float32) * ov * 0.55
    # photo card: springs in, then a slow push
    sp = spring((f - 2) / 26.0)
    sc = (0.86 + 0.14 * sp) * (1 + 0.035 * ease(f / n))
    a_card = min(1.0, max(0.0, (f - 2) / 8.0))
    hh, ww = card.shape[:2]
    M = np.float32([[sc, 0, 540 - sc * ww / 2], [0, sc, CARD_CY - sc * hh / 2 + 30 * (1 - sp)]])
    if a_card > 0:
        sh = cv2.warpAffine(CARD_A, M, (W, H)); sh = cv2.GaussianBlur(np.roll(sh, 26, 0), (0, 0), 26) * 0.42 * a_card
        fr = fr * (1 - sh[..., None] * 0.9)
        # floor reflection
        Mr = M.copy(); Mr[1, 1] = -sc; Mr[1, 2] = CARD_CY + sc * hh / 2 + 30 * (1 - sp) + sc * hh + 8
        rc = cv2.warpAffine(card, Mr, (W, H)); ra = cv2.warpAffine(CARD_A, Mr, (W, H))
        bot = CARD_CY + sc * hh / 2 + 8
        fade = np.clip(1 - (YY - bot) / 260, 0, 1) * (YY > bot) * 0.22 * a_card
        ra = cv2.GaussianBlur(ra * fade, (0, 0), 2)
        fr = fr * (1 - ra[..., None]) + cv2.GaussianBlur(rc, (0, 0), 2) * ra[..., None]
        C = cv2.warpAffine(card, M, (W, H)); A = cv2.warpAffine(CARD_A, M, (W, H)) * a_card
        fr = fr * (1 - A[..., None]) + C * A[..., None]
        sx = -500 + (W + 1000) * ease((f - 40) / 45)                         # one light pass over the products
        sw = np.exp(-(((XX - sx) + (YY - CARD_CY) * 0.45) / 110) ** 2) * A * 0.22
        fr = 1 - (1 - fr) * (1 - sw[..., None])
    # gold rule under the slogan (grows from the centre)
    gr = ease((f - 44) / 18)
    if gr > 0:
        L = int(250 * gr)
        fr[798:801, 540 - L:540 + L] = np.array([0.30, 0.62, 0.84], np.float32)
        cv2.fillConvexPoly(fr, np.int32([[540, 790], [549, 799], [540, 808], [531, 799]]), (0.30, 0.62, 0.84), cv2.LINE_AA)
    # slogan words pop in
    for rgb, a, cx, cy, st, gold in WORDS:
        u = (f - st) / 16.0
        if u <= 0: continue
        s = spring(u, 7.5, 0.38)
        sc_w = 0.35 + 0.65 * s
        shadow = cv2.GaussianBlur(a, (0, 0), 6)
        fr, _ = place(fr, np.zeros_like(rgb) + np.array([0.20, 0.35, 0.55], np.float32), shadow, cx + 3, cy + 7, sc_w, min(1, u * 3) * 0.35, 30 * (1 - s))
        rgbx = rgb
        if gold:                                                             # shimmer across the gold
            pos = -0.3 + 1.6 * ease((f - 62) / 22)
            xs = np.linspace(0, 1, a.shape[1])[None, :]; ys = np.linspace(0, 1, a.shape[0])[:, None]
            band = np.exp(-(((xs - pos) - (ys - 0.5) * 0.4) / 0.07) ** 2)[..., None]
            rgbx = np.clip(rgb + band * 0.55, 0, 1)
        fr, _ = place(fr, rgbx, a, cx, cy, sc_w, min(1, u * 3), 30 * (1 - s))
    for gx, gy, gf in GLINTS:                                                # star-glint pops
        u = (f - gf) / 14.0
        if 0 < u < 1: fr = glint(fr, gx, gy, math.sin(math.pi * u), math.sin(math.pi * u))
    return np.clip(fr * VIG, 0, 1)


if __name__ == '__main__':
    import sys
    out = [cv2.resize((end_frame(i) * 255).astype(np.uint8), (360, 640)) for i in (8, 30, 70, 134)]
    cv2.imwrite(sys.argv[1], np.hstack(out))
    cv2.imwrite(sys.argv[1].replace('.jpg', '_full.jpg'), (end_frame(134) * 255).astype(np.uint8))
