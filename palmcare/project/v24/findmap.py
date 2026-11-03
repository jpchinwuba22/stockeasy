import cv2, numpy as np, subprocess
def read(path, w, h, vf=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', path] + (['-vf', vf] if vf else []) + ['-f', 'rawvideo', '-pix_fmt', 'gray', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.uint8).reshape(-1, h, w)
P = read('../v17/P_fixed.mp4', 360, 640, 'scale=360:640')
F = read('cur.mp4', 360, 640, 'scale=360:640')
s = cv2.SIFT_create(1500)
kp = [s.detectAndCompute(p, None) for p in P]
bf = cv2.BFMatcher()
for f in (150, 165, 180, 200, 230, 260, 275, 285):
    kf, df = s.detectAndCompute(F[f], None)
    best = (0, -1, None)
    for i, (k, d) in enumerate(kp):
        if d is None or df is None: continue
        m = [a for a, b in bf.knnMatch(d, df, k=2) if a.distance < 0.7 * b.distance]
        if len(m) < 8: continue
        pa = np.float32([k[a.queryIdx].pt for a in m]); pb = np.float32([kf[a.trainIdx].pt for a in m])
        M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=2)
        if M is not None and inl.sum() > best[0]: best = (int(inl.sum()), i, M)
    print(f, best[1], best[0], None if best[2] is None else np.round([np.hypot(*best[2][:, 0]), best[2][0, 2], best[2][1, 2]], 2))
