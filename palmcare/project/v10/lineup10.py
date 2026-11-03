"""The PalmCare Collection set: all 11 REAL products (straightened cut-outs) on a two-tier marble riser built from the
Shot-1 marble, in the warm studio of the collection. Products are only ever scaled uniformly and moved (never rotated
or bent).
  hook : the products land one by one on the beat (packs on the top tier, bottles on the front tier), a slow push-in,
         a light sweep and "THE PALMCARE COLLECTION" title.
  end  : the finished collection with the slogan, both phone numbers, the shop address and ORDER NOW.
Usage: lineup10.py OUT(.mp4|.jpg) MODE SECONDS [VO_AT]"""
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT, MODE, DUR = sys.argv[1], sys.argv[2], float(sys.argv[3])
VO_AT = float(sys.argv[4]) if len(sys.argv) > 4 else 1.5
W, H, FPS = 1080, 1920, 24
D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
FD = D + "fonts/"
INK, GOLD, DEEP, CREAM, ESP = (46, 30, 18), (201, 150, 62), (150, 102, 30), (255, 247, 236), (40, 26, 16)
BEAT = 60 / 104
rng = np.random.default_rng(10)


def font(n, s):
    return ImageFont.truetype(FD + n, s)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def eob(x, c=1.8):
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


def gold(im):
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    top, mid, bot = np.array([238, 196, 110.0]), np.array([190, 136, 46.0]), np.array([140, 94, 22.0])
    a[..., :3] = np.where(g < 0.55, top * (1 - g / 0.55) + mid * (g / 0.55), mid * (1 - (g - 0.55) / 0.45) + bot * ((g - 0.55) / 0.45))
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


# ---------- the set: blurred marble room from Shot 1 + a two-tier marble riser ----------
cap = cv2.VideoCapture(D + "v10/src/P1.mp4")
room = cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2RGB)
room = cv2.resize(room, (W, H), interpolation=cv2.INTER_CUBIC)
marble = room[1500:1900, 60:1020].copy()                                 # real marble from the Shot-1 counter
bg = cv2.GaussianBlur(room, (0, 0), 18).astype(np.float32) / 255
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
bg = bg * 0.82 + 0.18
bg += np.exp(-(((XX - W * 0.6) / 560) ** 2 + ((YY - 760) / 600) ** 2))[..., None] * np.array([1.0, 0.86, 0.62]) * 0.20
BG = Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

TOP_Y, TOP_W, TOP_T = 930, 1000, 64          # top tier: surface y, width, front thickness
BOT_Y, BOT_W, BOT_T = 1400, 1060, 84         # front tier


