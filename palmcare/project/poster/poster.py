"""PalmCare Glow Collection poster: all 11 real product cutouts (exact labels) staged on the luxury podium set
(setP.png), warm-graded to the golden light, with contact shadows, polished reflections and brand typography.
Writes the flat poster plus Canva layers (background, products with shadows, no text).
Usage: poster.py OUTDIR"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "../v3")
from prodfx import bloom, premium, rim  # noqa: E402

S = 2                                     # render at 2x the 1536x2048 plate
F = "../fonts/"
PLATE = Image.open("setP.png").convert("RGB").resize((1536 * S, 2048 * S), Image.LANCZOS)
W, H = PLATE.size
PX_CM = 23.0                              # scale of the centre podium (a 27 cm wash = 620 px)

# (cutout, height in cm, centre x, base y, depth scale, surface: 'top' polished podium or 'floor' glossy floor)
ITEMS = [
    ("../hero/milky_cut.png", 26.5, 310, 1213, 0.97, "top"),
    ("../v2/citrus_cut.png", 26.5, 1231, 1213, 0.97, "top"),
    ("../group/trop_cut.png", 26.5, 652, 1081, 1.0, "top"),
    ("../group/dermalight_cut.png", 22.0, 895, 1083, 1.0, "top"),
    ("../hero/cacao_cut.png", 22.0, 150, 1662, 1.12, "floor"),
    ("../v2/molecular_cut.png", 22.0, 1388, 1662, 1.12, "floor"),
    ("../v3/vitac_fix.png", 11.5, 432, 1380, 1.06, "top"),
    ("../v3/glowshield_cut.png", 12.5, 588, 1380, 1.06, "top"),
    ("../v4/jar_cut.png", 6.4, 770, 1384, 1.06, "top"),
    ("../v4/n10_fix2.png", 10.5, 950, 1380, 1.06, "top"),
    ("../v5/dl_cut.png", 10.5, 1104, 1380, 1.06, "top"),
]


def finish(img):
    """Studio finish, then relight for the warm golden set: warm cast, gentle exposure, golden back-rim, base AO."""
    img = premium(img.crop(img.split()[-1].getbbox()))
    img = rim(img, strength=0.55, from_right=False)
    img = rim(img, strength=0.55, from_right=True)
    a = np.asarray(img).astype(np.float32)
    a[..., :3] *= np.array([1.0, 0.945, 0.86], np.float32) * 0.96
    y = np.linspace(0, 1, a.shape[0], dtype=np.float32)[:, None, None]
    a[..., :3] *= 1 - 0.18 * np.clip((y - 0.86) / 0.14, 0, 1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def body_width(im):
    al = np.asarray(im)[..., 3]
    return int((al[int(al.shape[0] * 0.8)] > 128).sum())


def build():
    placed = []
    for path, cm, cx, base, k, surf in ITEMS:
        im = finish(Image.open(path).convert("RGBA"))
        h = round(cm * PX_CM * k * S)
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        placed.append((im, cx * S, base * S, surf))
    # draw back-to-front: higher base line = further back
    placed.sort(key=lambda p: p[2])
    prod = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for im, cx, base, surf in placed:
        bw = body_width(im)
        # reflection: faint on polished stone, strong on the glossy floor
        r = im.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, im.width, int(im.height * (0.5 if surf == "floor" else 0.18))))
        ra = np.asarray(r).astype(np.float32)
        ra[..., 3] *= np.linspace(0.38 if surf == "floor" else 0.16, 0, r.height)[:, None]
        ra[..., :3] *= 0.8
        r = Image.fromarray(ra.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(3 * S if surf == "floor" else 2 * S))
        prod.alpha_composite(r, (int(cx - im.width / 2), int(base)))
        # contact shadow + soft forward shadow (the key light is the halo behind)
        sh = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(sh)
        d.ellipse((cx - bw * 0.62, base - bw * 0.06, cx + bw * 0.62, base + bw * 0.16), fill=120)
        sh = sh.filter(ImageFilter.GaussianBlur(10 * S))
        c2 = Image.new("L", (W, H), 0)
        ImageDraw.Draw(c2).ellipse((cx - bw * 0.5, base - bw * 0.05, cx + bw * 0.5, base + bw * 0.035), fill=235)
        c2 = c2.filter(ImageFilter.GaussianBlur(3 * S))
        m = Image.fromarray(np.maximum(np.asarray(sh), np.asarray(c2)))
        shadow = Image.new("RGBA", (W, H), (18, 8, 2, 0))
        shadow.putalpha(m)
        prod.alpha_composite(shadow)
        prod.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(base - im.height + 2 * S))))
    return prod


def text_img(s, font, fill, tracking=0, pad=40):
    w = sum(font.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c in s:
        d.text((x, pad), c, font=font, fill=fill)
        x += font.getlength(c) + tracking
    return im


def gold(im, c0=(255, 236, 196), c1=(196, 140, 62)):
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    a[..., :3] = np.array(c0, np.float32) * (1 - g) + np.array(c1, np.float32) * g
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def glow(im, colour=(255, 200, 120), blur=18, alpha=0.55):
    g = Image.new("RGBA", im.size, colour + (0,))
    g.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(im)
    return out


def shadowed(im, blur=10, alpha=0.7):
    sh = Image.new("RGBA", im.size, (8, 3, 0, 0))
    sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 4))
    out.alpha_composite(im)
    return out


def paste_c(dst, im, cy):
    dst.alpha_composite(im, (int(W / 2 - im.width / 2), int(cy - im.height / 2)))


def typography(img):
    cream = (250, 238, 218)
    logo = glow(gold(text_img("PalmCare", ImageFont.truetype(F + "Cormorant-SemiBold.ttf", 220 * S // 2 * 2), (255, 255, 255), tracking=6 * S)),
                blur=24 * S, alpha=0.45)
    paste_c(img, logo, 205 * S)
    tag = shadowed(text_img("THE   GLOW   COLLECTION", ImageFont.truetype(F + "Jost-Light.ttf", 40 * S), cream, tracking=14 * S))
    paste_c(img, tag, 318 * S)
    d = ImageDraw.Draw(img)
    half = tag.width / 2 - 40 + 28 * S          # gold rules start just clear of the lettering
    for x0, x1 in ((W / 2 - half - 90 * S, W / 2 - half), (W / 2 + half, W / 2 + half + 90 * S)):
        d.line((x0, 318 * S, x1, 318 * S), fill=(214, 168, 96, 255), width=2 * S)
    line = shadowed(text_img("Radiance, in every ritual.", ImageFont.truetype(F + "Cormorant-Italic.ttf", 74 * S), cream), blur=12, alpha=0.8)
    paste_c(img, line, 1792 * S)
    new = shadowed(text_img("NEW  ·  ADVANCED TROPICAL GLOW  &  DERMALIGHT", ImageFont.truetype(F + "Jost-Medium.ttf", 26 * S), (232, 190, 120), tracking=4 * S))
    paste_c(img, new, 1858 * S)
    info = shadowed(text_img("Shop A67, Kogi Plaza, BBA Market, Trade Fair Complex, Lagos", ImageFont.truetype(F + "Jost-Regular.ttf", 27 * S), cream, tracking=1 * S))
    paste_c(img, info, 1938 * S)
    ph = shadowed(text_img("0809 361 2901   |   0903 055 5424", ImageFont.truetype(F + "Jost-Medium.ttf", 33 * S), (255, 248, 236), tracking=2 * S))
    paste_c(img, ph, 1990 * S)
    return img


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    prod = build()
    # dark legibility scrims for the type, then the products, then a whisper of bloom on the whole frame
    base = np.asarray(PLATE).astype(np.float32)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    k = np.clip((0.19 - yy) / 0.19, 0, 1) ** 1.4 * 0.55 + np.clip((yy - 0.84) / 0.16, 0, 1) ** 1.2 * 0.62
    base = base * (1 - k) + np.array([14, 7, 2], np.float32) * k
    bg = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    bg.convert("RGB").save(os.path.join(outdir, "layer_background.jpg"), quality=95)
    prod.save(os.path.join(outdir, "layer_products.png"))
    comp = bg.copy()
    comp.alpha_composite(prod)
    arr = bloom(np.asarray(comp.convert("RGB")).astype(np.float32), threshold=232, radius=26 * S, amount=0.18)
    flat = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    flat.convert("RGB").save(os.path.join(outdir, "poster_notext.jpg"), quality=95)
    typography(flat).convert("RGB").save(os.path.join(outdir, "PalmCare_Glow_Collection_Poster.jpg"), quality=95)


if __name__ == "__main__":
    main(sys.argv[1])
