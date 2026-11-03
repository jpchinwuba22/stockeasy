"""Video 6 end card — its own "citrus editorial" design (nothing shared with the Video 4/5 card): the peach studio of
the reveal with citrus-droplet bokeh, a Cormorant serif slogan, the REAL box + jar on a glossy plinth with a mirror
reflection, the product line in italic, and an espresso-glass contact panel (orange-slice icons, both phone numbers,
the shop address) with a citrus ORDER NOW button that pulses on the beat.
Usage: endcard9b.py OUT(.mp4|.jpg) SECONDS [VO_AT]"""
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT, DUR = sys.argv[1], float(sys.argv[2])
VO_AT = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
W, H, FPS = 1080, 1920, 24
D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
FD = D + "fonts/"
INK, ORANGE, CREAM, ESP = (52, 30, 16), (240, 128, 36), (255, 244, 230), (38, 22, 12)
BEAT = 60 / 104
FLOOR = 1235
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def font(n, s):
    return ImageFont.truetype(FD + n, s)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def eob(x, c=2.0):
    x = c01(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def text_img(s, f, fill, tracking=0, pad=8):
    w = sum(f.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    a, d = f.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, a + d + 2 * pad), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = pad
    for c in s:
        dr.text((x, pad), c, font=f, fill=fill)
        x += f.getlength(c) + tracking
    return im


def citrus(im, top=(255, 200, 120), bot=(226, 100, 22)):
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    a[..., :3] = np.array(top, np.float32) * (1 - g) + np.array(bot, np.float32) * g
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def fade(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.split()[-1].point(lambda v: int(v * max(0.0, a))))
    return im


def paste(dst, im, cx, cy, a=1.0, sc=1.0):
    if a <= 0.003 or sc <= 0.02:
        return
    if abs(sc - 1) > 0.005:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    dst.alpha_composite(fade(im, a), (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


def slice_icon(d, cx, cy, r):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE + (255,))
    d.ellipse((cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), fill=(255, 196, 96, 255))
    for k in range(8):
        a = k * math.pi / 4
        d.line((cx, cy, cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8), fill=(255, 240, 214, 255), width=2)


# ---------- static: studio background ----------
cap = cv2.VideoCapture(D + "v9/src/C1.mp4")
cap.set(cv2.CAP_PROP_POS_FRAMES, int(7.5 * 24))
plate = cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2RGB)
plate = cv2.GaussianBlur(cv2.resize(plate, (W, H)).astype(np.float32) / 255, (0, 0), 14)
top, bot = np.array([253, 236, 218], np.float32) / 255, np.array([246, 206, 168], np.float32) / 255
g = (YY / H)[..., None]
bg = top * (1 - g) + bot * g
bg = bg * 0.80 + plate * 0.26
bg += np.exp(-(((XX - W * 0.5) / 560) ** 2 + ((YY - 860) / 520) ** 2))[..., None] * np.array([1.0, 0.85, 0.62]) * 0.20
fl = (YY > FLOOR).astype(np.float32)[..., None]
floor = np.array([240, 190, 150], np.float32) / 255 * (1 - 0.16 * np.clip((YY - FLOOR) / 500, 0, 1))[..., None]
bg = bg * (1 - fl) + floor * fl
bg += np.exp(-((YY - FLOOR) / 2.0) ** 2)[..., None] * 0.08
BG = np.clip(bg, 0, 1)

# the real box + jar (stacked, from the straightened photos)
# box and jar side by side (box standing, jar just in front of it), not stacked
_bx = Image.open(D + "v9/box_straight.png").convert("RGBA")
_jr = Image.open(D + "v9/jar_cut.png").convert("RGBA")
_bx = _bx.crop(_bx.getbbox()); _jr = _jr.crop(_jr.getbbox())
BH_ = 430
_bx = _bx.resize((round(_bx.width * BH_ / _bx.height), BH_), Image.LANCZOS)
JW_ = 330
_jr = _jr.resize((JW_, round(_jr.height * JW_ / _jr.width)), Image.LANCZOS)
PH = BH_ + 14
STACK = Image.new("RGBA", (_bx.width + JW_ + 16, PH), (0, 0, 0, 0))
STACK.alpha_composite(_bx, (0, 0))
_js = Image.new("RGBA", (JW_ + 80, 90), (0, 0, 0, 0))                          # jar contact shadow on the box's base line
ImageDraw.Draw(_js).ellipse((40, 30, JW_ + 40, 62), fill=(90, 40, 10, 120))
_js = _js.filter(ImageFilter.GaussianBlur(10))
STACK.alpha_composite(_js, (_bx.width + 16 - 40, PH - 60))
STACK.alpha_composite(_jr, (_bx.width + 16, PH - _jr.height))
REFL = STACK.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, STACK.width, int(PH * 0.08)))
ra = np.asarray(REFL).astype(np.float32)
ra[..., 3] *= (np.linspace(1, 0, REFL.height) ** 1.5 * 0.16)[:, None]
REFL = Image.fromarray(ra.astype(np.uint8), "RGBA")

