"""Straighten a product bottle in a raw clip. Its outer body edges are found by line search on a key frame; each
row is then stretched horizontally about the bottle axis so the body is exactly as wide at the base as at the
shoulder, with the axis made vertical (no row is ever squeezed, so the frame always stays filled: no zoom, no
crop). Rows above / below the body take the end values, eased over 120 px so the background has no kink.
Frames outside the product range are untouched.
Usage: kfix.py SRC OUT 't0,t1,tm,y0,y1,xl,xr,band'"""
import subprocess, sys
import cv2, numpy as np
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, "v2x"); sys.path.insert(0, "labelfix")
from linesearch import edges
from fixclip2 import read_frames, W, H, FPS


def maps(kl, ml, kr, mr, ym, y0, y1):
    y = np.arange(H, dtype=np.float64)
    yc = np.clip(y, y0, y1)
    xl, xr = ml + kl * (yc - ym), mr + kr * (yc - ym)
    w, c = xr - xl, (xl + xr) / 2
    s = gaussian_filter1d(w.max() / w, 40, mode="nearest")        # >= 1 everywhere: rows only ever widen
    c = gaussian_filter1d(c, 40, mode="nearest")
    c0 = c[int(round(ym))]
    X = np.arange(W, dtype=np.float64)
    mx = (c[:, None] + (X[None, :] - c0) / s[:, None]).astype(np.float32)
    my = np.repeat(y[:, None], W, 1).astype(np.float32)
    return mx, my, s, c0


if __name__ == "__main__":
    src, dst, spec = sys.argv[1], sys.argv[2], sys.argv[3]
    t0, t1, tm, y0, y1, xl, xr, band = map(float, spec.split(","))
    F = read_frames(src)
    key = cv2.cvtColor(F[int(round(tm * 24))], cv2.COLOR_RGB2BGR)
    (a, b), ym = edges(key, int(y0), int(y1), xl, xr, band=band)
    (_, kl, ml), (_, kr, mr) = a, b
    mx, my, s, c0 = maps(kl, ml, kr, mr, ym, y0, y1)
    print(f"before: L {np.degrees(np.arctan(kl)):+.2f}deg R {np.degrees(np.arctan(kr)):+.2f}deg  width {mr - ml:.1f}  max row stretch {s.max():.4f}")
    i0, i1 = int(round(t0 * 24)), int(round(t1 * 24))
    out = [cv2.remap(f, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE) if i0 <= i < i1 else f for i, f in enumerate(F)]
    chk = cv2.cvtColor(out[int(round(tm * 24))], cv2.COLOR_RGB2BGR)
    w_new = (mr - ml) * s[int(round(ym))]
    (a2, b2), _ = edges(chk, int(y0), int(y1), c0 - w_new / 2, c0 + w_new / 2, band=band)
    print(f"after:  L {np.degrees(np.arctan(a2[1])):+.2f}deg R {np.degrees(np.arctan(b2[1])):+.2f}deg  width {b2[2] - a2[2]:.1f}")
    cv2.imwrite(dst.replace(".mp4", "_chk.jpg"), np.hstack([key, chk])[::2, ::2])
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "8", "-preset", "medium",
                           "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
    for f in out:
        pr.stdin.write(np.ascontiguousarray(f).tobytes())
    pr.stdin.close(); pr.wait()
