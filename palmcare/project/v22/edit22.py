"""PalmCare collection edit from the user's seven Flow clips (silent, 1080x1920, 30 fps).
Clean shots only (label errors cut: Cacao ribbon-over-label, Molecular solo with the Citrus label, Dermalight wrong label
+ cream drip, Vitamin C box side panel and garbled tagline -> real box art locked on, serum clip with invented bottles).
Dermalight and the three serums are built from the REAL product photographs on a studio set lifted from the clip-5 wall
(soft window light, glossy white floor). Every shot gets its own camera move; cuts use realistic transitions: whip pans
with motion blur, light-leak dissolves, zoom-throughs and bloom dissolves. One grade + fine grain over everything.
Usage: edit22.py OUT.mp4 [preview]"""
import math, subprocess, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
V = R + 'v22/'
W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1]
PREVIEW = len(sys.argv) > 2
rng = np.random.default_rng(22)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def ease(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def eo(x):
    x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 3


# ---------- footage shots: (seg file, use frames [a,b), camera z0->z1, focus x,y, drift dx) ----------
CLIP = {
    's01': (0, 28, 1.10, 1.00, 0.5, 0.45, 0), 's02': (0, 60, 1.00, 1.08, 0.5, 0.6, 0), 's03': (0, 29, 1.0, 1.06, 0.5, 0.5, -20),
    's04': (0, 42, 1.0, 1.07, 0.5, 0.5, 0), 's05': (0, 36, 1.06, 1.0, 0.5, 0.4, 0), 's06': (0, 27, 1.0, 1.06, 0.5, 0.5, 15),
    's07': (0, 21, 1.04, 1.0, 0.5, 0.5, -15), 's08': (0, 59, 1.0, 1.08, 0.5, 0.55, 0), 's09': (0, 40, 1.05, 1.0, 0.5, 0.45, 0),
    's10': (0, 46, 1.0, 1.07, 0.5, 0.5, 0), 's11': (0, 57, 1.0, 1.06, 0.5, 0.5, 0), 's16': (0, 66, 1.0, 1.07, 0.5, 0.45, 0),
    's17': (0, 39, 1.30, 1.40, 0.5, 0.48, 0),
}
# ---------- timeline: (kind, id, frames, transition INTO this shot) ----------
TL = [('clip', 's01', 28, None), ('clip', 's02', 60, 'whip'), ('clip', 's03', 29, 'zoom'), ('clip', 's04', 42, 'leak'),
      ('clip', 's05', 36, 'whip'), ('clip', 's06', 27, 'dissolve'), ('clip', 's07', 21, 'zoom'),
      ('clip', 's08', 59, 'leak'), ('clip', 's09', 40, 'whip'), ('clip', 's10', 46, 'zoom'),
      ('clip', 's11', 57, 'leak'), ('comp', 'dermalight', 42, 'whip'),
      ('comp', 'n10', 36, 'leak'), ('comp', 'derma', 36, 'whip'), ('comp', 'vitac', 36, 'whip'),
      ('clip', 's16', 66, 'leak'), ('clip', 's17', 39, 'zoom'), ('comp', 'group', 66, 'leak'), ('brand', None, 42, 'dissolve')]
TR = {'whip': 8, 'zoom': 8, 'leak': 12, 'dissolve': 10}
starts, t = [], 0
for k, (_, _, n, tr) in enumerate(TL):
    if k > 0:
        t -= TR[tr] // 2                                  # transitions overlap half into each shot
    starts.append(t)
    t += n
TOTAL = t
print('total frames', TOTAL, 'seconds', TOTAL / FPS)


def read_seg(name):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', V + f'segs/{name}.mp4', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
    return a


SEG = {k: read_seg(k) for k in CLIP}

# ---------- studio set from the clip-5 wall ----------
c5 = cv2.imread(V + 'qa/c5_trio.png').astype(np.float32) / 255          # 720x1280
wall = c5[0:440]
wall = cv2.resize(wall, (W, 1240), interpolation=cv2.INTER_CUBIC)
wall = cv2.GaussianBlur(wall, (0, 0), 2)
floor = cv2.GaussianBlur(wall[::-1][:H - 1240], (0, 0), 6) * 0.55 + np.array([0.93, 0.93, 0.94], np.float32) * 0.45
g = np.linspace(0, 1, H - 1240)[:, None, None]
floor = floor * (1 - 0.12 * g)
STUDIO = np.concatenate([wall, floor], 0)
STUDIO[1232:1250] = cv2.GaussianBlur(STUDIO[1222:1260], (0, 0), 4)[10:28]
HORIZON = 1240


def load(name):
    a = cv2.imread(R + name, cv2.IMREAD_UNCHANGED)
    if a.shape[2] == 3:
        al = np.full(a.shape[:2], 255, np.uint8); al[0, :] = al[-1, :] = al[:, 0] = al[:, -1] = 128
        a = np.dstack([a, al])
    return a.astype(np.float32) / 255


PH = {'dermalight': load('remo/public/p/dermalight_cut.png'), 'n10_box': load('remo/public/p/n10_real_final.png'),
      'derma_box': load('remo/public/p/dermaluxe_box_final.png'), 'vitac_box': load('remo/public/p/vitac_real_final.png'),
      'n10_b': load('v5/assets/bottle_n10.png'), 'derma_b': load('v5/assets/bottle_dl.png'), 'vitac_b': load('v5/assets/bottle_vitac.png'),
      'milky': load('remo/public/p/milky.png'), 'cacao': load('remo/public/p/cacao.png'), 'citrus': load('remo/public/p/citrus_cut.png'),
      'molecular': load('remo/public/p/molecular_cut.png'), 'tropical': load('remo/public/p/tropical_cut.png'),
      'glow_box': load('remo/public/p/glowshield_box_flat.png'), 'vitc_box': load('remo/public/p/box_straight.png')}
CACHE = {}


def sized(key, h):
    k = (key, int(h))
    if k not in CACHE:
        a = PH[key]
        w = max(2, int(round(h * a.shape[1] / a.shape[0])))
        s = cv2.resize(a, (w, int(h)), interpolation=cv2.INTER_AREA)
        s[..., :3] = np.clip(0.03 + s[..., :3] * np.array([0.97, 0.985, 1.0], np.float32) * 0.95, 0, 1)   # studio match
        CACHE[k] = s
    return CACHE[k]


def over(dst, rgb, a, x0, y0):
    h, w = a.shape
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if X1 <= X0 or Y1 <= Y0: return
    sa = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None]
    dst[Y0:Y1, X0:X1] = dst[Y0:Y1, X0:X1] * (1 - sa) + rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * sa


