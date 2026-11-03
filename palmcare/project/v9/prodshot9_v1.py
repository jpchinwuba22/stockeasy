"""Video 6 product scenes, built ONLY from the real, straightened box and jar photos (uniform scale + translation only:
never rotated, sheared or warped). A peach studio with a glossy plinth, citrus-droplet bokeh from the hook clip, soft
contact shadows and true mirror reflections.
  reveal  : the box rises in, the jar drops in beside it, both land with a light ripple; a slow push-in, a light sweep
            and a glint on the gold collar.
  pair    : a short cutaway of both (slow drift, rack focus) for the application section.
  jar     : the jar alone, large and centred, slow push-in with rising dew droplets (ingredients are drawn by the overlay).
Usage: prodshot9.py OUT(.mp4|.jpg) MODE DURATION"""
import math
import subprocess
import sys

import cv2
import numpy as np

W, H, FPS = 1080, 1920, 24
OUT, MODE, DUR = sys.argv[1], sys.argv[2], float(sys.argv[3])
N = int(round(DUR * FPS))
D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v9/"
rng = np.random.default_rng(9)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def ebounce(x):
    """Ease-out with one soft settle (a landing)."""
    x = c01(x)
    return 1 - (1 - x) ** 3 * math.cos(x * math.pi * 1.5)


def load(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    rgb = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2RGB)
    a = im[..., 3:4]
    return np.dstack([rgb * a, a])                       # premultiplied


BOX, JAR = load(D + "box_straight.png"), load(D + "jar_cut.png")


def scaled(pm, h):
    w = max(1, round(pm.shape[1] * h / pm.shape[0]))
    return cv2.resize(pm, (w, max(1, round(h))), interpolation=cv2.INTER_AREA if h < pm.shape[0] else cv2.INTER_CUBIC)


def place(out, pm, cx, base, alpha=1.0, refl=True, floor_a=1.0):
    """Composite a premultiplied cut-out standing on y=base, centred on cx; contact shadow + mirror reflection."""
    h, w = pm.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(base - h))
    # contact shadow
    sh = np.exp(-(((XX - cx) / (w * 0.52)) ** 2 + ((YY - base - 4) / 16) ** 2)) * 0.45 * alpha * floor_a
    out *= (1 - sh[..., None] * np.array([0.55, 0.62, 0.7], np.float32))
    if refl and floor_a > 0:
        r = pm[::-1][: int(h * 0.45)]
        fade = (np.linspace(1, 0, r.shape[0]) ** 1.8 * 0.22 * alpha * floor_a)[:, None, None]
        comp(out, r * fade, x0, int(round(base + 2)))
    comp(out, pm * alpha, x0, y0)


def comp(out, pm, x0, y0):
    h, w = pm.shape[:2]
    xs, ys, xe, ye = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xe <= xs or ye <= ys:
        return
    p = pm[ys - y0:ye - y0, xs - x0:xe - x0]
    out[ys:ye, xs:xe] = p[..., :3] + out[ys:ye, xs:xe] * (1 - p[..., 3:4])


