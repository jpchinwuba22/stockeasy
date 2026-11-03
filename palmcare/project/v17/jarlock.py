"""Uploaded jar clip (P.mov): Flow garbled the small print. Lock the REAL jar label onto it. SIFT + RANSAC similarity
from the real cut-out to a reference frame, then reference -> every frame directly (no chaining, no drift), smoothed;
only the label body is replaced (feathered), the AI jar silhouette, lid and splash stay. Usage: jarlock.py OUT(.mp4|.jpg)"""
import subprocess
import sys

import cv2
import numpy as np

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
SRC, OUT = D + "v17/src/P.mov", sys.argv[1]
W, H = 720, 1280
REF_T = 3.2


def frames():
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            return
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)


F = list(frames())
jar = cv2.imread(D + "v9/jar_cut.png", -1)
jh, jw = jar.shape[:2]
sift = cv2.SIFT_create(4000)


def gray(x):
    return cv2.cvtColor(x[..., :3], cv2.COLOR_BGR2GRAY)


def match(a, ma, b, mb, ratio=0.75):
    ka, da = sift.detectAndCompute(gray(a), ma)
    kb, db = sift.detectAndCompute(gray(b), mb)
    m = cv2.BFMatcher().knnMatch(da, db, k=2)
    good = [x for x, y in m if x.distance < ratio * y.distance]
    pa = np.float32([ka[g.queryIdx].pt for g in good])
    pb = np.float32([kb[g.trainIdx].pt for g in good])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=2.5, maxIters=5000)
    return M, int(inl.sum()), len(good)


ri = int(REF_T * 24)
R = F[ri]
# jar region in the reference (jar sits roughly centre, lower half)
mR = np.zeros((H, W), np.uint8); mR[450:1000, 120:600] = 255
M0, n0, g0 = match(jar, (jar[..., 3] > 128).astype(np.uint8) * 255, R, mR, 0.8)
print("cut->ref inliers", n0, "/", g0, "scale", np.hypot(*M0[:, 0]))
# reference -> each frame (direct), region = pedestal + jar (rigid), splash excluded loosely
A = []
mRR = np.zeros((H, W), np.uint8); mRR[480:1180, 60:660] = 255
for i, fr in enumerate(F):
    if i == ri:
        A.append(np.float32([[1, 0, 0], [0, 1, 0]])); continue
    M, n, g = match(R, mRR, fr, None)
    A.append(M.astype(np.float32))
    if i % 24 == 0:
        print(i, n, g, round(float(np.hypot(*M[:, 0])), 3))
A = np.array(A)
# light temporal smoothing of the 6 params (camera push is smooth)
k = np.array([1, 2, 3, 2, 1], np.float32); k /= k.sum()
As = np.stack([np.convolve(np.pad(A[:, r, c], 2, mode="edge"), k, mode="valid") for r in range(2) for c in range(3)], 1).reshape(-1, 2, 3)

# label body mask on the cut-out: below the gold collar, inside the silhouette, feathered
lab = np.zeros((jh, jw), np.float32)
lab[int(jh * 0.69):, :] = 1
lab *= cv2.erode((jar[..., 3] > 128).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(np.float32)
lab = cv2.GaussianBlur(lab, (0, 0), 6)
src = jar[..., :3].astype(np.float32) / 255
ZONE = np.zeros((jh, jw), np.float32)
cv2.rectangle(ZONE, (int(-0.02 * jw), int(0.70 * jh)), (int(1.10 * jw), int(0.99 * jh)), 1, -1)
ZONE = cv2.GaussianBlur(ZONE, (0, 0), 5)


def compose(a, b):
    A3 = np.vstack([a, [0, 0, 1]]); B3 = np.vstack([b, [0, 0, 1]])
    return (A3 @ B3)[:2]


def comp(i):
    fr = F[i]
    M = compose(As[i], M0).astype(np.float32)
    wl = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_AREA)
    wa = cv2.warpAffine(lab, M, (W, H), flags=cv2.INTER_LINEAR)
    sc = float(np.hypot(*M[:, 0]))
    # wipe Flow's garbled print from the WHOLE (wider) AI label zone: grey dilation removes dark strokes on white
    zone = cv2.warpAffine(ZONE, M, (W, H), flags=cv2.INTER_LINEAR)
    kk = max(3, int(0.035 * jw * sc)) | 1
    clean = cv2.dilate(fr, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kk, kk)))
    clean = cv2.GaussianBlur(clean, (0, 0), kk * 0.4)
    z = zone * (clean.mean(2) > 175)
    fr = (fr * (1 - z[..., None]) + clean * z[..., None]).astype(np.uint8)
    f = fr.astype(np.float32) / 255
    m = wa > 0.9
    if m.sum() > 50:
        gain = np.clip(np.median(f[m], 0) / np.maximum(np.median(wl[m], 0), 1e-3), 0.8, 1.2)
        wl = np.clip(wl * gain, 0, 1)
    if sc > 0.9:                                        # upscaled beyond the photo: soften to the video's sharpness
        wl = cv2.GaussianBlur(wl, (0, 0), 0.4 * sc)
    out = f * (1 - wa[..., None]) + wl * wa[..., None]
    return np.clip(out * 255, 0, 255).astype(np.uint8)


if OUT.endswith(".jpg"):
    idx = [0, 40, 76, 120, len(F) - 1]
    cv2.imwrite(OUT, np.hstack([cv2.resize(comp(i), (360, 640)) for i in idx]))
    cv2.imwrite(OUT.replace(".jpg", "_zoom.jpg"), np.hstack([comp(i)[600:1000, 100:620] for i in (76, len(F) - 1)]))
    sys.exit()
wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "24", "-i", "-",
                       "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for i in range(len(F)):
    wr.stdin.write(comp(i).tobytes())
wr.stdin.close(); wr.wait()
