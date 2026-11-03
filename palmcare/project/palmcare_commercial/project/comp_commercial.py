"""PalmCare 10 s commercial, photographic compositing pass (silent, 1080x1920, 30 fps).

Plates (Flow footage, slowed + motion-interpolated): plate1 = golden-sweep stage (batch 1), plate2 = gold silk over a
mirror floor (batch 2). The 11 ORIGINAL product photographs are locked foreground layers: never regenerated, warped or
rotated; only uniformly scaled, colour-graded to the footage light and lit with an edge wrap from the plate behind.

Integration: products stand on the measured floor line (~y 1340, standing point at the ripple centre), soft contact
shadow, a reflection in the floor (rippled on the liquid surface, clean on the mirror floor), shallow depth of field on
the plate behind them, the plate's OWN liquid keyed out and laid back in front of the products (labels protected while
they hold), film grain over the whole frame. The camera moves the entire composite; products enter by rising out of
the liquid, settling in from above, or a rack-focus pull, and leave on a focus pull while the next arrives.
Usage: comp_commercial.py OUT.mp4 [preview]"""
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
P = R + 'palmcare_commercial/'
W, H, FPS, N = 1080, 1920, 30, 300
OUT = sys.argv[1]
PREVIEW = len(sys.argv) > 2
rng = np.random.default_rng(11)

PRODS = [('milky.png', 'bottle'), ('cacao.png', 'bottle'), ('citrus_cut.png', 'bottle'), ('molecular_cut.png', 'bottle'),
         ('tropical_cut.png', 'bottle'), ('dermalight_cut.png', 'bottle'), ('vitac_real_final.png', 'pack'),
         ('n10_real_final.png', 'pack'), ('dermaluxe_box_final.png', 'pack'), ('glowshield_box_flat.png', 'pack'),
         ('box_straight.png', 'box')]
T = [0.4, 1.05, 1.65, 2.25, 2.85, 3.45, 4.05, 4.65, 5.15, 5.85, 6.55, 7.25, 7.95]
WIN = [(T[i], T[i + 1]) for i in range(7)] + [(T[i], T[i + 1]) for i in range(8, 12)]
ENTR = ['rise', 'focus', 'settle', 'rise', 'focus', 'settle', 'rise', 'focus', 'rise', 'settle', 'focus']
GROUP0, CLOSE0 = 7.95, 9.4
F = lambda s: int(round(s * FPS))


def load(name):
    a = cv2.imread(P + 'products/' + name, cv2.IMREAD_UNCHANGED)
    if a.shape[2] == 3:                                   # carton photographed flat: opaque, 1px anti-aliased edge
        al = np.full(a.shape[:2], 255, np.uint8)
        al[0, :] = al[-1, :] = al[:, 0] = al[:, -1] = 128
        a = np.dstack([a, al])
    return a.astype(np.float32) / 255


SRC = [load(n) for n, _ in PRODS]


def grade(rgb):
    """match the product to the footage: warm white balance, slightly softer contrast, champagne lift in the shadows"""
    x = rgb * np.array([0.93, 0.985, 1.05], np.float32)             # BGR: less blue, more red
    x = 0.04 + x * 0.94
    x = x + (np.array([0.62, 0.74, 0.86], np.float32) - x) * 0.05   # pull a touch toward the plate's ambient beige
    return np.clip(x, 0, 1)


def scaled(i, h=None, w=None):
    a = SRC[i]
    ar = a.shape[1] / a.shape[0]
    if h is None:
        h = w / ar
    h = max(2, int(round(h)))
    ww = max(2, int(round(h * ar)))
    s = cv2.resize(a, (ww, h), interpolation=cv2.INTER_AREA)
    s[..., :3] = grade(s[..., :3])
    return s


CACHE = {}


def prod(i, h=None, w=None):
    key = (i, h, w)
    if key not in CACHE:
        CACHE[key] = scaled(i, h, w)
    return CACHE[key]