# ---------- the studio ----------
cap = cv2.VideoCapture(D + "src/C1.mp4")
cap.set(cv2.CAP_PROP_POS_FRAMES, int(7.0 * 24))
plate = cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2RGB)
plate = cv2.resize(plate, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255
BASE_Y = 1640 if MODE != "jar" else 1500
top, bot = np.array([252, 232, 212], np.float32) / 255, np.array([244, 198, 160], np.float32) / 255
grad = top * (1 - (YY / H)[..., None]) + bot * (YY / H)[..., None]
glow = np.exp(-(((XX - W * 0.62) / 620) ** 2 + ((YY - 700) / 640) ** 2))[..., None] * np.array([1.0, 0.86, 0.66], np.float32) * 0.22


def studio(t, blur):
    b = cv2.GaussianBlur(plate, (0, 0), blur)
    bg = grad * 0.78 + b * 0.30 + glow
    floor = np.clip((YY - BASE_Y) / 3 + 0.5, 0, 1)[..., None]
    fl = np.array([238, 186, 146], np.float32) / 255 * (1 - 0.18 * np.clip((YY - BASE_Y) / 360, 0, 1))[..., None]
    out = bg * (1 - floor) + fl * floor
    out += np.exp(-((YY - BASE_Y - 1) / 2.0) ** 2)[..., None] * 0.10      # plinth lip highlight
    return np.clip(out, 0, 1)


DROPS = [(rng.uniform(60, W - 60), rng.uniform(300, BASE_Y - 80), rng.uniform(4, 12), rng.uniform(0, 6.28)) for _ in range(26)]


def droplets(out, t, rise=30.0):
    for x, y, r, ph in DROPS:
        yy = y - (t * rise + ph * 40) % 900 + 300
        xx = x + 10 * math.sin(ph + t * 0.9)
        x0, x1, y0, y1 = int(max(0, xx - 3 * r)), int(min(W, xx + 3 * r)), int(max(0, yy - 3 * r)), int(min(H, yy + 3 * r))
        if x1 > x0 and y1 > y0:
            dd = np.exp(-(((XX[y0:y1, x0:x1] - xx) ** 2 + (YY[y0:y1, x0:x1] - yy) ** 2) / (2 * r * r)))[..., None]
            out[y0:y1, x0:x1] = 1 - (1 - out[y0:y1, x0:x1]) * (1 - dd * 0.35 * np.array([1, 0.92, 0.75], np.float32))


def sweep(out, mask, q, x0, w):
    if 0 < q < 1:
        pos = -300 + eio(q) * (w + 900)
        band = np.exp(-((((XX - x0) + (YY - 900) * 0.45) - pos) / 70) ** 2) * math.sin(math.pi * q) * 0.55
        out[:] = 1 - (1 - out) * (1 - (band * mask)[..., None])


def glint(out, gx, gy, s):
    if s <= 0:
        return
    st = (np.exp(-((XX - gx) / 3) ** 2 - ((YY - gy) / (70 * s + 1)) ** 2) + np.exp(-((YY - gy) / 3) ** 2 - ((XX - gx) / (70 * s + 1)) ** 2)) * s
    out[:] = 1 - (1 - out) * (1 - st[..., None] * 0.9)


def mask_of(pm, cx, base):
    m = np.zeros((H, W), np.float32)
    h, w = pm.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(base - h))
    xs, ys, xe, ye = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    m[ys:ye, xs:xe] = pm[ys - y0:ye - y0, xs - x0:xe - x0, 3]
    return m


def zoom(out, z, cx, cy):
    """Uniform camera push-in about (cx, cy)."""
    if abs(z - 1) < 1e-4:
        return out
    M = np.float32([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]])
    return cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


BOX_H, JAR_H = 700, 480                      # stacked hero: the box upright, the real jar resting on its top edge
BOX_S, JAR_S = scaled(BOX, BOX_H), scaled(JAR, JAR_H)


def with_top(pm, th=58):
    """Add the box's plain white top face in perspective (seen from slightly above, like the jar), so the jar can stand on it."""
    h, w = pm.shape[:2]
    top = np.zeros((th, w, 4), np.float32)
    yy = np.arange(th)[:, None]
    inset = (1 - yy / th) * w * 0.035
    xx = np.arange(w)[None, :]
    a = ((xx >= inset) & (xx <= w - 1 - inset)).astype(np.float32)
    shade = (0.90 + 0.07 * yy / th) * np.ones((1, w))
    col = np.array([0.985, 0.965, 0.95], np.float32)
    top[..., :3] = (shade[..., None] * col) * a[..., None]
    top[..., 3] = a
    top[-2:, :, :3] *= 0.9                                              # the front edge
    return np.vstack([top, pm])


BOX_S = with_top(BOX_S)
BOX_X = JAR_X = W / 2
JAR_BASE = BASE_Y - BOX_H - 26                                          # the jar stands on the middle of the top face
JAR_BIG = scaled(JAR, 820)


