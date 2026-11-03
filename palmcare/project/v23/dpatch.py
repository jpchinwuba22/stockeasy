# Lock the real Dermalight label panel onto the Flow bottle (frames 392-465), ECC-tracked from a reference frame.
import cv2, numpy as np
REF, N0, N1 = 430, 392, 466
r = cv2.imread('../remo/public/p/dermalight_cut.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
H = np.load('H_ref.npy')                                     # real -> ref frame (fits logo/bottom text horizontally)
ref = cv2.imread(f'fr/{REF:04d}.png').astype(np.float32)
Y0, Y1, X0, X1 = 893, 1438, 104, 492                         # band between logo and "Advanced UV" on the bottle face
# smooth label-white shading of the ref frame across the band (interpolated from clean rows above/below)
top = cv2.blur(ref[Y0 - 6:Y0], (1, 1)).mean(0); bot = ref[Y1:Y1 + 6].mean(0)
t = np.linspace(0, 1, Y1 - Y0)[:, None, None]
fill = top[None] * (1 - t) + bot[None] * t
fill = cv2.GaussianBlur(fill, (0, 0), 3)
# real panel as a ratio to its own label white, shifted so it sits in the band with the real spacing
rw = np.median(r[930:1000, 60:440, :3].reshape(-1, 3), 0)
ratio = np.clip(r[..., :3] / rw, 0, 1.2)
ratio[r[..., 3] < 200] = 1
ratio[:540] = 1; ratio[905:] = 1
DY = -20
T = np.float32([[1, 0, 0], [0, 1, DY], [0, 0, 1]])
Wr = cv2.warpPerspective(ratio, H @ T, (1080, 1920), flags=cv2.INTER_CUBIC, borderValue=(1, 1, 1))
patch = ref.copy()
patch[Y0:Y1, X0:X1] = fill[:, X0:X1] * Wr[Y0:Y1, X0:X1]
M = np.zeros((1920, 1080), np.float32); M[Y0:Y1, X0:X1] = 1
# second band: the "ACTIVE GLOW - FAST ABSORBING" line (Flow misspelt it)
B0, B1 = 1582, 1618
ratio2 = np.clip(r[..., :3] / rw, 0, 1.2); ratio2[r[..., 3] < 200] = 1; ratio2[:1165] = 1; ratio2[1215:] = 1
Wr2 = cv2.warpPerspective(ratio2, H, (1080, 1920), flags=cv2.INTER_CUBIC, borderValue=(1, 1, 1))
t2 = np.linspace(0, 1, B1 - B0)[:, None, None]
fill2 = cv2.GaussianBlur(ref[B0 - 5:B0].mean(0)[None] * (1 - t2) + ref[B1:B1 + 5].mean(0)[None] * t2, (0, 0), 3)
patch[B0:B1, X0:X1] = fill2[:, X0:X1] * Wr2[B0:B1, X0:X1]
M[B0:B1, X0:X1] = 1
M = cv2.GaussianBlur(M, (0, 0), 7)
M[Y0 + 14:Y1 - 14, X0 + 14:X1 - 14] = 1
fmask = np.zeros((1920, 1080), np.uint8); fmask[450:1760, 80:530] = 255  # track the Dermalight bottle only
gref = cv2.GaussianBlur(cv2.cvtColor(ref.astype(np.uint8), cv2.COLOR_BGR2GRAY), (0, 0), 1.5).astype(np.float32)
Hs = {}
crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
for n in range(N0, N1):
    g = cv2.GaussianBlur(cv2.imread(f'fr/{n:04d}.png', 0), (0, 0), 1.5).astype(np.float32)
    w = np.eye(3, dtype=np.float32)
    try: _, w = cv2.findTransformECC(gref, g, w, cv2.MOTION_HOMOGRAPHY, crit, fmask, 5)
    except cv2.error as e: print('ecc fail', n)
    Hs[n] = w
# temporal smoothing of the tracked corners
Q = np.float32([[X0, Y0], [X1, Y0], [X1, Y1], [X0, Y1]]).reshape(-1, 1, 2)
C = np.array([cv2.perspectiveTransform(Q, Hs[n]).reshape(-1) for n in range(N0, N1)])
k = np.array([1, 2, 3, 2, 1], np.float32); k /= k.sum()
Cs = np.array([np.convolve(np.pad(C[:, j], 2, mode='edge'), k, 'valid') for j in range(8)]).T
os_ = 'fx'; import os; os.makedirs(os_, exist_ok=True)
for i, n in enumerate(range(N0, N1)):
    f = cv2.imread(f'fr/{n:04d}.png').astype(np.float32)
    Hn = cv2.getPerspectiveTransform(Q.reshape(-1, 2), Cs[i].reshape(4, 2).astype(np.float32)) @ np.linalg.inv(
        cv2.getPerspectiveTransform(Q.reshape(-1, 2), Q.reshape(-1, 2)))
    P = cv2.warpPerspective(patch, Hn, (1080, 1920), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    m = cv2.warpPerspective(M, Hn, (1080, 1920))[..., None]
    # gain match: frame white vs ref white just above/below the band
    gm = []
    for yy in (Y0 - 8, Y1 + 4):
        pt = cv2.perspectiveTransform(np.float32([[[X0 + 40, yy]], [[X1 - 40, yy + 4]]]), Hn).reshape(-1, 2).astype(int)
        a = f[pt[0, 1]:pt[1, 1] + 1, pt[0, 0]:pt[1, 0]].reshape(-1, 3).mean(0)
        b = ref[yy:yy + 5, X0 + 40:X1 - 40].reshape(-1, 3).mean(0)
        gm.append(a / b)
    P = P * np.mean(gm, 0)
    out = f * (1 - m) + P * m
    out += np.random.normal(0, 1.2, out.shape).astype(np.float32) * m
    cv2.imwrite(f'fx/{n:04d}.png', np.clip(out, 0, 255).astype(np.uint8))
print('done')
