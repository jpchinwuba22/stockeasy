# Moving fix: in every frame the WHOLE Flow tube is replaced by the real GlowShield photo (true proportions), moved by the
# tube's own tracked motion (rigid, smoothed), light-matched; the background behind Flow's tube is rebuilt; her fingers
# stay in front. Usage: tubereplace.py OUT.mp4 | tubereplace.py SHEET.jpg
import sys, subprocess
import cv2, numpy as np
OUT = sys.argv[1]
import os
if os.path.exists('track_Ps.npy'):                       # cached tracking (smoothed rigid motion of the tube)
    Ps = np.load('track_Ps.npy'); N = len(os.listdir('tf')); F = [cv2.imread(f'tf/{i:04d}.png') for i in range(1, N + 1)]
    def sim(i):
        s_, a_, tx, ty = Ps[i]
        return np.float64([[s_ * np.cos(a_), -s_ * np.sin(a_), tx], [s_ * np.sin(a_), s_ * np.cos(a_), ty], [0, 0, 1]])
else:
    src = open('tubelock4.py').read().split("def comp(i):")[0]
    _o = OUT; sys.argv = ['x', 'none']; exec(src); OUT = _o
    np.save('track_Ps.npy', Ps)
S = 1.5; Sm = np.diag([S, S, 1.0])
art = cv2.imread('assets/tube_cut.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
ah2, aw2 = art.shape[:2]
sc = (985 - 398) / ah2                                   # real tube height = Flow tube height on the key frame
A2 = np.float64([[sc, 0, 245 - sc * aw2 / 2], [0, sc, 404], [0, 0, 1]])
KP = np.float32([[84, 390], [380, 390], [330, 1000], [140, 1000]])     # Flow tube (key frame), generous
kreg = np.zeros((1280, 720), np.uint8); cv2.fillConvexPoly(kreg, KP.astype(np.int32), 255)
FRONT = np.zeros((1280, 720), np.uint8)                   # where her hand can be in front of the tube (key frame)
cv2.rectangle(FRONT, (20, 560), (205, 1080), 255, -1)     # fingers wrapping the left side
cv2.rectangle(FRONT, (285, 680), (410, 930), 255, -1)     # thumb on the right
cv2.rectangle(FRONT, (120, 925), (360, 1100), 255, -1)    # palm under the tube
THUMB = np.zeros((1280, 720), np.uint8); cv2.rectangle(THUMB, (300, 690), (410, 925), 255, -1)
def frame(i):
    f = cv2.resize(F[i], (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
    Hk = sim(i); Hb = Sm @ Hk @ np.linalg.inv(Sm)
    reg = cv2.warpPerspective(kreg, Hk, (720, 1280)); reg = cv2.resize(reg, (1080, 1920), interpolation=cv2.INTER_NEAREST)
    reg = cv2.dilate(reg, np.ones((31, 31), np.uint8))
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    fz = cv2.resize(cv2.warpPerspective(FRONT, Hk, (720, 1280)), (1080, 1920), interpolation=cv2.INTER_NEAREST)
    sk = ((hsv[..., 1] > 45) & (hsv[..., 0] < 25) & (hsv[..., 2] > 35) & (hsv[..., 2] < 240) & (fz > 0)).astype(np.uint8)
    tz = cv2.resize(cv2.warpPerspective(THUMB, Hk, (720, 1280)), (1080, 1920), interpolation=cv2.INTER_NEAREST)
    sk |= ((hsv[..., 1] > 22) & (hsv[..., 0] < 25) & (hsv[..., 2] > 170) & (hsv[..., 2] < 248) & (tz > 0)).astype(np.uint8)   # sunlit thumb (not her shaded cheek)
    sk = cv2.morphologyEx(sk, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    fing = cv2.morphologyEx(sk, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    fing = cv2.erode(fing, np.ones((7, 7), np.uint8))                    # drop the light tube fringe around fingers
    # Flow's own tube, found directly (white plastic connected to the tracked region), so no sliver of it survives
    big = cv2.dilate(reg, np.ones((81, 81), np.uint8))
    wt = ((hsv[..., 2] > 140) & (hsv[..., 1] < 70) & (big > 0)).astype(np.uint8)
    n2, l2, _, _ = cv2.connectedComponentsWithStats(wt)
    k2 = np.zeros(n2, bool); k2[np.unique(l2[(reg > 0) & (wt > 0)])] = True; k2[0] = False
    wt = k2[l2].astype(np.uint8) * 255
    ff_ = wt.copy(); msk_ = np.zeros((wt.shape[0] + 2, wt.shape[1] + 2), np.uint8); cv2.floodFill(ff_, msk_, (0, 0), 255)
    wt = ((wt | cv2.bitwise_not(ff_)) > 0).astype(np.uint8)              # Flow's tube incl. its printed letters
    fing[wt > 0] = 0                                                     # anything inside the tube is tube, not finger
    pts = cv2.findNonZero(wt)                                            # Flow's whole tube silhouette (convex), with margin
    if pts is not None:
        hull = np.zeros_like(wt); cv2.fillConvexPoly(hull, cv2.convexHull(pts), 1); wt = np.maximum(wt, hull)
    wt = cv2.dilate(wt, np.ones((25, 25), np.uint8))
    wt[(cv2.dilate(reg, np.ones((61, 61), np.uint8)) == 0)] = 0                       # stay near the tube (not her shirt)
    hole = (((reg > 0) | (wt > 0)) & (fing == 0)).astype(np.uint8) * 255
    sm_ = cv2.resize(f, (360, 640), interpolation=cv2.INTER_AREA); hs = cv2.resize(hole, (360, 640), interpolation=cv2.INTER_NEAREST)
    inp = cv2.GaussianBlur(cv2.resize(cv2.inpaint(sm_, hs, 9, cv2.INPAINT_TELEA), (1080, 1920), interpolation=cv2.INTER_CUBIC).astype(np.float32), (0, 0), 6)
    ff = f.astype(np.float32)
    base = np.where(hole[..., None] > 0, inp, ff)
    Ha = Hb @ (Sm @ A2)
    rgb = cv2.warpPerspective(art[..., :3], Ha, (1080, 1920), flags=cv2.INTER_AREA)
    al = cv2.warpPerspective(art[..., 3] / 255, Ha, (1080, 1920), flags=cv2.INTER_LINEAR)
    w_old = (reg > 0) & (fing == 0) & (hsv[..., 2] > 185) & (hsv[..., 1] < 40)
    w_new = (al > 0.95) & (rgb.mean(2) > 185)
    if w_old.sum() > 200 and w_new.sum() > 200:
        rgb = np.clip(rgb * np.clip(np.median(ff[w_old], 0) / np.median(rgb[w_new], 0), 0.8, 1.2), 0, 255)
    sh = cv2.GaussianBlur(np.roll(np.roll(al, 14, 0), 10, 1), (0, 0), 14) * 0.30
    out = base * (1 - sh[..., None])
    out = out * (1 - al[..., None]) + rgb * al[..., None]
    fs = (cv2.medianBlur((fing * 255).astype(np.uint8), 11) > 127).astype(np.float32)   # smooth finger outline, no stair-steps
    fm = cv2.GaussianBlur(fs, (0, 0), 1.8)[..., None]
    out = out * (1 - fm) + ff * fm
    return np.clip(out, 0, 255).astype(np.uint8)
if OUT.endswith('.jpg'):
    cv2.imwrite(OUT, np.hstack([cv2.resize(frame(i)[450:1650, 0:760], (380, 600)) for i in (106, 125, 150, 175, 195)])); sys.exit()
w = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1080x1920', '-r', '24', '-i', '-',
                      '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for i in range(N):
    w.stdin.write((frame(i) if 96 <= i <= 215 else cv2.resize(F[i], (1080, 1920), interpolation=cv2.INTER_LANCZOS4)).tobytes())
w.stdin.close(); w.wait()
