"""PalmCare Video 2 product hero (Citrus Ritual): real bottle cutouts on a native 9:16 AI set.
Rack-focus label macros through foreground citrus bokeh, then a crane-down push-in reveal
with parallax bokeh, hard-sun shadows, light sweeps, gold shimmer and grain."""
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

FPS = 24
OW, OH = 1080, 1920
RNG = np.random.default_rng(11)

plate = Image.open("citrus_set.png").convert("RGB")  # 1152x2048
wash = Image.open("citrus_cut.png").convert("RGBA")
lotion = Image.open("molecular_cut.png").convert("RGBA")
wash = wash.crop(wash.split()[-1].getbbox())
lotion = lotion.crop(lotion.split()[-1].getbbox())


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * t * (t * (6 * t - 15) + 10)


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def grade_bottle(img, warm=(1.05, 0.975, 0.90)):
    """Warm the white plastic to the peach set, hard key from the left, rim light, base occlusion."""
    a = np.asarray(img).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3:]
    rgb = rgb * np.array(warm, np.float32)
    h, w = rgb.shape[:2]
    rgb = rgb * np.linspace(1.10, 0.82, w, dtype=np.float32)[None, :, None]
    ao = np.ones(h, np.float32)
    k = max(1, int(h * 0.06))
    ao[-k:] = np.linspace(1.0, 0.80, k)
    rgb = rgb * ao[:, None, None] + (1 - ao[:, None, None]) * np.array([150, 80, 45], np.float32) * 0.6
    al = img.split()[-1]
    edge = np.asarray(ImageChops.subtract(al, al.filter(ImageFilter.MinFilter(9)))).astype(np.float32) / 255.0
    edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255.0
    side = np.linspace(1.0, 0.0, w, dtype=np.float32)[None, :] ** 2
    rim = (edge * side)[..., None] * np.array([255, 214, 160], np.float32) * 0.6
    rgb = 255 - (255 - rgb) * (255 - rim) / 255
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8), "RGBA")


def screen(base, glow):
    return 255 - (255 - base) * (255 - glow) / 255


def sweep(mask, xw, yw, pos, width=200.0, angle=0.4, strength=0.30):
    d = (xw + yw * angle) - pos
    return np.exp(-(d / width) ** 2) * mask * strength


class Shimmer:
    """Tiny gold sparkles drifting in the sunbeam."""

    def __init__(self, n):
        self.p = np.column_stack([RNG.uniform(0, OW, n), RNG.uniform(0, OH, n)])
        self.r = RNG.uniform(1.5, 4.5, n)
        self.ph = RNG.uniform(0, 6.28, n)
        self.v = np.column_stack([RNG.uniform(-8, 8, n), RNG.uniform(-26, -10, n)])

    def draw(self, arr, t, sx, sy, par):
        layer = Image.new("L", (OW // 2, OH // 2), 0)
        d = ImageDraw.Draw(layer)
        for (px, py), r, ph, (vx, vy) in zip(self.p, self.r, self.ph, self.v):
            x = ((px + vx * t - sx * par) % OW) / 2
            y = ((py + vy * t - sy * par) % OH) / 2
            a = int(255 * (0.35 + 0.65 * max(0.0, np.sin(ph + t * 5.0))))
            d.ellipse((x - r / 2, y - r / 2, x + r / 2, y + r / 2), fill=a)
        g = np.asarray(layer.filter(ImageFilter.GaussianBlur(1.6)).resize((OW, OH), Image.BILINEAR)).astype(np.float32) / 255
        return screen(arr, g[..., None] * np.array([255, 214, 140], np.float32) * 0.9)


class Bokeh:
    """Large out-of-focus citrus discs close to the lens, moving faster than the set (parallax)."""

    def __init__(self, n, seed):
        r = np.random.default_rng(seed)
        self.items = [(r.uniform(-200, OW + 200), r.uniform(0, OH), r.uniform(90, 190),
                       [(255, 150, 60), (255, 120, 110), (255, 190, 90)][k % 3], r.uniform(0.25, 0.45)) for k in range(n)]

    def draw(self, arr, sx, sy, par, blur=28):
        layer = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for x, y, rad, col, a in self.items:
            cx, cy = x - sx * par, y - sy * par
            d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=col + (int(255 * a),))
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        la = np.asarray(layer).astype(np.float32)
        al = la[..., 3:] / 255
        return arr * (1 - al) + la[..., :3] * al


def finish(arr):
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vig = 1 - 0.14 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) ** 1.3
    arr = arr * np.clip(vig, 0.7, 1)[..., None]
    arr = arr + RNG.normal(0, 2.2, arr.shape[:2])[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


# ---------- world: plate at native res with the bottles seated on the plinth ----------
world = plate.filter(ImageFilter.GaussianBlur(0.8))
WW, WH = world.size
PL_CX, PL_TOP = 573, 1330


def place(img, height):
    s = height / img.height
    return grade_bottle(img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS))


wash_w, lot_w = place(wash, 820), place(lotion, 640)
placements = [(wash_w, PL_CX - 130, PL_TOP - 8), (lot_w, PL_CX + 150, PL_TOP + 34)]
world_rgba = world.convert("RGBA")
mask_world = Image.new("L", world.size, 0)
for img, cx, by in placements:
    x0 = round(cx - img.width / 2)
    al = img.split()[-1]
    # hard midday sun from upper left: crisp shadow thrown right across the plinth top
    sh_h = max(1, round(img.height * 0.12))
    sh = al.resize((img.width, sh_h)).transform((img.width + 320, sh_h), Image.AFFINE, (1, -2.2, 0, 0, 1, 0)).filter(ImageFilter.GaussianBlur(5))
    shadow = Image.new("RGBA", sh.size, (120, 60, 35, 0))
    shadow.putalpha(sh.point(lambda v: int(v * 0.42)))
    world_rgba.alpha_composite(shadow, (x0 + 6, by - sh_h + 4))
    cs = Image.new("L", (img.width + 60, 60), 0)
    cs.paste(255, (24, 24, img.width + 40, 36))
    cs = cs.filter(ImageFilter.GaussianBlur(6))
    cshadow = Image.new("RGBA", cs.size, (70, 32, 18, 0))
    cshadow.putalpha(cs.point(lambda v: int(v * 0.8)))
    world_rgba.alpha_composite(cshadow, (x0 - 24, by - 34))
