import sys, cv2, numpy as np
sys.path.insert(0, "v2x"); sys.path.insert(0, "remake"); sys.path.insert(0, "labelfix")
from edges import measure
import tl2b as tl
from straight_edit_boxes import B
cap = cv2.VideoCapture(sys.argv[1]); out = []
for k in map(int, sys.argv[3].split(",")):
    b, n = B[k]; a, d = tl.STARTS[k], tl.SHOTS[k][2]
    cap.set(cv2.CAP_PROP_POS_FRAMES, int((a+d*0.5)*24)); f = cap.read()[1]
    e = measure(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), b, n)
    for sd in "LR":
        if e[sd]:
            _, kk, m, _ = e[sd]
            for y0, y1 in ((0, 1920),):
                cv2.line(f, (int(kk*y0+m), y0), (int(kk*y1+m), y1), (0, 0, 255), 2)
    x0, y0, x1, y1 = b
    pad = int((x1-x0)*0.6)
    crop = f[max(0, y0-int(2.2*(y1-y0))-150):min(1920, y1+int(3*(y1-y0))+80), max(0, x0-pad):min(1080, x1+pad)]
    crop = cv2.resize(crop, (int(crop.shape[1]*900/crop.shape[0]), 900))
    out.append(crop)
cv2.imwrite(sys.argv[2], np.hstack(out))
