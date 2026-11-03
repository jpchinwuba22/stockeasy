import sys, cv2, numpy as np
cap = cv2.VideoCapture(sys.argv[1]); t0, t1, step = map(float, sys.argv[2:5])
by = tuple(map(int, sys.argv[5].split(",")))   # rows for bottle edge (white body vs bg), x search range
ly = tuple(map(int, sys.argv[6].split(",")))   # rows for banner, x search range
def edge(g, y0, y1, x0, x1, kind):
    band = g[y0:y1, x0:x1].astype(np.float32)
    if kind == "o":   # orange banner: saturation jump
        prof = band.mean(0)
    else:
        prof = band.mean(0)
    d = np.abs(np.diff(cv2.GaussianBlur(prof.reshape(1, -1), (9, 1), 2).ravel()))
    return x0 + np.argmax(d) + 0.5
t = t0
while t <= t1:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * 24)); f = cap.read()[1]
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); s = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)[..., 1]
    print(f"{t:6.2f} bottle-edge {edge(g, *by, 'w'):7.1f}  banner-edge {edge(s, *ly, 'o'):7.1f}")
    t += step
