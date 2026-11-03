# Clip 2 (new model holding the box): lock the REAL text band (Face Moisturiser / Brightening . Hydrating . Tone
# Refining / 30 mL | 1.0 fl. oz.) onto Flow's box. Per-frame SIFT homography real art -> frame (RANSAC), corner
# smoothing, light/gain match, feathered band mask that stays clear of her fingers. Usage: boxband.py OUT(.mp4|.jpg)
import subprocess, sys
import cv2, numpy as np
D = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
SRC, OUT = D + 'v27/clip2b.mp4', sys.argv[1]
W, H = 720, 1280
art = cv2.imread(D + 'remo/public/box_straight.png', cv2.IMREAD_UNCHANGED)
if art.shape[2] == 4:
    ys, xs = np.nonzero(art[..., 3] > 8); art = art[ys.min():ys.max() + 1, xs.min():xs.max() + 1, :3]
ah, aw = art.shape[:2]
p = subprocess.run(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
F = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
sift = cv2.SIFT_create(5000)
ka, da = sift.detectAndCompute(cv2.cvtColor(art, cv2.COLOR_BGR2GRAY), None)
roi = np.zeros((H, W), np.uint8); roi[650:1020, 180:600] = 255
Hs, ok = [], []
for f in F:
    kf, df = sift.detectAndCompute(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), roi)
    m = [a for a, b in cv2.BFMatcher().knnMatch(da, df, k=2) if a.distance < 0.75 * b.distance]
    Hh, inl = (cv2.findHomography(np.float32([ka[x.queryIdx].pt for x in m]), np.float32([kf[x.trainIdx].pt for x in m]), cv2.RANSAC, 3.0)
               if len(m) >= 12 else (None, None))
    Hs.append(Hh); ok.append(0 if Hh is None else int(inl.sum()))
print('inliers min/median', min(ok), int(np.median(ok)))
C0 = np.float32([[0, 0], [aw, 0], [aw, ah], [0, ah]]).reshape(-1, 1, 2)
C = np.array([cv2.perspectiveTransform(C0, h).reshape(-1) if h is not None else np.full(8, np.nan) for h in Hs])
for j in range(8):                                                     # fill failures, then smooth
    v = C[:, j]; idx = np.arange(len(v)); good = ~np.isnan(v); C[:, j] = np.interp(idx, idx[good], v[good])
k = np.array([1, 2, 3, 2, 1], np.float32); k /= k.sum()
Cs = np.array([np.convolve(np.pad(C[:, j], 2, mode='edge'), k, 'valid') for j in range(8)]).T
band = np.zeros((ah, aw), np.float32)
band[int(0.665 * ah):int(0.95 * ah), int(0.11 * aw):int(0.79 * aw)] = 1           # text band, left of the photo face
band = cv2.GaussianBlur(band, (0, 0), 0.012 * aw)
artf = art.astype(np.float32)
def comp(i):
    f = F[i].astype(np.float32)
    Hn = cv2.getPerspectiveTransform(C0.reshape(-1, 2), Cs[i].reshape(4, 2).astype(np.float32))
    wa = cv2.warpPerspective(artf, Hn, (W, H), flags=cv2.INTER_AREA)
    wm = cv2.warpPerspective(band, Hn, (W, H))
    m = wm > 0.6
    if m.sum() > 50:                                                     # match the box's light in the band
        g = np.median(f[m], 0) / np.maximum(np.median(wa[m], 0), 1)
        wa = wa * np.clip(g, 0.75, 1.3)
    wa = cv2.GaussianBlur(wa, (0, 0), 0.5)
    out = f * (1 - wm[..., None]) + wa * wm[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)
if OUT.endswith('.jpg'):
    cv2.imwrite(OUT, np.hstack([comp(i)[700:980, 200:580] for i in (24, 120, 230)])); sys.exit()
w = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '24', '-i', '-', '-i', SRC,
                      '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-shortest', OUT], stdin=subprocess.PIPE)
for i in range(len(F)): w.stdin.write(comp(i).tobytes())
w.stdin.close(); w.wait()
