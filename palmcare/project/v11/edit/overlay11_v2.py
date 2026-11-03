"""Video 6 v2 graphics over base11.mov, in the same "citrus editorial" system as the approved body (whose graphics are
already burnt into video9h): a serif product lower-third when she names the product, frosted citrus chips on key words
only, a "glow." headline on the glow cutaway, warm light-leak bursts on the big cuts. No running captions.
Usage: overlay11.py OUT.mp4 | overlay11.py SHEET.jpg t1,t2,..."""
import math
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v9/edit")
import overlay9 as o   # noqa: E402  (shared helpers: chip, serif, pop, life, shadowed, …)
from build11 import STARTS, TOTAL   # noqa: E402

W, H, FPS = 1080, 1920, 24
BASE = "base11.mov"
A, B, C1, C2, D1, D2, E, EC = STARTS[:8]
SAY = lambda clip_src_t, seg_start, seg_src_in: seg_start + (clip_src_t - seg_src_in)   # noqa: E731

NAME_CAPS = o.shadowed(o.text_img("P A L M C A R E", o.font(o.CAPS, 30), o.CREAM + (255,), tracking=4, pad=4), 10, 0.6)
NAME_SERIF = o.shadowed(o.serif("Vitamin C Face Moisturiser", 76, True, "cream"), 14, 0.6)
GLOW = o.shadowed(o.serif("glow.", 210, True, "citrus"), 18, 0.55)


def lower_third(img, t, s, e, y=1610):
    a = o.life(t, s, e, 0.18, 0.3)
    if a <= 0:
        return
    o.scrim(img, y - 170, y + 130, 0.55, a)
    u = t - s
    o.paste(img, NAME_CAPS, W / 2, y - 62, a * o.c01(u / 0.25), 1.0)
    o.paste(img, NAME_SERIF, W / 2, y + 8 + 18 * (1 - o.eo(u / 0.45)), a, 0.96 + 0.04 * o.eo(u / 0.45))


def draw(img, t):
    # cold open: she names the product
    lower_third(img, t, SAY(1.70, A, 0.0833), B - 0.05)
    # her payoff: "So light, never greasy… and look at this glow!"
    o.pop(img, o.chip("SO LIGHT  ·  NEVER GREASY"), W / 2, 1640, t, SAY(5.26, C1, 5.0), C2 - 0.05)
    a = o.life(t, SAY(7.96, C1, 5.0), D1 - 0.04, 0.14, 0.2)
    if a > 0:
        u = t - SAY(7.96, C1, 5.0)
        o.paste(img, GLOW, W / 2, 1560, a, 0.88 + 0.12 * o.eob(u / 0.5))
    # friends: the secret is the product, then the call to action
    lower_third(img, t, SAY(5.30, D2, 5.26), SAY(7.70, D2, 5.26))
    o.pop(img, o.chip("GET YOURS TODAY", True, 46, True), W / 2, 1640, t, SAY(8.70, D2, 5.26), E - 0.04)
    # hero: real box + jar
    o.pop(img, o.chip("HEALTHY INGREDIENTS"), W / 2, 330, t, E + 0.5, EC - 0.08)


def bloom(arr, t):
    for c in (B, C1, D1, E, EC):
        u = t - c
        if -0.12 < u < 0.4:
            k = math.exp(-((u - 0.02) / 0.13) ** 2)
            cx = W * (0.2 + 0.6 * o.c01((u + 0.12) / 0.52))
            g = np.exp(-(((o.XX - cx) / 520) ** 2 + ((o.YY - H * 0.45) / 900) ** 2)) * 0.95 + 0.2
            m = o.up(np.clip(g * k, 0, 1))
            arr = 255 - (255 - arr) * (1 - m[..., None] * np.array([1.0, 0.72, 0.38]))
    # jump-cut punch: a quick soft flash hides the cut inside the friends scene
    u = t - D2
    if -0.04 < u < 0.12:
        arr = arr + (255 - arr) * 0.18 * (1 - o.c01((u + 0.04) / 0.16))
    return arr


def compose(frame, t):
    body = B + 0.4 <= t < C1 - 0.15 or t >= EC + 0.45           # approved body / end card: untouched
    if body:
        return frame
    arr = bloom(frame.astype(np.float32), t)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    draw(img, t)
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]
    if out.endswith((".jpg", ".png")):
        ts = [float(x) for x in sys.argv[2].split(",")]
        ims = []
        for t in ts:
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", BASE, "-frames:v", "1", "-f", "rawvideo",
                                 "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            ims.append(Image.fromarray(compose(np.frombuffer(fr, np.uint8).reshape(H, W, 3), t)))
        sheet = Image.new("RGB", (360 * len(ims), 640))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((360, 640), Image.LANCZOS), (360 * k, 0))
        sheet.save(out, quality=90)
        sys.exit()
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", BASE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", out],
                          stdin=subprocess.PIPE)
    i = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        wr.stdin.write(compose(np.frombuffer(buf, np.uint8).reshape(H, W, 3), i / FPS).tobytes())
        i += 1
    wr.stdin.close()
    wr.wait()
    print("frames", i)