def frame(i):
    t = i / FPS
    if MODE == "reveal":
        out = studio(t, 16 - 6 * eo(t / 2.0))
        droplets(out, t)
        # the box rises in from below, the jar drops in from above and settles (motion-blurred while moving)
        acc = np.zeros_like(out)
        for k in range(3):
            tt = t - k * 0.012
            pb = eo((tt - 0.10) / 0.85)
            pj = ebounce((tt - 0.35) / 0.95)
            o = out.copy()
            if pb > 0:
                place(o, BOX_S, BOX_X, BASE_Y + (1 - pb) * 520, c01(pb * 3), floor_a=pb)
            if pj > 0:
                place(o, JAR_S, JAR_X, JAR_BASE - (1 - pj) * 700, c01(pj * 4), refl=False, floor_a=c01(pj) * 0.8)
            acc += o / 3
        out = acc
        # landing ripple on the plinth
        for land, cx, yb in ((0.95, BOX_X, BASE_Y), (1.30, JAR_X, JAR_BASE)):
            q = (t - land) / 0.9
            if 0 < q < 1:
                r = 60 + 420 * eo(q)
                ring = np.exp(-((np.sqrt((XX - cx) ** 2 + ((YY - yb) * 6) ** 2) - r) / 14) ** 2) * (1 - q) * 0.6
                out = 1 - (1 - out) * (1 - ring[..., None] * np.array([1, 0.85, 0.6], np.float32))
        m = np.maximum(mask_of(BOX_S, BOX_X, BASE_Y), mask_of(JAR_S, JAR_X, JAR_BASE))
        sweep(out, m, (t - 2.0) / 1.2, 0, W)
        gq = (t - 3.4) / 0.6
        if 0 < gq < 1:
            glint(out, JAR_X + JAR_S.shape[1] * 0.40, JAR_BASE - JAR_S.shape[0] * 0.53, math.sin(math.pi * gq))
        out = zoom(out, 1.0 + 0.05 * eio((t - 1.3) / (DUR - 1.3)), W / 2, BASE_Y - 560)
    elif MODE == "pair":
        out = studio(t, 10 + 5 * eio(t / DUR))
        droplets(out, t)
        place(out, BOX_S, BOX_X, BASE_Y)
        place(out, JAR_S, JAR_X, JAR_BASE, refl=False, floor_a=0.8)
        m = np.maximum(mask_of(BOX_S, BOX_X, BASE_Y), mask_of(JAR_S, JAR_X, JAR_BASE))
        sweep(out, m, (t - 0.3) / 1.4, 0, W)
        z = 1.10 - 0.05 * eio(t / DUR)
        out = zoom(out, z, W / 2 + 60 * (eio(t / DUR) - 0.5), BASE_Y - 560)
    else:  # jar
        out = studio(t, 14)
        droplets(out, t, rise=70.0)
        cx = W / 2
        place(out, JAR_BIG, cx, BASE_Y)
        halo = np.exp(-(((XX - cx) / 560) ** 2 + ((YY - (BASE_Y - 380)) / 560) ** 2)) * 0.18 * eo(t / 1.0)
        out = 1 - (1 - out) * (1 - halo[..., None] * np.array([1, 0.9, 0.7], np.float32))
        sweep(out, mask_of(JAR_BIG, cx, BASE_Y), (t - 0.6) / 1.6, 0, W)
        out = zoom(out, 1.0 + 0.06 * eio(t / DUR), cx, BASE_Y - 380)
    return np.clip(out * 255, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    if OUT.endswith(".jpg"):
        ts = [x * DUR for x in (0.05, 0.15, 0.25, 0.4, 0.6, 0.98)]
        ims = [cv2.resize(frame(int(t * FPS)), (360, 640), interpolation=cv2.INTER_AREA) for t in ts]
        cv2.imwrite(OUT, cv2.cvtColor(np.hstack(ims), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
        cv2.imwrite(OUT.replace(".jpg", "_last.png"), cv2.cvtColor(frame(N - 1), cv2.COLOR_RGB2BGR))
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    for i in range(N):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close()
    p.wait()
    print(MODE, N, "frames")
