"""Remove the old AI print remnant left of '1000mL' on the pool clip: inpaint pixels clearly darker than the white
label around them, inside a small box, frames 0-120."""
import subprocess, sys
import cv2, numpy as np
sys.path.insert(0, "labelfix")
from fixclip2 import read_frames, W, H, FPS
src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = 378, 1316, 412, 1356
F = read_frames(src); n = 0
for i in range(0, 121):
    f = F[i].copy()
    roi = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY).astype(np.float32)
    m = (np.abs(roi - np.median(roi)) > 14).astype(np.uint8)
    if m.any():
        mask = np.zeros(f.shape[:2], np.uint8); mask[y0:y1, x0:x1] = cv2.dilate(m, np.ones((3, 3)), 1) * 255
        F[i] = cv2.inpaint(f, mask, 4, cv2.INPAINT_TELEA); n += 1
print("frames cleaned", n)
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "10", "-preset", "medium",
                      "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
for f in F: p.stdin.write(np.ascontiguousarray(f).tobytes())
p.stdin.close(); p.wait()