def size_for(i, k=1.0):
    kind = PRODS[i][1]
    return dict(h=880 * k) if kind == 'bottle' else dict(h=800 * k) if kind == 'pack' else dict(w=640 * k)


def over(dst, src_rgb, src_a, x0, y0):
    h, w = src_a.shape
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(W, x0 + w), min(H, y0 + h)
    if X1 <= X0 or Y1 <= Y0:
        return
    sa = src_a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None]
    dst[Y0:Y1, X0:X1] = dst[Y0:Y1, X0:X1] * (1 - sa) + src_rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * sa


def place(frame, plate_soft, i, cx, base, k=1.0, lift=0.0, clip_floor=None, alpha=1.0, blur=0.0, ripple=False, t=0.0):
    """composite product i standing at (cx, base): shadow, reflection, edge light wrap, optional focus blur"""
    a = prod(i, **{kk: round(v) for kk, v in size_for(i, k).items()})
    h, w = a.shape[:2]
    rgb, al = a[..., :3].copy(), a[..., 3].copy() * alpha
    if blur > 0.4:
        rgb = cv2.GaussianBlur(rgb * al[..., None], (0, 0), blur)
        al = cv2.GaussianBlur(al, (0, 0), blur)
        rgb = rgb / np.maximum(al[..., None], 1e-4)
    x0, y0 = int(round(cx - w / 2)), int(round(base - h - lift))
    # light wrap: the plate's light bleeding over the product edges (back-lit set)
    ys, ye, xs, xe = max(0, y0), min(H, y0 + h), max(0, x0), min(W, x0 + w)
    if ye > ys and xe > xs:
        edge = np.clip(al - cv2.erode(al, np.ones((9, 9), np.uint8)), 0, 1)
        edge = cv2.GaussianBlur(edge, (0, 0), 3)
        bgpatch = plate_soft[ys:ye, xs:xe]
        sub = edge[ys - y0:ye - y0, xs - x0:xe - x0, None]
        rgb[ys - y0:ye - y0, xs - x0:xe - x0] = rgb[ys - y0:ye - y0, xs - x0:xe - x0] * (1 - sub * 0.45) + bgpatch * 1.05 * sub * 0.45
    # contact shadow on the floor (soft, warm), fades as the product lifts away
    so = alpha * min(1.0, max(0.0, 1 - lift / 160)) * (min(1.0, max(0.0, 1 + lift / (h * 0.4))) if lift < 0 else 1.0)
    if so > 0.02:
        sh = np.zeros((90, int(w * 1.5)), np.float32)
        cv2.ellipse(sh, (sh.shape[1] // 2, 45), (int(w * 0.55), 16), 0, 0, 360, 1.0, -1)
        sh = cv2.GaussianBlur(sh, (0, 0), 9) * 0.5 * so
        sx0, sy0 = int(cx - sh.shape[1] / 2), int(base - 45)
        over(frame, np.zeros(sh.shape + (3,), np.float32) + np.array([0.16, 0.22, 0.3], np.float32), sh, sx0, sy0)
    # reflection in the floor
    rh = int(h * 0.42)
    if rh > 4 and base < H:
        fl = rgb[::-1][:rh].copy() if lift <= 0 else rgb[::-1][:rh].copy()
        fa = al[::-1][:rh].copy() * np.linspace(0.34, 0, rh)[:, None] * alpha
        if ripple:                                          # liquid surface: gently rippled reflection
            yy = np.arange(rh, dtype=np.float32)[:, None]
            xx = np.arange(w, dtype=np.float32)[None, :]
            mx = (xx + 6 * np.sin(yy / 9 + t * 7) * (yy / rh + 0.2)).astype(np.float32)
            my = np.repeat(yy, w, 1).astype(np.float32)
            fl = cv2.remap(fl, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            fa = cv2.remap(fa, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        fl = cv2.GaussianBlur(fl, (0, 0), 1.6)
        if lift < 0:
            fa = fa * min(1.0, max(0.0, 1 + lift / (h * 0.5)))
        over(frame, fl, fa, x0, int(base + max(lift, 0)))
    if clip_floor is not None:                              # rising out of the liquid: hide what is under the surface
        cut = int(clip_floor - y0)
        if 0 < cut < h:
            al[cut:] = 0
        elif cut <= 0:
            al[:] = 0
    over(frame, rgb, al, x0, y0)
    return (x0, y0, w, h)


def liquid_key(plate):
    """the plate's own liquid (gold/clear splashes) as a transparent foreground layer"""
    hsv = cv2.cvtColor((plate * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    bg = cv2.GaussianBlur(plate, (0, 0), 40)
    hb = cv2.cvtColor((bg * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    ds = hsv[..., 1] - hb[..., 1]
    dv = np.abs(hsv[..., 2] - hb[..., 2])
    al = np.clip((ds - 12) / 40, 0, 1) * 0.75 + np.clip((dv - 12) / 40, 0, 1) * 0.6
    return cv2.GaussianBlur(np.clip(al, 0, 1), (0, 0), 1.2)


def reader(path):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    last = None
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) == W * H * 3:
            last = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
        yield last


r1, r2 = reader(P + 'bg/plate1.mp4'), reader(P + 'bg/plate2.mp4')
P1_END, P2_START = F(5.2), F(4.65)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.25 * np.clip(((XX - W / 2) / (W * 0.75)) ** 2 + ((YY - H * 0.47) / (H * 0.68)) ** 2, 0, 1.4) ** 1.4)[..., None]
FD = R + 'fonts/'


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def eo(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def camera(img, z, dx, dy, cx=540, cy=1250):
    M = np.float32([[z, 0, cx * (1 - z) + dx], [0, z, cy * (1 - z) + dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def text_layer():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FD + 'Cormorant-SemiBold.ttf', 132)
    f2 = ImageFont.truetype(FD + 'Cormorant-Italic.ttf', 70)
    word = 'PALMCARE'
    track = 30
    tw = sum(f1.getlength(c) for c in word) + track * (len(word) - 1)
    x = (W - tw) / 2
    for c in word:
        d.text((x, 790), c, font=f1, fill=(255, 255, 255, 255))
        x += f1.getlength(c) + track
    m1 = np.asarray(im)[..., 3].astype(np.float32) / 255
    im2 = Image.new('L', (W, H), 0)
    d2 = ImageDraw.Draw(im2)
    s = 'Pamper your skin with PalmCare.'
    d2.text(((W - f2.getlength(s)) / 2, 1005), s, font=f2, fill=255)
    m2 = np.asarray(im2).astype(np.float32) / 255
    g = np.linspace(0, 1, H)[:, None, None]
    gold = np.array([0.36, 0.67, 0.85], np.float32) * (1 - g) + np.array([0.13, 0.33, 0.49], np.float32) * g   # BGR gold
    return m1, m2, gold


TXT1, TXT2, GOLD = text_layer()

wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-an', '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'medium' if PREVIEW else 'slow', '-crf', '20' if PREVIEW else '13',
                       '-pix_fmt', 'yuv420p'] + (['-vf', 'scale=540:960'] if PREVIEW else []) + ['-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
p1 = p2 = None
for fi in range(N):
    t = fi / FPS
    if fi < P1_END:
        p1 = next(r1)
    if fi >= P2_START:
        p2 = next(r2)
    # background: plate 1, liquid wipe to plate 2 between 4.65 and 5.15
    if fi < P2_START:
        plate = p1.copy()
    elif fi >= F(5.15):
        plate = p2.copy()
    else:
        u = ease((t - 4.65) / 0.5)
        front = (XX * 0.55 + (H - YY) * 0.85) / (W * 0.55 + H * 0.85)       # diagonal, bottom-left to top-right
        m = np.clip((u * 1.3 - front) / 0.18 + 0.5, 0, 1)[..., None]
        plate = p1 * (1 - m) + p2 * m
        band = np.exp(-((u * 1.3 - front) / 0.05) ** 2)[..., None] * math.sin(math.pi * u)
        plate = 1 - (1 - plate) * (1 - band * np.array([0.55, 0.78, 0.95], np.float32) * 0.6)
    plate = np.clip(plate * np.array([0.985, 1.0, 1.02], np.float32), 0, 1)
    sharp = plate
    # which products are on screen (with overlap for focus-pull handovers)
    active = []
    for i, (s, e) in enumerate(WIN):
        a0, a1 = F(s) - 3, F(e) + 3
        if a0 <= fi < a1:
            active.append((i, fi - a0, a1 - a0))
    in_group = F(GROUP0) - 2 <= fi < F(CLOSE0) + 8
    soft_amt = 2.6 if (active or in_group) else 0.0
    plate_soft = cv2.GaussianBlur(plate, (0, 0), soft_amt) if soft_amt else plate
    frame = plate_soft.copy()
    protect = np.zeros((H, W), np.float32)
    batch2 = fi >= F(5.15)
    floor = 1500 if not batch2 else 1520
    for i, lf, ln in active:
        kind = ENTR[i]
        e_in = eo(lf / 9)
        e_out = ease((lf - (ln - 6)) / 6)
        alpha = min(1.0, lf / 3) * (1 - e_out)
        blur = (1 - e_in) * 10 if kind == 'focus' else 0.0
        blur += e_out * 9
        k = (1.06 - 0.06 * e_in) if kind == 'focus' else 1.0
        lift, clipf = 0.0, None
        if kind == 'rise':
            hgt = size_for(i)['h'] if 'h' in size_for(i) else size_for(i)['w'] / (SRC[i].shape[1] / SRC[i].shape[0])
            lift = -(1 - e_in) * hgt * 0.9                    # starts below the surface
            clipf = floor
        elif kind == 'settle':
            lift = (1 - eo(lf / 11)) * 260
        hold = (1 - e_out) * min(1.0, lf / 9)
        box = place(frame, plate_soft, i, 540, floor, k=k, lift=lift, clip_floor=clipf, alpha=alpha, blur=blur,
                    ripple=not batch2, t=t)
        x0, y0, w, h = box
        cv2.rectangle(protect, (x0 + int(w * 0.03), y0 + int(h * 0.02)), (x0 + int(w * 0.97), y0 + int(h * 0.98)), float(max(hold, alpha)), -1)
        if kind == 'rise' and lf < 14:                       # surface rings where it breaks through
            ring = np.zeros((H, W), np.float32)
            rr = 40 + lf * 22
            cv2.ellipse(ring, (540, floor), (int(rr), int(rr * 0.12)), 0, 0, 360, 1.0, 3)
            ring = cv2.GaussianBlur(ring, (0, 0), 2) * (1 - lf / 14) * 0.55
            frame = 1 - (1 - frame) * (1 - ring[..., None] * np.array([0.8, 0.92, 1.0], np.float32))
    if in_group:
        g = fi - (F(GROUP0) - 2)
        back = [(7, -282, 1290), (6, -96, 1290), (8, 96, 1290), (9, 276, 1290)]
        # clear acrylic riser for the back row (transparent block, polished edges)
        rp = eo(g / 8)
        if rp > 0:
            x0r, x1r, y0r, y1r = 150, 930, 1290, 1560
            blk = frame[y0r:y1r, x0r:x1r]
            frame[y0r:y1r, x0r:x1r] = blk * (1 - 0.10 * rp) + np.array([0.86, 0.92, 0.97], np.float32) * 0.10 * rp
            frame[y0r - 2:y0r + 2, x0r:x1r] = frame[y0r - 2:y0r + 2, x0r:x1r] * (1 - 0.8 * rp) + 0.98 * 0.8 * rp
            frame[y0r:y1r, x0r:x0r + 2] = frame[y0r:y1r, x0r:x0r + 2] * (1 - 0.5 * rp) + 0.95 * 0.5 * rp
            frame[y0r:y1r, x1r - 2:x1r] = frame[y0r:y1r, x1r - 2:x1r] * (1 - 0.5 * rp) + 0.95 * 0.5 * rp
        for k_, (i, dx, b) in enumerate(back):
            a_ = eo((g - k_ * 2) / 8)
            if a_ > 0:
                place(frame, plate_soft, i, 540 + dx, b, k=0.4, lift=(1 - a_) * 60, alpha=a_)
        front = [(0, -452, 'h', 310), (1, -322, 'h', 310), (2, -200, 'h', 304), (10, 0, 'w', 262), (3, 200, 'h', 304), (4, 322, 'h', 310), (5, 450, 'h', 304)]
        for k_, (i, dx, dim, v) in enumerate(front):
            a_ = eo((g - 3 - abs(k_ - 3) * 2) / 8)
            if a_ > 0:
                ref = size_for(i)
                kk = v / (ref['h'] if dim == 'h' and 'h' in ref else ref['w'] if dim == 'w' else ref['h'])
                place(frame, plate_soft, i, 540 + dx, 1580, k=kk, lift=(1 - a_) * 70, alpha=a_)
        protect[930:1665, 15:1065] = np.maximum(protect[930:1665, 15:1065], min(1.0, g / 6))
    # the plate's own liquid back in front of the products (protected over the labels while they hold)
    if fi >= F(0.3) and fi < F(CLOSE0):
        protect = cv2.GaussianBlur(protect, (0, 0), 6)
        lk = liquid_key(sharp) * (1 - np.clip(protect * 1.15, 0, 1)) * 0.9
        frame = frame * (1 - lk[..., None]) + sharp * lk[..., None]
    # closing frame
    if fi >= F(CLOSE0) - 1:
        c = fi - (F(CLOSE0) - 1)
        bgk = eo(c / 6)
        cl = 0.5 + 0.5 * np.exp(-(((XX - 540) / 620) ** 2 + ((YY - 940) / 640) ** 2))[..., None]
        champ = np.array([0.80, 0.90, 0.97], np.float32) * cl + np.array([0.42, 0.62, 0.79], np.float32) * (1 - cl)
        frame = frame * (1 - bgk) + champ * bgk
        a1, a2 = eo((c - 2) / 6), eo((c - 5) / 6)
        frame = frame * (1 - TXT1[..., None] * a1) + GOLD * TXT1[..., None] * a1
        frame = frame * (1 - TXT2[..., None] * a2) + (GOLD * 0.75) * TXT2[..., None] * a2
        lw = int(170 * a2)
        frame[968:970, 540 - lw:540 + lw] = frame[968:970, 540 - lw:540 + lw] * 0.3 + np.array([0.18, 0.53, 0.72], np.float32) * 0.7
    # camera: gentle push/drift of the whole composite (different per section)
    if fi < F(CLOSE0):
        if fi < F(4.65):
            z = 1.0 + 0.06 * ease(t / 4.65)
        elif fi < F(GROUP0):
            z = 1.0 + 0.06 * ease((t - 4.65) / (GROUP0 - 4.65))
        else:
            z = 1.0 + 0.04 * ease((t - GROUP0) / 1.45)
        frame = camera(frame, z, 6 * math.sin(t * 1.3), 0)
    frame = frame * VIG
    frame = frame + rng.normal(0, 0.012, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)   # fine grain
    wr.stdin.write((np.clip(frame, 0, 1) * 255).astype(np.uint8).tobytes())
    if fi % 30 == 0:
        print('frame', fi, flush=True)
wr.stdin.close()
wr.wait()
print('done', OUT)
