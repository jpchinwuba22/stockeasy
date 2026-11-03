"""Cover / thumbnail images (1080x1920) for the five PalmCare videos: the strongest clean frame,
PalmCare logo, a bold headline and the video's real products, kept inside the 3:4 grid-safe zone.
Usage: covers.py [N ...]"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "../v3")
from prodfx import premium  # noqa: E402

F = "../fonts/"
W, H = 1080, 1920
# frame, shift-up px, products [(cutout, height px)], headline lines, sub, accent, shade, out
COVERS = {
    1: ("f1s_1.6.png", 70, [("../hero/milky_cut.png", 400), ("../hero/cacao_cut.png", 332)],
        ("The Ritual", "After."), "Milky Hydro-Glow Wash  +  Cacao & Collagen Lotion", (226, 168, 112), (40, 22, 12), "PalmCare_01_Cacao_Ritual_cover"),
    2: ("f2_9.5.png", 200, [("../v2/citrus_cut.png", 380), ("../v2/molecular_cut.png", 316)],
        ("Bottled", "sunshine."), "Citrus Vitamin Glow Wash  +  Molecular Glow Lotion", (255, 170, 80), (46, 20, 6), "PalmCare_02_Citrus_Ritual_cover"),
    3: ("f3_c8.3.png", 0, [("../v3/vitac_fix.png", 330), ("../v3/glowshield_cut.png", 360)],
        ("Made for", "the sun."), "Vita C+ Serum  +  GlowShield SPF 50+", (240, 190, 120), (44, 20, 8), "PalmCare_03_Shadow_and_Light_cover"),
    4: ("f4_0.2.png", 0, [("../v4/n10_fix2.png", 330), ("../v4/jar_cut.png", 170)],
        ("Even tone.", "Every day."), "N10 Niacinamide Serum  +  Vitamin C Moisturiser", (150, 225, 218), (6, 30, 34), "PalmCare_04_Still_Water_cover"),
    5: ("f5_8.8.png", 150, [("../v5/dl_cut.png", 360)],
        ("Wake up", "glowing."), "Dermaluxe Pro Hydrating Night Repair Serum", (246, 176, 196), (34, 6, 20), "PalmCare_05_After_Dark_cover"),
    7: ("f1n_c.png", 60, [("../straight/out/milky.png", 400), ("../straight/out/cacao.png", 330)],
        ("Pamper your", "skin."), "PalmCare Milky Hydro-Glow  +  Cacao & Collagen", (226, 168, 112), (40, 22, 12), "PalmCare_01_Milky_Cacao_cover"),
    6: ("f6_9.0.png", 120, [("../group/trop_cut.png", 400), ("../group/dermalight_cut.png", 332)],
        ("Tropical", "glow."), "Advanced Tropical Glow Wash  +  Dermalight Lotion", (234, 178, 98), (38, 20, 6), "PalmCare_06_Tropical_Glow_cover"),
}


def text_img(s, font, fill, tracking=0, shadow=0.6, blur=10):
    w = sum(font.getlength(c) for c in s) + tracking * (len(s) - 1)
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (int(w) + 60, asc + desc + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 30
    for c in s:
        d.text((x, 30), c, font=font, fill=fill)
        x += font.getlength(c) + tracking
    if not shadow:
        return im
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * shadow)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 4))
    out.alpha_composite(im)
    return out


def gradient_text(s, font, c0, c1):
    im = text_img(s, font, (255, 255, 255), shadow=0)
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    a[..., :3] = np.array(c0, np.float32) * (1 - g) + np.array(c1, np.float32) * g
    im = Image.fromarray(a.astype(np.uint8), "RGBA")
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.7)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 5))
    out.alpha_composite(im)
    return out


def paste_c(dst, im, cx, y):
    dst.alpha_composite(im, (int(cx - im.width / 2), int(y)))


def product(path, h):
    im = Image.open(path).convert("RGBA")
    im = premium(im.crop(im.split()[-1].getbbox()))
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def build(n):
    frame, dy, prods, head, sub, acc, shade, out = COVERS[n]
    src = Image.open(frame).convert("RGB").resize((W, H), Image.LANCZOS)
    img = Image.new("RGB", (W, H), shade)
    img.paste(src, (0, -dy))
    arr = np.asarray(img).astype(np.float32)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    # top scrim for the logo, deep bottom scrim for headline + products
    top = (0.17, 0.85) if n == 7 else (0.12, 0.6)    # the bright shower frame needs a deeper top scrim for the logo
    k = np.clip((top[0] - yy) / top[0], 0, 1) ** 1.5 * top[1] + np.clip((yy - 0.52) / 0.30, 0, 1) ** 1.3 * 0.9
    arr = arr * (1 - k) + np.array(shade, np.float32) * k
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

    paste_c(img, text_img("PalmCare", ImageFont.truetype(F + "Cormorant-SemiBold.ttf", 80), (255, 246, 236), tracking=2), W / 2, 22)
    paste_c(img, text_img("ADVANCED  SKIN  CARE", ImageFont.truetype(F + "Jost-Medium.ttf", 24), acc, tracking=7, shadow=0.7), W / 2, 104)

    # products: soft glow pool + contact shadow, base just above the grid-safe bottom (y 1680)
    base = 1730
    ims = [product(p, h) for p, h in prods]
    gap = 26
    tot = sum(i.width for i in ims) + gap * (len(ims) - 1)
    x = W / 2 - tot / 2
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((W / 2 - tot * 0.75, base - 260, W / 2 + tot * 0.75, base + 60), fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    gl = Image.new("RGBA", (W, H), acc + (0,))
    gl.putalpha(glow)
    img.alpha_composite(gl)
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).ellipse((W / 2 - tot * 0.58, base - 14, W / 2 + tot * 0.58, base + 16), fill=230)
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)), (0, 0))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    black.putalpha(sh.point(lambda v: int(v * 0.75)))
    img.alpha_composite(black)
    tops = []
    for im in ims:
        img.alpha_composite(im, (int(x), base - im.height))
        tops.append(base - im.height)
        x += im.width + gap

    # headline sits right above the tallest product
    y_top = min(tops)
    l1 = text_img(head[0], ImageFont.truetype(F + "Cormorant-Italic.ttf", 118), (255, 250, 246), blur=14)
    l2 = gradient_text(head[1], ImageFont.truetype(F + "Cormorant-Italic.ttf", 150), (255, 244, 232), acc)
    sb = text_img(sub, ImageFont.truetype(F + "Jost-Regular.ttf", 30), (255, 246, 238), shadow=0.8)
    y2 = y_top - 40 - sb.height
    paste_c(img, sb, W / 2, y2)
    y1 = y2 - l2.height + 18
    paste_c(img, l2, W / 2, y1)
    paste_c(img, l1, W / 2, y1 - l1.height + 52)
    # call-to-action pill
    pill = Image.new("RGBA", (300, 64), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle((0, 0, 299, 63), radius=32, outline=acc + (255,), width=2, fill=(0, 0, 0, 70))
    t = text_img("WATCH  NOW", ImageFont.truetype(F + "Jost-Medium.ttf", 26), (255, 250, 246), tracking=5, shadow=0)
    pill.alpha_composite(t, ((300 - t.width) // 2, (64 - t.height) // 2))
    paste_c(img, pill, W / 2, base + 40)
    img.convert("RGB").save(out + ".jpg", quality=95)
    return out + ".jpg"


if __name__ == "__main__":
    ns = [int(a) for a in sys.argv[1:]] or sorted(COVERS)
    for n in ns:
        print(build(n))
