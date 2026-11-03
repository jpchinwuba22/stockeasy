import cv2, numpy as np
j = cv2.imread('jar_cut_orig.png', -1); g = cv2.cvtColor(j[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
bg = cv2.GaussianBlur(g, (0, 0), 15)
ink = np.clip((bg - g) / 60, 0, 1) * (j[..., 3] > 200)
guides = {  # name: (x0, x1, guide curve from rough read, half window)
 'logo':  (228, 500, lambda x: 486 + 0 * x, 26),
 'vitc':  (330, 495, lambda x: 532 + 0 * x, 9),
 'face':  (228, 480, lambda x: np.interp(x, [227, 350, 479], [563, 561, 554]), 9),
 'rule':  (228, 600, lambda x: np.interp(x, [227, 350, 460, 535, 591], [579, 573, 562, 550, 532]), 6),
 'brt':   (228, 600, lambda x: np.interp(x, [229, 350, 460, 491, 540, 591], [592, 590, 586, 576, 564, 545]), 9),
 'ml':    (228, 410, lambda x: 618 + 0 * x, 8)}
out = {}
for k, (x0, x1, gd, hw) in guides.items():
    xs, ys = [], []
    for x in range(x0, x1 - 12, 8):
        c = int(gd(x + 6)); w = ink[c - hw:c + hw, x:x + 12]
        s = w.sum()
        if s > (2 if k == 'rule' else 6):
            xs.append(x + 6); ys.append(c - hw + (w.sum(1) * np.arange(w.shape[0])).sum() / s)
    xs, ys = np.array(xs), np.array(ys)
    deg = 3 if k in ('rule', 'brt') else (2 if k == 'face' else 1)
    p = np.polyfit(xs, ys, deg); res = ys - np.polyval(p, xs)
    out[k] = (p, xs.min(), xs.max())
    print(k, 'n', len(xs), 'fit', np.round(np.polyval(p, [xs.min(), (xs.min() + xs.max()) / 2, xs.max()]), 1), 'resid sd', round(float(res.std()), 2))
np.save('curves.npy', out, allow_pickle=True)
