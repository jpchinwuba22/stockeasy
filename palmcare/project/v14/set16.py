"""Rich product sets on the marble pedestals (plate0): the REAL jar / box cut-outs seated on the pedestal tops with
contact shadows, a soft cast shadow, warm colour match and rim light, a golden halo, a light sweep that crosses the
products, a glint on the gold collar, rising gold dust and a slow eased push-in. Nothing moves except the camera.
Usage: set16.py jar|hero OUT(.mp4|.jpg) SECONDS"""
import math
import subprocess
import sys

import cv2
import numpy as np

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
W, H, FPS = 1080, 1920, 24
MODE, OUT, DUR = sys.argv[1], sys.argv[2], float(sys.argv[3])
plate = cv2.resize(cv2.imread(D + "v13/qa/plate0.png"), (W, H)).astype(np.float32) / 255
JAR = cv2.imread(D + "v9/jar_cut.png", -1).astype(np.float32) / 255
BOX = cv2.imread(D + "v9/box_straight.png", -1).astype(np.float32) / 255
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def warm(rgba, rim_side=-1):
    x = rgba.copy()
    x[..., :3] *= np.array([0.95, 0.995, 1.045], np.float32)                 # BGR: match the warm studio light
    h, w = x.shape[:2]
    u = np.linspace(0, 1, w)[None, :]
    a = cv2.GaussianBlur(x[..., 3], (0, 0), 6)
    edge = np.clip(x[..., 3] - a, 0, 1) * 3                                   # inner edge band
    side = (1 - u) if rim_side < 0 else u
    rim = np.clip(edge * side ** 2, 0, 1)[..., None]
    x[..., :3] = x[..., :3] * (1 - rim * 0.5) + np.array([0.75, 0.92, 1.0], np.float32) * rim * 0.5
    shade = (1.03 - 0.08 * u)[..., None] if rim_side < 0 else (0.95 + 0.08 * u)[..., None]
    x[..., :3] *= shade
    return x


def place(canvas, rgba, cx, base_y, width, base_frac):
    """paste a cut-out so that its base point (bottom-centre, lifted by base_frac of its height) lands on (cx, base_y)"""
    s = width / rgba.shape[1]
    im = cv2.resize(rgba, (int(width), int(rgba.shape[0] * s)), interpolation=cv2.INTER_AREA)
    h = im.shape[0]
    x0, y0 = int(cx - width / 2), int(base_y - h * (1 - base_frac))
    a = im[..., 3:]
    canvas[y0:y0 + h, x0:x0 + im.shape[1]] = canvas[y0:y0 + h, x0:x0 + im.shape[1]] * (1 - a) + im[..., :3] * a
    m = np.zeros((H, W), np.float32)
    m[y0:y0 + h, x0:x0 + im.shape[1]] = im[..., 3]
    return (x0, y0, im.shape[1], h), m


def shadow(canvas, cx, cy, rx, ry, k=0.55, cast=1.0):
    """contact shadow (tight, dark) + soft cast shadow falling to the right-back (key light from the top left)"""
    s = np.exp(-(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2) * 3.2)
    c = np.exp(-(((XX - cx - rx * 0.45) / (rx * 1.35)) ** 2 + ((YY - cy + ry * 0.2) / (ry * 1.6)) ** 2) * 2.0) * 0.45 * cast
    ao = np.exp(-(((XX - cx) / (rx * 0.92)) ** 6 + ((YY - cy - ry * 0.15) / (ry * 0.45)) ** 2)) * 0.55   # tight occlusion line
    sh = np.clip(s * k + c + ao, 0, 0.85)[..., None]
    return canvas * (1 - sh * np.array([0.62, 0.55, 0.45], np.float32))