def stand(frame, key, cx, base, h, alpha=1.0, lift=0.0):
    a = sized(key, h)
    hh, ww = a.shape[:2]
    rgb, al = a[..., :3], a[..., 3] * alpha
    x0, y0 = int(round(cx - ww / 2)), int(round(base - hh - lift))
    sh = np.zeros((70, int(ww * 1.5)), np.float32)
    cv2.ellipse(sh, (sh.shape[1] // 2, 35), (int(ww * 0.55), 12), 0, 0, 360, 1.0, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 8) * 0.45 * alpha * max(0.0, 1 - lift / 120)
    over(frame, np.zeros(sh.shape + (3,), np.float32) + 0.35, sh, int(cx - sh.shape[1] / 2), int(base - 35))
    rh = int(hh * 0.45)
    fl = cv2.GaussianBlur(rgb[::-1][:rh], (0, 0), 1.5)
    fa = al[::-1][:rh] * np.linspace(0.38, 0, rh)[:, None]
    over(frame, fl, fa, x0, int(base + lift))
    over(frame, rgb, al, x0, y0)


def studio_frame(kind, f, n):
    fr = STUDIO.copy()
    sw = -0.3 + 1.6 * f / max(1, n)                                   # slow window-light drift across the wall
    band = np.exp(-(((XX / W) * 0.6 - (YY / H) * 0.4 - sw + 0.2) / 0.12) ** 2)[..., None] * 0.10
    fr = 1 - (1 - fr) * (1 - band)
    ein = eo(f / 12)
    if kind == 'dermalight':
        stand(fr, 'dermalight', 540, 1330, 900, alpha=min(1, f / 3), lift=(1 - ein) * 160)
    elif kind in ('n10', 'derma', 'vitac'):
        stand(fr, kind + '_box', 430, 1300, 760, alpha=min(1, f / 3), lift=(1 - ein) * 90)
        e2 = eo((f - 4) / 12)
        stand(fr, kind + '_b', 720, 1380, 560 if kind != 'n10' else 520, alpha=min(1, max(0, f - 4) / 3), lift=(1 - e2) * 140)
    elif kind == 'group':
        rp = eo(f / 8)
        x0r, x1r, y0r, y1r = 150, 930, 1270, 1560
        fr[y0r:y1r, x0r:x1r] = fr[y0r:y1r, x0r:x1r] * (1 - 0.08 * rp) + 0.97 * 0.08 * rp
        fr[y0r - 2:y0r + 2, x0r:x1r] = fr[y0r - 2:y0r + 2, x0r:x1r] * (1 - 0.6 * rp) + 0.99 * 0.6 * rp
        back = [('n10_box', -282), ('vitac_box', -96), ('derma_box', 96), ('glow_box', 276)]
        for k, (key, dx) in enumerate(back):
            a_ = eo((f - k * 2) / 8)
            if a_ > 0: stand(fr, key, 540 + dx, 1270, 320, alpha=a_, lift=(1 - a_) * 50)
        front = [('milky', -452, 310), ('cacao', -322, 310), ('citrus', -200, 304), ('vitc_box', 0, 204),
                 ('molecular', 200, 304), ('tropical', 322, 310), ('dermalight', 450, 304)]
        for k, (key, dx, h) in enumerate(front):
            a_ = eo((f - 3 - abs(k - 3) * 2) / 8)
            if a_ > 0: stand(fr, key, 540 + dx, 1580, h, alpha=a_, lift=(1 - a_) * 60)
    return fr


def camera(img, z, fx, fy, dx=0.0):
    cx, cy = fx * W, fy * H
    M = np.float32([[z, 0, cx * (1 - z) + dx], [0, z, cy * (1 - z)]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def text_layers():
    FD = R + 'fonts/'
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FD + 'Cormorant-SemiBold.ttf', 132); f2 = ImageFont.truetype(FD + 'Cormorant-Italic.ttf', 70)
    word, track = 'PALMCARE', 30
    tw = sum(f1.getlength(c) for c in word) + track * (len(word) - 1); x = (W - tw) / 2
    for c in word:
        d.text((x, 790), c, font=f1, fill=255); x += f1.getlength(c) + track
    m1 = np.asarray(im).astype(np.float32) / 255
    im2 = Image.new('L', (W, H), 0); d2 = ImageDraw.Draw(im2)
    s = 'Pamper your skin with PalmCare.'
    d2.text(((W - f2.getlength(s)) / 2, 1005), s, font=f2, fill=255)
    return m1, np.asarray(im2).astype(np.float32) / 255


TX1, TX2 = text_layers()
GOLD = (np.array([0.36, 0.67, 0.85], np.float32) * (1 - np.linspace(0, 1, H)[:, None, None]) +
        np.array([0.13, 0.33, 0.49], np.float32) * np.linspace(0, 1, H)[:, None, None])


def brand_frame(f):
    cl = 0.5 + 0.5 * np.exp(-(((XX - 540) / 620) ** 2 + ((YY - 940) / 640) ** 2))[..., None]
    fr = np.array([0.82, 0.91, 0.97], np.float32) * cl + np.array([0.45, 0.64, 0.80], np.float32) * (1 - cl)
    a1, a2 = eo((f - 4) / 10), eo((f - 9) / 10)
    fr = fr * (1 - TX1[..., None] * a1) + GOLD * TX1[..., None] * a1
    fr = fr * (1 - TX2[..., None] * a2) + GOLD * 0.75 * TX2[..., None] * a2
    lw = int(170 * a2)
    if lw > 0: fr[968:970, 540 - lw:540 + lw] = np.array([0.18, 0.53, 0.72], np.float32)
    return fr


def shot_frame(k, f):
    kind, sid, n, _ = TL[k]
    p = f / max(1, n - 1)
    if kind == 'clip':
        a, b, z0, z1, fx, fy, dx = CLIP[sid]
        arr = SEG[sid]
        img = arr[min(len(arr) - 1, a + max(0, min(f, n - 1)))].astype(np.float32) / 255
        e = ease(p)
        return camera(img, z0 + (z1 - z0) * e, fx, fy, dx * (e - 0.5) * 2)
    if kind == 'comp':
        img = studio_frame(sid, max(0, f), n)
        z0, dz, fy = {'group': (1.0, 0.03, 0.78), 'dermalight': (1.12, 0.06, 0.62)}.get(sid, (1.22, 0.06, 0.66))
        return camera(img, z0 + dz * ease(p), 0.5, fy)
    return brand_frame(f)


def grade(img):
    x = img * np.array([0.985, 1.0, 1.015], np.float32)
    x = 0.015 + x * 0.985
    return x


VIG = (1 - 0.18 * np.clip(((XX - W / 2) / (W * 0.75)) ** 2 + ((YY - H * 0.47) / (H * 0.7)) ** 2, 0, 1.4) ** 1.5)[..., None]


def hblur(img, amt):
    k = max(1, int(amt)) | 1
    return cv2.blur(img, (k, 1))


def transition(kind, A, B, u, d):
    """A outgoing, B incoming, u in [0,1]; d = direction"""
    if kind == 'whip':
        e = ease(u)
        sh = int(e * W * 0.35 * d)
        a = np.roll(hblur(A, 60 * math.sin(math.pi * min(1, u * 1.3))), -sh, axis=1)
        b = np.roll(hblur(B, 60 * math.sin(math.pi * max(0, u * 1.3 - 0.3))), int((1 - e) * W * 0.35 * d), axis=1)
        m = np.clip((u - 0.35) / 0.3, 0, 1)
        return a * (1 - m) + b * m
    if kind == 'zoom':
        e = ease(u)
        za = 1 + 0.35 * e; zb = 1.25 - 0.25 * e
        a = camera(A, za, 0.5, 0.5); b = camera(B, zb, 0.5, 0.5)
        bl = 1 + 14 * math.sin(math.pi * u)
        a = cv2.GaussianBlur(a, (0, 0), bl); b = cv2.GaussianBlur(b, (0, 0), bl * 0.8)
        m = np.clip((u - 0.3) / 0.4, 0, 1)
        return a * (1 - m) + b * m
    if kind == 'leak':
        e = ease(u)
        x = A * (1 - e) + B * e
        cx = W * (0.15 + 0.7 * u)
        leak = np.exp(-(((XX - cx) / 520) ** 2 + ((YY - H * 0.35) / 900) ** 2))[..., None]
        s = math.sin(math.pi * u)
        warm = np.array([0.55, 0.78, 1.0], np.float32)
        return 1 - (1 - x) * (1 - leak * warm * 0.85 * s) + 0.0
    # dissolve with a soft bloom
    e = ease(u)
    x = A * (1 - e) + B * e
    s = math.sin(math.pi * u) * 0.25
    return x + (cv2.GaussianBlur(x, (0, 0), 25) - x * 0.5) * s


wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-an', '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'medium' if PREVIEW else 'slow', '-crf', '20' if PREVIEW else '13',
                       '-pix_fmt', 'yuv420p'] + (['-vf', 'scale=540:960'] if PREVIEW else []) + ['-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for fi in range(TOTAL):
    act = [k for k in range(len(TL)) if starts[k] <= fi < starts[k] + TL[k][2]]
    if len(act) == 1:
        k = act[0]
        img = shot_frame(k, fi - starts[k])
    else:
        ka, kb = act[0], act[1]
        tr = TL[kb][3]
        d0 = TR[tr]
        u = (fi - starts[kb]) / max(1, (starts[ka] + TL[ka][2]) - starts[kb])
        img = transition(tr, shot_frame(ka, fi - starts[ka]), shot_frame(kb, fi - starts[kb]), u, 1 if kb % 2 else -1)
    img = grade(img) * VIG
    img = img + rng.normal(0, 0.011, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
    wr.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    if fi % 60 == 0: print('frame', fi, flush=True)
wr.stdin.close(); wr.wait(); print('done', OUT, TOTAL)
