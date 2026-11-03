"""Clip 6, client round 3: the jar in her hand becomes the REAL PalmCare Vitamin C Face Moisturiser jar in every frame.
The whole AI jar is replaced by the real product photo (v9/jar_cut.png): placed from the template-match track
(uniform scale + translation, always upright, heavily smoothed so it never jitters), the photo's lid-top ellipse
flattened to the camera's eye-level angle, light-matched, softened and grained to sit in the footage. Her fingers stay
in front through a jar-relative finger matte that is smoothed over time (no flicker).
Usage: render6c.py OUT(.mp4|.jpg)"""
import json
import subprocess
import sys

import cv2
import numpy as np

OUT = sys.argv[1]
sys.argv = [sys.argv[0], "x"]
from jarfix import F0, F1, frames, D, W, H   # noqa: E402

BOX0 = (16, 688, 180, 860)                 # AI jar on frame F0: lid top .. base bottom
TPL = (40, 692, 150, 845)
cx0, cy0 = (TPL[0] + TPL[2]) / 2, (TPL[1] + TPL[3]) / 2
tr = np.array(json.load(open(D + "v11/qa/track2.json")))
sm = tr.copy()
k = np.hanning(13)[1:-1]
k /= k.sum()
for j in range(3):                         # heavy, zero-lag smoothing: the jar glides with her hand, never jitters
    sm[:, j] = np.convolve(np.pad(tr[:, j], len(k) // 2, mode="edge"), k, mode="valid")

# real jar: crop, flatten the lid-top ellipse (photo shot from above -> eye level), warm light match
jar = cv2.imread(D + "v9/jar_cut.png", cv2.IMREAD_UNCHANGED)
ys, xs = np.nonzero(jar[..., 3] > 8)
jar = jar[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32) / 255
full = (jar[..., 3] > 0.5).sum(1) > 0.97 * jar.shape[1] * 0.9          # rows where the jar is (nearly) full width
lid_front = int(np.argmax(full))                                       # first full-width row = front edge of lid top
top = cv2.resize(jar[:lid_front], (jar.shape[1], max(1, int(lid_front * 0.5))), interpolation=cv2.INTER_AREA)
jar = np.vstack([top, jar[lid_front:]])
RH, RW = jar.shape[:2]

MG = 40                                    # finger-matte window margin around the jar box (jar-relative grid)
GW, GH = 240, 260


def box(i):
    x, y, s, _ = sm[i - F0]
    return x + (BOX0[0] - cx0) * s, y + (BOX0[1] - cy0) * s, (BOX0[2] - BOX0[0]) * s, (BOX0[3] - BOX0[1]) * s


def grid_xy(i):
    bx, by, bw, bh = box(i)
    sx, sy = (bw + 2 * MG) / GW, (bh + 2 * MG) / GH
    return bx - MG, by - MG, sx, sy


def skin(fr, i):
    """Her fingers only: deep skin tones (the jar's gold band is a lighter, yellower hue) that reach in from outside."""
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV).astype(int)
    m = ((hsv[..., 1] > 95) & (hsv[..., 2] < 218) & ((hsv[..., 0] < 15) | (hsv[..., 0] > 165))).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    bx, by, bw, bh = box(i)
    inner = np.zeros_like(m)
    cv2.rectangle(inner, (int(bx) + 4, int(by) + 4), (int(bx + bw) - 4, int(by + bh) - 4), 1, -1)
    n, lb, st, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    for c in range(1, n):
        cc = lb == c
        if (cc & (inner == 0)).sum() > 40 and (cc & (inner == 1)).any():
            keep[cc] = 1
    return keep


def to_grid(m, i):
    x0, y0, sx, sy = grid_xy(i)
    M = np.float32([[sx, 0, x0], [0, sy, y0]])
    return cv2.warpAffine(m.astype(np.float32), M, (GW, GH), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)


def from_grid(g, i):
    x0, y0, sx, sy = grid_xy(i)
    M = np.float32([[sx, 0, x0], [0, sy, y0]])
    return cv2.warpAffine(g, M, (W, H), flags=cv2.INTER_LINEAR)


def light_gain(fr):
    lid = fr[700:722, 70:160].reshape(-1, 3).astype(np.float32).mean(0) / 255
    rl = jar[int(RH * 0.12):int(RH * 0.3), int(RW * 0.3):int(RW * 0.7)]
    real = (rl[..., :3] * rl[..., 3:]).reshape(-1, 3).sum(0) / rl[..., 3].sum()
    return np.clip(lid / real, 0.85, 1.12).astype(np.float32)


def comp(fr, i, fing, gain, rng):
    bx, by, bw, bh = box(i)
    s = max(bw / RW, bh / RH) * 1.035
    pw, ph = int(round(RW * s)), int(round(RH * s))
    pj = cv2.resize(jar, (pw, ph), interpolation=cv2.INTER_AREA)
    rgb = np.clip(pj[..., :3] * gain * np.array([0.92, 0.965, 1.0], np.float32) * 0.97, 0, 1)   # warm room light (BGR)
    shade = np.linspace(0.93, 1.03, pw, dtype=np.float32)[None, :, None]   # window light from her left (screen right)
    rgb = cv2.GaussianBlur(rgb * shade, (0, 0), 0.75)
    a = cv2.GaussianBlur(pj[..., 3], (0, 0), 0.9)
    x0 = int(round(bx + bw / 2 - pw / 2))
    y0 = int(round(by + bh + 1 - ph))
    lay = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W), np.float32)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + pw), min(H, y0 + ph)
    lay[ya:yb, xa:xb] = rgb[ya - y0:yb - y0, xa - x0:xb - x0]
    al[ya:yb, xa:xb] = a[ya - y0:yb - y0, xa - x0:xb - x0]
    f = fr.astype(np.float32) / 255
    # remove the AI jar wherever the real one does not cover it (narrow slivers at its sides): inpaint from surroundings
    ai = np.zeros((H, W), np.uint8)
    cv2.rectangle(ai, (int(bx) - 2, int(by) - 2), (int(bx + bw) + 2, int(by + bh) + 3), 1, -1)
    left = (ai > 0) & (al < 0.5) & (fing < 0.5)
    if left.any():
        f8 = (f * 255).astype(np.uint8)
        f = cv2.inpaint(f8, left.astype(np.uint8), 5, cv2.INPAINT_TELEA).astype(np.float32) / 255
    al = al * (1 - fing)
    grain = rng.normal(0, 0.011, (H, W, 1)).astype(np.float32)
    out = f * (1 - al[..., None]) + (lay + grain) * al[..., None]
    return np.clip(out * 255, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    fr_all = []
    for i, fr in enumerate(frames()):
        if i > F1:
            break
        if i >= F0:
            fr_all.append(fr)
    # finger matte: per-frame skin in jar-relative coords, smoothed over +-8 frames, thresholded, soft edge
    grids = np.array([to_grid(skin(fr, F0 + n), F0 + n) for n, fr in enumerate(fr_all)])
    gs = np.array([grids[max(0, n - 8):n + 9].mean(0) for n in range(len(grids))])
    gain = light_gain(fr_all[0])
    rng = np.random.default_rng(3)
    picks = [F0, 30, 60, 90, 120, 150, 170]
    sel = []
    wr = None
    if not OUT.endswith(".jpg"):
        wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "24",
                               "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT],
                              stdin=subprocess.PIPE)
    for n, fr in enumerate(fr_all):
        i = F0 + n
        if wr is None and i not in picks:
            continue
        g = cv2.GaussianBlur((gs[n] > 0.5).astype(np.float32), (0, 0), 1.2)
        fing = np.clip(from_grid(g, i), 0, 1)
        c = comp(fr, i, fing, gain, rng)
        if wr is None:
            sel.append(np.vstack([fr[620:930, 0:260], c[620:930, 0:260]]))
        else:
            wr.stdin.write(c.tobytes())
    if wr is None:
        cv2.imwrite(OUT, cv2.resize(np.hstack(sel), None, fx=1.3, fy=1.3, interpolation=cv2.INTER_CUBIC), [cv2.IMWRITE_JPEG_QUALITY, 92])
    else:
        wr.stdin.close()
        wr.wait()
