"""Clip 6 label fix: Flow drew the lid and gold band correctly but invented the label. The jar BODY (below the gold band)
is replaced every frame with a clean white body carrying the REAL PalmCare label (palm leaf, PalmCare / VITAMIN C /
FACE MOISTURISER / Brightening · Hydrating · Tone Refining / 30 mL | 1.0 fl. oz.) from the product photo, tracked to
the jar (uniform scale + translation, upright), light-matched, her fingers kept in front.
Usage: render6b.py OUT(.mp4|.jpg)"""
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
BODY = (0.01, 0.415, 0.985, 0.97)       # body inside the jar box (x0, y0, x1, y1 as fractions)
LABEL_W = 0.84                         # label block width / body width (real jar proportion)
cx0, cy0 = (TPL[0] + TPL[2]) / 2, (TPL[1] + TPL[3]) / 2
tr = np.array(json.load(open(D + "v11/qa/track2.json")))
sm = tr.copy()
k = np.array([1, 2, 3, 2, 1], float); k /= k.sum()
for j in range(3):
    sm[:, j] = np.convolve(np.pad(tr[:, j], 2, mode="edge"), k, mode="valid")

ed = np.array(json.load(open(D + "v11/qa/edges.json")))         # measured band bottom / right edge per frame
for j in range(2):
    med = np.array([np.median(ed[max(0, i - 4):i + 5, j]) for i in range(len(ed))])
    ed[:, j] = np.convolve(np.pad(med, 3, mode="edge"), np.ones(7) / 7, mode="valid")
