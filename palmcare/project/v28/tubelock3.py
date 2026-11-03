# Lock the REAL GlowShield tube label onto Flow's tube. Key frame 170: the real artwork placed at TRUE proportions
# (uniform scale, centred on the tube, top on the crimp). Every other frame: Flow's tube tracked by SIFT homography
# (key frame -> frame, RANSAC, using the tube's own texture), smoothed. Flow's garbled print is wiped from the white body
# (holes in the white mask are filled, fingers stay in front), then the real label is laid on. Usage: tubelock2.py OUT
import subprocess, sys, os
import cv2, numpy as np
D = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v28/'
OUT = sys.argv[1]; KEY = 170
art = cv2.imread(D + 'assets/tube_cut.png', cv2.IMREAD_UNCHANGED); ah, aw = art.shape[:2]
argb = art[..., :3].astype(np.float32); aal = art[..., 3]
N = len(os.listdir(D + 'tf')); F = [cv2.imread(D + f'tf/{i:04d}.png') for i in range(1, N + 1)]
S = 0.35; TOPC = np.array([(111 + 379) / 2, 404.0])
A_key = np.float64([[S, 0, TOPC[0] - S * aw / 2], [0, S, TOPC[1]], [0, 0, 1]])
TQ = np.float32([[113, 408], [377, 412], [318, 975], [176, 975]])               # Flow tube body on the key frame
km = np.zeros((1280, 720), np.uint8); cv2.fillConvexPoly(km, TQ.astype(np.int32), 255)
sift = cv2.SIFT_create(8000)
kk, dk = sift.detectAndCompute(cv2.cvtColor(F[KEY - 1], cv2.COLOR_BGR2GRAY), km)
G = [cv2.GaussianBlur(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (0, 0), 1.2).astype(np.float32) for f in F]
crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 120, 1e-6)
def direct(i):
    kf, df = sift.detectAndCompute(cv2.cvtColor(F[i], cv2.COLOR_BGR2GRAY), None)
    m = [a for a, b in cv2.BFMatcher().knnMatch(dk, df, k=2) if a.distance < 0.75 * b.distance]
    if len(m) < 20: return None, 0
    Hh, inl = cv2.findHomography(np.float32([kk[x.queryIdx].pt for x in m]), np.float32([kf[x.trainIdx].pt for x in m]), cv2.RANSAC, 3.0)
    return (Hh, int(inl.sum())) if Hh is not None else (None, 0)
Hs = [None] * N; Hs[KEY - 1] = np.eye(3)
nre = 0
for seq in (range(KEY, N), range(KEY - 2, -1, -1)):
    prev = KEY - 1
    for i in seq:
        Hp = Hs[prev]
        mk = cv2.warpPerspective(km, Hp, (720, 1280))                     # tube region in the previous frame
        w = np.eye(3, dtype=np.float32)
        try:
            _, w = cv2.findTransformECC(G[prev], G[i], w, cv2.MOTION_HOMOGRAPHY, crit, mk, 5)
            Hi = w.astype(np.float64) @ Hp
        except cv2.error:
            Hi = Hp
        Hd, n = direct(i)
        if Hd is not None and n >= 60:                                    # strong direct fit: re-anchor (kills drift)
            d = np.abs(cv2.perspectiveTransform(TQ.reshape(-1, 1, 2), Hd) - cv2.perspectiveTransform(TQ.reshape(-1, 1, 2), Hi)).max()
            if d < 25: Hi = Hd; nre += 1
        Hs[i] = Hi; prev = i
print('re-anchored', nre, 'of', N)
Q = TQ.reshape(-1, 1, 2)
C = np.array([cv2.perspectiveTransform(Q, h).reshape(-1) if h is not None else np.full(8, np.nan) for h in Hs])
idx = np.arange(N)
for j in range(8):
    v = C[:, j]; ok = ~np.isnan(v); C[:, j] = np.interp(idx, idx[ok], v[ok])
k = np.array([1, 2, 3, 4, 3, 2, 1], np.float32); k /= k.sum()
Cs = np.array([np.convolve(np.pad(C[:, j], 3, mode='edge'), k, 'valid') for j in range(8)]).T
label = np.zeros((ah, aw), np.float32); label[int(0.075 * ah):int(0.84 * ah), :] = 1
label *= (aal > 200); label = cv2.GaussianBlur(cv2.erode(label, np.ones((7, 7), np.uint8)), (0, 0), 2)
body = np.zeros((1280, 720), np.float32); cv2.fillConvexPoly(body, np.int32([[120, 430], [370, 434], [314, 962], [180, 962]]), 1)
def fill_holes(m):
    ff = m.copy(); msk = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, msk, (0, 0), 255); return m | cv2.bitwise_not(ff)
def comp(i):
    f = F[i].astype(np.float32)
    Hk = cv2.getPerspectiveTransform(TQ, Cs[i].reshape(4, 2).astype(np.float32))      # key -> frame i
    Ha = Hk @ A_key                                                                    # art -> frame i
    wa = cv2.warpPerspective(argb, Ha, (720, 1280), flags=cv2.INTER_AREA)
    wl = cv2.warpPerspective(label, Ha, (720, 1280))
    wb = cv2.warpPerspective(body, Hk, (720, 1280))
    hsv = cv2.cvtColor(F[i], cv2.COLOR_BGR2HSV)
    sat = ((hsv[..., 1] > 62) | (hsv[..., 2] < 95)).astype(np.uint8)
    sat = cv2.morphologyEx(sat, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n_, lab_, st_, _ = cv2.connectedComponentsWithStats(sat)
    outside = (wb < 0.5)
    keep = np.zeros(n_, bool)                                                     # fingers reach in from outside the tube;
    hit = np.unique(lab_[outside & (sat > 0)]); keep[hit] = True; keep[0] = False   # the print (leaf, letters) sits inside it
    skin = cv2.dilate(keep[lab_].astype(np.uint8), np.ones((5, 5), np.uint8))
    white = ((wb > 0.5) & (skin == 0)).astype(np.uint8) * 255
    tm = cv2.GaussianBlur(cv2.erode(white, np.ones((3, 3), np.uint8)).astype(np.float32) / 255, (0, 0), 1.0)
    # clean white plate (Flow's print removed): smooth shading of the tube's own white
    sel = white > 0
    plate = cv2.GaussianBlur(cv2.dilate(f, np.ones((15, 15), np.uint8)), (0, 0), 9)
    out = f * (1 - tm[..., None]) + plate * tm[..., None]
    m = wl * tm
    br = (m > 0.8) & (cv2.cvtColor(wa.astype(np.uint8), cv2.COLOR_BGR2GRAY) > 200)
    if br.sum() > 50: wa = wa * np.clip(np.median(plate[br], 0) / np.maximum(np.median(wa[br], 0), 1), 0.7, 1.3)
    out = out * (1 - m[..., None]) + wa * m[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)
if OUT.endswith('.jpg'):
    def crop(i):
        c = Cs[i].reshape(4, 2); x0, y0 = c.min(0); x1, y1 = c.max(0); p = 40
        im = comp(i)[max(0, int(y0 - p)):int(y1 + p), max(0, int(x0 - p)):int(x1 + p)]
        return cv2.resize(im, (int(im.shape[1] * 440 / im.shape[0]), 440))
    cv2.imwrite(OUT, np.hstack([crop(i) for i in (5, 70, 125, 169, 235)])); sys.exit()
w = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '720x1280', '-r', '24', '-i', '-',
                      '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for i in range(N): w.stdin.write(comp(i).tobytes())
w.stdin.close(); w.wait()