def tier(w, t, depth=46):
    """A marble riser tier: lit top surface (perspective strip) + marble front face + soft drop shadow."""
    im = Image.new("RGBA", (w + 80, depth + t + 70), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rectangle((40, depth + 10, 40 + w, depth + t + 30), fill=120)
    sh = Image.new("RGBA", im.size, (60, 40, 20, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(sh)
    face = cv2.resize(marble, (w, t), interpolation=cv2.INTER_AREA).astype(np.float32)
    face = face * np.linspace(1.02, 0.86, t)[:, None, None]
    im.alpha_composite(Image.fromarray(np.dstack([np.clip(face, 0, 255).astype(np.uint8), np.full((t, w), 255, np.uint8)]), "RGBA"), (40, depth))
    topm = cv2.resize(marble, (w, depth), interpolation=cv2.INTER_AREA).astype(np.float32) * 1.08 + 10
    topi = Image.fromarray(np.dstack([np.clip(topm, 0, 255).astype(np.uint8), np.full((depth, w), 255, np.uint8)]), "RGBA")
    mk = Image.new("L", (w, depth), 0)
    ImageDraw.Draw(mk).polygon([(26, 0), (w - 26, 0), (w, depth), (0, depth)], fill=255)
    topi.putalpha(mk)
    im.alpha_composite(topi, (40, 0))
    ImageDraw.Draw(im).line((40, depth, 40 + w, depth), fill=(255, 252, 244, 200), width=2)
    return im, depth


TIER_TOP, DT = tier(TOP_W, TOP_T)
TIER_BOT, DB = tier(BOT_W, BOT_T)


def cut(p, h):
    im = Image.open(D + p).convert("RGBA")
    im = im.crop(im.getbbox())
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


# top tier: the face-care packs (VitC moisturiser box in the centre; packs only); front tier: the six body-care bottles
TOP = [cut("v5/assets/n10_real_final.png", 290), cut("v5/assets/vitac_real_final.png", 300), cut("v9/box_straight.png", 215),
       cut("v5/assets/dermaluxe_box_final.png", 290), cut("v5/assets/glowshield_box_flat.png", 300)]
BOT = [cut("straight/out/milky.png", 440), cut("straight/out/cacao.png", 425), cut("v3/assets/citrus_cut.png", 418),
       cut("v3/assets/molecular_cut.png", 410), cut("v4/assets/tropical_cut.png", 425), cut("v4/assets/dermalight_cut.png", 410)]


def row_x(items, width, gap):
    tot = sum(i.width for i in items) + gap * (len(items) - 1)
    x, xs = W / 2 - tot / 2, []
    for i in items:
        xs.append(x + i.width / 2)
        x += i.width + gap
    return xs


TOP_X, BOT_X = row_x(TOP, TOP_W, 16), row_x(BOT, BOT_W, 10)
# landing order on the beat: alternate tiers so the set builds across the frame
LAND = [("b", 0), ("t", 2), ("b", 5), ("t", 0), ("b", 2), ("t", 4), ("b", 3), ("t", 1), ("b", 1), ("t", 3), ("b", 4)]
STEP = BEAT / 2
T0 = 0.25

T_TITLE = text_img("THE  PALMCARE  COLLECTION", font("Jost-Medium.ttf", 34), INK + (255,), tracking=7)
T_T1 = gold(text_img("THE  PALMCARE", font("Jost-Medium.ttf", 54), (255, 255, 255, 255), tracking=14))   # bold title (client round)
T_T2 = gold(text_img("Collection", font("Cormorant-SemiBold.ttf", 200), (255, 255, 255, 255)))
T_BRAND = gold(text_img("PalmCare", font("DMSerifDisplay.ttf", 150), (255, 255, 255, 255), pad=18))
T_SUB = text_img("ADVANCED  SKIN  CARE", font("Jost-Medium.ttf", 26), INK + (255,), tracking=9)
T_S1 = text_img("Pamper your skin", font("Cormorant-SemiBold.ttf", 82), INK + (255,))
T_S2 = gold(text_img("with PalmCare.", font("Cormorant-Italic.ttf", 108), (255, 255, 255, 255), pad=12))


def panel():
    w, h = 980, 236
    im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((30, 40, 30 + w, 40 + h), radius=36, fill=110)
    sh = Image.new("RGBA", im.size, (50, 26, 6, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, 30 + w, 30 + h), radius=36, fill=ESP + (232,), outline=GOLD + (255,), width=2)
    ph1 = text_img("0903 055 5424", font("Jost-Medium.ttf", 44), CREAM + (255,), tracking=1)
    ph2 = text_img("0809 361 2901", font("Jost-Medium.ttf", 44), CREAM + (255,), tracking=1)
    for k, ph in enumerate((ph1, ph2)):
        cx = 30 + w * (0.285 if k == 0 else 0.735) + 18
        ix = cx - ph.width / 2 - 34                       # gold phone disc, clear of the digits
        d.ellipse((ix - 18, 30 + 60, ix + 18, 30 + 96), fill=GOLD + (255,))
        d.rounded_rectangle((ix - 6, 30 + 67, ix + 6, 30 + 89), radius=3, outline=(255, 255, 255, 255), width=2)
        im.alpha_composite(ph, (int(cx - ph.width / 2), 30 + 38))
    d.line((30 + 60, 30 + 128, 30 + w - 60, 30 + 128), fill=GOLD + (170,), width=1)
    ad = text_img("Shop A67, Kogi Plaza, BBA Market, Trade Fair Complex, Lagos", font("Jost-Light.ttf", 31), CREAM + (255,))
    im.alpha_composite(ad, (int(30 + w / 2 - ad.width / 2), 30 + 152))
    return im


def order_btn():
    lab = text_img("ORDER NOW", font("Jost-Medium.ttf", 32), (255, 255, 255, 255), tracking=8)
    w, h = lab.width + 90, 82
    g_ = np.zeros((h, w, 4), np.uint8)
    q = np.linspace(0, 1, w)[None, :, None]
    g_[..., :3] = (np.array([226, 172, 76]) * (1 - q) + np.array([160, 106, 24]) * q).astype(np.uint8)
    mm = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mm).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=255)
    g_[..., 3] = np.asarray(mm)
    im = Image.new("RGBA", (w + 50, h + 50), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((25, 33, 25 + w, 33 + h), radius=h // 2, fill=110)
    sh = Image.new("RGBA", im.size, (110, 70, 10, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(sh)
    im.alpha_composite(Image.fromarray(g_, "RGBA"), (25, 25))
    im.alpha_composite(lab, (25 + (w - lab.width) // 2, 25 + (h - lab.height) // 2 - 2))
    return im


PANEL, ORDER = panel(), order_btn()
SPARK = [(rng.uniform(40, W - 40), rng.uniform(80, 1500), rng.uniform(2, 5), rng.uniform(0, 6.28)) for _ in range(40)]


def stand(img, im, cx, base, a, drop):
    """A product standing on a tier top: contact shadow + the cut-out (dropping in from above while it lands)."""
    if a <= 0:
        return
    sh = Image.new("RGBA", (im.width + 80, 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((20, 12, im.width + 60, 30), fill=(70, 40, 16, int(120 * a)))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)), (int(cx - sh.width / 2), int(base - 24)))
    img.alpha_composite(fade(im, c01(a * 2)), (int(round(cx - im.width / 2)), int(round(base - im.height - drop))))


def frame(i):
    t = i / FPS
    img = BG.copy()
    d = ImageDraw.Draw(img)
    for x, y, r, ph in SPARK:                                    # drifting gold light motes
        tw = 0.5 + 0.5 * math.sin(ph * 3 + t * 3)
        yy = (y - t * 14) % 1500 + 60
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=(255, 236, 190, int(140 * tw)))
    img.alpha_composite(TIER_TOP, (int(W / 2 - TIER_TOP.width / 2), TOP_Y - DT))
    land = {}
    for k, (row, idx) in enumerate(LAND):
        land[(row, idx)] = T0 + k * STEP if MODE == "hook" else -1.0
    # top tier products (behind), the front tier, then its products
    for idx, (im, cx) in enumerate(zip(TOP, TOP_X)):
        u = t - land[("t", idx)]
        if u > 0:
            stand(img, im, cx, TOP_Y + 6, eo(u / 0.35), 260 * (1 - eob(u / 0.42)))
    img.alpha_composite(TIER_BOT, (int(W / 2 - TIER_BOT.width / 2), BOT_Y - DB))
    for idx, (im, cx) in enumerate(zip(BOT, BOT_X)):
        u = t - land[("b", idx)]
        if u > 0:
            stand(img, im, cx, BOT_Y + 8, eo(u / 0.35), 260 * (1 - eob(u / 0.42)))
    # one light sweep across the whole collection
    t_sw = T0 + 11 * STEP + 0.3 if MODE == "hook" else 1.1
    q = (t - t_sw) / 1.3
    arr = np.asarray(img).astype(np.float32)
    if 0 < q < 1:
        band = np.exp(-((((XX - (YY - 900) * 0.4) - (-300 + eio(q) * (W + 700))) / 90) ** 2)) * math.sin(math.pi * q) * 0.35
        msk = ((YY > 600) & (YY < BOT_Y + 10)).astype(np.float32)
        arr[..., :3] = 255 - (255 - arr[..., :3]) * (1 - (band * msk)[..., None])
    img = Image.fromarray(arr.astype(np.uint8), "RGBA")
    if MODE == "hook":
        u = t - 0.35
        if u > 0:                                    # big title from the first beat, while the packs land below
            paste(img, T_T1, W / 2, 250 - 16 * (1 - eo(u / 0.5)), c01(u / 0.35))
            u2 = t - 0.75
            if u2 > 0:
                paste(img, T_T2, W / 2, 395, c01(u2 / 0.25), 0.82 + 0.18 * eob(u2 / 0.5))
            dd = ImageDraw.Draw(img)
            rp = eo((u - 0.9) / 0.6)
            dd.line((W / 2 - 200 * rp, 520, W / 2 + 200 * rp, 520), fill=GOLD + (255,), width=3)
        # camera: a slow push-in across the build
        z = 1.0 + 0.06 * eio(t / DUR)
    elif MODE == "group":                            # finale: the whole collection, no text, slow push-in
        z = 1.0 + 0.08 * eio(t / DUR)
    else:
        u = t - 0.2
        paste(img, T_BRAND, W / 2, 170, c01(u / 0.4), 0.92 + 0.08 * eob(u / 0.5))
        paste(img, T_SUB, W / 2, 270, c01((t - 0.6) / 0.4))
        dd = ImageDraw.Draw(img)
        rp = eo((t - 0.8) / 0.6)
        dd.line((W / 2 - 150 * rp, 308, W / 2 + 150 * rp, 308), fill=GOLD + (255,), width=2)
        u = t - (VO_AT - 0.1)
        if u > 0:
            paste(img, T_S1, W / 2, 392 - 10 * (1 - eo(u / 0.5)), c01(u / 0.3))
        u = t - (VO_AT + 0.45)
        if u > 0:
            paste(img, T_S2, W / 2, 486, c01(u / 0.15), 0.85 + 0.15 * eob(u / 0.45))
        u = t - (VO_AT + 0.9)
        if u > 0:
            paste(img, PANEL, W / 2, 1640 + (1 - eo(u / 0.5)) * 50, c01(u / 0.3))
        u = t - (VO_AT + 1.7)
        if u > 0:
            pulse = 1 + 0.03 * max(0.0, math.sin(2 * math.pi * t / BEAT)) * c01((u - 0.5) / 0.3)
            paste(img, ORDER, W / 2, 1830, c01(u / 0.15), (0.6 + 0.4 * eob(u / 0.45, 2.4)) * pulse)
        z = 1.0
    out = np.asarray(img.convert("RGB"))
    if z > 1.0005:
        M = np.float32([[z, 0, W / 2 * (1 - z)], [0, z, 1150 * (1 - z)]])
        out = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return out


if __name__ == "__main__":
    n = round(DUR * FPS)
    if OUT.endswith(".jpg"):
        picks = [int(FPS * s) for s in (0.5, 1.4, 2.4, 3.3, 4.5)] + [n - 1]
        sheet = Image.new("RGB", (432 * len(picks), 768))
        for k, i in enumerate(picks):
            sheet.paste(Image.fromarray(frame(i)).resize((432, 768), Image.LANCZOS), (432 * k, 0))
        sheet.save(OUT, quality=90)
        Image.fromarray(frame(n - 1)).save(OUT.replace(".jpg", "_last.png"))
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close()
    p.wait()
    print(MODE, n, "frames")
