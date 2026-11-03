"""Measure how straight a bottle stands: find its left and right body edges row by row (strongest horizontal
luminance step inside windows placed from the orange name banner), fit lines, report each edge's lean in degrees
(0 = perfectly vertical; left and right leaning opposite ways = keystone 'bent' look).
Usage: edges.py CLIP.mp4 label t [roi]   (import: measure(frame, banner, name) -> dict)"""
import sys

import cv2
import numpy as np

sys.path.insert(0, "labelfix")
import labelpatch as lp  # noqa: E402
import fixclip3 as f3  # noqa: E402

# bottle body width / banner width, banner-to-body vertical spans (in banner heights) from the straight cutouts
GEOM = {"citrus": (1.23, -1.0, 2.6), "molecular": (1.19, -1.2, 2.6), "milky": (1.25, -1.0, 2.5), "cacao": (1.25, -1.0, 2.5)}


def measure(frame, b, name):
    x0, y0, x1, y1 = b[:4]
    bw, bh = x1 - x0, y1 - y0
    ratio, up, down = GEOM[name]
    cx = (x0 + x1) / 2
    half = bw * ratio / 2
    g = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 1.5)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    out = {}
    for side, xc in (("L", cx - half), ("R", cx + half)):
        pts = []
        for y in np.linspace(y0 + up * bh, y1 + down * bh, 40).astype(int):
            if not 0 <= y < frame.shape[0]:
                continue
            a, c = int(max(0, xc - 0.16 * bw)), int(min(frame.shape[1] - 1, xc + 0.16 * bw))
            row = np.abs(gx[y, a:c])
            if row.size and row.max() > 6:
                pts.append((y, a + int(np.argmax(row))))
        if len(pts) < 10:
            out[side] = None
            continue
        P = np.array(pts, float)
        # robust fit: drop the worst 30% residuals twice
        for _ in range(2):
            k, m = np.polyfit(P[:, 0], P[:, 1], 1)
            r = np.abs(P[:, 1] - (k * P[:, 0] + m))
            P = P[r <= np.percentile(r, 70)]
        k, m = np.polyfit(P[:, 0], P[:, 1], 1)
        out[side] = (float(np.degrees(np.arctan(k))), float(k), float(m), float(np.median(np.abs(P[:, 1] - (k * P[:, 0] + m)))))
    return out


if __name__ == "__main__":
    from fixclip2 import read_frames
    clip, name, t = sys.argv[1], sys.argv[2], float(sys.argv[3])
    roi = [int(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else (0, 0, 1080, 1920)
    fr = read_frames(clip)[min(int(t * 24), 239)]
    f3.use_mask(name)
    lbl = lp.Label(*f3.LABELS[name])
    asp = (lbl.banner[2] - lbl.banner[0]) / (lbl.banner[3] - lbl.banner[1])
    b = lp.find_banner(fr, roi, aspect=asp * 0.9, close=6, min_fill=0.6)
    if b is None:
        print("no banner")
        sys.exit()
    e = measure(fr, b, name)
    print(f"banner {tuple(int(v) for v in b[:4])}  L {e['L'][0] if e['L'] else None:+.2f}deg  R {e['R'][0] if e['R'] else None:+.2f}deg  "
          f"(fit err L {e['L'][3] if e['L'] else 0:.1f}px R {e['R'][3] if e['R'] else 0:.1f}px)")
