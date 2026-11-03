"""Clip E: lock the REAL PalmCare box front onto the box in her hands. The box is flat, so its motion is a pure
homography: ECC homography tracking of the box face (frame 0 -> t), the real artwork warped through it, light-matched,
her fingers (dark skin) kept in front. Usage: boxlock.py OUT(.mp4|.jpg)"""
import subprocess
import sys

import cv2
import numpy as np

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
SRC, OUT = D + "v14/src/E.mp4", sys.argv[1]
W, H = 720, 1280
Q0 = np.float32([[261, 739], [479, 739], [479, 911], [261, 911]])        # box face on frame 0

box = cv2.imread(D + "v9/box_straight.png", cv2.IMREAD_UNCHANGED)
ys, xs = np.nonzero(box[..., 3] > 8)
box = box[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32) / 255
bh, bw = box.shape[:2]
A0 = cv2.getPerspectiveTransform(np.float32([[0, 0], [bw, 0], [bw, bh], [0, bh]]), Q0)


def frames():
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            return
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)


fr_all = list(frames())
# track the four box corners directly (box edge + her fingers around each corner are stable features), frame by frame,
# so the label moves exactly with her hands; only a very light smoothing removes sub-pixel noise
def grad(fr):
    g = cv2.GaussianBlur(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.2)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)
    return np.sqrt(gx * gx + gy * gy)


PR, SR_ = 34, 26                                           # patch radius, search radius
G0 = grad(fr_all[0])
tpl = [G0[int(y) - PR:int(y) + PR, int(x) - PR:int(x) + PR].copy() for x, y in Q0]
pos = [np.float32(q) for q in Q0]
C = []
for fr in fr_all:
    G = grad(fr)
    cur = []
    for k in range(4):
        x, y = pos[k]
        x0, y0 = int(x) - PR - SR_, int(y) - PR - SR_
        win = G[max(0, y0):y0 + 2 * (PR + SR_), max(0, x0):x0 + 2 * (PR + SR_)]
        r = cv2.matchTemplate(win, tpl[k], cv2.TM_CCOEFF_NORMED)
        _, _, _, ml = cv2.minMaxLoc(r)
        # sub-pixel peak
        px, py = ml
        if 0 < px < r.shape[1] - 1 and 0 < py < r.shape[0] - 1:
            dx = (r[py, px + 1] - r[py, px - 1]) / (2 * (2 * r[py, px] - r[py, px + 1] - r[py, px - 1]) + 1e-9)
            dy = (r[py + 1, px] - r[py - 1, px]) / (2 * (2 * r[py, px] - r[py + 1, px] - r[py - 1, px]) + 1e-9)
        else:
            dx = dy = 0
        nx = max(0, x0) + px + dx + PR
        ny = max(0, y0) + py + dy + PR
        cur.append(np.float32([nx, ny]))
    pos = cur
    C.append(np.array(cur))
C = np.array(C)
# keep the box a rigid rectangle: fit a similarity-ish model from the 4 tracked corners each frame (no shear jitter)
Cf = []
for c in C:
    M, _ = cv2.estimateAffinePartial2D(Q0, c.astype(np.float32))
    Cf.append(cv2.transform(Q0[None], M)[0])
Cf = np.array(Cf)
k = np.array([1, 2, 3, 2, 1], np.float64); k /= k.sum()     # ~0.2 s light smoothing only
Cs = np.stack([np.convolve(np.pad(Cf[:, i, j], 2, mode="edge"), k, mode="valid") for i in range(4) for j in range(2)], 1).reshape(-1, 4, 2)
np.save("qa/box_corners.npy", Cs)


def comp(fr, q):
    Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [bw, 0], [bw, bh], [0, bh]]), q.astype(np.float32))
    wb = cv2.warpPerspective(box, Hm, (W, H), flags=cv2.INTER_AREA)
    a = wb[..., 3]
    f = fr.astype(np.float32) / 255
    m = a > 0.95
    gain = np.clip(f[m].mean(0) / np.maximum(wb[..., :3][m].mean(0), 1e-3), 0.85, 1.15)
    rgb = np.clip(wb[..., :3] * gain, 0, 1)
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV).astype(int)
    sk = ((hsv[..., 2] < 175) & (hsv[..., 1] > 70)).astype(np.uint8)
    inner = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(inner, q.astype(np.int32), 1)
    top = int(min(q[0][1], q[1][1]))
    edge = inner.copy(); edge[top + 26:] = 0                                # fingertips only reach over the top edge
    edge[:, int(q[0][0]) + 50:] = 0                                         # ...at the left corner (right corner = the face's hair)
    keep = cv2.morphologyEx(sk * edge, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(np.float32)
    keep = cv2.GaussianBlur(keep, (0, 0), 1.0)
    a = cv2.GaussianBlur(a, (0, 0), 0.6) * (1 - keep)
    g = np.random.normal(0, 0.008, (H, W, 1)).astype(np.float32)
    out = f * (1 - a[..., None]) + (cv2.GaussianBlur(rgb, (0, 0), 0.5) + g) * a[..., None]
    return np.clip(out * 255, 0, 255).astype(np.uint8)


if OUT.endswith(".jpg"):
    sel = [comp(fr_all[i], Cs[i])[650:1000, 180:560] for i in (0, 80, 160, 238)]
    cv2.imwrite(OUT, np.hstack(sel))
    sys.exit()
wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "24", "-i", "-",
                       "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for fr, q in zip(fr_all, Cs):
    wr.stdin.write(comp(fr, q).tobytes())
wr.stdin.close(); wr.wait()
