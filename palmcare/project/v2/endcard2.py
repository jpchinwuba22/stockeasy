"""Video 2 end card: blurred hero still under a cream veil, real bottles, brand type and contact details."""
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
F = "../fonts/"
bg = Image.open(sys.argv[1]).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(38))
veil = Image.new("RGB", (W, H), (251, 239, 227))
card = Image.blend(bg, veil, 0.72).convert("RGBA")

# real bottles, small, centred
bot = []
for name, h in [("citrus_cut.png", 470), ("molecular_cut.png", 370)]:
    im = Image.open(name).convert("RGBA")
    im = im.crop(im.split()[-1].getbbox())
    bot.append(im.resize((round(im.width * h / im.height), h), Image.LANCZOS))
base = 820
x = W // 2 - (bot[0].width + bot[1].width + 30) // 2
for im in bot:
    sh = Image.new("RGBA", (im.width + 80, 50), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((10, 10, im.width + 70, 40), fill=(120, 60, 30, 110))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x - 40, base - 28))
    card.alpha_composite(im, (x, base - im.height))
    x += im.width + 30

d = ImageDraw.Draw(card)
ORANGE, DARK, MID = (196, 96, 29), (58, 36, 24), (110, 80, 62)


def centre(text, y, font, fill):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)


centre("PalmCare", 900, ImageFont.truetype(F + "Playfair-Medium.ttf", 128), ORANGE)
centre("T H E   R I T U A L   A F T E R", 1060, ImageFont.truetype(F + "Montserrat-Medium.ttf", 30), DARK)
centre("Citrus Vitamin Glow Body Wash  +  Molecular Glow Body Lotion", 1120, ImageFont.truetype(F + "Montserrat-Regular.ttf", 27), MID)
d.line((W * 0.32, 1200, W * 0.68, 1200), fill=ORANGE + (170,), width=3)
f = ImageFont.truetype(F + "Montserrat-Regular.ttf", 36)
centre("Shop A67, Kogi Plaza, BBA Market", 1250, f, DARK)
centre("Trade Fair Complex, Lagos", 1300, f, DARK)
centre("0809 361 2901   |   0903 055 5424", 1385, ImageFont.truetype(F + "Montserrat-Medium.ttf", 46), ORANGE)
card.convert("RGB").save(sys.argv[2], quality=95)
