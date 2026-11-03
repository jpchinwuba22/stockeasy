"""Find a bottle's straight outer body edges by line search: the line x = m + k*(y - ymid) over the body's full height
with the highest mean horizontal gradient (long body edges win over shorter label edges)."""
import sys, cv2, numpy as np
def frame(path, t):
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * 24))); f = cap.read()[1]
    return cv2.resize(f, (1080, 1920), interpolation=cv2.INTER_LANCZOS4) if f.shape[1] != 1080 else f
def edges(img, y0, y1, xl, xr, band=22):
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0)
    gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3))
    ys = np.arange(y0, y1, 2); ym = (y0 + y1) / 2
    res = []
    for xc in (xl, xr):
        best = (-1, 0, 0)
        for k in np.linspace(-0.12, 0.12, 121):
            for m in np.arange(xc - band, xc + band, 0.5):
                xs = m + k * (ys - ym)
                xi = np.clip(xs, 0, 1078); x0 = xi.astype(int); fr = xi - x0
                v = gx[ys, x0] * (1 - fr) + gx[ys, x0 + 1] * fr
                s = np.median(v) * 0.5 + v.mean() * 0.5
                if s > best[0]: best = (s, k, m)
        res.append(best)
    return res, ym
if __name__ == "__main__":
    R = {"C2": (2.5, 580, 1360, 370, 740), "C1B": (1.0, 690, 1470, 350, 724), "C3": (1.6, 690, 1470, 346, 724),
         "C4": (2.5, 760, 1470, 386, 700), "C5": (1.5, 740, 1470, 344, 696)}
    which = sys.argv[1] if len(sys.argv) > 1 else "src"
    for c, (t, y0, y1, xl, xr) in R.items():
        path = f"v2x/src/{c}.mp4" if which == "src" else f"v2x/{which}/{ {'C1B': 'C1B_s1'}.get(c, c)}.mp4"
        f = frame(path, t)
        (sl, kl, ml), (sr, kr, mr), ym = *edges(f, y0, y1, xl, xr)[0], edges(f, y0, y1, xl, xr)[1]
        wt, wb = (mr + kr * (y0 - ym)) - (ml + kl * (y0 - ym)), (mr + kr * (y1 - ym)) - (ml + kl * (y1 - ym))
        print(f"{c:4s} L {np.degrees(np.arctan(kl)):+.2f}deg x {ml:.1f} (s{sl:.0f})  R {np.degrees(np.arctan(kr)):+.2f}deg x {mr:.1f} (s{sr:.0f})  width top {wt:.1f} bottom {wb:.1f}")
