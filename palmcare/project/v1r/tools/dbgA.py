import sys, numpy as np, runpy
sys.path.insert(0, "labelfix")
import labelpatch as lp, fixclip3 as f3
from fixclip2 import read_frames, key_matrix, render
from PIL import Image
fr = read_frames("v1n/A.mp4")
lbl = lp.Label(*f3.LABELS["milky"])
aspect = (lbl.banner[2] - lbl.banner[0]) / (lbl.banner[3] - lbl.banner[1])
i = 144
b = lp.find_banner(fr[i], (40, 760, 400, 1020), aspect=aspect * 0.9, close=6, min_fill=0.6)
M = key_matrix(lbl, lp.similarity_from_banner(lbl.banner, b))
rgb, al = render(lbl, M)
a = f3.composite(fr[i], rgb, al, occlude_skin=False)
c = f3.composite(fr[i], rgb, al, occlude_skin=True)
d = lp.composite(fr[i], rgb, al, occlude_skin=True)
row = np.concatenate([x[650:1400, 0:450] for x in (fr[i], a, c, d)], 1)
Image.fromarray(row).save("v1r/dbgA.png")
