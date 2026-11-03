import sys, cv2, numpy as np
sys.path.insert(0, "remake"); import tl2b as tl
B = {2: ((395,752,697,914),(454,324,616,486)), 3: ((379,739,784,914),(298,194,816,421)),
     4: ((382,859,690,1069),(399,421,593,599)), 5: ((382,875,690,1085),(324,1166,437,1490)),
     8: ((411,923,671,1085),(460,518,622,697)), 9: ((366,914,684,1085),(318,1231,431,1490))}
cap = cv2.VideoCapture(sys.argv[1]); F = []
while True:
    ok, f = cap.read()
    if not ok: break
    F.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32))
def track(b, i0, i1):
    x0, y0, x1, y1 = b; pos, cur = [np.zeros(2)], np.zeros(2)
    w = cv2.createHanningWindow((x1 - x0, y1 - y0), cv2.CV_32F)
    for f0, f1 in zip(F[i0:i1 - 1], F[i0 + 1:i1]):
        (dx, dy), r = cv2.phaseCorrelate(f0[y0:y1, x0:x1], f1[y0:y1, x0:x1], w)
        cur = cur + [dx, dy]; pos.append(cur.copy())
    return np.array(pos)
for k, (L, R) in (B.items() if len(sys.argv) < 3 else []):
    a, d = tl.STARTS[k], tl.SHOTS[k][2]
    i0 = int((a + (0.55 if k not in (5, 8) else 0.05)) * 24); i1 = int((a + d - 0.05) * 24)
    Lt, Rt = track(L, i0, i1), track(R, i0, i1); rel = Lt - Rt
    print(f"shot {k} {tl.SHOTS[k][0]:5s} {a:5.2f}-{a+d:5.2f}  label {np.ptp(Lt[:,0]):4.1f},{np.ptp(Lt[:,1]):4.1f}  ref {np.ptp(Rt[:,0]):4.1f},{np.ptp(Rt[:,1]):4.1f}  rel {np.ptp(rel[:,0]):4.1f},{np.ptp(rel[:,1]):4.1f}  maxstep {np.abs(np.diff(rel,axis=0)).max():.2f}")
if len(sys.argv) > 2:
    k = int(sys.argv[2]); L = tuple(map(int, sys.argv[3].split(","))); R = tuple(map(int, sys.argv[4].split(",")))
    a, d = tl.STARTS[k], tl.SHOTS[k][2]; i0 = int(a * 24) + 1; i1 = int((a + d) * 24)
    Lt, Rt = track(L, i0, i1), track(R, i0, i1)
    for j in range(0, len(Lt), 6): print(f"{(i0+j)/24:6.2f} label {Lt[j][0]:6.1f},{Lt[j][1]:6.1f}  ref {Rt[j][0]:6.1f},{Rt[j][1]:6.1f}")
