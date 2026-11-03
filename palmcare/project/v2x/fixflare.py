"""Remove the green lens-flare ghost on the rooftop close-up (Clip 6, lower-left background): bright, saturated
green pixels (real foliage there is dark) are masked and inpainted from the surrounding blurred city.
Usage: fixflare.py IN.mp4 OUT.mp4"""
import subprocess
import sys

import cv2
import numpy as np
from scipy import ndimage

sys.path.insert(0, "labelfix")
from fixclip2 import read_frames, W, H, FPS  # noqa: E402

src, dst = sys.argv[1], sys.argv[2]
frames = read_frames(src)
out, hits = [], 0
for i, f in enumerate(frames):
    if i < 120:
        out.append(f)
        continue
    x0, y0, x1, y1 = 0, 1285, 340, 1480
    roi = f[y0:y1, x0:x1]
    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
    m = ((h > 45) & (h < 190) & (s > 0.20) & (v > 0.50)) | ((h > 45) & (h < 75) & (s > 0.30) & (v > 0.45))
    m = ndimage.binary_opening(m, iterations=1)
    lab, n = ndimage.label(m)
    if n:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        m = np.isin(lab, 1 + np.nonzero(sizes > 60)[0])
    if m.any():
        hits += 1
        m = ndimage.binary_dilation(m, iterations=12).astype(np.uint8) * 255
        fixed = cv2.inpaint(np.ascontiguousarray(roi), m, 9, cv2.INPAINT_TELEA)
        a = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 4)[..., None]
        g = f.copy()
        g[y0:y1, x0:x1] = (roi * (1 - a) + cv2.GaussianBlur(fixed, (0, 0), 3) * a).astype(np.uint8)
        # any leftover cyan/green tint from the flare's fringe: pull it to the neutral grey of the city behind
        r2 = g[y0:y1, x0:x1].astype(np.float32)
        hv = cv2.cvtColor(r2.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
        tint = ((hv[..., 0] * 2 > 90) & (hv[..., 0] * 2 < 210) & (hv[..., 1] > 25) & (hv[..., 2] > 110)).astype(np.float32)
        tint = cv2.GaussianBlur(tint, (0, 0), 3)[..., None] * a.clip(0, 1) ** 0.3
        grey = r2.mean(-1, keepdims=True)
        g[y0:y1, x0:x1] = (r2 * (1 - tint) + (grey * 0.6 + r2 * 0.4) * tint).astype(np.uint8)
        out.append(g)
    else:
        out.append(f)
    # teal flare fringe (hue 135-205; nothing else in this background has that hue): neutral grey, every frame
    g = out[-1].copy()
    r2 = g[y0:y1, x0:x1].astype(np.float32)
    hv = cv2.cvtColor(r2.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    tint = ((hv[..., 0] * 2 > 135) & (hv[..., 0] * 2 < 205) & (hv[..., 1] > 22)).astype(np.float32)
    tint = np.clip(cv2.GaussianBlur(tint, (0, 0), 5) * 1.6, 0, 1)[..., None]
    grey = r2.mean(-1, keepdims=True) * np.array([1.02, 1.0, 0.97])
    g[y0:y1, x0:x1] = (r2 * (1 - tint) + grey * tint).astype(np.uint8)
    out[-1] = g
print("frames cleaned", hits)
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                      "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "12", "-preset", "slow",
                      "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
for f in out:
    p.stdin.write(f.tobytes())
p.stdin.close()
p.wait()
