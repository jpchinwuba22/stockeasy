# Lock the REAL GlowShield tube artwork onto Flow's tube: per-frame SIFT homography (real art -> frame, RANSAC) in a
# window that follows the tube, corner smoothing, light/gain match. Only the tube's white body is replaced (holes = Flow's
# garbled print are filled in), so her fingers stay in front. Usage: tubelock.py OUT(.mp4|.jpg)
import subprocess, sys, os
import cv2, numpy as np
D = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v28/'
OUT = sys.argv[1]
art = cv2.imread(D + 'assets/tube_cut.png', cv2.IMREAD_UNCHANGED)
ah, aw = art.shape[:2]
argb = art[..., :3]; aal = art[..., 3]
sift = cv2.SIFT_create(6000)
am = np.zeros((ah, aw), np.uint8); am[int(0.08 * ah):int(0.82 * ah), int(0.06 * aw):int(0.94 * aw)] = 255
ka, da = sift.detectAndCompute(cv2.cvtColor(argb, cv2.COLOR_BGR2GRAY), am)
N = len(os.listdir(D + 'tf'))
F = [cv2.imread(D + f'tf/{i:04d}.png') for i in range(1, N + 1)]
Hs, nin = [], []
roi = None
for i, f in enumerate(F):
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    mk = np.zeros_like(g)
    if roi is None: mk[:] = 255
    else:
        x0, y0, x1, y1 = roi; mk[max(0, y0):y1, max(0, x0):x1] = 255
    kf, df = sift.detectAndCompute(g, mk)
    Hh = None
    if df is not None and len(kf) > 10:
        m = [a for a, b in cv2.BFMatcher().knnMatch(da, df, k=2) if a.distance < 0.78 * b.distance]
        if len(m) >= 10:
            Hh, inl = cv2.findHomography(np.float32([ka[x.queryIdx].pt for x in m]), np.float32([kf[x.trainIdx].pt for x in m]), cv2.RANSAC, 4.0)
            if Hh is not None and inl.sum() < 10: Hh = None
            nin.append(0 if Hh is None else int(inl.sum()))
    Hs.append(Hh)
    if Hh is not None:
        c = cv2.perspectiveTransform(np.float32([[[0, 0]], [[aw, 0]], [[aw, ah]], [[0, ah]]]), Hh).reshape(-1, 2)
        x0, y0 = c.min(0); x1, y1 = c.max(0); p = 0.25 * max(x1 - x0, y1 - y0)
        roi = (int(x0 - p), int(y0 - p), int(x1 + p), int(y1 + p))
print('frames with fit', sum(h is not None for h in Hs), '/', N, 'inliers median', int(np.median(nin)) if nin else 0)
C0 = np.float32([[0, 0], [aw, 0], [aw, ah], [0, ah]]).reshape(-1, 1, 2)
C = np.array([cv2.perspectiveTransform(C0, h).reshape(-1) if h is not None else np.full(8, np.nan) for h in Hs])
idx = np.arange(N)
for j in range(8):
    v = C[:, j]; ok = ~np.isnan(v); C[:, j] = np.interp(idx, idx[ok], v[ok])
k = np.array([1, 2, 3, 2, 1], np.float32); k /= k.sum()
Cs = np.array([np.convolve(np.pad(C[:, j], 2, mode='edge'), k, 'valid') for j in range(8)]).T
np.save(D + 'tube_corners.npy', Cs)
label = np.zeros((ah, aw), np.float32); label[int(0.075 * ah):int(0.835 * ah), :] = 1
label *= (aal > 200); label = cv2.GaussianBlur(cv2.erode(label, np.ones((9, 9), np.uint8)), (0, 0), 3)
def fill_holes(m):
    h, w = m.shape; ff = m.copy(); msk = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, msk, (0, 0), 255); return m | cv2.bitwise_not(ff)
def comp(i):
    f = F[i].astype(np.float32)
    Hn = cv2.getPerspectiveTransform(C0.reshape(-1, 2), Cs[i].reshape(4, 2).astype(np.float32))
    wa = cv2.warpPerspective(argb.astype(np.float32), Hn, (720, 1280), flags=cv2.INTER_AREA)
    wm = cv2.warpPerspective(label, Hn, (720, 1280))
    hsv = cv2.cvtColor(F[i], cv2.COLOR_BGR2HSV)
    tube = (((hsv[..., 2] > 150) & (hsv[..., 1] < 70)) & (wm > 0.05)).astype(np.uint8) * 255
    tube = cv2.morphologyEx(tube, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    tube = fill_holes(tube)                                           # Flow's printed text is replaced, fingers are not holes
    tm = cv2.GaussianBlur(cv2.erode(tube, np.ones((3, 3), np.uint8)).astype(np.float32) / 255, (0, 0), 1.2)
    m = wm * tm
    sel = m > 0.8
    if sel.sum() > 100:
        bright = sel & (cv2.cvtColor(wa.astype(np.uint8), cv2.COLOR_BGR2GRAY) > 200)
        if bright.sum() > 50:
            wa = wa * np.clip(np.median(f[bright], 0) / np.maximum(np.median(wa[bright], 0), 1), 0.7, 1.3)
    sc = np.hypot(*(Cs[i][2:4] - Cs[i][0:2])) / aw
    if sc < 0.9: wa = cv2.GaussianBlur(wa, (0, 0), 0.35)
    out = f * (1 - m[..., None]) + wa * m[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)
if OUT.endswith('.jpg'):
    sel = [30, 90, 150, 190, 230]
    def crop(i):
        c = Cs[i].reshape(4, 2); x0, y0 = c.min(0); x1, y1 = c.max(0); p = 30
        im = comp(i)[max(0, int(y0 - p)):int(y1 + p), max(0, int(x0 - p)):int(x1 + p)]
        return cv2.resize(im, (int(im.shape[1] * 420 / im.shape[0]), 420))
    cv2.imwrite(OUT, np.hstack([crop(i) for i in sel])); sys.exit()
w = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '720x1280', '-r', '24', '-i', '-',
                      '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for i in range(N): w.stdin.write(comp(i).tobytes())
w.stdin.close(); w.wait()
