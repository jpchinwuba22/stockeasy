"""Video 2 cover (distinct from Video 1's cream/serif cover): sunlit pool still of the Citrus bottle on the left half,
bold Unbounded type in orange colour blocks, the two real product cutouts, and an orange 'NEW' seal.
Usage: cover_v2.py BG_FRAME.png OUT.jpg"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

F = "../fonts/"
W, H = 1080, 1920
ORANGE, INK, WHITE = (255, 122, 26), (16, 38, 41), (255, 255, 255)
# warm sun-to-sand gradient with a soft sun disc behind the products and faint water caustics from the clip
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
top, mid, bot = np.array([255, 150, 60.0]), np.array([255, 205, 150.0]), np.array([250, 236, 214.0])
t = yy / H
a = np.where(t[..., None] < 0.55, top + (mid - top) * (t[..., None] / 0.55), mid + (bot - mid) * ((t[..., None] - 0.55) / 0.45))
sun = np.exp(-(((xx - 700) / 420) ** 2 + ((yy - 980) / 420) ** 2))[..., None]
a = a + sun * np.array([255, 245, 225]) * 0.55
water = np.asarray(Image.open(sys.argv[1]).convert("L").resize((W, H)).filter(ImageFilter.GaussianBlur(2))).astype(np.float32)
caus = (water - water.mean()) / (water.std() + 1e-6)
a = a + np.clip(caus, 0, 3)[..., None] * 6 * (t[..., None] > 0.45)
img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
d = ImageDraw.Draw(img)


def block(text, size, y, fill, tcol, x=64):
    f = ImageFont.truetype(F + "Unbounded-ExtraBold.ttf", size)
    asc, desc = f.getmetrics()
    w = f.getlength(text)
    d.rectangle((x, y, x + w + 56, y + asc + desc - 4), fill=fill)
    d.text((x + 28, y - desc * 0.15), text, font=f, fill=tcol)
    return y + asc + desc + 10


y = 150
y = block("CITRUS", 128, y, ORANGE, WHITE)
y = block("GLOW", 128, y, INK, ORANGE)
y = block("+ MOLECULAR", 74, y + 8, WHITE, INK)
f = ImageFont.truetype(F + "Bricolage-Bold.ttf", 40)
d.text((70, y + 24), "PalmCare  ·  Body Wash + Body Lotion", font=f, fill=INK)

# products
for path, h, cx in (("../straight/out/citrus.png", 980, 360), ("../straight/out/molecular.png", 760, 760)):
    p = Image.open(path).convert("RGBA")
    p = p.resize((round(p.width * h / p.height), h), Image.LANCZOS)
    pad = 80
    al = Image.new("L", (p.width + 2 * pad, p.height + 2 * pad), 0)
    al.paste(p.split()[-1], (pad, pad))
    sh = Image.new("RGBA", al.size, (60, 30, 10, 0))
    sh.putalpha(al.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.45)))
    base = 1820
    img.alpha_composite(sh, (int(cx - p.width / 2 + 22 - pad), int(base - h + 26 - pad)))
    img.alpha_composite(p, (int(cx - p.width / 2), int(base - h)))

# seal
R = 120
seal = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
sd = ImageDraw.Draw(seal)
sd.ellipse((0, 0, 2 * R - 1, 2 * R - 1), fill=ORANGE)
sd.ellipse((10, 10, 2 * R - 11, 2 * R - 11), outline=WHITE, width=3)
t1 = ImageFont.truetype(F + "Unbounded-ExtraBold.ttf", 54)
t2 = ImageFont.truetype(F + "Bricolage-Bold.ttf", 21)
sd.text((R, R - 18), "NEW", font=t1, fill=WHITE, anchor="mm")
sd.text((R, R + 34), "BODY CARE DUO", font=t2, fill=WHITE, anchor="mm")
seal = seal.rotate(-12, resample=Image.BICUBIC, expand=True)
img.alpha_composite(seal, (W - seal.width - 40, 760))
img.convert("RGB").save(sys.argv[2], quality=94)