jar = cv2.imread(D + "v9/jar_cut.png", cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
body = jar[455:646]
prof = body[2:9, :, :3].mean(0)                                 # white body shading across the width (cylinder)
al = body[2:9, :, 3].mean(0)
prof = prof[al > 0.98]
prof = np.repeat(prof.mean(1, keepdims=True), 3, 1) / prof.mean()   # luminance-only shading, colour comes from gain
lab = body[0:172, 90:650, :3] * body[0:172, 90:650, 3:] + (1 - body[0:172, 90:650, 3:]) * 0.9
white = np.dstack([cv2.GaussianBlur(cv2.morphologyEx(lab[..., c], cv2.MORPH_CLOSE, np.ones((45, 45), np.uint8)), (0, 0), 8)
                   for c in range(3)])
ink = np.clip(lab / np.maximum(white, 1e-3), 0, 1)
dark = 1 - ink.min(2)                                            # how much ink is printed at each pixel
soft = np.clip((dark - 0.10) / 0.15, 0, 1)[..., None]            # paper stays exactly paper (no block edge)
ink = 1 - (1 - ink) * soft
_h = cv2.cvtColor((ink * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
_blue = (_h[..., 0] > 95) & (_h[..., 0] < 150)
_h[..., 1] = np.where(_blue, _h[..., 1] // 5, _h[..., 1])          # black print, not the photo's blue cast
ink = cv2.cvtColor(_h, cv2.COLOR_HSV2BGR).astype(np.float32) / 255   # 1 = white, <1 = printed ink (keeps the gold colour)


def patch(bw, bh, gain, src=None):
    if src is not None:
        # clean white of the AI body (only near-neutral bright pixels: no print, no fingers), as a smooth left-right profile
        hs = cv2.cvtColor((src * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
        ok = (hs[..., 1] < 40) & (hs[..., 2] > 190)
        ok[:int(bh * 0.05)] = False
        glob = np.median(src[ok], axis=0) if ok.sum() > 50 else np.array([0.9, 0.9, 0.9])
        col = np.array([np.median(src[ok[:, c], c], axis=0) if ok[:, c].sum() > 8 else glob for c in range(bw)])
        col = cv2.GaussianBlur(col[None].astype(np.float32), (0, 0), 6)[0]
        base = np.repeat(col[None], bh, 0).astype(np.float32)
        base = cv2.GaussianBlur(base, (0, 0), 2)
    else:
        base = cv2.resize(prof[None], (bw, bh), interpolation=cv2.INTER_LINEAR) * gain
    lw = int(round(bw * LABEL_W)); lh = int(round(lw * ink.shape[0] / ink.shape[1]))
    li = cv2.resize(ink, (lw, lh), interpolation=cv2.INTER_AREA)
    x = (bw - lw) // 2 + int(0.02 * bw); y = int((bh - lh) * 0.42)
    base[y:y + lh, x:x + lw] *= li
    a = np.ones((bh, bw), np.float32)
    r = max(2, int(0.07 * bw))                                   # rounded base of the jar
    m = np.zeros((bh, bw), np.uint8)
    cv2.ellipse(m, (bw // 2, bh - r), (bw // 2, r), 0, 0, 180, 1, -1)
    a[bh - r:] = m[bh - r:]
    a[:2] *= 0.6
    return base, cv2.GaussianBlur(a, (0, 0), 0.7)


def comp(fr, i, gain):
    x, y, s, _ = sm[i - F0]
    bx, by = x + (BOX0[0] - cx0) * s, y + (BOX0[1] - cy0) * s
    bw0, bh0 = (BOX0[2] - BOX0[0]) * s, (BOX0[3] - BOX0[1]) * s
    top, right = ed[i - F0]
    X1 = right - 1
    X0, Y0 = int(round(X1 - 0.965 * bw0)), int(round(top + 1))
    pw, ph = int(round(X1)) - X0, int(round(by + BODY[3] * bh0)) - Y0
    cut = max(0, -X0)                                            # jar partly off the left edge of frame
    srcf = cv2.copyMakeBorder(fr, 0, 0, cut, 0, cv2.BORDER_REPLICATE)[Y0:Y0 + ph, X0 + cut:X0 + cut + pw].astype(np.float32) / 255
    rgb, a = patch(pw, ph, gain, srcf)                           # full-size label, so it never shifts
    rgb, a = rgb[:, cut:], a[:, cut:]
    X0, pw = X0 + cut, pw - cut
    rgb = cv2.GaussianBlur(rgb, (0, 0), 0.6)
    f = fr.astype(np.float32) / 255
    reg = fr[Y0:Y0 + ph, X0:X0 + pw]
    # fingers = skin blobs that reach in from OUTSIDE the jar body (the AI logo/ink inside the body is never kept)
    M = 24
    ex = fr[max(0, Y0 - M):Y0 + ph + M, max(0, X0 - M):X0 + pw + M]
    ox, oy = X0 - max(0, X0 - M), Y0 - max(0, Y0 - M)
    hsv = cv2.cvtColor(ex, cv2.COLOR_BGR2HSV).astype(int)
    sk = (((hsv[..., 1] > 95) & (hsv[..., 2] < 225)) & ((hsv[..., 0] < 16) | (hsv[..., 0] > 165))).astype(np.uint8)
    sk = cv2.morphologyEx(sk, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lb, st, _ = cv2.connectedComponentsWithStats(sk)
    inside = np.zeros_like(sk); inside[oy:oy + ph, ox:ox + pw] = 1
    keep = np.zeros_like(sk)
    for c in range(1, n):
        comp_c = lb == c
        if (comp_c & (inside == 0)).sum() > 30 and (comp_c & (inside == 1)).sum() > 0:
            keep[comp_c] = 1
    zone = np.ones((ph, pw), np.uint8)                           # the label core never has fingers over it
    zone[:, int(0.15 * pw):int(0.62 * pw)] = 0
    zone[:int(0.5 * ph), int(0.62 * pw):int(0.80 * pw)] = 0
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    keep = cv2.morphologyEx(keep, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    skin = cv2.dilate(keep[oy:oy + ph, ox:ox + pw] & zone, np.ones((3, 3), np.uint8)).astype(np.float32)
    skin = np.clip(cv2.GaussianBlur(skin, (0, 0), 1.4) * 1.3, 0, 1)
    a = a[:reg.shape[0], :reg.shape[1]] * (1 - skin)
    g = np.random.normal(0, 0.010, reg.shape[:2] + (1,)).astype(np.float32)
    sub = f[Y0:Y0 + ph, X0:X0 + pw]
    f[Y0:Y0 + ph, X0:X0 + pw] = sub * (1 - a[..., None]) + (rgb[:reg.shape[0], :reg.shape[1]] + g) * a[..., None]
    return np.clip(f * 255, 0, 255).astype(np.uint8)


it = frames()
for _ in range(F0):
    next(it)
fr0 = next(it)
ai_white = fr0[764:772, 60:150].reshape(-1, 3).astype(np.float32).mean(0) / 255
gain = (ai_white / prof[len(prof) // 3:2 * len(prof) // 3].mean(0)).astype(np.float32)
print("gain", gain.round(3))

if OUT.endswith(".jpg"):
    picks = [F0, 40, 80, 120, 150, 172]
    sel = []
    for i, fr in enumerate(frames()):
        if i in picks:
            c = comp(fr, i, gain)
            sel.append(np.vstack([fr[620:920, 0:260], c[620:920, 0:260]]))
        if i >= max(picks):
            break
    im = np.hstack(sel)
    cv2.imwrite(OUT, cv2.resize(im, None, fx=1.4, fy=1.4, interpolation=cv2.INTER_CUBIC), [cv2.IMWRITE_JPEG_QUALITY, 92])
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
