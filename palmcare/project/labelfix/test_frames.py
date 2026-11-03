import sys
sys.path.insert(0, "labelfix")
import numpy as np
from PIL import Image
import labelpatch as lp

MILKY = lp.Label("straight/out/milky.png", (0.07, 1.04, 0.07, 3.07))
CACAO = lp.Label("straight/out/cacao.png", (0.07, 1.75, 0.07, 3.4))
tests = [("D_1.5", [(MILKY, (230, 850, 520, 1080)), (CACAO, (580, 980, 840, 1140))]),
         ("B_1.0", [(MILKY, (330, 800, 740, 1080))]),
         ("E_1.0", [(CACAO, (340, 960, 720, 1200))]),
         ("A_6.8", [(MILKY, (40, 820, 330, 1010))]),
         ("E_8.5", [(CACAO, (170, 880, 400, 1020))])]
outs = []
for k, items in tests:
    fr = np.asarray(Image.open(f"v1n/fr/{k}.png").convert("RGB").resize((1080, 1920), Image.LANCZOS))
    res = fr
    for lbl, roi in items:
        b = lp.find_banner(fr, roi, close=6)
        print(k, b)
        T = lp.similarity_from_banner(lbl.banner, b)
        rgb, al = lp.render_patch(lbl, T, fr.shape[:2])
        res = lp.composite(res, rgb, al)
    pair = np.concatenate([fr, res], 1)
    outs.append(Image.fromarray(pair))
    Image.fromarray(res).save(f"labelfix/t_{k}.png")
s = Image.new("RGB", (2160 // 2 * 2, 960 * len(outs)))
for i, o in enumerate(outs):
    s.paste(o.resize((1080, 960)), (0, 960 * i))
s.save("labelfix/test_sheet.jpg", quality=88)
