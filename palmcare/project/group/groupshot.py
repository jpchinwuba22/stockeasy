"""PalmCare collection launch photo: all 11 real product cutouts on the two-tier travertine stage (setG_b),
studio-finished, seated with contact + cast shadows and a soft reflection, plus launch typography.
Usage: groupshot.py OUT.png [notext]"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "../v3")
from prodfx import bloom, premium  # noqa: E402

S = 2                                  # render at 2x the 1536x2048 plate
F = "../fonts/"
BG = Image.open("setG_b.png").convert("RGB").resize((1536 * S, 2048 * S), Image.LANCZOS)
W, H = BG.size
BACK_Y, FRONT_Y = 1302, 1512           # base lines on the upper / lower tier (plate px)
PX_CM = 20.5                           # back-tier scale; the front tier is a touch closer to camera
FRONT_K = 1.24

# (file, height cm, tier) -- new launches (Tropical Glow + Dermalight) take the centre of the top tier
BACK = [("../hero/cacao_cut.png", 22.0), ("../hero/milky_cut.png", 26.5), ("trop_cut.png", 26.5),
        ("dermalight_cut.png", 22.0), ("../v2/citrus_cut.png", 26.5), ("../v2/molecular_cut.png", 22.0)]
FRONT = [("../v3/vitac_fix.png", 11.5), ("../v3/glowshield_cut.png", 12.5), ("../v4/jar_cut.png", 6.4),
         ("../v4/n10_fix2.png", 10.5), ("../v5/dl_cut.png", 10.5)]


def load(path, h_px):
    im = Image.open(path).convert("RGBA")
    im = im.crop(im.split()[-1].getbbox())
    im = premium(im)
    im = im.resize((max(1, round(im.width * h_px / im.height)), round(h_px)), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    # warm the neutral studio white towards the peach plate light, keep the label colours honest
    a[..., :3] *= np.array([1.0, 0.975, 0.935], np.float32)
    # gentle shading: the left side falls away from the key light (sun from the right)
    x = np.linspace(0, 1, im.width, dtype=np.float32)[None, :, None]
    a[..., :3] *= 0.90 + 0.10 * x
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def body_width(im):
    al = np.asarray(im)[..., 3]
    return int((al[int(al.shape[0] * 0.75)] > 128).sum())


def layout(items, k, x0, x1):
    ims = [load(p, h * PX_CM * k * S) for p, h in items]
    tot = sum(i.width for i in ims)
    gap = (x1 - x0 - tot) / (len(ims) - 1)
    xs, x = [], x0
    for i in ims:
        xs.append(x + i.width / 2)
        x += i.width + gap
    return ims, xs


def shadow_layer(ims, xs, base, off=(-34, -10), blur=22, amt=0.42):
    """Soft silhouette shadow thrown back-left by the high-right key light, plus tight contact occlusion."""
    sh = Image.new("L", (W, H), 0)
    for im, cx in zip(ims, xs):
        al = im.split()[-1].point(lambda v: int(v * amt))
        sh.paste(al, (int(cx - im.width / 2 + off[0] * S), int(base * S - im.height + off[1] * S)), al)
    sh = sh.filter(ImageFilter.GaussianBlur(blur * S))
    ct = Image.new("L", (W, H), 0)
    for im, cx in zip(ims, xs):
        bw = body_width(im)
        d = ImageDraw.Draw(ct)
        d.ellipse((cx - bw * 0.52, base * S - 9 * S, cx + bw * 0.48, base * S + 7 * S), fill=255)
    ct = ct.filter(ImageFilter.GaussianBlur(5 * S))
    return Image.fromarray(np.maximum(np.asarray(sh), np.asarray(ct)))


def reflection(canvas, ims, xs, base):
    for im, cx in zip(ims, xs):
        r = im.transpose(Image.FLIP_TOP_BOTTOM)
        r = r.crop((0, 0, r.width, int(r.height * 0.22)))
        a = np.asarray(r).astype(np.float32)
        fade = np.linspace(0.16, 0, r.height, dtype=np.float32)[:, None] ** 1.0
        a[..., 3] *= fade
        r = Image.fromarray(a.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(3 * S))
        canvas.alpha_composite(r, (int(cx - im.width / 2), int(base * S)))


def place(canvas, ims, xs, base):
    for im, cx in zip(ims, xs):
        canvas.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(base * S - im.height + 3 * S))))


def darken(canvas, mask, colour=(92, 58, 38), strength=0.62):
    arr = np.asarray(canvas).astype(np.float32)
    m = np.asarray(mask).astype(np.float32)[..., None] / 255 * strength
    arr[..., :3] = arr[..., :3] * (1 - m) + np.array(colour, np.float32) * m * (arr[..., :3] / 255)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def text(canvas, s, font, fill, cy, tracking=0, glow=None):
    w = sum(font.getlength(c) for c in s) + tracking * (len(s) - 1)
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (int(w) + 80, asc + desc + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 40
    for c in s:
        d.text((x, 40), c, font=font, fill=fill)
        x += font.getlength(c) + tracking
    if glow:
        g = Image.new("RGBA", im.size, glow + (0,))
        g.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(14 * S)).point(lambda v: int(v * 0.8)))
        canvas.alpha_composite(g, (int(W / 2 - im.width / 2), int(cy - im.height / 2)))
    canvas.alpha_composite(im, (int(W / 2 - im.width / 2), int(cy - im.height / 2)))


def main(out, with_text=True):
    canvas = BG.convert("RGBA")
    bims, bxs = layout(BACK, 1.0, 120 * S, 1416 * S)
    fims, fxs = layout(FRONT, FRONT_K, 200 * S, 1336 * S)
    # front items sit in the gaps between the back bottles so no label is hidden
    gaps = [(bxs[i] + bxs[i + 1]) / 2 for i in range(5)]
    fxs = gaps
    canvas = darken(canvas, shadow_layer(bims, bxs, BACK_Y))
    reflection(canvas, bims, bxs, BACK_Y)
    place(canvas, bims, bxs, BACK_Y)
    canvas = darken(canvas, shadow_layer(fims, fxs, FRONT_Y))
    reflection(canvas, fims, fxs, FRONT_Y)
    place(canvas, fims, fxs, FRONT_Y)
    rgb = np.asarray(canvas.convert("RGB")).astype(np.float32)
    rgb = bloom(rgb, threshold=236, radius=30 * S, amount=0.22)
    if with_text:
        img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
        gold, ink = (176, 122, 58), (92, 58, 34)
        text(img, "PalmCare", ImageFont.truetype(F + "Cormorant-SemiBold.ttf", 132 * S), gold, 205 * S, 3 * S, glow=(255, 246, 228))
        text(img, "THE  GLOW  COLLECTION", ImageFont.truetype(F + "Jost-Medium.ttf", 30 * S), ink, 300 * S, 9 * S, glow=(255, 246, 228))
        # footer on the floor
        text(img, "Introducing  Advanced Tropical Glow  &  Dermalight", ImageFont.truetype(F + "Cormorant-Italic.ttf", 50 * S), ink, 1700 * S, 0, glow=(255, 246, 232))
        text(img, "Shop A67, Kogi Plaza, BBA Market, Trade Fair Complex, Lagos", ImageFont.truetype(F + "Jost-Regular.ttf", 26 * S), ink, 1880 * S, 1 * S, glow=(255, 246, 232))
        text(img, "0809 361 2901   |   0903 055 5424", ImageFont.truetype(F + "Jost-Medium.ttf", 32 * S), ink, 1930 * S, 2 * S, glow=(255, 246, 232))
        rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(out)


if __name__ == "__main__":
    main(sys.argv[1], "notext" not in sys.argv)