# typography
T_BRAND = text_img("P A L M C A R E", font("Jost-Medium.ttf", 28), INK + (255,), tracking=5)
T_S1 = text_img("Pamper your skin", font("Cormorant-SemiBold.ttf", 96), INK + (255,))
T_S2 = citrus(text_img("with PalmCare.", font("Cormorant-Italic.ttf", 128), (255, 255, 255, 255), pad=12))
T_NAME = text_img("Vitamin C  ·  Face Moisturiser", font("Cormorant-Italic.ttf", 54), INK + (255,))


def panel():
    w, h = 940, 380
    im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((30, 40, 30 + w, 40 + h), radius=40, fill=120)
    sh = Image.new("RGBA", im.size, (50, 20, 4, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, 30 + w, 30 + h), radius=40, fill=ESP + (232,), outline=(246, 168, 92, 255), width=2)
    return im


PANEL = panel()
PH1 = text_img("0903 055 5424", font("Jost-Medium.ttf", 58), CREAM + (255,), tracking=2)
PH2 = text_img("0809 361 2901", font("Jost-Medium.ttf", 58), CREAM + (255,), tracking=2)
AD1 = text_img("Shop A67, Kogi Plaza, BBA Market,", font("Jost-Light.ttf", 34), CREAM + (255,))
AD2 = text_img("Trade Fair Complex, Lagos", font("Jost-Light.ttf", 34), (250, 200, 150, 255))


