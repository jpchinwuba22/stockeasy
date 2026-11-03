import sys, cv2, numpy as np
sys.path.insert(0, "v2x"); from bodyedge import frame, fit
R = {"C2": (2.5, (354,545,389,1385), (739,545,737,1385)),
     "C1B": (1.0, (336,641,371,1525), (739,641,725,1525)),
     "C3": (1.6, (336,650,368,1490), (734,650,714,1490)),
     "C4": (2.5, (375,740,396,1520), (707,740,697,1520)),
     "C5": (1.5, (333,720,350,1550), (676,720,690,1550))}
out = []
for c, (t, L, Rr) in R.items():
    f = frame(f"v2x/src/{c}.mp4", t); vis = f.copy()
    res = []
    for rough in (L, Rr):
        k, m, err, n = fit(f, rough); res.append((k, m))
        cv2.line(vis, (int(m + k * 300), 300), (int(m + k * 1700), 1700), (0, 0, 255), 2)
        print(f"{c} {'LR'[len(res)-1]} {np.degrees(np.arctan(k)):+.2f}deg  x@600={m+k*600:.1f} x@1500={m+k*1500:.1f} err {err:.1f} n {n}")
    out.append(cv2.resize(vis[300:1700, 200:900], (350, 700)))
cv2.imwrite("v2x/kmeasure.jpg", np.hstack(out))
