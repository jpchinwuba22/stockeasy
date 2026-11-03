"""For each product shot in the edit: find the orange label banner, then track it and the pump/cap above it."""
import sys, cv2, numpy as np
sys.path.insert(0, "remake")
import tl2b as tl
cap = cv2.VideoCapture(sys.argv[1])
F = []
while True:
    ok, f = cap.read()
    if not ok: break
    F.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) if True else None)
cap = cv2.VideoCapture(sys.argv[1]); C = []
for k in [int((a + d / 2) * 24) for (c, s, d, *_), a in zip(tl.SHOTS, tl.STARTS)]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, k); C.append(cap.read()[1])
for k in map(int, sys.argv[2].split(",")):
    a, d = tl.STARTS[k], tl.SHOTS[k][2]
    hsv = cv2.cvtColor(C[k], cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 0] >= 7) & (hsv[..., 0] <= 20) & (hsv[..., 1] > 140) & (hsv[..., 2] > 80)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    i = 1 + np.argmax([s[4] if s[2] < s[3] * 4 and s[2] > 60 else 0 for s in st[1:]])
    x, y, w, h = st[i][:4]
    L = (x, y, x + w, y + h)
    P = (x + w // 6, max(0, y - int(2.6 * h)), x + w - w // 6, y - int(1.3 * h))
    i0, i1 = int((a + 0.55) * 24), int((a + d - 0.05) * 24)
    def track(b):
        x0, y0, x1, y1 = b; pos, cur = [np.zeros(2)], np.zeros(2)
        win = cv2.createHanningWindow((x1 - x0, y1 - y0), cv2.CV_32F)
        for f0, f1 in zip(F[i0:i1 - 1], F[i0 + 1:i1]):
            (dx, dy), r = cv2.phaseCorrelate(f0[y0:y1, x0:x1], f1[y0:y1, x0:x1], win)
            cur = cur + [dx, dy]; pos.append(cur.copy())
        return np.array(pos)
    print(k, L, P, flush=True)
    if P[3] - P[1] < 8: continue
    Lt, Pt = track(L), track(P)
    rel = Lt - Pt
    print(f"shot {k:2d} {tl.SHOTS[k][0]:5s} banner {L} | label moved {np.ptp(Lt[:,0]):.1f},{np.ptp(Lt[:,1]):.1f}  cap moved {np.ptp(Pt[:,0]):.1f},{np.ptp(Pt[:,1]):.1f}  label-vs-cap {np.ptp(rel[:,0]):.1f},{np.ptp(rel[:,1]):.1f}px  max step {np.abs(np.diff(rel,axis=0)).max():.2f}")
