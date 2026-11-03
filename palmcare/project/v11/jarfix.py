"""Clip 6 jar replacement: the AI-invented jar in her hand is swapped, frame by frame, for the REAL PalmCare Vitamin C
Face Moisturiser jar (v9/jar_cut.png). The AI jar is found as the bright, low-saturation blob in her hand; its box is
smoothed over time; the real jar is placed upright (uniform scale + translation only) to cover it; her fingers (dark skin
pixels) are kept in front; any AI-jar remnant outside the real jar is inpainted away.
Usage: jarfix.py track            -> qa/boxes.json + qa/track.jpg
       jarfix.py render OUT.mp4   -> fixed clip (frames F0..F1)"""
import json
import subprocess
import sys

import cv2
import numpy as np

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
SRC = D + "v11/src/C6.mp4"
W, H = 720, 1280
F0, F1 = 2, 176                      # frame 0 has no jar; from ~7.35 s the hands glitch (cut there)
ROI = (0, 560, 330, 1000)           # x0, y0, x1, y1 search window for the jar


def frames():
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            return
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()


def white_mask(fr):
    """AI jar = bright, low-saturation pixels (white lid/body, pale gold band) in the jar window."""
    x0, y0, x1, y1 = ROI
    hsv = cv2.cvtColor(fr[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    s, v = hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    m = (v > 170) & (s < 60)                      # white lid + white body (the gold band is bridged by the close below)
    m = cv2.morphologyEx(m.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((45, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None, None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    blob = (lab == k).astype(np.uint8) * 255
    full = np.zeros((H, W), np.uint8)
    full[y0:y1, x0:x1] = blob
    x, y, w, h = st[k, :4]
    return full, (x + x0, y + y0, x + x0 + w, y + y0 + h)


def smooth(a, r=4):
    a = np.array(a, float)
    out = a.copy()
    for i in range(len(a)):
        lo, hi = max(0, i - r), min(len(a), i + r + 1)
        out[i] = np.median(a[lo:hi], axis=0)
    k = np.ones(5) / 5
    for j in range(a.shape[1]):
        pad = np.pad(out[:, j], 2, mode="edge")
        out[:, j] = np.convolve(pad, k, mode="valid")
    return out


def load_jar():
    im = cv2.imread(D + "v9/jar_cut.png", cv2.IMREAD_UNCHANGED)
    ys, xs = np.nonzero(im[..., 3] > 8)
    return im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "track":
        # ECC affine tracking of the jar's own texture against frame F0, seeded with the previous warp
        BOX0 = (16, 688, 180, 860)                      # jar on frame F0 (lid top .. base bottom)
        it = frames()
        for i in range(F0):
            next(it)
        g0 = cv2.cvtColor(next(it), cv2.COLOR_BGR2GRAY).astype(np.float32)
        tm = np.zeros((H, W), np.uint8)
        tm[692:850, 38:172] = 255
        tm[790:870, 140:200] = 0                        # her thumb sits over the lower-right of the label
        Ms, M, sel = [np.eye(2, 3, dtype=np.float32)], np.eye(2, 3, dtype=np.float32), []
        for i, fr in enumerate(it, start=F0 + 1):
            if i > F1:
                break
            g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32)
            for sc in (0.5, 1.0):
                a = cv2.GaussianBlur(cv2.resize(g0, None, fx=sc, fy=sc), (0, 0), 1.2)
                b = cv2.GaussianBlur(cv2.resize(g, None, fx=sc, fy=sc), (0, 0), 1.2)
                m = cv2.resize(tm, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_NEAREST)
                Mi = M.copy(); Mi[:, 2] *= sc
                try:
                    _, Mi = cv2.findTransformECC(a, b, Mi, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6), m, 3)
                    M = Mi.copy(); M[:, 2] /= sc
                except cv2.error:
                    print("ecc fail", i)
            Ms.append(M.copy())
            if i in (40, 80, 120, 150, F1):
                v = fr.copy()
                c = np.array([[BOX0[0], BOX0[1], 1], [BOX0[2], BOX0[1], 1], [BOX0[2], BOX0[3], 1], [BOX0[0], BOX0[3], 1]], np.float32)
                q = (M @ c.T).T.astype(np.int32)
                cv2.polylines(v, [q], True, (0, 255, 0), 2)
                sel.append(cv2.resize(v[560:1000, 0:330], (198, 264)))
        json.dump([m.tolist() for m in Ms], open(D + "v11/qa/warps.json", "w"))
        cv2.imwrite(D + "v11/qa/track.jpg", np.hstack(sel))
        sys.exit()
    if mode == "track_old":
        boxes, sel = [], []
        for i, fr in enumerate(frames()):
            if i < F0 or i > F1:
                continue
            m, b = white_mask(fr)
            boxes.append(b)
            if i in (F0, 40, 80, 120, 150, F1):
                v = fr.copy()
                v[m > 0] = (v[m > 0] * 0.5 + np.array([0, 0, 255]) * 0.5).astype(np.uint8)
                cv2.rectangle(v, b[:2], b[2:], (0, 255, 0), 2)
                sel.append(cv2.resize(v[500:1050, 0:400], (240, 330)))
        json.dump([list(map(int, b)) for b in boxes], open(D + "v11/qa/boxes.json", "w"))
        cv2.imwrite(D + "v11/qa/track.jpg", np.hstack(sel))
        b = np.array(boxes)
        print("w", b[:, 2].min() - 0, "bbox w range", (b[:, 2] - b[:, 0]).min(), (b[:, 2] - b[:, 0]).max(),
              "h range", (b[:, 3] - b[:, 1]).min(), (b[:, 3] - b[:, 1]).max())
        sys.exit()
