"""Video 4 end card: the three PalmCare serums (Vita C+, N10 Niacinamide, DermaLuxe Pro), shown as their packs only (client correction:
no bottles), in a sunlit studio with a soft drifting palm-leaf shadow. Pop-up edition: the bright sunlit studio set built from the real (straightened) product photos,
with every caption arriving as a pop-up: gold-foil logo shimmer, slogan popping in with the voice, product-name tags
under each bottle, two phone chips, an address chip and a pulsing ORDER NOW pill, each with a sparkle.
Usage: endcard5.py OUT.mp4 SECONDS [VO_AT]   (OUT.jpg -> preview sheet)"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT, DUR = sys.argv[1], float(sys.argv[2])
VO_AT = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5           # slogan line starts (local time)
W, H, FPS = 1080, 1920, 24
F = "../fonts/"
A5 = "../v5/assets/"
ORANGE, DEEP, INK, CREAM = (201, 142, 30), (146, 96, 14), (40, 28, 18), (255, 250, 242)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
FLOOR = 1390                                                       # where the bottles stand


def font(n, s):
    return ImageFont.truetype(F + n, s)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def eob(x, c=2.0):
    """Ease-out with a gentle overshoot: the pop."""
    x = c01(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


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


def paste(dst, im, cx, cy, a=1.0, sc=1.0):
    if a <= 0.003 or sc <= 0.02:
        return
    if abs(sc - 1) > 0.005:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    dst.alpha_composite(fade(im, a), (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


def pop(dst, im, cx, cy, t0, tt, dur=0.45):
    """Pop-up: scale from 0.6 with overshoot, quick fade-in."""
    u = tt - t0
    if u <= 0:
        return 0.0
    paste(dst, im, cx, cy, c01(u / 0.12), 0.6 + 0.4 * eob(u / dur, 2.2))
    return u


def star(d, x, y, r, al):
    if r <= 0.5:
        return
    d.polygon([(x, y - r), (x + r * 0.16, y - r * 0.16), (x + r, y), (x + r * 0.16, y + r * 0.16), (x, y + r),
               (x - r * 0.16, y + r * 0.16), (x - r, y), (x - r * 0.16, y - r * 0.16)], fill=(255, 250, 230, int(255 * al)))


def gold(im):
    """Recolour an RGBA text image with a vertical gold-foil gradient."""
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    top, mid, bot = np.array([236, 184, 72.0]), np.array([176, 118, 22.0]), np.array([128, 82, 10.0])
    a[..., :3] = np.where(g < 0.55, top * (1 - g / 0.55) + mid * (g / 0.55), mid * (1 - (g - 0.55) / 0.45) + bot * ((g - 0.55) / 0.45))
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def shine(im, q):
    """A diagonal specular band across an RGBA image (q: 0..1 position)."""
    if not (0 < q < 1):
        return im
    a = np.asarray(im).astype(np.float32)
    xs = np.arange(a.shape[1])[None, :]
    ys = np.arange(a.shape[0])[:, None]
    band = np.exp(-(((xs + ys * 0.4) - q * (a.shape[1] + 300) + 150) / 40) ** 2) * 0.75
    a[..., :3] += (255 - a[..., :3]) * band[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


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
bg -= np.exp(-((YY - FLOOR) / 3) ** 2)[..., None] * 18


def load_bottle(path, h):
    p = Image.open(path).convert("RGBA")
    return p.resize((round(p.width * h / p.height), h), Image.LANCZOS)


BOXH = [600, 660, 600]          # packs only (client: no bottles)
NAMES = [("vitac_real_final", "bottle_vitac"), ("n10_real_final", "bottle_n10"), ("dermaluxe_box_final", "bottle_dl")]
BOX_X = [W / 2 - 330, W / 2, W / 2 + 330]
BOXES = [load_bottle(A5 + f"{bx}.png", h) for (bx, _), h in zip(NAMES, BOXH)]
BOT = [(bx, cx) for bx, cx in zip(BOXES, BOX_X)]          # (image, centre x) for the glints and the sweep


def palm_shadow(tt):
    """A soft palm-frond shadow drifting across the backdrop, as if from a window: sells the sunlit studio."""
    m = Image.new("L", (W // 4, FLOOR // 4), 0)
    d = ImageDraw.Draw(m)
    sway = math.sin(tt * 0.6) * 0.06
    ox, oy = 20, 30
    for k in range(18):
        t = k / 17
        bx, by = ox + 200 * t, oy + 40 * t + 20 * t * t
        ang = -1.9 + sway + (0.5 if k % 2 else -0.5)
        L = 70 * (1 - abs(t - 0.45))
        ex, ey = bx + L * math.cos(ang + (0.9 if k % 2 else -0.9)), by + L * math.sin(ang + (0.9 if k % 2 else -0.9))
        d.polygon([(bx, by), (ex, ey), (bx + 6, by + 4)], fill=255)
    d.line((ox, oy, ox + 200, oy + 60), fill=255, width=2)
    m = m.filter(ImageFilter.GaussianBlur(5)).resize((W, FLOOR), Image.BICUBIC)
    return np.asarray(m).astype(np.float32) / 255


def caustics(tt):
    x, y = XX[:FLOOR:4, ::4], YY[:FLOOR:4, ::4]
    v = (np.sin(x / 37 + tt * 0.9) + np.sin((x * 0.6 + y) / 29 - tt * 0.7) + np.sin((x - y * 0.8) / 41 + tt * 0.5))
    v = np.clip((v - 1.4) / 1.6, 0, 1) ** 1.6
    small = Image.fromarray((v * 255).astype(np.uint8)).resize((W, FLOOR), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    return np.asarray(small).astype(np.float32) / 255


LOGO = gold(text_img("PalmCare", font("DMSerifDisplay.ttf", 150), (255, 255, 255), pad=20))
REG = text_img("®", font("DMSerifDisplay.ttf", 48), ORANGE, pad=0)
SUB = text_img("ADVANCED  SKIN  CARE", font("Jost-Medium.ttf", 24), INK, tracking=9, pad=6)
SL1 = text_img("Pamper your skin", font("Playfair-Medium.ttf", 66), INK, pad=10)
SL2 = gold(text_img("with PalmCare.", font("Playfair-Italic.ttf", 96), (255, 255, 255), pad=14))


def tag(l1, l2):
    """Product-name pop-up tag: white rounded card, gold keyline, spaced caps name + soft sub-line."""
    a = text_img(l1, font("Jost-SemiBold.ttf", 20), INK, tracking=4, pad=0)
    b = text_img(l2, font("Playfair-Italic.ttf", 22), DEEP, pad=0)
    w, h = max(a.width, b.width) + 44, a.height + b.height + 34
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((20, 26, 20 + w, 26 + h), radius=22, fill=55)
    sh = Image.new("RGBA", im.size, (90, 60, 20, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(12)))
    im.alpha_composite(sh)
    ImageDraw.Draw(im).rounded_rectangle((20, 20, 20 + w, 20 + h), radius=22, fill=(255, 255, 255, 240), outline=ORANGE + (255,), width=2)
    im.alpha_composite(a, (20 + (w - a.width) // 2, 34))
    im.alpha_composite(b, (20 + (w - b.width) // 2, 34 + a.height + 6))
    return im


def chip(text, icon, size=40, bold=True):
    """Contact pop-up chip: white pill, gold icon disc, dark text."""
    f = font("Bricolage-ExtraBold.ttf" if bold else "Bricolage-Medium.ttf", size)
    ti = text_img(text, f, INK, pad=0)
    h = 92
    w = ti.width + 120
    im = Image.new("RGBA", (w + 40, h + 44), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((20, 28, 20 + w, 28 + h), radius=h // 2, fill=70)
    sh = Image.new("RGBA", im.size, (90, 60, 20, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(13)))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), radius=h // 2, fill=(255, 255, 255, 245), outline=ORANGE + (255,), width=3)
    cx, cy = 20 + 48, 20 + h // 2
    d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=ORANGE + (255,))
    if icon == "phone":
        d.rounded_rectangle((cx - 9, cy - 15, cx + 9, cy + 15), radius=4, outline=(255, 255, 255), width=3)
        d.line((cx - 3, cy + 10, cx + 3, cy + 10), fill=(255, 255, 255), width=2)
    else:
        d.ellipse((cx - 10, cy - 16, cx + 10, cy + 4), fill=(255, 255, 255))
        d.polygon([(cx - 8, cy - 1), (cx + 8, cy - 1), (cx, cy + 15)], fill=(255, 255, 255))
        d.ellipse((cx - 4, cy - 10, cx + 4, cy - 2), fill=ORANGE)
    im.alpha_composite(ti, (20 + 92, 20 + (h - ti.height) // 2 - 2))
    return im


def address_chip():
    a1 = text_img("Shop A67, Kogi Plaza, BBA Market,", font("Bricolage-Medium.ttf", 30), INK, pad=0)
    a2 = text_img("Trade Fair Complex, Lagos", font("Bricolage-Medium.ttf", 30), (96, 74, 52), pad=0)
    w, h = max(a1.width, a2.width) + 130, a1.height + a2.height + 44
    im = Image.new("RGBA", (w + 40, h + 44), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((20, 28, 20 + w, 28 + h), radius=36, fill=70)
    sh = Image.new("RGBA", im.size, (90, 60, 20, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(13)))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), radius=36, fill=(255, 255, 255, 245), outline=ORANGE + (255,), width=3)
    cx, cy = 20 + 52, 20 + h // 2
    d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=ORANGE + (255,))
    d.ellipse((cx - 10, cy - 16, cx + 10, cy + 4), fill=(255, 255, 255))
    d.polygon([(cx - 8, cy - 1), (cx + 8, cy - 1), (cx, cy + 15)], fill=(255, 255, 255))
    d.ellipse((cx - 4, cy - 10, cx + 4, cy - 2), fill=ORANGE)
    im.alpha_composite(a1, (20 + 104, 20 + 20))
    im.alpha_composite(a2, (20 + 104, 20 + 20 + a1.height + 4))
    return im


def order_pill():
    lab = text_img("ORDER NOW", font("Jost-SemiBold.ttf", 30), (255, 255, 255), tracking=7, pad=0)
    w, h = lab.width + 80, 76
    im = Image.new("RGBA", (w + 40, h + 44), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((20, 28, 20 + w, 28 + h), radius=h // 2, fill=90)
    sh = Image.new("RGBA", im.size, (120, 70, 10, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(sh)
    g = np.zeros((h, w, 4), np.uint8)
    q = np.linspace(0, 1, w)[None, :, None]
    g[..., :3] = (np.array([226, 164, 46]) * (1 - q) + np.array([160, 100, 14]) * q).astype(np.uint8)
    mm = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mm).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=255)
    g[..., 3] = np.asarray(mm)
    im.alpha_composite(Image.fromarray(g, "RGBA"), (20, 20))
    im.alpha_composite(lab, (20 + (w - lab.width) // 2, 20 + (h - lab.height) // 2 - 2))
    return im


TAGS = [tag("VITA C+", "Serum"), tag("N10 NIACINAMIDE", "Serum"), tag("DERMALUXE PRO", "Night Repair Serum")]
PH1, PH2 = chip("0903 055 5424", "phone", 38), chip("0809 361 2901", "phone", 38)
ADDR, ORDER = address_chip(), order_pill()
# placement (centres)
TAG_Y = FLOOR + 70
PH_Y, ADDR_Y, ORD_Y = 1592, 1712, 1832
PH_X = (W / 2 - PH1.width / 2 + 2, W / 2 + PH2.width / 2 - 2)
T_TAG, T_PH1, T_PH2, T_ADDR, T_ORD = 2.3, 3.0, 3.3, 3.65, 4.1


def frame(i):
    tt = i / FPS
    arr = bg.copy()
    c = caustics(tt * 1.4)
    arr[:FLOOR] += c[..., None] * np.array([255, 226, 170]) * 0.20 * (0.6 + 0.4 * sun[:FLOOR])
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    # palm-leaf window shadow on the backdrop
    ps = palm_shadow(tt)
    arr2 = np.asarray(img.convert("RGB")).astype(np.float32)
    arr2[:FLOOR] *= (1 - 0.16 * ps[..., None])
    img = Image.fromarray(np.clip(arr2, 0, 255).astype(np.uint8)).convert("RGBA")
    # boxes rise into place, then each bottle lands in front of its box (uniform motion only: never bent)
    for k in (0, 2, 1):                                    # centre serum stands in front
        bx_im, cx = BOXES[k], BOX_X[k]
        for layer, (im_, base, delay) in enumerate(((bx_im, FLOOR, 0.15 + 0.2 * k),)):
            p = eo((tt - delay) / 1.1)
            if p <= 0:
                continue
            y = base - im_.height + (1 - p) * 70
            x = int(cx - im_.width / 2)
            sh = Image.new("RGBA", (im_.width + 200, 120), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse((70, 44, im_.width + 130, 84), fill=(90, 50, 20, int((120 if layer else 90) * p)))
            img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (x - 100, base - 64))
            ref = im_.transpose(Image.FLIP_TOP_BOTTOM)
            ra = np.asarray(ref).astype(np.float32)
            ra[..., 3] *= np.clip(1 - np.arange(ref.height) / 200, 0, 1)[:, None] ** 1.6 * (0.22 if layer else 0.26)
            ref = Image.fromarray(ra.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(1.5))
            if not layer:
                img.alpha_composite(fade(ref, p), (x, int(base + (1 - p) * 70)))
            img.alpha_composite(fade(im_, p), (x, int(y)))
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
    # logo pops in, then a shine crosses it every few seconds
    u = tt - 0.45
    if u > 0:
        q = ((tt - 1.0) % 3.5) / 0.9
        lg = shine(LOGO, q if tt > 1.0 else 0)
        paste(img, lg, W / 2, 170, c01(u / 0.12), 0.7 + 0.3 * eob(u / 0.5, 2.0))
        paste(img, REG, W / 2 + LOGO.width / 2 - 26, 126, c01((u - 0.3) / 0.2))
    pop(img, SUB, W / 2, 272, 0.9, tt)
    rp = eo((tt - 1.0) / 0.6)
    if rp > 0:
        d.line((W / 2 - 150 * rp, 310, W / 2 + 150 * rp, 310), fill=ORANGE + (255,), width=2)
    # slogan pops with the voice
    pop(img, SL1, W / 2, 392, VO_AT - 0.1, tt)
    u2 = pop(img, SL2, W / 2, 478, VO_AT + 0.45, tt, 0.5)
    if 0.25 < u2 < 1.0:
        star(d, W / 2 + SL2.width / 2 - 30, 448, 26 * math.sin(math.pi * (u2 - 0.25) / 0.75), math.sin(math.pi * (u2 - 0.25) / 0.75))
    # product-name tags pop under the bottles
    for k, (tg, cx) in enumerate(zip(TAGS, BOX_X)):
        pop(img, tg, cx, TAG_Y, T_TAG + 0.2 * k, tt)
    # contact pop-ups
    for im, x, y, t0 in ((PH1, PH_X[0], PH_Y, T_PH1), (PH2, PH_X[1], PH_Y, T_PH2), (ADDR, W / 2, ADDR_Y, T_ADDR)):
        u = pop(img, im, x, y, t0, tt)
        if 0.15 < u < 0.85:
            s_ = math.sin(math.pi * (u - 0.15) / 0.7)
            star(d, x + im.width / 2 - 34, y - 30, 20 * s_, s_)
    u = tt - T_ORD
    if u > 0:
        pulse = 1 + 0.035 * math.sin(max(0.0, u - 0.6) * 2 * math.pi / 1.4) * c01((u - 0.6) / 0.3)
        o = shine(ORDER, ((tt - T_ORD - 0.7) % 2.8) / 0.8 if u > 0.7 else 0)
        paste(img, o, W / 2, ORD_Y, c01(u / 0.12), (0.6 + 0.4 * eob(u / 0.45, 2.2)) * pulse)
    # glints on the boxes
    for k, (gx, gy) in enumerate(((BOT[0][1] + 40, FLOOR - BOT[0][0].height + 70), (BOT[1][1] + 30, FLOOR - BOT[1][0].height + 70))):
        gp = (tt - 2.6 - 1.1 * k) % 3.2
        if gp < 0.5 and tt > 2.4:
            star(d, gx, gy, 30 * math.sin(math.pi * gp / 0.5), 0.92)
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    n = round(DUR * FPS)
    if OUT.endswith(".jpg"):
        picks = [int(FPS * s) for s in (0.6, 1.9, 2.6, 3.4, 3.9)] + [n - 1]
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
