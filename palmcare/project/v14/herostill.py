"""Real-jar hero, built from the real product photo on the citrus set (start_shot1.png): seated exactly on the pedestal,
smooth eased push-in, rising gold sparkles and a soft light sweep. Rock steady, no AI redraw. -> jar_hero.mp4 (3 s)"""
import math
import subprocess

import cv2
import numpy as np

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
W, H, FPS, DUR = 1080, 1920, 24, 3.0
base = cv2.imread(D + "v14/qa/hero_still.png").astype(np.float32)
rng = np.random.default_rng(7)
P = [(rng.uniform(0, W), rng.uniform(300, 1900), rng.uniform(2, 6), rng.uniform(40, 120), rng.uniform(0, 6.3)) for _ in range(120)]
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", D + "v14/hero_static.mp4"], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for i in range(n):
    t = i / FPS
    p = i / (n - 1)
    e = p * p * (3 - 2 * p)
    z = 1.0 + 0.10 * e
    cx, cy = W * 0.55, H * 0.55
    M = np.float32([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]])
    fr = cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    q = -0.4 + 1.8 * p                                                  # soft light sweep
    band = np.exp(-(((XX / W * 0.8 + YY / H * 0.6) - q) / 0.06) ** 2) * 0.22
    fr = 255 - (255 - fr) * (1 - band[..., None] * np.array([0.6, 0.85, 1.0], np.float32))
    ov = np.zeros((H, W), np.float32)
    for x0, y0, r, sp, ph in P:                                        # gold dust rising
        y = (y0 - sp * t) % H
        x = x0 + 12 * math.sin(t * 1.5 + ph)
        a = 0.5 + 0.5 * math.sin(t * 4 + ph)
        cv2.circle(ov, (int(x), int(y)), int(r), a, -1, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 1.6)[..., None]
    fr = fr * (1 - ov * 0.8) + np.array([110, 200, 255], np.float32) * ov * 0.8
    wr.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
wr.stdin.close(); wr.wait()
