"""Clip 7 (Vitamin C box): lock the REAL box-front artwork over Flow's front face (garbled tagline) for the front-on
section 4.95-6.03 s. ECC homography tracking of the face (reference frame 5.95 s), light smoothing, real art scaled
uniformly to the face width and bottom-aligned, light-matched, feathered top edge into the plain white of the box."""
import subprocess, sys
import cv2, numpy as np
D = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
W, H = 720, 1280
A, B = 4.95, 6.03
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(A), '-t', str(B - A), '-i', D + 'v22/src/c7.mp4', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
fr = []
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    fr.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
ref = len(fr) - 2
Q = np.float32([[80, 445], [645, 445], [645, 940], [80, 940]])          # face corners on the reference frame
g = lambda x: cv2.GaussianBlur(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY), (0, 0), 1.5).astype(np.float32)
m = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(m, Q.astype(np.int32), 255); m = cv2.erode(m, np.ones((15, 15), np.uint8))
G0 = g(fr[ref])
Hs = [None] * len(fr)
Hs[ref] = np.eye(3, dtype=np.float32)
for direction in (-1, 1):
    Hm = np.eye(3, dtype=np.float32)
    i = ref + direction
    while 0 <= i < len(fr):
        try:
            _, Hm = cv2.findTransformECC(G0, g(fr[i]), Hm, cv2.MOTION_HOMOGRAPHY,
                                         (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-5), m, 5)
        except cv2.error:
            pass
        Hs[i] = Hm.copy()
        i += direction
C = np.array([cv2.perspectiveTransform(Q[None], np.linalg.inv(h))[0] if True else None for h in Hs])   # ref->frame mapping
k = np.array([1, 2, 3, 2, 1], np.float32); k /= k.sum()
Cs = np.stack([np.convolve(np.pad(C[:, a, b], 2, mode='edge'), k, mode='valid') for a in range(4) for b in range(2)], 1).reshape(-1, 4, 2)
art = cv2.imread(D + 'remo/public/p/box_straight.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
ah, aw = art.shape[:2]
out = []
for f, q in zip(fr, Cs):
    # face rectangle in frame: width spans the face; the art is bottom-aligned with its own aspect (no stretch)
    tl, tr, br, bl = q
    fw = np.linalg.norm(tr - tl); fh = np.linalg.norm(bl - tl)
    ar = ah / aw
    t = 1 - min(1.0, ar * fw / fh)                                   # fraction of face height above the art
    pad = int(round(ah * t / max(1e-3, 1 - t)))                      # extend the art upward with its own plain top rows
    artp = np.concatenate([np.repeat(np.repeat(art[2:6, 10:300].reshape(-1, 4).mean(0)[None, None], aw, 1), pad, 0), art], 0) if pad > 0 else art
    ph = artp.shape[0]
    Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [aw, 0], [aw, ph], [0, ph]]), np.float32([tl, tr, br, bl]))
    wa = cv2.warpPerspective(artp, Hm, (W, H), flags=cv2.INTER_AREA)
    al = wa[..., 3]
    # real art mirrored into the glossy table (replaces Flow's reflection)
    flip = artp[::-1].copy()
    fade = np.linspace(0.32, 0, ph)[:, None] ** 1.3
    flip[..., 3] *= fade
    rq = np.float32([bl, br, br + (br - tr), bl + (bl - tl)])
    Hr = cv2.getPerspectiveTransform(np.float32([[0, 0], [aw, 0], [aw, ph], [0, ph]]), np.float32([bl, br, br + (br - tr), bl + (bl - tl)]))
    wr_ = cv2.warpPerspective(flip, Hr, (W, H), flags=cv2.INTER_AREA)
    wr_[..., :3] = cv2.GaussianBlur(wr_[..., :3], (0, 0), 2)
    # remove Flow's reflection under the box first: fill from the clean table just below
    rmask = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(rmask, rq.astype(np.int32), 1)
    al = cv2.GaussianBlur(al, (0, 0), 0.7)
    ff = f.astype(np.float32) / 255
    tbl = cv2.GaussianBlur(ff, (0, 0), 18)
    rm = cv2.GaussianBlur(rmask.astype(np.float32), (0, 0), 6)[..., None]
    ff = ff * (1 - rm * 0.85) + tbl * rm * 0.85
    ff = ff * (1 - wr_[..., 3:]) + wr_[..., :3] * wr_[..., 3:]
    sel = al > 0.95
    gain = np.clip(np.median(ff[sel], 0) / np.maximum(np.median(wa[..., :3][sel], 0), 1e-3), 0.85, 1.15)
    rgb = np.clip(wa[..., :3] * gain, 0, 1)
    rgb = cv2.GaussianBlur(rgb, (0, 0), 0.5)
    o = ff * (1 - al[..., None]) + rgb * al[..., None]
    out.append((np.clip(o, 0, 1) * 255).astype(np.uint8))
if len(sys.argv) > 1 and sys.argv[1].endswith('.jpg'):
    cv2.imwrite(sys.argv[1], np.hstack([cv2.resize(out[i], (360, 640)) for i in (0, len(out) // 2, len(out) - 1)]))
    sys.exit()
wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '24', '-i', '-',
                       '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', D + 'v22/c7_fixed.mp4'], stdin=subprocess.PIPE)
for o in out: wr.stdin.write(o.tobytes())
wr.stdin.close(); wr.wait(); print('ok', len(out))