def build(mode):
    cv = plate.copy()
    boxes, mask = [], np.zeros((H, W), np.float32)
    if mode == "jar":
        jw, jx, jy = 440, 508, 1302
        cv = shadow(cv, jx, jy + 14, jw * 0.47, 30)
        r, m = place(cv, warm(JAR), jx, jy, jw, 35 / 646)
        boxes.append(("jar", r)); mask = np.maximum(mask, m)
        focus = (jx, 1150)
    else:
        bw, bx, by = 400, 700, 1126
        cv = shadow(cv, bx, by - 2, bw * 0.52, 16, 0.5, 0.8)
        r, m = place(cv, warm(BOX, 1), bx, by, bw, 0)
        boxes.append(("box", r)); mask = np.maximum(mask, m)
        jw, jx, jy = 360, 338, 1318
        cv = shadow(cv, jx, jy + 14, jw * 0.47, 26)
        r, m = place(cv, warm(JAR), jx, jy, jw, 35 / 646)
        boxes.append(("jar", r)); mask = np.maximum(mask, m)
        focus = (560, 1060)
    return np.clip(cv, 0, 1), mask, boxes, focus


BASE, MASK, BOXES, FOCUS = build(MODE)
# golden halo behind the products (only on the backdrop, above the pedestal line)
HALO = np.exp(-(((XX - FOCUS[0]) / 520) ** 2 + ((YY - FOCUS[1] + 120) / 560) ** 2))[..., None] * (YY < 1250)[..., None]
HALO = cv2.GaussianBlur(HALO.astype(np.float32), (0, 0), 30)[..., None] if HALO.ndim == 2 else HALO
BASE = 1 - (1 - BASE) * (1 - HALO * 0.22 * np.array([0.55, 0.85, 1.0], np.float32))
rng = np.random.default_rng(16)
P = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4.5), rng.uniform(30, 90), rng.uniform(0, 6.3)) for _ in range(90)]
jar_r = [r for k, r in BOXES if k == "jar"][0]
GLINT = (jar_r[0] + jar_r[2] * 0.80, jar_r[1] + jar_r[3] * 0.47)          # on the gold collar


def frame(i):
    t = i / FPS
    p = i / max(1, round(DUR * FPS) - 1)
    fr = BASE.copy()
    q = -0.3 + 1.6 * p                                                    # light sweep across the products only
    band = np.exp(-(((XX / W * 0.7 + YY / H * 0.5) - q - 0.25) / 0.05) ** 2)
    fr = 1 - (1 - fr) * (1 - (band * MASK)[..., None] * 0.35)
    gp = (t - DUR * 0.45) / 0.6                                          # star glint on the gold collar
    if 0 < gp < 1:
        s = math.sin(math.pi * gp)
        gx, gy = GLINT
        st = np.exp(-(((XX - gx) / 2.5) ** 2 + ((YY - gy) / (60 * s + 1)) ** 2)) + np.exp(-(((XX - gx) / (60 * s + 1)) ** 2 + ((YY - gy) / 2.5) ** 2))
        st += np.exp(-((XX - gx) ** 2 + (YY - gy) ** 2) / (2 * (10 * s + 1) ** 2))
        fr = 1 - (1 - fr) * (1 - np.clip(st, 0, 1)[..., None] * 0.9 * s)
    ov = np.zeros((H, W), np.float32)
    for x0, y0, r, sp, ph in P:                                          # gold dust rising
        cv2.circle(ov, (int(x0 + 10 * math.sin(t * 1.4 + ph)), int((y0 - sp * t) % H)), int(r), 0.5 + 0.5 * math.sin(t * 3 + ph), -1, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 1.5)[..., None]
    fr = fr * (1 - ov * 0.7) + np.array([0.45, 0.80, 1.0], np.float32) * ov * 0.7
    e = p * p * (3 - 2 * p)
    z = 1.0 + 0.08 * e                                                    # eased push-in
    cx, cy = FOCUS
    M = np.float32([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]])
    fr = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return np.clip(fr * 255, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    n = round(DUR * FPS)
    if OUT.endswith(".jpg"):
        cv2.imwrite(OUT, np.hstack([cv2.resize(frame(i), (540, 960)) for i in (0, n // 2, n - 1)]))
        sys.exit()
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    for i in range(n):
        wr.stdin.write(frame(i).tobytes())
    wr.stdin.close(); wr.wait()
