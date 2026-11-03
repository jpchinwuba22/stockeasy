"""Video 2 end card: a bright, sunlit studio set built from the real (straightened) product photos.
Warm-white seamless backdrop with a soft sun, slow moving water-caustic light, a glossy floor with true reflections,
both bottles rising into place with a slow light sweep, serif logo, slogan with the voice, product names and a bright
contact bar. Usage: endcard2b.py OUT.mp4 SECONDS [VO_AT]   (OUT.jpg -> preview sheet)"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT, DUR = sys.argv[1], float(sys.argv[2])
VO_AT = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5           # slogan line starts (local time)
W, H, FPS = 1080, 1920, 24
F = "../fonts/"
ORANGE, DEEP, INK, CREAM = (238, 110, 20), (196, 82, 10), (40, 28, 18), (255, 250, 242)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
FLOOR = 1430                                                       # where the bottles stand


def font(n, s):
    return ImageFont.truetype(F + n, s)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def text_img(s, f, fill, tracking=0, pad=12):
    w = sum(f.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    a, d = f.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, a + d + 2 * pad), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = pad
    for c in s:
        dr.text((x, pad), c, font=f, fill=fill)
        x += f.getlength(c) + tracking
    return im


def fade(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.split()[-1].point(lambda v: int(v * max(0, a))))
    return im


def paste(dst, im, cx, cy, a=1.0):
    if a > 0.003:
        dst.alpha_composite(fade(im, a), (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


# ---------- static layers ----------
t = YY / H
bg = np.zeros((H, W, 3), np.float32)
top, mid = np.array([255, 236, 210.0]), np.array([255, 248, 238.0])
bg[:] = top * (1 - t[..., None]) + mid * t[..., None]
sun = np.exp(-(((XX - 790) / 520) ** 2 + ((YY - 520) / 520) ** 2))[..., None]
bg += sun * np.array([255, 214, 150]) * 0.35
floor = (YY > FLOOR).astype(np.float32)[..., None]
fl = np.array([246, 230, 208.0]) * (1 - 0.12 * np.clip((YY - FLOOR) / 500, 0, 1))[..., None]
bg = bg * (1 - floor) + fl * floor
horizon = np.exp(-((YY - FLOOR) / 3) ** 2)[..., None] * 18
bg -= horizon


def load_bottle(path, h):
    p = Image.open(path).convert("RGBA")
    return p.resize((round(p.width * h / p.height), h), Image.LANCZOS)


BOT = [(load_bottle("../straight/out2/citrus.png", 830), 385), (load_bottle("../straight/out2/molecular.png", 690), 735)]


def caustics(tt):
    """Moving water-light pattern (sum of interfering waves), used softly on the backdrop."""
    x, y = XX[:FLOOR:4, ::4], YY[:FLOOR:4, ::4]
    v = (np.sin(x / 37 + tt * 0.9) + np.sin((x * 0.6 + y) / 29 - tt * 0.7) + np.sin((x - y * 0.8) / 41 + tt * 0.5))
    v = np.clip((v - 1.4) / 1.6, 0, 1) ** 1.6
    small = Image.fromarray((v * 255).astype(np.uint8)).resize((W, FLOOR), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    return np.asarray(small).astype(np.float32) / 255


LOGO_F = font("DMSerifDisplay.ttf", 158)
LOGO = text_img("PalmCare", LOGO_F, (255, 255, 255), pad=20)
_a = np.asarray(LOGO).astype(np.float32)
_g = np.linspace(0, 1, _a.shape[0])[:, None, None]
_a[..., :3] = np.array(ORANGE, np.float32) * (1 - _g) + np.array(DEEP, np.float32) * _g
LOGO = Image.fromarray(_a.astype(np.uint8), "RGBA")
REG = text_img("®", font("DMSerifDisplay.ttf", 52), ORANGE, pad=0)
SUB = text_img("ADVANCED  SKIN  CARE", font("Unbounded-Light.ttf", 22), INK, tracking=8, pad=6)
SL1 = text_img("Pamper your skin", font("Bricolage-Medium.ttf", 64), INK, pad=10)
SL2 = text_img("with PalmCare.", font("DMSerifDisplay-Italic.ttf", 92), DEEP, pad=10)
N1 = text_img("CITRUS VITAMIN GLOW", font("Unbounded-Medium.ttf", 19), INK, tracking=2, pad=4)
N1b = text_img("Infusion Body Wash", font("Bricolage-Medium.ttf", 24), (110, 90, 70), pad=4)
N2 = text_img("MOLECULAR GLOW", font("Unbounded-Medium.ttf", 19), INK, tracking=2, pad=4)
N2b = text_img("Body Lotion", font("Bricolage-Medium.ttf", 24), (110, 90, 70), pad=4)


def contact_bar(a):
    w, h = W - 120, 196
    bar = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(bar)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=40, fill=(255, 255, 255, 235), outline=ORANGE + (255,), width=3)
    ph = text_img("0903 055 5424   ·   0809 361 2901", font("Bricolage-ExtraBold.ttf", 42), INK, pad=0)
    a1 = text_img("Shop A67, Kogi Plaza, BBA Market,", font("Bricolage-Medium.ttf", 27), (90, 72, 56), pad=0)
    a2 = text_img("Trade Fair Complex, Lagos", font("Bricolage-Medium.ttf", 27), (90, 72, 56), pad=0)
    for k, y in enumerate((24, 108)):
        d.ellipse((28, y, 80, y + 52), fill=ORANGE + (255,))
        cx, cy = 54, y + 26
        if k == 0:
            d.rounded_rectangle((cx - 9, cy - 15, cx + 9, cy + 15), radius=4, outline=(255, 255, 255), width=3)
        else:
            d.ellipse((cx - 10, cy - 15, cx + 10, cy + 5), fill=(255, 255, 255))
            d.polygon([(cx - 8, cy), (cx + 8, cy), (cx, cy + 15)], fill=(255, 255, 255))
            d.ellipse((cx - 4, cy - 9, cx + 4, cy - 1), fill=ORANGE)
    bar.alpha_composite(ph, (100, 28))
    bar.alpha_composite(a1, (100, 104))
    bar.alpha_composite(a2, (100, 104 + a1.height + 6))
    lab = text_img("ORDER NOW", font("Unbounded-ExtraBold.ttf", 22), (255, 255, 255), tracking=4, pad=0)
    pw = lab.width + 44
    pill = Image.new("RGBA", (pw, 50), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle((0, 0, pw - 1, 49), radius=25, fill=ORANGE + (255,))
    pill.alpha_composite(lab, (22, (50 - lab.height) // 2 - 1))
    bar.alpha_composite(pill, (w - pw - 26, 120))
    sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    m = Image.new("L", sh.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((40, 50, 40 + w, 50 + h), radius=40, fill=60)
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(18)))
    sh.alpha_composite(bar, (40, 40))
    return fade(sh, a)


BAR = None


def frame(i):
    global BAR
    tt = i / FPS
    arr = bg.copy()
    # caustic light dancing on the backdrop (soft, warm)
    c = caustics(tt * 1.4)
    arr[:FLOOR] += c[..., None] * np.array([255, 226, 170]) * 0.20 * (0.6 + 0.4 * sun[:FLOOR])
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    # bottles rise into place, with reflections and contact shadows
    for k, (b, cx) in enumerate(BOT):
        p = eo((tt - 0.15 - 0.25 * k) / 1.3)
        if p <= 0:
            continue
        y = FLOOR - b.height + (1 - p) * 60
        x = int(cx - b.width / 2)
        sh = Image.new("RGBA", (b.width + 200, 120), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((60, 40, b.width + 140, 86), fill=(90, 50, 20, int(120 * p)))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), (x - 100, FLOOR - 64))
        ref = b.transpose(Image.FLIP_TOP_BOTTOM)
        ra = np.asarray(ref).astype(np.float32)
        grad = np.clip(1 - np.arange(ref.height) / 260, 0, 1)[:, None] ** 1.6 * 0.30
        ra[..., 3] *= grad
        ref = Image.fromarray(ra.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(1.5))
        img.alpha_composite(fade(ref, p), (x, int(FLOOR + (1 - p) * 60)))
        img.alpha_composite(fade(b, p), (x, int(y)))
    # one slow light sweep across both bottles
    sp = (tt - 1.6) / 1.6
    if 0 < sp < 1:
        bx = -200 + (W + 400) * eio(sp)
        band = np.exp(-(((XX - bx) - (YY - 1000) * 0.3) / 60) ** 2) * 0.55
        mask = np.zeros((H, W), np.float32)
        for b, cx in BOT:
            al = np.asarray(b.split()[-1]).astype(np.float32) / 255
            x = int(cx - b.width / 2)
            mask[FLOOR - b.height:FLOOR, x:x + b.width] = np.maximum(mask[FLOOR - b.height:FLOOR, x:x + b.width], al)
        a = np.asarray(img.convert("RGB")).astype(np.float32)
        a = 255 - (255 - a) * (1 - (band * mask)[..., None] * np.array([1, 0.95, 0.85]))
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # logo + sub
    pl = eo((tt - 0.6) / 0.8)
    paste(img, LOGO, W / 2, 180 + (1 - pl) * 20, pl)
    paste(img, REG, W / 2 + LOGO.width / 2 - 26, 133 + (1 - pl) * 20, pl)
    paste(img, SUB, W / 2, 287, eo((tt - 1.0) / 0.6))
    # thin orange rule draws out
    rp = eo((tt - 1.1) / 0.7)
    if rp > 0:
        d.line((W / 2 - 150 * rp, 327, W / 2 + 150 * rp, 327), fill=ORANGE + (255,), width=2)
    # slogan with the voice
    a1 = eo((tt - (VO_AT - 0.15)) / 0.5)
    paste(img, SL1, W / 2, 400 + (1 - a1) * 16, a1)
    a2 = eo((tt - (VO_AT + 0.5)) / 0.5)
    paste(img, SL2, W / 2, 482 + (1 - a2) * 16, a2)
    # product names under the bottles
    for k, (n, nb, (b, cx)) in enumerate(((N1, N1b, BOT[0]), (N2, N2b, BOT[1]))):
        p = eo((tt - 2.2 - 0.2 * k) / 0.5)
        paste(img, n, cx, FLOOR + 52, p)
        paste(img, nb, cx, FLOOR + 86, p)
    # contact bar
    pc = eo((tt - 3.0) / 0.6)
    if pc > 0:
        if BAR is None:
            BAR = contact_bar(1.0)
        img.alpha_composite(fade(BAR, pc), (20, int(1648 + (1 - pc) * 30)))
    # glints on the pumps
    for k, (gx, gy) in enumerate(((BOT[0][1] + 40, FLOOR - BOT[0][0].height + 70), (BOT[1][1] + 30, FLOOR - BOT[1][0].height + 70))):
        gp = (tt - 2.6 - 1.1 * k) % 3.2
        if gp < 0.5 and tt > 2.4:
            r = 30 * math.sin(math.pi * gp / 0.5)
            d.polygon([(gx, gy - r), (gx + r * 0.16, gy - r * 0.16), (gx + r, gy), (gx + r * 0.16, gy + r * 0.16), (gx, gy + r),
                       (gx - r * 0.16, gy + r * 0.16), (gx - r, gy), (gx - r * 0.16, gy - r * 0.16)], fill=(255, 255, 255, 235))
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    n = round(DUR * FPS)
    if OUT.endswith(".jpg"):
        picks = [int(n * f) for f in (0.03, 0.12, 0.2, 0.35, 0.99)]
        sheet = Image.new("RGB", (432 * len(picks), 768))
        for k, i in enumerate(picks):
            sheet.paste(Image.fromarray(frame(i)).resize((432, 768), Image.LANCZOS), (432 * k, 0))
        sheet.save(OUT, quality=90)
        Image.fromarray(frame(n - 1)).save(OUT.replace(".jpg", "_last.png"))
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", OUT], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close()
    p.wait()
    print("end card", n, "frames")
