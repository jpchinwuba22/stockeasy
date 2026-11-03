# Molecular Glow (frames 355-391): replace the WHOLE front label with the real one, in true proportion (uniform scale to
# the sticker width, anchored at the sticker top so the real logo lands on Flow's logo), following the bottle's lean with
# a perspective map; Flow's sticker area (old citrus label, orange edge strip) is wiped to clean white first.
# ECC homography tracking from the reference frame, smoothed; light/gain matched; fine grain.
import cv2, numpy as np, os
REF, N0, N1 = 373, 355, 392
r = cv2.imread('../remo/public/p/molecular_cut.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
ref = cv2.imread(f'frm/{REF:04d}.png').astype(np.float32)
H, W = ref.shape[:2]
rw = np.median(r[880:980, 80:400, :3].reshape(-1, 3), 0)                     # real label paper
ratio = np.clip(r[..., :3] / rw, 0, 1.15); ratio[r[..., 3] < 200] = 1
RL = np.float32([[42, 339], [450, 339], [450, 1350], [42, 1350]])               # real label sticker
tl, tr = np.array([318, 656.]), np.array([681, 656.])
s = (tr[0] - tl[0]) / (450 - 42); yb = 656 + s * (1350 - 339)
lean_l, lean_r = 23 / 1031, 33 / 1031
FL = np.float32([tl, tr, [681 - (yb - 656) * lean_r, yb], [318 - (yb - 656) * lean_l, yb]])
Hm = cv2.getPerspectiveTransform(RL, FL)
Wr = cv2.warpPerspective(ratio, Hm, (W, H), flags=cv2.INTER_AREA, borderValue=(1, 1, 1))
# Flow sticker (to be wiped): full height of the old label
ST = np.float32([[312, 646], [688, 646], [656, 1696], [288, 1696]])
M = np.zeros((H, W), np.float32); cv2.fillConvexPoly(M, ST.astype(np.int32), 1)
y0, y1 = 640, 1704
top = cv2.GaussianBlur(ref[y0 - 4:y0].max(0)[None], (0, 0), 10)[0]; bot = cv2.GaussianBlur(ref[y1:y1 + 4].max(0)[None], (0, 0), 10)[0]
t = np.linspace(0, 1, y1 - y0)[:, None, None]
fill = cv2.GaussianBlur(top[None] * (1 - t) + bot[None] * t, (0, 0), 3)
patch = ref.copy(); patch[y0:y1] = fill * Wr[y0:y1]
M = cv2.GaussianBlur(M, (0, 0), 3)
fmask = np.zeros((H, W), np.uint8); fmask[550:1720, 260:760] = 255
gref = cv2.GaussianBlur(cv2.cvtColor(ref.astype(np.uint8), cv2.COLOR_BGR2GRAY), (0, 0), 1.5).astype(np.float32)
crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
HD = {REF: np.eye(3, dtype=np.float32)}
for seq in (range(REF + 1, N1), range(REF - 1, N0 - 1, -1)):
    prev = REF
    for n in seq:
        g = cv2.GaussianBlur(cv2.imread(f'frm/{n:04d}.png', 0), (0, 0), 1.5).astype(np.float32)
        w = HD[prev].copy()
        try: _, w = cv2.findTransformECC(gref, g, w, cv2.MOTION_HOMOGRAPHY, crit, fmask, 5)
        except cv2.error: print('ecc fail', n)
        HD[n] = w; prev = n
Q = np.float32([[300, 640], [700, 640], [700, 1704], [300, 1704]]).reshape(-1, 1, 2)
C = np.array([cv2.perspectiveTransform(Q, HD[n]).reshape(-1) for n in range(N0, N1)])
k = np.array([1, 2, 3, 2, 1], np.float32); k /= k.sum()
Cs = np.array([np.convolve(np.pad(C[:, j], 2, mode='edge'), k, 'valid') for j in range(8)]).T
os.makedirs('fxm2', exist_ok=True)
for i, n in enumerate(range(N0, N1)):
    f = cv2.imread(f'frm/{n:04d}.png').astype(np.float32)
    Hn = cv2.getPerspectiveTransform(Q.reshape(-1, 2), Cs[i].reshape(4, 2).astype(np.float32))
    P = cv2.warpPerspective(patch, Hn, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    m = cv2.warpPerspective(M, Hn, (W, H))[..., None]
    gm = []
    for yy in (y0 - 6, y1 + 2):
        pt = cv2.perspectiveTransform(np.float32([[[360, yy]], [[640, yy + 4]]]), Hn).reshape(-1, 2).astype(int)
        a = f[pt[0, 1]:pt[1, 1] + 1, pt[0, 0]:pt[1, 0]].reshape(-1, 3)
        if len(a): gm.append(a.mean(0) / ref[yy:yy + 5, 360:640].reshape(-1, 3).mean(0))
    gmv = np.mean(gm, 0) if gm else np.ones(3)
    P = P * (gmv if np.all(np.isfinite(gmv)) else 1)
    out = f * (1 - m) + P * m + np.random.normal(0, 1.2, f.shape).astype(np.float32) * m
    cv2.imwrite(f'fxm2/{n:04d}.png', np.clip(out, 0, 255).astype(np.uint8))
print('done')
