"""PalmCare collection, client round 2 (silent, 1080x1920, 30 fps).
- Molecular Glow: the whole real front label mapped onto the bottle in true proportion and perspective (fxm2).
- Serums: Flow's invented serums replaced by the REAL N10 / DermaLuxe / Vita C+ boxes and bottles on a studio set
  (each pair, then all three together).
- Finale: the REAL photo of the whole PalmCare range, revealed with a slow pull-back and the slogan.
Usage: edit26.py OUT.mp4 [preview]"""
import math, subprocess, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v26')
import endcard27 as END

R = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
V = R + 'v23/'
V26 = R + 'v26/'
W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1]
PREVIEW = len(sys.argv) > 2
rng = np.random.default_rng(23)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def ease(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def eo(x):
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


p = subprocess.run(['ffmpeg', '-v', 'error', '-i', V + 'src.mov', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
SRC = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3).copy()
for n in range(355, 392): SRC[n] = cv2.imread(V + f'fxm6/{n:04d}.png')
for n in range(392, 466): SRC[n] = cv2.imread(V + f'fx/{n:04d}.png')
print('source frames', len(SRC))
p = subprocess.run(['ffmpeg', '-v', 'error', '-i', V + 'mol_slow.mp4', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
MOL = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
print('molecular slow frames', len(MOL))

# ---------- shots: (src in, src out, camera z0 -> z1, focus x, focus y, horizontal drift px) ----------
SHOTS = [(0, 61, 1.00, 1.07, 0.5, 0.50, 0), (61, 93, 1.06, 1.00, 0.5, 0.45, 0), (93, 140, 1.00, 1.06, 0.5, 0.45, 0),
         (140, 205, 1.00, 1.07, 0.5, 0.50, 0), (205, 250, 1.05, 1.00, 0.5, 0.50, -18), (250, 310, 1.00, 1.06, 0.5, 0.55, 0),
         (310, 355, 1.06, 1.00, 0.5, 0.50, 0), (0, 73, 1.00, 1.04, 0.5, 0.50, 10), (392, 466, 1.00, 1.06, 0.5, 0.50, 0),
         (466, 666, 1.00, 1.08, 0.5, 0.55, 0), (666, 690, 1.03, 1.00, 0.5, 0.45, 0), (690, 767, 1.00, 1.06, 0.5, 0.42, 0),
         (767, 853, 1.00, 1.05, 0.5, 0.50, 0)]
# timeline: (kind, id, frames) and the transition INTO each entry (kind, overlap frames)
TL = [('shot', k, SHOTS[k][1] - SHOTS[k][0]) for k in range(9)] + \
     [('comp', 'n10', 54), ('comp', 'derma', 54), ('comp', 'vitac', 54), ('comp', 'trio', 74)] + \
     [('shot', k, SHOTS[k][1] - SHOTS[k][0]) for k in (10, 11, 12)] + [('final', None, 170)]
TRS = [None, ('zoom', 8), ('whip', 8), ('leak', 14), ('whip', 8), ('leak', 14), ('zoom', 8), ('whip', 8), ('leak', 14),
       ('dissolve', 12), ('whip', 8), ('whip', 8), ('leak', 12),
       ('leak', 10), ('zoom', 6), ('whip', 8), ('dissolve', 16)]
starts, t = [], 0
for k, (_, _, n) in enumerate(TL):
    if k > 0: t -= TRS[k][1]
    starts.append(t); t += n
TOTAL = t
print('total frames', TOTAL, 'seconds', round(TOTAL / FPS, 2))


def camera(img, z, fx, fy, dx=0.0):
    cx, cy = fx * W, fy * H
    M = np.float32([[z, 0, cx * (1 - z) + dx], [0, z, cy * (1 - z)]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


# ---------- slogan-only end card ----------
def slogan_mask():
    f = ImageFont.truetype(R + 'fonts/Cormorant-Italic.ttf', 96)
    s1, s2 = 'Pamper your skin', 'with PalmCare.'
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.text(((W - f.getlength(s1)) / 2, 830), s1, font=f, fill=255)
    d.text(((W - f.getlength(s2)) / 2, 950), s2, font=f, fill=255)
    return cv2.GaussianBlur(np.asarray(im).astype(np.float32) / 255, (0, 0), 0.6)


TX = slogan_mask()
GOLD = (np.array([0.40, 0.70, 0.88], np.float32) * (1 - np.linspace(0, 1, H)[:, None, None]) +
        np.array([0.16, 0.38, 0.58], np.float32) * np.linspace(0, 1, H)[:, None, None])
CL = (0.5 + 0.5 * np.exp(-(((XX - 540) / 640) ** 2 + ((YY - 940) / 700) ** 2)))[..., None]
CARD_BG = np.array([0.86, 0.93, 0.98], np.float32) * CL + np.array([0.55, 0.70, 0.83], np.float32) * (1 - CL)


def card_frame(f):
    fr = CARD_BG.copy()
    a = eo((f - 8) / 22)
    z = 1.04 - 0.04 * eo(f / CARD_N)                                    # slow settle
    m = camera(TX[..., None].repeat(3, 2), z, 0.5, 0.49)[..., 0] * a
    sx = -300 + (W + 600) * ease((f - 26) / 30)                         # one soft shimmer sweep across the letters
    sh = np.exp(-(((XX - sx) - (YY - 950) * 0.35) / 90) ** 2)[..., None] * 0.55
    gold = np.clip(GOLD + sh, 0, 1)
    fr = fr * (1 - m[..., None]) + gold * m[..., None]
    return fr



# ---------- studio set (the soft window-lit wall of the Flow serum clip) for the REAL serum boxes + bottles ----------
_c5 = cv2.imread(R + 'v22/qa/c5_trio.png').astype(np.float32) / 255
_wall = cv2.GaussianBlur(cv2.resize(_c5[0:440], (W, 1240), interpolation=cv2.INTER_CUBIC), (0, 0), 2)
_floor = cv2.GaussianBlur(_wall[::-1][:H - 1240], (0, 0), 6) * 0.55 + np.array([0.93, 0.93, 0.94], np.float32) * 0.45
_floor = _floor * (1 - 0.12 * np.linspace(0, 1, H - 1240)[:, None, None])
STUDIO = np.concatenate([_wall, _floor], 0)
STUDIO[1232:1250] = cv2.GaussianBlur(STUDIO[1222:1260], (0, 0), 4)[10:28]


def _load(path):
    a = cv2.imread(R + path, cv2.IMREAD_UNCHANGED)
    if a.shape[2] == 3:
        al = np.full(a.shape[:2], 255, np.uint8); al[0, :] = al[-1, :] = al[:, 0] = al[:, -1] = 128
        a = np.dstack([a, al])
    return a.astype(np.float32) / 255


PH = {'n10_box': _load('remo/public/p/n10_real_final.png'), 'derma_box': _load('remo/public/p/dermaluxe_box_final.png'),
      'vitac_box': _load('remo/public/p/vitac_real_final.png'), 'n10_b': _load('v5/assets/bottle_n10.png'),
      'derma_b': _load('v5/assets/bottle_dl.png'), 'vitac_b': _load('v5/assets/bottle_vitac.png')}
_CACHE = {}


def sized(key, h):
    k = (key, int(h))
    if k not in _CACHE:
        a = PH[key]; w = max(2, int(round(h * a.shape[1] / a.shape[0])))
        sm = cv2.resize(a, (w, int(h)), interpolation=cv2.INTER_AREA)
        sm[..., :3] = np.clip(0.02 + sm[..., :3] * np.array([0.97, 0.985, 1.0], np.float32) * 0.96, 0, 1)
        _CACHE[k] = sm
    return _CACHE[k]


def over(dst, rgb, a, x0, y0):
    h, w = a.shape
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if X1 <= X0 or Y1 <= Y0: return
    sa = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None]
    dst[Y0:Y1, X0:X1] = dst[Y0:Y1, X0:X1] * (1 - sa) + rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * sa


def stand(frame, key, cx, base, h, alpha=1.0, lift=0.0):
    a = sized(key, h); hh, ww = a.shape[:2]
    rgb, al = a[..., :3], a[..., 3] * alpha
    x0, y0 = int(round(cx - ww / 2)), int(round(base - hh - lift))
    sh = np.zeros((90, int(ww * 1.6)), np.float32)
    cv2.ellipse(sh, (sh.shape[1] // 2, 45), (int(ww * 0.56), 14), 0, 0, 360, 1.0, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 10) * 0.5 * alpha * max(0.0, 1 - lift / 120)
    over(frame, np.zeros(sh.shape + (3,), np.float32) + 0.33, sh, int(cx - sh.shape[1] / 2), int(base - 45))
    rh = int(hh * 0.45)
    fl = cv2.GaussianBlur(rgb[::-1][:rh], (0, 0), 1.6)
    fa = al[::-1][:rh] * np.linspace(0.36, 0, rh)[:, None]
    over(frame, fl, fa, x0, int(base + lift))
    over(frame, rgb, al, x0, y0)


def comp_frame(kind, f, n):
    fr = STUDIO.copy()
    sw = -0.3 + 1.6 * f / max(1, n)                                     # soft window light drifting across the wall
    band = np.exp(-(((XX / W) * 0.6 - (YY / H) * 0.4 - sw + 0.2) / 0.12) ** 2)[..., None] * 0.10
    fr = 1 - (1 - fr) * (1 - band)
    if kind == 'trio':
        for k, key in enumerate(('n10', 'derma', 'vitac')):
            e = eo((f - k * 3) / 12)
            stand(fr, key + '_box', 195 + 345 * k, 1330, 560, alpha=min(1, e * 1.4), lift=(1 - e) * 70)
        for k, key in enumerate(('n10', 'derma', 'vitac')):
            e = eo((f - 4 - k * 3) / 12)
            stand(fr, key + '_b', 268 + 345 * k, 1395, 372 if key != 'n10' else 345, alpha=min(1, e * 1.4), lift=(1 - e) * 90)
        z = 1.0 + 0.07 * ease(f / max(1, n - 1)); return camera(fr, z, 0.5, 0.6)
    e = eo(f / 12)
    stand(fr, kind + '_box', 415, 1470, 1000, alpha=min(1, f / 3), lift=(1 - e) * 80)
    e2 = eo((f - 5) / 12)
    stand(fr, kind + '_b', 770, 1550, 640 if kind != 'n10' else 600, alpha=min(1, max(0, f - 5) / 3), lift=(1 - e2) * 130)
    z = 1.04 + 0.06 * ease(f / max(1, n - 1)); return camera(fr, z, 0.52, 0.62)


# ---------- finale: the REAL photo of the whole range + slogan ----------
_G = cv2.imread(V26 + 'group_clean.png').astype(np.float32) / 255
_G = np.clip((_G - 0.02) * np.array([0.97, 1.0, 1.04], np.float32) * 1.03, 0, 1)        # light warm polish
_gh, _gw = _G.shape[:2]
_bs = H / _gh
_big = cv2.resize(_G, (int(_gw * _bs), H), interpolation=cv2.INTER_AREA)
_x = (_big.shape[1] - W) // 2
FBG = cv2.GaussianBlur(_big[:, _x:_x + W], (0, 0), 38) * np.array([0.52, 0.56, 0.62], np.float32)
_fm = np.zeros((_gh, _gw), np.float32); _fm[30:-30, 8:-8] = 1; _FM = cv2.GaussianBlur(_fm, (0, 0), 26)


def slogan_mask2():
    f = ImageFont.truetype(R + 'fonts/Cormorant-Italic.ttf', 100)
    s1, s2 = 'Pamper your skin', 'with PalmCare.'
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.text(((W - f.getlength(s1)) / 2, 395), s1, font=f, fill=255)
    d.text(((W - f.getlength(s2)) / 2, 520), s2, font=f, fill=255)
    return cv2.GaussianBlur(np.asarray(im).astype(np.float32) / 255, (0, 0), 0.6)


TX2 = slogan_mask2()
TX2S = cv2.GaussianBlur(TX2, (0, 0), 9)


def final_frame(f):
    fr = FBG.copy()
    p = eo(f / 80)
    s = (W / _gw) * (1.42 - 0.42 * p)                                   # starts close on the range, pulls back to all of it
    cx, cy = 540, 1075 - 40 * (1 - p)
    M = np.float32([[s, 0, cx - s * _gw / 2], [0, s, cy - s * _gh / 2]])
    fg = cv2.warpAffine(_G, M, (W, H), flags=cv2.INTER_CUBIC)
    m = cv2.warpAffine(_FM, M, (W, H))[..., None]
    sx = -400 + (W + 800) * ease((f - 30) / 50)                         # one soft light pass over the products
    sweep = np.exp(-(((XX - sx) + (YY - 1000) * 0.4) / 120) ** 2)[..., None] * 0.18 * m
    fr = fr * (1 - m) + fg * m
    fr = 1 - (1 - fr) * (1 - sweep)
    a = eo((f - 45) / 25)
    if a > 0:
        fr = fr * (1 - TX2S[..., None] * 0.35 * a)
        sh = np.exp(-(((XX - (-200 + 1500 * ease((f - 75) / 35))) - (YY - 500) * 0.35) / 80) ** 2)[..., None] * 0.5
        gold = np.clip(GOLD + sh, 0, 1)
        fr = fr * (1 - TX2[..., None] * a) + gold * TX2[..., None] * a
    return fr


def shot_frame(k, f):
    kind, sid, n = TL[k]
    if kind == 'card': return card_frame(f)
    if kind == 'comp': return comp_frame(sid, max(0, f), n)
    if kind == 'final': return END.end_frame(f, 170)
    a, b, z0, z1, fx, fy, dx = SHOTS[sid]
    arr = MOL if sid == 7 else SRC                                      # Molecular Glow: slow-motion take
    img = arr[a + max(0, min(f, n - 1))].astype(np.float32) / 255
    e = ease(f / max(1, n - 1))
    return camera(img, z0 + (z1 - z0) * e, fx, fy, dx * (e - 0.5) * 2)


def hblur(img, amt):
    k = max(1, int(amt)) | 1
    return cv2.blur(img, (k, 1)) if k > 1 else img


def transition(kind, A, B, u, d):
    """A outgoing, B incoming, u in [0,1], d = whip direction"""
    if kind == 'whip':
        e = ease(u)
        a = np.roll(hblur(A, 90 * math.sin(math.pi * min(1, u * 1.4))), -int(e * W * 0.4 * d), axis=1)
        b = np.roll(hblur(B, 90 * math.sin(math.pi * max(0, u * 1.4 - 0.4))), int((1 - e) * W * 0.4 * d), axis=1)
        m = ease((u - 0.35) / 0.3)
        return a * (1 - m) + b * m
    if kind == 'zoom':
        e = ease(u)
        a = camera(A, 1 + 0.30 * e, 0.5, 0.5); b = camera(B, 1.22 - 0.22 * e, 0.5, 0.5)
        bl = 0.5 + 12 * math.sin(math.pi * u)
        a = cv2.GaussianBlur(a, (0, 0), bl); b = cv2.GaussianBlur(b, (0, 0), bl * 0.8)
        m = ease((u - 0.3) / 0.4)
        return a * (1 - m) + b * m
    if kind == 'leak':
        e = ease(u)
        x = A * (1 - e) + B * e
        cx = W * (0.1 + 0.8 * u)
        leak = np.exp(-(((XX - cx) / 560) ** 2 + ((YY - H * 0.35) / 950) ** 2))[..., None]
        s = math.sin(math.pi * u)
        warm = np.array([0.50, 0.76, 1.0], np.float32)
        return 1 - (1 - x) * (1 - leak * warm * 0.8 * s)
    e = ease(u)                                                         # bloom dissolve
    x = A * (1 - e) + B * e
    s = math.sin(math.pi * u) * 0.28
    return x + (cv2.GaussianBlur(x, (0, 0), 28) - x * 0.5) * s


VIG = (1 - 0.12 * np.clip(((XX - W / 2) / (W * 0.75)) ** 2 + ((YY - H * 0.47) / (H * 0.7)) ** 2, 0, 1.4) ** 1.5)[..., None]

wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-an', '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'medium' if PREVIEW else 'slow', '-crf', '20' if PREVIEW else '14',
                       '-pix_fmt', 'yuv420p'] + (['-vf', 'scale=540:960'] if PREVIEW else []) + ['-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for fi in range(TOTAL):
    act = [k for k in range(len(TL)) if starts[k] <= fi < starts[k] + TL[k][2]]
    if len(act) == 1:
        img = shot_frame(act[0], fi - starts[act[0]])
    else:
        ka, kb = act[0], act[1]
        u = (fi - starts[kb] + 0.5) / TRS[kb][1]
        img = transition(TRS[kb][0], shot_frame(ka, fi - starts[ka]), shot_frame(kb, fi - starts[kb]), u, 1 if kb % 2 else -1)
    img = img * VIG
    img = img + rng.normal(0, 0.008, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
    wr.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if fi % 120 == 0: print('frame', fi, flush=True)
wr.stdin.close(); wr.wait(); print('done', OUT, TOTAL)
