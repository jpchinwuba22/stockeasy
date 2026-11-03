"""End-card plate for Video 2 from the label-fixed packshot (one still frame, so the bottles can never drift):
1. remove the glass block in front of the lotion (the 'eyes'): rebuild the lotion's lower body from its own plain
   white rows, shaded like the body wash's base; rebuild the table under it with a contact shadow
2. remove the AI's leftover '1000mL' print under the body-wash label
Then render a 16-beat clip: slow push-in on the still (+ the faint shimmer of the original light, kept subtle).
Usage: ecplate.py IN_FRAME.png OUT_PLATE.png OUT_CLIP.mp4 SECONDS"""
import subprocess
import sys

import cv2
import numpy as np

src, out_png, out_mp4, dur = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
a = cv2.cvtColor(cv2.imread(src), cv2.COLOR_BGR2RGB).astype(np.float32)
H, W = a.shape[:2]
rng = np.random.default_rng(4)

# ---- 2. body wash: leftover AI print rows -> plain bottle (vertical interpolation per column)
y0, y1, x0, x1 = 1414, 1454, 150, 535
top, bot = a[y0 - 3:y0].mean(0), a[y1:y1 + 3].mean(0)
for k, y in enumerate(range(y0, y1)):
    t = (k + 0.5) / (y1 - y0)
    a[y, x0:x1] = top[x0:x1] * (1 - t) + bot[x0:x1] * t
a[y0:y1, x0:x1] += rng.normal(0, 1.2, (y1 - y0, x1 - x0, 1))

# ---- 1. lotion lower body
LX0, LX1, BODY_TOP, BASE = 591, 830, 1384, 1489
base_row = np.median(a[1318:1346], axis=0)                     # plain white between the label lines
# body-wash shading from the same height range to its base, normalised
cw = a[1458:1494, 180:380].mean(1).mean(-1)
shade = np.interp(np.linspace(0, 1, BASE - BODY_TOP), np.linspace(0, 1, len(cw)), cw / cw[0])
for k, y in enumerate(range(BODY_TOP, BASE)):
    a[y, LX0:LX1] = base_row[LX0:LX1] * shade[k]
# seamless join with the label's plain white just above
for k, y in enumerate(range(1382, BODY_TOP + 8)):
    t = (k + 0.5) / (BODY_TOP + 8 - 1382)
    a[y, LX0 + 40:LX1 - 6] = a[1381, LX0 + 40:LX1 - 6] * (1 - t) + a[BODY_TOP + 9, LX0 + 40:LX1 - 6] * t
# rounded bottom corners + edge darkening like the body wash
edge = np.ones(LX1 - LX0)
edge[:8] = np.linspace(0.86, 1, 8)
edge[-8:] = np.linspace(1, 0.86, 8)
a[BODY_TOP:BASE, LX0:LX1] *= edge[None, :, None]
a[BODY_TOP:BASE, LX0:LX1] += rng.normal(0, 1.1, (BASE - BODY_TOP, LX1 - LX0, 1))

# ---- gap between the bottles: smooth vertical blend from the background above to the table below
gx0, gx1, gy0, gy1 = 509, LX0, 1378, 1548
top, bot = a[gy0 - 4:gy0].mean(0), a[gy1:gy1 + 4].mean(0)
for k, y in enumerate(range(gy0, gy1)):
    t = ((k + 0.5) / (gy1 - gy0)) ** 1.3
    a[y, gx0:gx1] = top[gx0:gx1] * (1 - t) + bot[gx0:gx1] * t
a[gy0:gy1, gx0:gx1] += rng.normal(0, 1.4, (gy1 - gy0, gx1 - gx0, 1))

# ---- table under the lotion (inside the old glass footprint): inpaint, then table grain and a contact shadow
m = np.zeros((H, W), np.uint8)
m[BASE:1545, 505:800] = 255                                    # table under the old block

img8 = np.clip(a, 0, 255).astype(np.uint8)
fill = cv2.inpaint(img8, m, 12, cv2.INPAINT_TELEA).astype(np.float32)
grain = a[BASE:1545, 130:410] - cv2.GaussianBlur(a[BASE:1545, 130:410], (0, 0), 3)   # table texture
ys, xs = np.nonzero(m)
tex = np.zeros_like(a)
tex[BASE:1545, 505:785] = grain[:, :280]
mf = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 3)[..., None]
a = a * (1 - mf) + (fill + tex * 0.9) * mf
# contact shadow under the lotion, matching the body wash's
sh = np.zeros((H, W), np.float32)
cv2.ellipse(sh, ((LX0 + LX1) // 2, BASE + 4), ((LX1 - LX0) // 2 + 10, 12), 0, 0, 360, 1, -1)
sh = cv2.GaussianBlur(sh, (0, 0), 7) * 0.32
a = a * (1 - sh[..., None])
# the bottle edge at the base stays crisp
a[BASE - 2:BASE, LX0:LX1] *= 0.93

plate = np.clip(a, 0, 255).astype(np.uint8)
cv2.imwrite(out_png, cv2.cvtColor(plate, cv2.COLOR_RGB2BGR))

# ---- clip: slow push-in (1.00 -> 1.06) centred on the bottles, eased
n = round(dur * 24)
cx, cy = 520, 1080
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24", "-i", "-",
                      "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "12",
                      "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out_mp4], stdin=subprocess.PIPE)
base = plate.astype(np.float32)
for i in range(n):
    q = i / max(1, n - 1)
    e = q * q * (3 - 2 * q)
    z = 1.0 + 0.06 * e
    M = np.float32([[z, 0, cx - cx * z], [0, z, cy - cy * z]])
    fr = cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    fr = fr + rng.normal(0, 1.0, (H, W, 1))                    # keep a living grain (no frozen-frame look)
    p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
p.stdin.close()
p.wait()
print("plate + clip", n, "frames")
