# Minimal fix on the Flow clip: ONLY the garbled small lines on the tube are replaced with the real ones (from the real
# tube photo). Flow's tube, PalmCare logo, leaf, GLOWSHIELD, her hand: untouched. The patch is tracked on Flow's own
# logo/leaf/GLOWSHIELD (affine, key 170 -> frame, refined by ECC every frame, lightly smoothed), so it cannot drift
# against them. Usage: smalltext.py OUT.mp4 | smalltext.py SHEET.jpg
import sys, os, subprocess
import cv2, numpy as np
OUT = sys.argv[1]; S = 1.5; KEY = 169
N = len(os.listdir('tf')); F = [cv2.imread(f'tf/{i:04d}.png') for i in range(1, N + 1)]
Ps = np.load('track_Ps.npy')
def sim(i):
    s_, a_, tx, ty = Ps[i]
    return np.float32([[s_ * np.cos(a_), -s_ * np.sin(a_), tx], [s_ * np.sin(a_), s_ * np.cos(a_), ty]])
# ---- tracking on Flow's own big print (rows 455-740, inside the tube, away from fingers)
G = [cv2.GaussianBlur(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (0, 0), 1.0).astype(np.float32) for f in F]
km = np.zeros((1280, 720), np.uint8); km[452:742, 186:322] = 255
crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
A = {}
R0, R1 = 96, 216
A[KEY] = np.float32([[1, 0, 0], [0, 1, 0]])
def ok(w, prev):                                                          # reject jumps / divergence
    return np.all(np.isfinite(w)) and abs(w[0, 0] - prev[0, 0]) < 0.06 and abs(w[1, 1] - prev[1, 1]) < 0.06 and np.abs(w[:, 2] - prev[:, 2]).max() < 25
for seq in (range(KEY + 1, R1), range(KEY - 1, R0 - 1, -1)):
    prev = KEY
    for i in seq:
        w = A[prev].copy()
        try:
            _, w2 = cv2.findTransformECC(G[KEY], G[i], w.copy(), cv2.MOTION_AFFINE, crit, km, 3)
            w = w2 if ok(w2, A[prev]) else w
        except cv2.error: pass
        A[i] = w; prev = i
P = np.array([A[i].reshape(-1) for i in range(R0, R1)])
k = np.array([1, 2, 3, 2, 1], np.float32); k /= k.sum()
Psm = np.array([np.convolve(np.pad(P[:, j], 2, mode='edge'), k, 'valid') for j in range(6)]).T
# ---- key-frame layer (1080 space): real lines as ink ratio + wipe bands
t = cv2.imread('assets/tube_cut.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
tg = t[..., :3]; paper = cv2.GaussianBlur(cv2.dilate(tg, np.ones((25, 25), np.uint8)), (0, 0), 10)
ratio_full = np.clip(tg / np.maximum(paper, 1), 0, 1.0)
ratio_full = np.where(ratio_full.mean(2, keepdims=True) > 0.86, 1.0, ratio_full)   # ink only: no grey panel
sc = 0.3533 * S
cx_real, cx_flow = 428.0, 253.5 * S
def place(layer, r0, r1, y_top):                                          # real rows r0..r1 -> key rows from y_top
    crop = ratio_full[r0:r1, 150:700]
    h = int(round((r1 - r0) * sc)); w = int(round(crop.shape[1] * sc))
    c = cv2.resize(crop, (w, h), interpolation=cv2.INTER_AREA)
    x0 = int(round(cx_flow - (428 - 150) * sc)); y0 = int(round(y_top))
    layer[y0:y0 + h, x0:x0 + w] = np.minimum(layer[y0:y0 + h, x0:x0 + w], c)
L = np.ones((1920, 1080, 3), np.float32)
place(L, 280, 333, 495 * S)                     # "Advanced Skin Care" under Flow's PalmCare
place(L, 960, 1232, 745 * S)                    # description, SPF 50+ PA++++, 50 mL | 1.7 fl. oz. under GLOWSHIELD
WIPE = np.zeros((1920, 1080), np.uint8)
cv2.rectangle(WIPE, (int(158 * S), int(493 * S)), (int(340 * S), int(518 * S)), 255, -1)
cv2.rectangle(WIPE, (int(156 * S), int(741 * S)), (int(340 * S), int(854 * S)), 255, -1)
Sm = np.float32([[S, 0, 0], [0, S, 0], [0, 0, 1]]); Si = np.linalg.inv(Sm)
def frame(i):
    f = cv2.resize(F[i], (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
    if not (R0 <= i < R1): return f
    a = np.vstack([Psm[i - R0].reshape(2, 3), [0, 0, 1]]).astype(np.float32)
    M = (Sm @ a @ Si)[:2]
    wipe = cv2.warpAffine(WIPE, M, (1080, 1920), flags=cv2.INTER_NEAREST)
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    skin = ((hsv[..., 1] > 60) & (hsv[..., 0] < 25)).astype(np.uint8)
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    skin = cv2.dilate(skin, np.ones((7, 7), np.uint8))
    hole = ((wipe > 0) & (skin == 0)).astype(np.uint8) * 255
    clean = cv2.inpaint(f, hole, 7, cv2.INPAINT_TELEA).astype(np.float32)
    clean = np.where(hole[..., None] > 0, cv2.GaussianBlur(clean, (0, 0), 2.0), f.astype(np.float32))
    lay = cv2.warpAffine(L, M, (1080, 1920), flags=cv2.INTER_LINEAR, borderValue=(1, 1, 1))
    lay = cv2.GaussianBlur(lay, (0, 0), 0.6)
    lay = 1 - (1 - lay) * (skin == 0)[..., None]                          # fingers stay in front
    return np.clip(clean * lay, 0, 255).astype(np.uint8)
if OUT.endswith('.jpg'):
    for i in (106, 150, 169, 207): print(i, np.round(Psm[i - R0], 3))
    def crop(i):
        return cv2.resize(frame(i)[450:1650, 0:760], (380, 600))
    cv2.imwrite(OUT, np.hstack([crop(i) for i in (106, 125, 150, 169, 190, 207)])); sys.exit()
w = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1080x1920', '-r', '24', '-i', '-',
                      '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for i in range(N): w.stdin.write(frame(i).tobytes())
w.stdin.close(); w.wait()