for img, cx, by in placements:
    x0, y0 = round(cx - img.width / 2), round(by - img.height)
    world_rgba.alpha_composite(img, (x0, y0))
    mask_world.paste(img.split()[-1], (x0, y0), img.split()[-1])
world_rgb = world_rgba.convert("RGB")


def window(cx, cy, H):
    Wd = H * OW / OH
    box = (cx - Wd / 2, cy - H / 2, cx + Wd / 2, cy + H / 2)
    rgb = np.asarray(world_rgb.transform((OW, OH), Image.EXTENT, box, Image.BICUBIC)).astype(np.float32)
    m = np.asarray(mask_world.transform((OW, OH), Image.EXTENT, box, Image.BILINEAR)).astype(np.float32) / 255
    u = np.linspace(box[0], box[2], OW, dtype=np.float32)[None, :]
    v = np.linspace(box[1], box[3], OH, dtype=np.float32)[:, None]
    return rgb, m, u, v


def shot_reveal(dur):
    """Crane down off the palm shadows and push in onto the duo on the plinth."""
    sh, bk = Shimmer(70), Bokeh(5, 3)
    n = round(dur * FPS)
    for i in range(n):
        t = i / (n - 1)
        e = ease(t)
        H = lerp(1480, 1380, ease_out(t))
        cy = lerp(H / 2 + 10, PL_TOP + 0.5 * H - 0.70 * H, e)
        cx = lerp(PL_CX - 40, PL_CX + 10, e)
        rgb, m, u, v = window(cx, cy, H)
        pos = lerp(150, 1500, ease(min(1, max(0, (t - 0.45) / 0.55))))
        rgb = screen(rgb, sweep(m, u, v, pos, 170, 0.45, 0.38)[..., None] * 255)
        rgb = sh.draw(rgb, i / FPS, cx, cy, 1.0)
        rgb = bk.draw(rgb, cx - PL_CX, cy - 1000, 1.9)
        yield finish(rgb)


def shot_macro(bottle, dur, Hb, y_from, y_to, x_off, rot_from, rot_to, sweep_dir, bg_box, seed):
    """Tight label move; a soft citrus disc crosses the lens first (rack-focus feel)."""
    big = grade_bottle(bottle.resize((round(bottle.width * Hb / bottle.height), Hb), Image.LANCZOS)).filter(ImageFilter.UnsharpMask(2, 70, 2))
    bg = plate.crop(bg_box).resize((OW + 200, OH + 200), Image.BICUBIC).filter(ImageFilter.GaussianBlur(24))
    sh, bk = Shimmer(40), Bokeh(3, seed)
    n = round(dur * FPS)
    for i in range(n):
        t = i / (n - 1)
        e = ease(t)
        ox = round(100 + 70 * (e - 0.5))
        canvas = bg.crop((ox, 100, ox + OW, 100 + OH)).convert("RGBA")
        b = big.rotate(lerp(rot_from, rot_to, e), Image.BICUBIC, expand=True)
        x, y = (OW - b.width) / 2 + x_off, lerp(y_from, y_to, e)
        box = (round(-x), round(-y), round(-x) + OW, round(-y) + OH)
        canvas.alpha_composite(b.crop(box))
        rgb = np.asarray(canvas.convert("RGB")).astype(np.float32)
        m = np.asarray(b.split()[-1].crop(box)).astype(np.float32) / 255
        u = np.arange(OW, dtype=np.float32)[None, :]
        v = np.arange(OH, dtype=np.float32)[:, None]
        pos = lerp(-500, OW + 1500, t) if sweep_dir > 0 else lerp(OW + 1500, -500, t)
        rgb = screen(rgb, sweep(m, u, v, pos, 160, 0.5, 0.30)[..., None] * 255)
        rgb = sh.draw(rgb, i / FPS, 0, y, 0.2)
        # foreground citrus disc slides off the lens over the first 40% of the shot
        rgb = bk.draw(rgb, lerp(-900, 900, ease(min(1, t / 0.45))) * sweep_dir, 0, 1.0, blur=34)
        yield finish(rgb)


def shots():
    yield from shot_macro(wash, 1.9, 2500, -240, -720, 160, 2.6, 1.0, +1, (650, 300, 1150, 1189), 5)
    yield from shot_macro(lotion, 1.9, 2600, -980, -470, -160, -2.4, -0.8, -1, (0, 300, 500, 1189), 9)
    yield from shot_reveal(3.6)


if __name__ == "__main__":
    out = sys.argv[1]
    if out.endswith(".jpg"):
        idx = sorted(int(x) for x in sys.argv[2].split(","))
        frames = []
        for k, f in enumerate(shots()):
            if k in idx:
                Image.fromarray(f).save(f"t2_{k}.jpg", quality=92)
                frames.append(Image.fromarray(f).resize((270, 480)))
            if k >= idx[-1]:
                break
        sheet = Image.new("RGB", (270 * len(frames), 480))
        for k, f in enumerate(frames):
            sheet.paste(f, (270 * k, 0))
        sheet.save(out)
    else:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for f in shots():
            p.stdin.write(f.tobytes())
        p.stdin.close()
        p.wait()
