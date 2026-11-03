# Blend the leftover cream patches on both cheeks (clip 3, after the hand leaves the face) into the surrounding skin.
# Only pale, raised-brightness blobs inside cheek zones are pulled to the local skin base (L, a, b), nothing else.
import cv2, numpy as np, os
N = len(os.listdir('f3'))
REF = 168                                                       # 7.0 s: cheek patches at (220,530) and (490,517)
G = lambda i: cv2.GaussianBlur(cv2.imread(f'f3/{i:04d}.png', 0), (0, 0), 2).astype(np.float32)
fm = np.zeros((1280, 720), np.uint8); fm[230:780, 120:600] = 255
crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5)
A = {REF: np.float32([[1, 0, 0], [0, 1, 0]])}
for seq in (range(REF + 1, N + 1), range(REF - 1, 120, -1)):
    prev = REF
    for i in seq:
        w = A[prev].copy()
        try: _, w = cv2.findTransformECC(G(REF), G(i), w, cv2.MOTION_AFFINE, crit, fm, 5)
        except cv2.error: pass
        A[i] = w; prev = i
CHEEKS = [(220, 530), (490, 517)]
os.makedirs('f3c', exist_ok=True)
START = 128                                                     # hand has left the cheek (~5.3 s); ramp in over 10 frames
for i in range(1, N + 1):
    f = cv2.imread(f'f3/{i:04d}.png')
    w = np.clip((i - START) / 10, 0, 1)
    if w > 0:
        Z = np.zeros(f.shape[:2], np.float32)
        M = A.get(i, A[REF]); sc = float(np.hypot(*M[:, 0]))
        for cx, cy in CHEEKS:                                   # cheek ellipses tracked from the reference frame
            px, py = M @ np.array([cx, cy, 1.0])
            cv2.ellipse(Z, (int(px), int(py)), (int(78 * sc), int(58 * sc)), 0, 0, 360, 1, -1)
        Z = cv2.GaussianBlur(Z, (0, 0), 6)
        lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.float32)
        base = cv2.medianBlur(lab.astype(np.uint8), 31).astype(np.float32)
        ex = np.clip((lab[..., 0] - base[..., 0] - 2) / 6, 0, 1)
        pale = np.clip(((base[..., 1] - lab[..., 1]) + (base[..., 2] - lab[..., 2])) / 6 + 0.3, 0, 1)
        m = cv2.GaussianBlur(ex * pale, (0, 0), 2.5) * Z * w
        lab = lab * (1 - m[..., None]) + base * m[..., None]
        f = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    cv2.imwrite(f'f3c/{i:04d}.png', f)
print('done', N)
