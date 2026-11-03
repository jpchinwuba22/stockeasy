"""Banner boxes per sampled time. Usage: findb.py CLIP label t1,t2,.. [roi] [min_fill]"""
import sys
sys.path.insert(0, "labelfix")
import labelpatch as lp, fixclip3 as f3
from fixclip2 import read_frames
fr = read_frames(sys.argv[1]); name = sys.argv[2]; f3.use_mask(name); lbl = lp.Label(*f3.LABELS[name])
asp = (lbl.banner[2]-lbl.banner[0])/(lbl.banner[3]-lbl.banner[1])
roi = [int(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else (0, 0, 1080, 1920)
mf = float(sys.argv[5]) if len(sys.argv) > 5 else 0.6
print("cutout banner", lbl.banner, "aspect", round(asp, 2))
for t in sys.argv[3].split(","):
    i = min(len(fr)-1, int(float(t)*24))
    print(t, lp.find_banner(fr[i], roi, aspect=asp*0.9, close=6, min_fill=mf))
