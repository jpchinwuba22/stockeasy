import sys, cv2, numpy as np
sys.path.insert(0, "v2x"); sys.path.insert(0, "remake"); sys.path.insert(0, "labelfix")
from edges import measure
import tl2b as tl
B = {2: ((395,752,697,914),"citrus"), 3: ((379,739,784,914),"citrus"), 4: ((382,859,690,1069),"citrus"),
     5: ((382,875,690,1085),"citrus"), 8: ((411,923,671,1085),"molecular"), 9: ((366,914,684,1085),"molecular")}
cap = cv2.VideoCapture(sys.argv[1])
for k,(b,n) in B.items():
    a,d = tl.STARTS[k], tl.SHOTS[k][2]
    for frac in (0.3, 0.7):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((a+d*frac)*24)); f = cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2RGB)
        e = measure(f, b, n)
        s = "  ".join(f"{sd} {e[sd][0]:+.2f}deg err{e[sd][3]:.1f}" if e[sd] else f"{sd} --" for sd in "LR")
        print(f"shot {k} {tl.SHOTS[k][0]:5s} t={a+d*frac:5.2f}  {s}")
