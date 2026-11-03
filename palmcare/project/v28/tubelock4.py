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
# --- rigid (similarity) motion: the label never shears or leans; heavy temporal smoothing kills jitter ---
P = []
for i in range(N):
    M, _ = cv2.estimateAffinePartial2D(TQ, Cs[i].reshape(4, 2).astype(np.float32))
    sc = float(np.hypot(M[0, 0], M[1, 0])); ang = float(np.arctan2(M[1, 0], M[0, 0]))
    P.append([sc, ang, M[0, 2], M[1, 2]])
P = np.array(P)
kk2 = np.hanning(13); kk2 /= kk2.sum()
Ps = np.array([np.convolve(np.pad(P[:, j], 6, mode='edge'), kk2, 'valid') for j in range(4)]).T
def sim(i):
    sc, ang, tx, ty = Ps[i]
    return np.float64([[sc * np.cos(ang), -sc * np.sin(ang), tx], [sc * np.sin(ang), sc * np.cos(ang), ty], [0, 0, 1]])
# ink-only label: the real artwork as a ratio to its own white plastic (1 = no ink), pasted by multiplication,
# so there is no panel, no edge and Flow's own tube shading / light stays underneath
paper = cv2.GaussianBlur(cv2.dilate(argb, np.ones((25, 25), np.uint8)), (0, 0), 12)   # the plastic's own local white
ratio = np.clip(argb / np.maximum(paper, 1), 0, 1.0); ratio[aal < 200] = 1
band = np.zeros((ah, aw), np.float32); band[int(0.075 * ah):int(0.84 * ah), int(0.04 * aw):int(0.96 * aw)] = 1
band = cv2.GaussianBlur(band, (0, 0), 6); ratio = 1 + (ratio - 1) * band[..., None]
body = np.zeros((1280, 720), np.float32); cv2.fillConvexPoly(body, np.int32([[120, 430], [370, 434], [316, 990], [180, 990]]), 1)
def comp(i):
    f = F[i]; ff = f.astype(np.float32)
    Hk = sim(i)
    Ha = Hk @ A_key
    wr = cv2.warpPerspective(ratio.astype(np.float32), Ha, (720, 1280), flags=cv2.INTER_AREA, borderValue=(1, 1, 1))
    wb = cv2.warpPerspective(body, Hk, (720, 1280))
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    sat = ((hsv[..., 1] > 62) & (hsv[..., 0] < 30)).astype(np.uint8)          # warm skin hue + saturation (grey print is not skin)
    sat = cv2.morphologyEx(sat, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n_, lab_, _, _ = cv2.connectedComponentsWithStats(sat)
    keep = np.zeros(n_, bool); keep[np.unique(lab_[(wb < 0.5) & (sat > 0)])] = True; keep[0] = False
    skin = keep[lab_].astype(np.uint8)
    tube = ((wb > 0.5) & (skin == 0)).astype(np.uint8)
    # wipe Flow's garbled print: inpaint every darker/coloured mark on the tube (fingers excluded)
    loc = cv2.GaussianBlur(cv2.dilate(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), np.ones((9, 9), np.uint8)), (0, 0), 3).astype(np.float32)
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
    ink = (((loc - g) > 6) | (hsv[..., 1] > 34)) & (tube > 0)
    ink = cv2.dilate(ink.astype(np.uint8), np.ones((7, 7), np.uint8)) & tube
    clean = cv2.inpaint(f, ink * 255, 5, cv2.INPAINT_TELEA).astype(np.float32)
    clean = ff * (1 - tube[..., None]) + cv2.GaussianBlur(clean, (0, 0), 1.0) * tube[..., None]
    tm = cv2.GaussianBlur(cv2.erode(tube * 255, np.ones((3, 3), np.uint8)).astype(np.float32) / 255, (0, 0), 1.0)[..., None]
    out = clean * (1 - tm + tm * wr)                       # real ink printed on the tube's own surface
    return np.clip(out, 0, 255).astype(np.uint8)
if OUT.endswith('.jpg'):
    def crop(i):
        c = Cs[i].reshape(4, 2); x0, y0 = c.min(0); x1, y1 = c.max(0); p = 40
        im = comp(i)[max(0, int(y0 - p)):int(y1 + p), max(0, int(x0 - p)):int(x1 + p)]
        return cv2.resize(im, (int(im.shape[1] * 440 / im.shape[0]), 440))
    cv2.imwrite(OUT, np.hstack([crop(i) for i in (100, 125, 150, 175, 200)])); sys.exit()
w = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '720x1280', '-r', '24', '-i', '-',
                      '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for i in range(N): w.stdin.write(comp(i).tobytes())
w.stdin.close(); w.wait()
