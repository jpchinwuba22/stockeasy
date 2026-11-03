# Real Molecular Glow label onto the Flow bottle (frames 355-391): logo-anchored similarity fit, real label blocks
# re-spaced to the Flow bottle's taller face, ECC-tracked, light/gain matched.
import cv2, numpy as np, os
REF, N0, N1 = 373, 355, 392
r = cv2.imread('../remo/public/p/molecular_cut.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
H = np.load('Hm_ref.npy')
ref = cv2.imread(f'frm/{REF:04d}.png').astype(np.float32)
rw = np.median(r[960:1020, 60:410, :3].reshape(-1, 3), 0)
ratio = np.clip(r[..., :3] / rw, 0, 1.2); ratio[r[..., 3] < 200] = 1
canvas = np.ones((1500, r.shape[1], 3), np.float32)
for a, b, d in [(540, 935, 15), (1035, 1130, 60), (1212, 1247, 105), (1255, 1292, 152)]:
    canvas[a + d:b + d] = ratio[a:b]
XL, XR, YT, YB = 24, 446, 512, 1452                          # band in (re-spaced) real coordinates
Wr = cv2.warpPerspective(canvas, H, (1080, 1920), flags=cv2.INTER_CUBIC, borderValue=(1, 1, 1))
band = np.zeros((1500, r.shape[1]), np.float32); band[YT:YB, XL:XR] = 1
M = cv2.warpPerspective(band, H, (1080, 1920), flags=cv2.INTER_LINEAR)
ys, xs = np.where(M > 0.5); y0, y1, x0, x1 = ys.min() - 4, ys.max() + 5, xs.min() - 4, xs.max() + 5
print('band bbox', y0, y1, x0, x1)
top = cv2.GaussianBlur(ref[y0 - 3:y0 + 1].max(0)[None], (0, 0), 14)[0]; bot = cv2.GaussianBlur(ref[y1:y1 + 4].max(0)[None], (0, 0), 14)[0]
t = np.linspace(0, 1, y1 - y0)[:, None, None]
fill = cv2.GaussianBlur(top[None] * (1 - t) + bot[None] * t, (0, 0), 3)
patch = ref.copy(); patch[y0:y1] = fill * Wr[y0:y1]
M = cv2.GaussianBlur(M, (0, 0), 4)
fmask = np.zeros((1920, 1080), np.uint8); fmask[550:1720, 260:860] = 255
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
Hs = [HD[n] for n in range(N0, N1)]
Q = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]).reshape(-1, 1, 2)
C = np.array([cv2.perspectiveTransform(Q, h).reshape(-1) for h in Hs])
k = np.array([1, 2, 3, 2, 1], np.float32); k /= k.sum()
Cs = np.array([np.convolve(np.pad(C[:, j], 2, mode='edge'), k, 'valid') for j in range(8)]).T
os.makedirs('fxm', exist_ok=True)
for i, n in enumerate(range(N0, N1)):
    f = cv2.imread(f'frm/{n:04d}.png').astype(np.float32)
    Hn = cv2.getPerspectiveTransform(Q.reshape(-1, 2), Cs[i].reshape(4, 2).astype(np.float32))
    P = cv2.warpPerspective(patch, Hn, (1080, 1920), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    m = cv2.warpPerspective(M, Hn, (1080, 1920))[..., None]
    gm = []
    for yy in (y0 - 6, y1 + 2):
        pt = cv2.perspectiveTransform(np.float32([[[x0 + 60, yy]], [[x1 - 60, yy + 4]]]), Hn).reshape(-1, 2).astype(int)
        gm.append(f[pt[0, 1]:pt[1, 1] + 1, pt[0, 0]:pt[1, 0]].reshape(-1, 3).mean(0) / ref[yy:yy + 5, x0 + 60:x1 - 60].reshape(-1, 3).mean(0))
    gm = np.mean(gm, 0); P = P * (gm if np.all(np.isfinite(gm)) else 1)
    out = f * (1 - m) + P * m + np.random.normal(0, 1.2, f.shape).astype(np.float32) * m
    cv2.imwrite(f'fxm/{n:04d}.png', np.clip(out, 0, 255).astype(np.uint8))
print('done')
