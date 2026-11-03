"""Video 5 hero end card, built for click-through: the real Dermaluxe bottle on the live moonlit set warming
towards dawn, a bold "Wake up glowing." headline, a pulsing ORDER NOW button, phone numbers and address.
Usage: endcard5.py OUT.mp4|OUT.jpg [SECONDS]"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import hero5 as h

OW, OH, FPS = h.OW, h.OH, h.FPS
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 5.5
F = "../fonts/"
ROSE, GOLD, WHITE = (246, 196, 206), (232, 190, 140), (255, 250, 248)
P = h.Product(h.DL, h.POD_X, h.POD_Y + 14, 660)
YY, XX = h.YY, h.XX


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eob(x):
    """ease-out-back: a small overshoot for the button pop."""
    x = c01(x)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def text_img(text, font, fill, tracking=0, shadow=True):
    w = sum(font.getlength(ch) for ch in text) + tracking * (len(text) - 1)
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (int(w) + 40, asc + desc + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 20
    for ch in text:
        d.text((x, 20), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    if shadow:
        sh = Image.new("RGBA", im.size, (20, 0, 12, 0))
        sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.7)))
        out = Image.new("RGBA", im.size, (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 4))
        out.alpha_composite(im)
        return out
    return im


def gradient_text(text, font, c0, c1, tracking=0):
    im = text_img(text, font, (255, 255, 255), tracking, shadow=False)
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    a[..., :3] = np.array(c0, np.float32) * (1 - g) + np.array(c1, np.float32) * g
    im = Image.fromarray(a.astype(np.uint8), "RGBA")
    sh = Image.new("RGBA", im.size, (20, 0, 12, 0))
    sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.75)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 5))
    out.alpha_composite(im)
    return out


LOGO = text_img("PalmCare", ImageFont.truetype(F + "Cormorant-SemiBold.ttf", 76), GOLD, tracking=2)
L1 = text_img("Wake up", ImageFont.truetype(F + "Cormorant-Italic.ttf", 120), WHITE)
L2 = gradient_text("glowing.", ImageFont.truetype(F + "Cormorant-Italic.ttf", 176), (255, 222, 228), (226, 120, 150))
NAME = text_img("DERMALUXE PRO", ImageFont.truetype(F + "Jost-Medium.ttf", 46), WHITE, tracking=10)
SUB = text_img("Hydrating Night Repair Serum", ImageFont.truetype(F + "Cormorant-Italic.ttf", 50), ROSE)
PH1 = text_img("0809 361 2901   |   0903 055 5424", ImageFont.truetype(F + "Jost-Medium.ttf", 46), WHITE)
fa = ImageFont.truetype(F + "Jost-Regular.ttf", 31)
AD1 = text_img("Shop A67, Kogi Plaza, BBA Market", fa, (236, 214, 222))
AD2 = text_img("Trade Fair Complex, Lagos", fa, (236, 214, 222))


def button(scale, glow):
    w, hh = int(560 * scale), int(118 * scale)
    if w < 10:
        return None
    pad = 70
    im = Image.new("RGBA", (w + 2 * pad, hh + 2 * pad), (0, 0, 0, 0))
    g = Image.new("L", im.size, 0)
    ImageDraw.Draw(g).rounded_rectangle((pad, pad, pad + w, pad + hh), radius=hh // 2, fill=int(255 * glow))
    gl = Image.new("RGBA", im.size, (255, 120, 170, 0))
    gl.putalpha(g.filter(ImageFilter.GaussianBlur(26)))
    im.alpha_composite(gl)
    body = np.zeros((hh, w, 4), np.float32)
    x = np.linspace(0, 1, w)[None, :, None]
    body[..., :3] = np.array([214, 40, 104.0]) * (1 - x) + np.array([244, 120, 150.0]) * x
    m = Image.new("L", (w, hh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, hh - 1), radius=hh // 2, fill=255)
    body[..., 3] = np.asarray(m)
    bi = Image.fromarray(body.astype(np.uint8), "RGBA")
    ImageDraw.Draw(bi).rounded_rectangle((1, 1, w - 2, hh - 2), radius=hh // 2, outline=(255, 225, 235, 200), width=2)
    t = text_img("ORDER NOW", ImageFont.truetype(F + "Jost-Medium.ttf", max(10, int(48 * scale))), WHITE, tracking=int(8 * scale), shadow=False)
    bi.alpha_composite(t, ((w - t.width) // 2, (hh - t.height) // 2))
    im.alpha_composite(bi, (pad, pad))
    return im


def paste(dst, im, cx, y, alpha, mask_rise=0.0):
    """Centre-paste with alpha; mask_rise>0 reveals the image bottom-up (text rising out of a mask)."""
    if im is None or alpha <= 0:
        return
    im = im.copy()
    a = np.asarray(im.split()[-1]).astype(np.float32) * alpha
    if mask_rise < 1:
        rows = np.arange(a.shape[0])[:, None]
        a *= np.clip((rows - (1 - mask_rise) * a.shape[0] * 0.0) / 1, 0, 1)
    im.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    dst.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(y))))


TOPDARK = np.clip(1 - YY / 520, 0, 1) ** 1.6 * 0.55
BOTDARK = np.clip((YY - 1180) / 420, 0, 1) ** 1.2 * 0.78
SPARK = h.Sparkles(50, 21)


def frame(i):
    t = i / FPS
    q = t / DUR
    Hh = 1840 - 90 * h.ease(q)
    cam = h.clamp_cam(h.POD_X, 927 - 15 * q, Hh, 0.0)
    light = 0.35 + 0.65 * h.ease(c01(t / 0.6))
    plate = h.plate_at(40 + t, [P], light)
    rgb, m = h.render(plate, [P], cam)
    # moonlight -> dawn: warm the whole frame gradually
    w = h.ease(c01((t - 0.8) / 4.2))
    rgb = rgb * np.array([1 + 0.10 * w, 1 + 0.02 * w, 1 - 0.08 * w], np.float32)
    # light sweep on the bottle + flare as it lands
    s = c01((t - 0.15) / 0.9)
    if 0 < s < 1:
        rgb = h.screen(rgb, h.sweep(m, -500 + s * (OW + 1600))[..., None] * 255)
    fl = math.sin(math.pi * c01((t - 0.2) / 0.7)) * 0.8
    rgb = h.flare(rgb, OW * (0.9 - 0.55 * c01((t - 0.2) / 0.7)), 600, fl)
    rgb = SPARK.draw(rgb, t, 1.0)
    # legibility gradients
    dark = np.array([26, 4, 18], np.float32)
    k = (TOPDARK + BOTDARK)[..., None]
    rgb = rgb * (1 - k) + dark * k
    rgb = h.bloom(rgb, threshold=222, radius=28, amount=0.28)
    rgb = rgb * h.VIG[..., None]
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    # typography
    paste(img, LOGO, OW / 2, 70 + (1 - eo((t - 0.3) / 0.5)) * 14, eo((t - 0.3) / 0.5))
    a1 = eo((t - 0.55) / 0.55)
    paste(img, L1, OW / 2, 170 + (1 - a1) * 50, a1)
    a2 = eo((t - 0.8) / 0.6)
    l2 = L2
    gs = c01((t - 1.7) / 0.9)
    if 0 < gs < 1:   # gold shimmer across "glowing."
        arr = np.asarray(L2).astype(np.float32)
        xs = np.arange(arr.shape[1])[None, :]
        ys = np.arange(arr.shape[0])[:, None]
        band = np.exp(-(((xs + ys * 0.4) - (-150 + gs * (arr.shape[1] + 300))) / 45) ** 2)[..., None]
        arr[..., :3] = arr[..., :3] * (1 - band) + 255 * band
        l2 = Image.fromarray(arr.astype(np.uint8), "RGBA")
    paste(img, l2, OW / 2, 270 + (1 - a2) * 60, a2)
    an = eo((t - 1.3) / 0.5)
    paste(img, NAME, OW / 2, 1300 + (1 - an) * 20, an)
    paste(img, SUB, OW / 2, 1362 + (1 - an) * 20, eo((t - 1.45) / 0.5))
    bt = c01((t - 1.8) / 0.45)
    if bt > 0:
        pulse = 0.55 + 0.45 * (0.5 + 0.5 * math.sin((t - 2.2) * 2 * math.pi / 1.1)) if t > 2.2 else 0.5
        sc = eob(bt) * (1 + 0.025 * math.sin(max(0, t - 2.2) * 2 * math.pi / 1.1))
        b = button(sc, pulse)
        paste(img, b, OW / 2, 1468 - (b.height - 118 * sc) / 2 if b else 0, min(1, bt * 1.5))
    ap = eo((t - 2.25) / 0.5)
    paste(img, PH1, OW / 2, 1640 + (1 - ap) * 16, ap)
    for k2, ad in enumerate((AD1, AD2)):
        aa = eo((t - 2.5 - 0.12 * k2) / 0.5)
        paste(img, ad, OW / 2, 1722 + k2 * 44 + (1 - aa) * 12, aa)
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    fl_in = c01(1 - t / 0.3)
    if fl_in > 0:
        arr = arr * (1 - fl_in) + np.array([255, 228, 236.0]) * fl_in
    arr = arr + h.RNG.normal(0, 1.4, (OH, OW))[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    out = sys.argv[1]
    n = round(DUR * FPS)
    if out.endswith(".jpg"):
        picks = [int(n * f) for f in (0.08, 0.25, 0.45, 0.98)]
        sheet = Image.new("RGB", (360 * 4, 640))
        for k, i in enumerate(picks):
            sheet.paste(Image.fromarray(frame(i)).resize((360, 640), Image.LANCZOS), (360 * k, 0))
        sheet.save(out, quality=92)
        Image.fromarray(frame(n - 1)).save(out.replace(".jpg", "_last.png"))
    else:
        pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for i in range(n):
            pr.stdin.write(frame(i).tobytes())
        pr.stdin.close()
        pr.wait()
