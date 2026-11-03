"""PalmCare Videos 1-3 (remake) end card: both real products on the video's live set behind a gold hairline frame
that draws itself on, a shimmering gold PalmCare logo with a ruled tagline, a two-line headline, a pulsing ORDER NOW
button and a frosted-glass contact panel (phones + shop address) with drawn icons.
The video is chosen with PCV (1, 2 or 3).  Usage: endcardR.py OUT.mp4|OUT.jpg [SECONDS]"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, ".")
import heroR as h  # noqa: E402

OW, OH, FPS = h.OW, h.OH, h.FPS
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 7.0
F = "../fonts/"
V = h.V
# tagline, headline line 1, headline line 2, camera (cy, Hh start, Hh end), ink, headline gradient end
CARD = {
    1: ("THE  CACAO  RITUAL", "The Ritual", "After.", (1300, 1620, 1560), (42, 24, 12), (206, 146, 84)),
    2: ("THE  RITUAL  AFTER", "Bottled", "sunshine.", (1010, 1960, 1880), (48, 22, 6), (238, 150, 60)),
    3: ("SUN-READY  SKIN", "Made for", "the sun.", (1300, 1560, 1500), (44, 18, 4), (232, 154, 66)),
}[V]
TAGLINE, HL1, HL2, CAMP, INK, HLEND = CARD
GOLD, GOLD2, CREAM, WHITE = (232, 190, 124), (190, 132, 58), (250, 236, 214), (255, 251, 245)
PS = h.duo_products()
YY, XX = h.YY, h.XX


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eob(x):
    x = c01(x)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def text_img(text, font, fill, tracking=0, shadow=0.7, pad=20):
    w = sum(font.getlength(ch) for ch in text) + tracking * (len(text) - 1)
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for ch in text:
        d.text((x, pad), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    if not shadow:
        return im
    sh = Image.new("RGBA", im.size, (20, 10, 2, 0))
    sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * shadow)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 4))
    out.alpha_composite(im)
    return out


def gradient_text(text, font, c0, c1, tracking=0, shadow=0.8):
    im = text_img(text, font, (255, 255, 255), tracking=tracking, shadow=0, pad=30)
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    a[..., :3] = np.array(c0, np.float32) * (1 - g) + np.array(c1, np.float32) * g
    im = Image.fromarray(a.astype(np.uint8), "RGBA")
    sh = Image.new("RGBA", im.size, (20, 10, 2, 0))
    sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * shadow)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 5))
    out.alpha_composite(im)
    return out


def shimmer(im, s, width=45):
    """A bright band travelling across the artwork (s 0..1)."""
    if not 0 < s < 1:
        return im
    arr = np.asarray(im).astype(np.float32)
    xs = np.arange(arr.shape[1])[None, :]
    ys = np.arange(arr.shape[0])[:, None]
    band = np.exp(-(((xs + ys * 0.4) - (-150 + s * (arr.shape[1] + 300))) / width) ** 2)[..., None]
    arr[..., :3] = arr[..., :3] * (1 - band) + 255 * band
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


LOGO = gradient_text("PalmCare", ImageFont.truetype(F + "Cormorant-SemiBold.ttf", 104), (255, 238, 200), GOLD2, tracking=2, shadow=0.6)
SUB = text_img("ADVANCED  SKIN  CARE", ImageFont.truetype(F + "Jost-Light.ttf", 22), CREAM, tracking=8, shadow=0.6)
TAG = text_img(TAGLINE, ImageFont.truetype(F + "Jost-Medium.ttf", 30), WHITE, tracking=8)
L1 = text_img(HL1, ImageFont.truetype(F + "Cormorant-Italic.ttf", 108), WHITE)
L2 = gradient_text(HL2, ImageFont.truetype(F + "Cormorant-Italic.ttf", 146), (255, 240, 214), HLEND)
fp = ImageFont.truetype(F + "Jost-Medium.ttf", 42)
fa = ImageFont.truetype(F + "Jost-Regular.ttf", 29)
PH1 = text_img("0809 361 2901", fp, WHITE, tracking=1, shadow=0.4)
PH2 = text_img("0903 055 5424", fp, WHITE, tracking=1, shadow=0.4)
AD1 = text_img("Shop A67, Kogi Plaza, BBA Market", fa, CREAM, shadow=0.4)
AD2 = text_img("Trade Fair Complex, Lagos", fa, CREAM, shadow=0.4)
CALL = text_img("CALL  TO  ORDER", ImageFont.truetype(F + "Jost-Medium.ttf", 21), GOLD, tracking=6, shadow=0)
VISIT = text_img("VISIT  OUR  SHOP", ImageFont.truetype(F + "Jost-Medium.ttf", 21), GOLD, tracking=6, shadow=0)


def icon_phone(sz=34):
    im = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = sz * 0.56
    x0 = (sz - w) / 2
    d.rounded_rectangle((x0, 1, x0 + w, sz - 2), radius=sz * 0.12, outline=GOLD + (255,), width=3)
    d.line((x0 + w * 0.32, 5, x0 + w * 0.68, 5), fill=GOLD + (255,), width=2)
    d.ellipse((sz / 2 - 2.5, sz - 9, sz / 2 + 2.5, sz - 4), fill=GOLD + (255,))
    return im


def icon_pin(sz=34):
    im = Image.new("RGBA", (sz * 4, sz * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    S = sz * 4
    r = S * 0.3
    cx, cy = S / 2, S * 0.36
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD + (255,))
    d.polygon([(cx - r * 0.82, cy + r * 0.5), (cx + r * 0.82, cy + r * 0.5), (cx, S - 4)], fill=GOLD + (255,))
    d.ellipse((cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4), fill=(0, 0, 0, 0))
    return im.resize((sz, sz), Image.LANCZOS)


ICP, ICL = icon_phone(), icon_pin()


def button(scale, glow):
    w, hh = int(600 * scale), int(112 * scale)
    if w < 10:
        return None
    pad = 70
    im = Image.new("RGBA", (w + 2 * pad, hh + 2 * pad), (0, 0, 0, 0))
    g = Image.new("L", im.size, 0)
    ImageDraw.Draw(g).rounded_rectangle((pad, pad, pad + w, pad + hh), radius=hh // 2, fill=int(255 * glow))
    gl = Image.new("RGBA", im.size, (255, 190, 90, 0))
    gl.putalpha(g.filter(ImageFilter.GaussianBlur(26)))
    im.alpha_composite(gl)
    body = np.zeros((hh, w, 4), np.float32)
    x = np.linspace(0, 1, w)[None, :, None]
    y = np.linspace(0, 1, hh)[:, None, None]
    body[..., :3] = (np.array([170, 98, 26.0]) * (1 - x) + np.array([234, 172, 82.0]) * x) * (1.08 - 0.16 * y)
    m = Image.new("L", (w, hh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, hh - 1), radius=hh // 2, fill=255)
    body[..., 3] = np.asarray(m)
    bi = Image.fromarray(np.clip(body, 0, 255).astype(np.uint8), "RGBA")
    ImageDraw.Draw(bi).rounded_rectangle((1, 1, w - 2, hh - 2), radius=hh // 2, outline=(255, 236, 200, 220), width=2)
    t = text_img("ORDER  NOW", ImageFont.truetype(F + "Jost-Medium.ttf", max(10, int(46 * scale))), WHITE, tracking=int(7 * scale), shadow=0.35)
    bi.alpha_composite(t, ((w - t.width) // 2, (hh - t.height) // 2))
    # arrow chevron
    d = ImageDraw.Draw(bi)
    ax, ay, s = w - hh * 0.62, hh / 2, hh * 0.13
    d.line((ax - s * 0.6, ay - s, ax + s * 0.4, ay, ax - s * 0.6, ay + s), fill=WHITE + (235,), width=max(1, int(4 * scale)), joint="curve")
    im.alpha_composite(bi, (pad, pad))
    return im


def paste(dst, im, cx, y, alpha):
    if im is None or alpha <= 0:
        return
    im = im.copy()
    a = np.asarray(im.split()[-1]).astype(np.float32) * alpha
    im.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    dst.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(y))))


# camera and where the products' base lands on screen -> the headline sits just under it
CY, HH0, HH1 = CAMP
_c = h.clamp_cam(h.POD_X + 12, CY, HH1, 0.0)
BASE_OUT = OH / 2 + (h.POD_Y - _c[1]) * OH / _c[2]
Y_L1 = min(max(1150, BASE_OUT + 10), 1190)
Y_L2 = Y_L1 + 112
Y_BTN = 1505
PANEL = (80, 1650, OW - 80, 1858)
TOPDARK = np.clip(1 - YY / 360, 0, 1) ** 1.5 * 0.6
BOTDARK = np.clip((YY - (Y_L1 - 40)) / 380, 0, 1) ** 1.1 * 0.84
DUST = h.Dust(50, 23)
FRAME_IN = 34


def draw_frame(img, t):
    """Gold hairline frame drawn on from the four corners, with small diamond corner ornaments."""
    p = eo((t - 0.35) / 1.0)
    if p <= 0:
        return
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    m = FRAME_IN
    col = GOLD + (200,)
    lx, ly = (OW / 2 - m) * p, (OH / 2 - m) * p
    for cx, sx in ((m, 1), (OW - m, -1)):
        for cy, sy in ((m, 1), (OH - m, -1)):
            d.line((cx, cy, cx + sx * lx, cy), fill=col, width=2)
            d.line((cx, cy, cx, cy + sy * ly), fill=col, width=2)
            r = 9 * eob((t - 0.35) / 0.5)
            if r > 0:
                d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=GOLD + (255,))
    img.alpha_composite(lay)


def draw_panel(img, rgb_bg, t):
    a = eo((t - 2.3) / 0.6)
    if a <= 0:
        return
    x0, y0, x1, y1 = PANEL
    y0r = y0 + (1 - a) * 30
    # frosted glass: blurred, darkened background inside a rounded rect with a gold edge
    crop = Image.fromarray(np.clip(rgb_bg, 0, 255).astype(np.uint8)).crop((x0, int(y0r), x1, int(y0r) + (y1 - y0)))
    crop = crop.filter(ImageFilter.GaussianBlur(18))
    ca = np.asarray(crop).astype(np.float32) * 0.42 + np.array(INK, np.float32) * 0.38
    glass = Image.fromarray(np.clip(ca, 0, 255).astype(np.uint8)).convert("RGBA")
    m = Image.new("L", glass.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, glass.width - 1, glass.height - 1), radius=34, fill=int(255 * a))
    glass.putalpha(m)
    ImageDraw.Draw(glass).rounded_rectangle((1, 1, glass.width - 2, glass.height - 2), radius=34, outline=GOLD + (int(170 * a),), width=2)
    # divider
    ImageDraw.Draw(glass).line((glass.width / 2, 34, glass.width / 2, glass.height - 34), fill=GOLD + (int(110 * a),), width=1)
    img.alpha_composite(glass, (x0, int(y0r)))
    cl, cr = x0 + (x1 - x0) * 0.25, x0 + (x1 - x0) * 0.75
    yb = y0r + 26
    for k, (cx, lab, ic, l1, l2, big) in enumerate(((cl, CALL, ICP, PH1, PH2, True), (cr, VISIT, ICL, AD1, AD2, False))):
        aa = eo((t - 2.55 - 0.15 * k) / 0.5)
        lw = lab.width + ic.width + 10
        lx = cx - lw / 2
        paste(img, ic, lx + ic.width / 2, yb + 2, aa)
        paste(img, lab, lx + ic.width + 10 + lab.width / 2, yb + (ic.height - lab.height) / 2 + 2, aa)
        g1 = 52 if big else 46
        paste(img, l1, cx, yb + 44 + (1 - aa) * 10, aa)
        paste(img, l2, cx, yb + 44 + g1 + (1 - aa) * 10, aa)


def frame(i):
    t = i / FPS
    q = t / DUR
    Hh = HH0 - (HH0 - HH1) * h.ease(q)
    cam = h.clamp_cam(h.POD_X + 12, CY - 10 * q, Hh, 0.0)
    plate = h.plate_at(20 + t, PS, 1.0)
    rgb, m = h.render(plate, PS, cam)
    s = c01((t - 0.1) / 0.9)
    if 0 < s < 1:
        rgb = h.screen(rgb, h.sweep(m, -500 + s * (OW + 1600))[..., None] * 255)
    fl = math.sin(math.pi * c01((t - 0.1) / 0.7)) * 0.75
    rgb = h.flare(rgb, OW * (0.92 - 0.6 * c01((t - 0.1) / 0.7)), 560, fl)
    rgb = DUST.draw(rgb, t, 1.0)
    dark = np.array(INK, np.float32)
    k = (TOPDARK + BOTDARK)[..., None]
    rgb = rgb * (1 - k) + dark * k
    rgb = h.bloom(rgb, threshold=228, radius=28, amount=0.24)
    rgb = rgb * h.VIG[..., None]
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    draw_frame(img, t)
    al = eo((t - 0.4) / 0.6)
    paste(img, shimmer(LOGO, c01((t - 1.2) / 1.0), 40), OW / 2, 58 + (1 - al) * 14, al)
    paste(img, SUB, OW / 2, 176 + (1 - al) * 10, al * 0.9)
    at = eo((t - 0.75) / 0.5)
    paste(img, TAG, OW / 2, 226 + (1 - at) * 12, at)
    d = ImageDraw.Draw(img)
    rl = 90 * eo((t - 0.85) / 0.6)
    if rl > 1:
        yy = 226 + TAG.height / 2 + 2
        hw = TAG.width / 2 - 6
        d.line((OW / 2 - hw - 14 - rl, yy, OW / 2 - hw - 14, yy), fill=GOLD + (230,), width=2)
        d.line((OW / 2 + hw + 14, yy, OW / 2 + hw + 14 + rl, yy), fill=GOLD + (230,), width=2)
    a1 = eo((t - 1.1) / 0.55)
    paste(img, L1, OW / 2, Y_L1 + (1 - a1) * 40, a1)
    a2 = eo((t - 1.35) / 0.6)
    paste(img, shimmer(L2, c01((t - 2.2) / 0.9)), OW / 2, Y_L2 + (1 - a2) * 50, a2)
    bt = c01((t - 1.9) / 0.45)
    if bt > 0:
        pulse = 0.55 + 0.45 * (0.5 + 0.5 * math.sin((t - 2.3) * 2 * math.pi / 1.1)) if t > 2.3 else 0.5
        sc = eob(bt) * (1 + 0.025 * math.sin(max(0, t - 2.3) * 2 * math.pi / 1.1))
        b = button(sc, pulse)
        if b:
            paste(img, b, OW / 2, Y_BTN - (b.height - 112 * sc) / 2, min(1, bt * 1.5))
    draw_panel(img, rgb, t)
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    fl_in = c01(1 - t / 0.3)
    if fl_in > 0:
        arr = arr * (1 - fl_in) + np.array([255, 240, 214.0]) * fl_in
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
