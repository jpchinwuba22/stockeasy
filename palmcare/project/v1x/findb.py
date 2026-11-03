"""Report banner boxes found per sampled frame. Usage: findb.py CLIP label t1,t2,.. [roi]"""
import sys
sys.path.insert(0, "labelfix")
import labelpatch as lp, fixclip3 as f3
from fixclip2 import read_frames
fr = read_frames(sys.argv[1]); lbl = lp.Label(*f3.LABELS[sys.argv[2]])
asp = (lbl.banner[2]-lbl.banner[0])/(lbl.banner[3]-lbl.banner[1])
roi = [int(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else (0, 0, 1080, 1920)
for t in sys.argv[3].split(","):
    i = int(float(t)*24)
    print(t, lp.find_banner(fr[i], roi, aspect=asp*0.9, close=6, min_fill=0.6))
