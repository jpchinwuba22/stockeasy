"""Render clip 6 with the REAL jar: per-frame placement from track2.json (uniform scale + translation, always upright),
warm light match to the scene, slight softening + grain to sit in the AI footage, her fingers kept in front.
Usage: render6.py OUT(.mp4|.jpg)"""
import json
import subprocess
import sys

import cv2
import numpy as np

OUT = sys.argv[1]
sys.argv = [sys.argv[0], "x"]
from jarfix import F0, F1, frames, D, W, H

BOX0 = (16, 688, 180, 860)
TPL = (40, 692, 150, 845)
cx0, cy0 = (TPL[0] + TPL[2]) / 2, (TPL[1] + TPL[3]) / 2
tr = np.array(json.load(open(D + "v11/qa/track2.json")))
# temporal smoothing of position and scale (removes 1-px match jitter)
sm = tr.copy()
k = np.array([1, 2, 3, 2, 1], float); k /= k.sum()
for j in range(3):
    sm[:, j] = np.convolve(np.pad(tr[:, j], 2, mode="edge"), k, mode="valid")

jar = cv2.imread(D + "v9/jar_cut.png", cv2.IMREAD_UNCHANGED)
ys, xs = np.nonzero(jar[..., 3] > 8)
jar = jar[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32) / 255
RH, RW = jar.shape[:2]


def boxes(i):
    x, y, s, _ = sm[i - F0]
    return x + (BOX0[0] - cx0) * s, y + (BOX0[1] - cy0) * s, (BOX0[2] - BOX0[0]) * s, (BOX0[3] - BOX0[1]) * s


def comp(fr, i, gain):
    bx, by, bw, bh = boxes(i)
    s = max(bw / RW, bh / RH) * 1.03
    pw, ph = int(round(RW * s)), int(round(RH * s))
    pj = cv2.resize(jar, (pw, ph), interpolation=cv2.INTER_AREA)
    rgb = np.clip(pj[..., :3] * gain, 0, 1)
    rgb = cv2.GaussianBlur(rgb, (0, 0), 0.7)
    a = cv2.GaussianBlur(pj[..., 3], (0, 0), 0.8)
    x0 = int(round(bx + bw / 2 - pw / 2))
    y0 = int(round(by + bh + 2 - ph))
    lay = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W), np.float32)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + pw), min(H, y0 + ph)
    lay[ya:yb, xa:xb] = rgb[ya - y0:yb - y0, xa - x0:xb - x0]
    al[ya:yb, xa:xb] = a[ya - y0:yb - y0, xa - x0:xb - x0]
    f = fr.astype(np.float32) / 255
    # her fingers stay in front: skin pixels that belong to the hand (connected to skin outside the jar box)
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV).astype(int)
    skin = ((hsv[..., 1] > 70) & (hsv[..., 2] < 225) & (hsv[..., 0] < 22)).astype(np.uint8)
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # the gold band of the AI jar looks skin-like: keep only the finger zones (left edge, right thumb, below the base)
    zone = np.zeros((H, W), np.uint8)
    L, R, T, B = int(bx), int(bx + bw), int(by), int(by + bh)
    zone[T:B + 40, max(0, L - 30):L + int(0.16 * bw)] = 1
    zone[T + int(0.55 * bh):B + 40, L + int(0.68 * bw):R + 40] = 1
    zone[B - int(0.04 * bh):B + 60, L - 30:R + 40] = 1
    zone[:, :] &= 1
    fing = (skin & zone).astype(np.float32)
    fing = cv2.GaussianBlur(fing, (0, 0), 1.0)
    al = al * (1 - fing)
    grain = np.random.normal(0, 0.012, (H, W, 1)).astype(np.float32)
    out = f * (1 - al[..., None]) + (lay + grain) * al[..., None]
    return np.clip(out * 255, 0, 255).astype(np.uint8)


# light match: scene white of the AI jar lid on F0 vs the real lid
it = frames()
for _ in range(F0):
    next(it)
fr0 = next(it)
ai_lid = fr0[700:725, 70:160].reshape(-1, 3).astype(np.float32).mean(0) / 255
rl = jar[int(RH * 0.1):int(RH * 0.3), int(RW * 0.3):int(RW * 0.7)]
real_lid = (rl[..., :3] * rl[..., 3:]).reshape(-1, 3).sum(0) / rl[..., 3].sum()
gain = np.clip(ai_lid / real_lid, 0.8, 1.15).astype(np.float32)
print("gain BGR", gain.round(3))

if OUT.endswith(".jpg"):
    picks = [F0, 40, 80, 120, 150, 172]
    sel = []
    it = frames()
    for i, fr in enumerate(it):
        if i in picks:
            c = comp(fr, i, gain)
            sel.append(np.vstack([fr[560:1000, 0:330], c[560:1000, 0:330]]))
        if i >= max(picks):
            break
    cv2.imwrite(OUT, np.hstack(sel), [cv2.IMWRITE_JPEG_QUALITY, 92])
    sys.exit()
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "24", "-i", "-",
                      "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for i, fr in enumerate(frames()):
    if i < F0:
        continue
    if i > F1:
        break
    p.stdin.write(comp(fr, i, gain).tobytes())
p.stdin.close()
p.wait()
