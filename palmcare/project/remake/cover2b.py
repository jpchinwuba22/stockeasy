"""Video 2 cover: the teaser. Her sun-lit portrait (untouched skin, no brightening), a quiet serif question in the open
sky, and the two straight product cutouts standing in the corner light. Usage: cover2b.py OUT.jpg"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
F = "../fonts/"
INK, ORANGE, WHITE, CREAM = (48, 30, 18), (226, 104, 18), (255, 255, 255), (255, 240, 222)


def font(n, s):
    return ImageFont.truetype(F + n, s)


def text_img(s, fnt, fill, tracking=0, pad=20):
    w = sum(fnt.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    asc, desc = fnt.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c in s:
        d.text((x, pad), c, font=fnt, fill=fill)
        x += fnt.getlength(c) + tracking
    return im


def glow(im, blur, alpha, col):
    """Soft halo behind im. The canvas grows by 3*blur on every side (callers offset by -GP(blur))."""
    p = 3 * blur
    big = Image.new("RGBA", (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
    big.alpha_composite(im, (p, p))
    im = big
    g = Image.new("RGBA", im.size, col + (0,))
    g.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(im)
    return out


def GP(blur):
    return 3 * blur


def bottle(path, h):
    b = Image.open(path).convert("RGBA")
    a = np.asarray(b.split()[-1]).astype(np.float32)
    b.putalpha(Image.fromarray(np.clip((a - 60) * 255 / 195, 0, 255).astype(np.uint8)))   # drop the faint matte box
    b = b.crop(b.getbbox())
    return b.resize((round(b.width * h / b.height), h), Image.LANCZOS)


bg = Image.open("../v2x/cov_9.8.png").convert("RGBA")
img = bg.copy()
# a soft sky veil on the left top only (keeps the face as shot) so the headline reads
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
veil = np.clip(1 - np.hypot((xx - 120) / 760, (yy - 260) / 430), 0, 1) ** 1.4 * 0.55
v = Image.fromarray(np.dstack([np.full((H, W), 255, np.uint8), np.full((H, W), 247, np.uint8), np.full((H, W), 236, np.uint8),
                               (veil * 255).astype(np.uint8)]), "RGBA")
img.alpha_composite(v)
# warm floor glow + gentle bottom shade for the products and the tag
sh = np.clip((yy - 1300) / 620, 0, 1) ** 1.3 * 0.55
img.alpha_composite(Image.fromarray(np.dstack([np.full((H, W), 40, np.uint8), np.full((H, W), 22, np.uint8), np.full((H, W), 10, np.uint8),
                                               (sh * 255).astype(np.uint8)]), "RGBA"))

# brand + question
logo = text_img("PalmCare", font("DMSerifDisplay.ttf", 58), ORANGE + (255,), pad=10)
img.alpha_composite(logo, (58, 70))
reg = text_img("®", font("DMSerifDisplay.ttf", 22), ORANGE + (255,), pad=4)
img.alpha_composite(reg, (58 + logo.width - 16, 82))
l1 = text_img("Her glow", font("DMSerifDisplay.ttf", 100), INK + (255,), pad=10)
l2 = text_img("has a secret.", font("DMSerifDisplay-Italic.ttf", 80), ORANGE + (255,), pad=10)
img.alpha_composite(glow(l1, 14, 0.55, (255, 250, 240)), (52 - GP(14), 170 - GP(14)))
img.alpha_composite(glow(l2, 14, 0.55, (255, 250, 240)), (54 - GP(14), 284 - GP(14)))
hint = text_img("TWO NEW WAYS TO GLOW", font("Jost-SemiBold.ttf", 24), INK + (230,), tracking=5, pad=6)
img.alpha_composite(glow(hint, 8, 0.6, (255, 250, 240)), (62 - GP(8), 420 - GP(8)))

# products: straight cutouts with a soft contact shadow and a warm rim glow
cit, mol = bottle("../straight/out2/citrus.png", 520), bottle("../straight/out2/molecular.png", 418)
floor = 1790
pool = Image.new("RGBA", (700, 200), (0, 0, 0, 0))
ImageDraw.Draw(pool).ellipse((0, 40, 700, 160), fill=(255, 214, 160, 120))
img.alpha_composite(pool.filter(ImageFilter.GaussianBlur(40)), (560, floor - 100))
for b, x in ((cit, 640), (mol, 862)):
    s = Image.new("RGBA", (b.width + 160, 80), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse((40, 22, b.width + 120, 62), fill=(20, 10, 4, 150))
    img.alpha_composite(s.filter(ImageFilter.GaussianBlur(14)), (x - 80, floor - 44))
for b, x in ((cit, 640), (mol, 862)):
    img.alpha_composite(glow(b, 22, 0.35, (255, 214, 160)), (x - GP(22), floor - b.height - GP(22)))

tag = text_img("Citrus Vitamin Glow  +  Molecular Glow", font("Jost-SemiBold.ttf", 30), CREAM + (255,), tracking=1, pad=8)
img.alpha_composite(glow(tag, 10, 0.7, (20, 10, 4)), (W - tag.width - 40 - GP(10), floor + 26 - GP(10)))
img.convert("RGB").save(sys.argv[1], quality=95)
print("ok")