def order_btn():
    lab = text_img("ORDER NOW", font("Jost-Medium.ttf", 32), (255, 255, 255, 255), tracking=8)
    w, h = lab.width + 90, 84
    g_ = np.zeros((h, w, 4), np.uint8)
    q = np.linspace(0, 1, w)[None, :, None]
    g_[..., :3] = (np.array([252, 170, 70]) * (1 - q) + np.array([222, 96, 20]) * q).astype(np.uint8)
    mm = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mm).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=255)
    g_[..., 3] = np.asarray(mm)
    im = Image.new("RGBA", (w + 50, h + 50), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((25, 33, 25 + w, 33 + h), radius=h // 2, fill=110)
    sh = Image.new("RGBA", im.size, (120, 50, 6, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(sh)
    im.alpha_composite(Image.fromarray(g_, "RGBA"), (25, 25))
    im.alpha_composite(lab, (25 + (w - lab.width) // 2, 25 + (h - lab.height) // 2 - 2))
    return im


ORDER = order_btn()
_sl = Image.open(D + "v9/orange_slice.png").convert("RGBA")
SLICE = Image.new("RGBA", (_sl.width + 40, _sl.height + 40), (0, 0, 0, 0))
SLICE.paste(_sl, (20, 20))
_rb = np.random.default_rng(11)
BURST = [(a, _rb.uniform(420, 900), _rb.uniform(120, 230), _rb.choice([-1, 1]) * _rb.uniform(0.6, 1.6), _rb.uniform(0, 0.08))
         for a in np.linspace(0, 2 * math.pi, 14, endpoint=False) + _rb.uniform(-0.2, 0.2, 14)]
BSL = [SLICE, SLICE.filter(ImageFilter.GaussianBlur(1))]
JUICE = [(_rb.uniform(0, 2 * math.pi), _rb.uniform(250, 750), _rb.uniform(5, 13), _rb.uniform(0, 0.1)) for _ in range(46)]
SL = [(150, 600, 190, 15, 8, 2), (935, 760, 160, -20, -6, 3), (120, 1060, 120, 40, 10, 4), (965, 1110, 130, 0, -9, 4)]
rng = np.random.default_rng(6)
DROPS = [(rng.uniform(40, W - 40), rng.uniform(0, FLOOR), rng.uniform(4, 11), rng.uniform(0, 6.28)) for _ in range(22)]
T_IN, T_SL1, T_SL2, T_NM, T_PAN, T_P1, T_P2, T_AD, T_OR = 0.1, VO_AT - 0.1, VO_AT + 0.45, VO_AT + 1.1, 2.9, 3.2, 3.45, 3.75, 4.3


def frame(i):
    t = i / FPS
    arr = BG.copy()
    for x, y, r, ph in DROPS:                               # drifting citrus droplets
        yy = (y - t * 26 - ph * 30) % FLOOR
        xx = x + 9 * math.sin(ph + t * 0.8)
        x0, x1, y0, y1 = int(max(0, xx - 3 * r)), int(min(W, xx + 3 * r)), int(max(0, yy - 3 * r)), int(min(H, yy + 3 * r))
        if x1 > x0 and y1 > y0:
            dd = np.exp(-(((XX[y0:y1, x0:x1] - xx) ** 2 + (YY[y0:y1, x0:x1] - yy) ** 2) / (2 * r * r)))[..., None]
            arr[y0:y1, x0:x1] = 1 - (1 - arr[y0:y1, x0:x1]) * (1 - dd * 0.30 * np.array([1, 0.9, 0.7]))
    img = Image.fromarray((arr * 255).astype(np.uint8)).convert("RGBA")
    for k, (sx, sy, sz, a0, sp, bl) in enumerate(SL):     # real orange slices drifting behind the products
        q = eo((t - 0.4 - 0.2 * k) / 0.9)
        if q > 0:
            im = SLICE.resize((sz, int(sz * SLICE.height / SLICE.width)), Image.LANCZOS).rotate(a0 + sp * t, Image.BICUBIC, expand=True)
            if bl:
                im = im.filter(ImageFilter.GaussianBlur(bl))
            paste(img, im, sx + 8 * math.sin(t * 0.7 + k), sy - 10 * t, q * 0.9)
    # ORANGE BURST: real orange slices and juice drops explode out from behind the products, then clear the frame
    if t < 1.6:
        for k, (ang, spd, sz, rot, delay) in enumerate(BURST):
            u = t - delay
            if u <= 0:
                continue
            d = spd * (1 - math.exp(-u * 3.2))
            bx_ = W / 2 + math.cos(ang) * d
            by_ = 1000 + math.sin(ang) * d + 260 * u * u
            sc = 0.35 + 0.65 * eo(u / 0.35)
            im = BSL[k % len(BSL)].resize((int(sz * sc), int(sz * sc * SLICE.height / SLICE.width)), Image.BILINEAR).rotate(rot * u * 120, Image.BILINEAR, expand=True)
            if u < 0.25:
                im = im.filter(ImageFilter.GaussianBlur(3 * (1 - u / 0.25)))
            paste(img, im, bx_, by_, c01(u / 0.08) * (1 - c01((t - 1.15) / 0.4)))
        d = ImageDraw.Draw(img, "RGBA")
        for ang, spd, r, delay in JUICE:
            u = t - delay
            if u <= 0:
                continue
            dd = spd * (1 - math.exp(-u * 3.0))
            jx_, jy_ = W / 2 + math.cos(ang) * dd, 1000 + math.sin(ang) * dd + 420 * u * u
            al = int(230 * (1 - c01((t - 0.9) / 0.6)))
            d.ellipse((jx_ - r, jy_ - r, jx_ + r, jy_ + r), fill=(250, 150, 40, al))
            d.ellipse((jx_ - r * 0.4, jy_ - r * 0.6, jx_ + r * 0.1, jy_ - r * 0.1), fill=(255, 235, 200, al))
        fl = math.exp(-t / 0.12) * 0.8                                         # flash at the burst
        if fl > 0.02:
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 236, 205, int(255 * fl))))
    # products rise onto the plinth
    p = eo((t - 0.35) / 0.8)
    if p > 0:
        y = FLOOR - PH + (1 - p) * 80
        sh = Image.new("RGBA", (STACK.width + 240, 140), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((70, 50, STACK.width + 170, 96), fill=(110, 50, 14, int(110 * p)))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), (int(W / 2 - sh.width / 2), FLOOR - 70))
        img.alpha_composite(fade(REFL, p), (int(W / 2 - STACK.width / 2), FLOOR + 2))
        st_ = STACK
        q = (t - 1.3) / 1.2                                 # one light sweep across the products
        if 0 < q < 1:
            a = np.asarray(STACK).astype(np.float32)
            xs = np.arange(a.shape[1])[None, :]
            ys = np.arange(a.shape[0])[:, None]
            band = np.exp(-(((xs + ys * 0.45) - (-300 + eio(q) * (a.shape[1] + 900))) / 60) ** 2) * math.sin(math.pi * q) * 0.5
            a[..., :3] += (255 - a[..., :3]) * band[..., None]
            st_ = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        img.alpha_composite(fade(st_, c01(p * 2)), (int(W / 2 - STACK.width / 2), int(y)))
    d = ImageDraw.Draw(img)
    # brand line and slogan (with the voice)
    u = t - T_IN
    paste(img, T_BRAND, W / 2, 120, c01(u / 0.4))
    rp = eo((t - 0.4) / 0.6)
    if rp > 0:
        d.line((W / 2 - 110 * rp, 160, W / 2 + 110 * rp, 160), fill=ORANGE + (255,), width=2)
    u = t - T_SL1
    if u > 0:
        paste(img, T_S1, W / 2, 248 - 12 * (1 - eo(u / 0.5)), c01(u / 0.3))
    u = t - T_SL2
    if u > 0:
        paste(img, T_S2, W / 2, 365, c01(u / 0.15), 0.8 + 0.2 * eob(u / 0.45, 2.4))
    u = t - T_NM
    if u > 0:
        paste(img, T_NAME, W / 2, 1296, c01(u / 0.35))
    # espresso contact panel slides up
    u = t - T_PAN
    if u > 0:
        py = 1560 + (1 - eo(u / 0.5)) * 60
        paste(img, PANEL, W / 2, py, c01(u / 0.3))
        d = ImageDraw.Draw(img)
        for k, (im, cy, t0) in enumerate(((PH1, py - 128, T_P1), (PH2, py - 48, T_P2))):    # one number per line, large
            uu = t - t0
            if uu > 0:
                slice_icon(d, W / 2 - im.width / 2 - 26, cy + 2, 26 * eob(uu / 0.4))
                paste(img, im, W / 2 + 22, cy, c01(uu / 0.2))
        uu = t - T_AD
        if uu > 0:
            d.line((W / 2 - 400, py + 12, W / 2 + 400, py + 12), fill=(246, 168, 92, int(160 * c01(uu / 0.3))), width=1)
            paste(img, AD1, W / 2, py + 66, c01(uu / 0.3))
            paste(img, AD2, W / 2, py + 116, c01((uu - 0.15) / 0.3))
    u = t - T_OR
    if u > 0:
        pulse = 1 + 0.03 * max(0.0, math.sin(2 * math.pi * (t / BEAT))) * c01((u - 0.5) / 0.3)    # pulses on the beat
        paste(img, ORDER, W / 2, 1822, c01(u / 0.15), (0.6 + 0.4 * eob(u / 0.45, 2.4)) * pulse)
    # glint on the jar's gold collar
    gp = (t - 2.2) % 2.8
    if gp < 0.5 and t > 2.0:
        s = math.sin(math.pi * gp / 0.5)
        gx, gy = W / 2 + STACK.width / 2 - JW_ * 0.2, FLOOR - _jr.height * 0.55
        d = ImageDraw.Draw(img)
        r = 28 * s
        d.polygon([(gx, gy - r), (gx + r * 0.16, gy - r * 0.16), (gx + r, gy), (gx + r * 0.16, gy + r * 0.16), (gx, gy + r),
                   (gx - r * 0.16, gy + r * 0.16), (gx - r, gy), (gx - r * 0.16, gy - r * 0.16)], fill=(255, 250, 235, int(235 * s)))
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    n = round(DUR * FPS)
    if OUT.endswith(".jpg"):
        picks = [int(FPS * s) for s in (0.6, 1.9, 2.6, 3.5, 4.0)] + [n - 1]
        sheet = Image.new("RGB", (432 * len(picks), 768))
        for k, i in enumerate(picks):
            sheet.paste(Image.fromarray(frame(i)).resize((432, 768), Image.LANCZOS), (432 * k, 0))
        sheet.save(OUT, quality=90)
        Image.fromarray(frame(n - 1)).save(OUT.replace(".jpg", "_last.png"))
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close()
    p.wait()
    print("end card", n, "frames")
