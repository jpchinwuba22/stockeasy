"""Label drift relative to the bottle: track bottle body texture (pump + bottle edges, outside the label) and the
label itself frame to frame; report how much the label moves relative to the bottle (pixels)."""
import sys, cv2, numpy as np
sys.path.insert(0, "labelfix")
from fixclip2 import read_frames
clip, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
lab = [int(v) for v in sys.argv[4].split(",")]      # label box (inside)
bot = [int(v) for v in sys.argv[5].split(",")]      # bottle reference box (pump/shoulder, no label)
F = read_frames(clip)
i0, i1 = int(t0 * 24), min(len(F), int(t1 * 24))
g = [cv2.cvtColor(F[i], cv2.COLOR_RGB2GRAY).astype(np.float32) for i in range(i0, i1)]
def track(box):
    x0, y0, x1, y1 = box
    pos, cur = [np.zeros(2)], np.zeros(2)
    for a, b in zip(g[:-1], g[1:]):
        (dx, dy), r = cv2.phaseCorrelate(a[y0:y1, x0:x1], b[y0:y1, x0:x1])
        cur = cur + [dx, dy]
        pos.append(cur.copy())
    return np.array(pos)
L, B = track(lab), track(bot)
rel = L - B
print(f"bottle moved {np.ptp(B[:,0]):.1f},{np.ptp(B[:,1]):.1f}px  label-vs-bottle drift range x {np.ptp(rel[:,0]):.1f} y {np.ptp(rel[:,1]):.1f}px  max step {np.abs(np.diff(rel,axis=0)).max():.1f}px")
