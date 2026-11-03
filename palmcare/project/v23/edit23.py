"""PalmCare collection, user's cut (silent, 1080x1920, 30 fps).
Real labels locked onto Molecular Glow (frames 355-391) and Dermalight (392-465). Every shot gets a camera move; every
cut becomes a realistic transition (motion-blurred whip pans, zoom-throughs, warm light leaks, bloom dissolves).
Ends on a slogan-only card. Usage: edit23.py OUT.mp4 [preview]"""
import math, subprocess, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
V = R + 'v23/'
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
for n in range(355, 392): SRC[n] = cv2.imread(V + f'fxm/{n:04d}.png')
for n in range(392, 466): SRC[n] = cv2.imread(V + f'fx/{n:04d}.png')
print('source frames', len(SRC))

# ---------- shots: (src in, src out, camera z0 -> z1, focus x, focus y, horizontal drift px) ----------
SHOTS = [(0, 61, 1.00, 1.07, 0.5, 0.50, 0), (61, 93, 1.06, 1.00, 0.5, 0.45, 0), (93, 140, 1.00, 1.06, 0.5, 0.45, 0),
         (140, 205, 1.00, 1.07, 0.5, 0.50, 0), (205, 250, 1.05, 1.00, 0.5, 0.50, -18), (250, 310, 1.00, 1.06, 0.5, 0.55, 0),
         (310, 355, 1.06, 1.00, 0.5, 0.50, 0), (355, 392, 1.00, 1.05, 0.5, 0.50, 16), (392, 466, 1.00, 1.06, 0.5, 0.50, 0),
         (466, 666, 1.00, 1.08, 0.5, 0.55, 0), (666, 690, 1.03, 1.00, 0.5, 0.45, 0), (690, 767, 1.00, 1.06, 0.5, 0.42, 0),
         (767, 853, 1.00, 1.05, 0.5, 0.50, 0)]
CARD_N = 75
# transition INTO shot k (k>=1), and the end card: (kind, overlap frames)
TRS = [None, ('zoom', 8), ('whip', 8), ('leak', 14), ('whip', 8), ('leak', 14), ('zoom', 8), ('whip', 8), ('leak', 14),
       ('dissolve', 12), ('leak', 10), ('zoom', 6), ('whip', 8), ('dissolve', 16)]
TL = [('shot', k, b - a) for k, (a, b, *_) in enumerate(SHOTS)] + [('card', None, CARD_N)]
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


def shot_frame(k, f):
    kind, sid, n = TL[k]
    if kind == 'card': return card_frame(f)
    a, b, z0, z1, fx, fy, dx = SHOTS[sid]
    img = SRC[a + max(0, min(f, n - 1))].astype(np.float32) / 255
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
