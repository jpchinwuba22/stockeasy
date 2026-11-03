"""PalmCare Video 3 product sequence ("Shadow & Light"): real bottle cutouts as big-brand pack shots.
Seamless burnt-orange studio, floor reflections, animated palm-frond gobo shadows, light sweeps,
slow push-ins, a label macro and a duo reveal on a plinth. Usage: hero3.py SHOT OUT.mp4|OUT.jpg"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

FPS = 24
OW, OH = 1080, 1920
RNG = np.random.default_rng(23)

vitac = Image.open("vitac_cut.png").convert("RGBA")
glow = Image.open("glowshield_cut.png").convert("RGBA")
vitac = vitac.crop(vitac.split()[-1].getbbox())
glow = glow.crop(glow.split()[-1].getbbox())


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * t * (t * (6 * t - 15) + 10)


def lerp(a, b, t):
    return a + (b - a) * t


def screen(base, glow_arr):
    return 255 - (255 - base) * (255 - glow_arr) / 255


def grade(img, warm=(1.04, 0.97, 0.88), key_from_right=True):
    a = np.asarray(img).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3:]
    h, w = rgb.shape[:2]
    rgb = rgb * np.array(warm, np.float32)
    ramp = np.linspace(0.80, 1.10, w, dtype=np.float32) if key_from_right else np.linspace(1.10, 0.80, w, dtype=np.float32)
    rgb = rgb * ramp[None, :, None]
    ao = np.ones(h, np.float32)
    k = max(1, int(h * 0.06))
    ao[-k:] = np.linspace(1.0, 0.78, k)
    rgb = rgb * ao[:, None, None] + (1 - ao[:, None, None]) * np.array([120, 55, 25], np.float32) * 0.6
    alpha = img.split()[-1]
    edge = np.asarray(ImageChops.subtract(alpha, alpha.filter(ImageFilter.MinFilter(9)))).astype(np.float32) / 255
    edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
    side = (np.linspace(0, 1, w, dtype=np.float32) if key_from_right else np.linspace(1, 0, w, dtype=np.float32))[None, :] ** 2
    rgb = screen(rgb, (edge * side)[..., None] * np.array([255, 205, 150], np.float32) * 0.7)
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al]).astype(np.uint8), "RGBA")


def frond(size=2600, seed=0):
    """A palm-frond silhouette (white on black) used as a moving shadow gobo."""
    r = np.random.default_rng(seed)
    im = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(im)
    pts = [(size * 0.08 + size * 0.84 * s, size * 0.5 + math.sin(s * 2.4) * size * 0.06) for s in np.linspace(0, 1, 60)]
    d.line(pts, fill=255, width=int(size * 0.008))
    for k in range(4, 58, 2):
        x, y = pts[k]
        nx, ny = pts[k + 1][0] - x, pts[k + 1][1] - y
        ang = math.atan2(ny, nx)
        length = size * (0.22 - 0.16 * (k / 60)) * r.uniform(0.85, 1.1)
        for side in (-1, 1):
            a = ang + side * math.radians(55 - 20 * (k / 60)) + r.uniform(-0.08, 0.08)
            tip = (x + math.cos(a) * length, y + math.sin(a) * length)
            perp = (-math.sin(a) * size * 0.012, math.cos(a) * size * 0.012)
            mid = (x + math.cos(a) * length * 0.45, y + math.sin(a) * length * 0.45)
            d.polygon([(x, y), (mid[0] + perp[0], mid[1] + perp[1]), tip, (mid[0] - perp[0], mid[1] - perp[1])], fill=255)
    return im


GOBO = frond(seed=4)


def gobo_mask(angle, cx, cy, scale, blur):
    g = GOBO.rotate(angle, Image.BICUBIC)
    s = scale * OH / g.height
    g = g.resize((round(g.width * s), round(g.height * s)), Image.BILINEAR)
    canvas = Image.new("L", (OW, OH), 0)
    canvas.paste(g, (round(cx - g.width / 2), round(cy - g.height / 2)))
    return np.asarray(canvas.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255


def studio_bg(glow_x=0.62, glow_y=0.42):
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    d = np.sqrt(((xx - OW * glow_x) / OW) ** 2 + ((yy - OH * glow_y) / OH * 0.75) ** 2)
    t = np.clip(d / 0.75, 0, 1)[..., None]
    inner, outer = np.array([244, 146, 76], np.float32), np.array([138, 62, 26], np.float32)
    bg = inner * (1 - t) + outer * t
    floor = (yy > OH * 0.74)[..., None]
    bg = np.where(floor, bg * 0.82, bg)
    horizon = np.exp(-((yy - OH * 0.74) / 22) ** 2)[..., None]
    return bg + horizon * 18


class Dust:
    def __init__(self, n):
        self.p = np.column_stack([RNG.uniform(0, OW, n), RNG.uniform(0, OH, n)])
        self.r = RNG.uniform(1.5, 4.0, n)
        self.v = np.column_stack([RNG.uniform(-6, 6, n), RNG.uniform(-20, -8, n)])
        self.ph = RNG.uniform(0, 6.28, n)

    def draw(self, arr, t):
        layer = Image.new("L", (OW // 2, OH // 2), 0)
        d = ImageDraw.Draw(layer)
        for (px, py), r, (vx, vy), ph in zip(self.p, self.r, self.v, self.ph):
            x, y = ((px + vx * t) % OW) / 2, ((py + vy * t) % OH) / 2
            a = int(200 * (0.3 + 0.7 * max(0.0, math.sin(ph + t * 3))))
            d.ellipse((x - r / 2, y - r / 2, x + r / 2, y + r / 2), fill=a)
        g = np.asarray(layer.filter(ImageFilter.GaussianBlur(1.4)).resize((OW, OH), Image.BILINEAR)).astype(np.float32) / 255
        return screen(arr, g[..., None] * np.array([255, 220, 170], np.float32) * 0.7)


def finish(arr):
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    vig = 1 - 0.12 * (((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH / 2) / (OH / 2)) ** 2) ** 1.2
    arr = arr * np.clip(vig, 0.72, 1)[..., None] + RNG.normal(0, 2.4, (OH, OW))[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


def sweep(mask, pos, width=150.0, angle=0.45, strength=0.32):
    u = np.arange(OW, dtype=np.float32)[None, :]
    v = np.arange(OH, dtype=np.float32)[:, None]
    return np.exp(-(((u + v * angle) - pos) / width) ** 2) * mask * strength


def pack_shot(bottle, dur, h_from, h_to, drift, gobo_from, gobo_to, key_from_right, glow_x):
    """Single product, low hero angle on the seamless with a floor reflection."""
    g = grade(bottle, key_from_right=key_from_right).filter(ImageFilter.UnsharpMask(2, 60, 2))
    bg = studio_bg(glow_x=glow_x)
    dust = Dust(40)
    n = round(dur * FPS)
    for i in range(n):
        t = i / (n - 1)
        e = ease_out(t)
        H = lerp(h_from, h_to, e)
        b = g.resize((round(g.width * H / g.height), round(H)), Image.LANCZOS)
        floor_y = OH * 0.80
        x0 = round(OW / 2 - b.width / 2 + lerp(-drift, drift, e))
        y0 = round(floor_y - b.height)
        frame = Image.fromarray(bg.astype(np.uint8)).convert("RGBA")
        # contact shadow and soft floor shadow toward the left (key from the right)
        sh = Image.new("L", (b.width + 400, 160), 0)
        ImageDraw.Draw(sh).ellipse((150, 50, b.width + 250, 110), fill=200)
        sh = sh.filter(ImageFilter.GaussianBlur(28))
        shadow = Image.new("RGBA", sh.size, (40, 14, 4, 0))
        shadow.putalpha(sh)
        frame.alpha_composite(shadow, (x0 - 260 if key_from_right else x0 - 140, round(floor_y - 85)))
        # reflection
        ref = b.transpose(Image.FLIP_TOP_BOTTOM)
        fade = np.linspace(0.32, 0.0, ref.height, dtype=np.float32) ** 1.4
        ra = (np.asarray(ref.split()[-1]).astype(np.float32) * fade[:, None]).astype(np.uint8)
        ref.putalpha(Image.fromarray(ra))
        frame.alpha_composite(ref.filter(ImageFilter.GaussianBlur(3)), (x0, round(floor_y)))
        frame.alpha_composite(b, (x0, y0))
        arr = np.asarray(frame.convert("RGB")).astype(np.float32)
        mask = np.zeros((OH, OW), np.float32)
        mask[y0:y0 + b.height, x0:x0 + b.width] = np.asarray(b.split()[-1]).astype(np.float32)[: OH - y0, : OW - x0] / 255
        # moving palm shadow over everything above the floor
        gm = gobo_mask(lerp(gobo_from[0], gobo_to[0], e), lerp(gobo_from[1], gobo_to[1], e), lerp(gobo_from[2], gobo_to[2], e), 1.15, 9)
        gm[int(OH * 0.80):, :] *= 0.35
        arr = arr * (1 - 0.42 * gm[..., None])
        arr = screen(arr, sweep(mask, lerp(-600, OW + 1700, t) if key_from_right else lerp(OW + 1700, -600, t))[..., None] * 255)
        arr = dust.draw(arr, i / FPS)
        ts = i / FPS
        if ts < 0.4:
            arr = np.asarray(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur((1 - ts / 0.4) * 12))).astype(np.float32)
        yield finish(arr)


def label_macro(bottle, dur, Hb, y_from, y_to, rot_from, rot_to):
    big = grade(bottle).resize((round(bottle.width * Hb / bottle.height), Hb), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 70, 2))
    bg = Image.fromarray(studio_bg(0.3, 0.3).astype(np.uint8)).filter(ImageFilter.GaussianBlur(20))
    n = round(dur * FPS)
    for i in range(n):
        t = i / (n - 1)
        e = ease(t)
        b = big.rotate(lerp(rot_from, rot_to, e), Image.BICUBIC, expand=True)
        x, y = (OW - b.width) / 2, lerp(y_from, y_to, e)
        box = (round(-x), round(-y), round(-x) + OW, round(-y) + OH)
        frame = bg.convert("RGBA")
        frame.alpha_composite(b.crop(box))
        arr = np.asarray(frame.convert("RGB")).astype(np.float32)
        m = np.asarray(b.split()[-1].crop(box)).astype(np.float32) / 255
        gm = gobo_mask(lerp(-18, -10, e), lerp(300, 820, e), lerp(700, 1100, e), 1.6, 12)
        arr = arr * (1 - 0.38 * gm[..., None])
        arr = screen(arr, sweep(m, lerp(OW + 1500, -500, t), 170, 0.5, 0.3)[..., None] * 255)
        yield finish(arr)


def duo(dur):
    plate = Image.open("studio_set.png").convert("RGB").resize((1152, 2048), Image.LANCZOS)
    PL_CX, PL_TOP = 576, 1310
    world = plate.convert("RGBA")
    mask_w = Image.new("L", world.size, 0)
    vb = grade(vitac).resize((round(vitac.width * 730 / vitac.height), 730), Image.LANCZOS)
    gb = grade(glow).resize((round(glow.width * 690 / glow.height), 690), Image.LANCZOS)
    for im, cx, by in [(vb, PL_CX - 150, PL_TOP + 4), (gb, PL_CX + 155, PL_TOP + 30)]:
        x0 = round(cx - im.width / 2)
        cs = Image.new("L", (im.width + 80, 70), 0)
        ImageDraw.Draw(cs).ellipse((20, 22, im.width + 60, 46), fill=230)
        c = Image.new("RGBA", cs.size, (40, 14, 4, 0))
        c.putalpha(cs.filter(ImageFilter.GaussianBlur(8)))
        world.alpha_composite(c, (x0 - 40, by - 40))
        world.alpha_composite(im, (x0, by - im.height))
        mask_w.paste(im.split()[-1], (x0, by - im.height), im.split()[-1])
    world_rgb = world.convert("RGB")
    dust = Dust(50)
    n = round(dur * FPS)
    for i in range(n):
        t = i / (n - 1)
        e = ease(t)
        e = ease_out(t)
        Hh = lerp(2000, 1460, e)
        cx, cy = lerp(560, PL_CX + 10, e), lerp(1000, PL_TOP - 0.2 * Hh, e)
        Wd = Hh * OW / OH
        box = (cx - Wd / 2, cy - Hh / 2, cx + Wd / 2, cy + Hh / 2)
        arr = np.asarray(world_rgb.transform((OW, OH), Image.EXTENT, box, Image.BICUBIC)).astype(np.float32)
        m = np.asarray(mask_w.transform((OW, OH), Image.EXTENT, box, Image.BILINEAR)).astype(np.float32) / 255
        gm = gobo_mask(lerp(-30, -14, e), lerp(820, 380, e), lerp(520, 760, e), 1.25, 10)
        arr = arr * (1 - 0.40 * gm[..., None])
        arr = screen(arr, sweep(m, lerp(-500, OW + 1600, ease(min(1, max(0, (t - 0.3) / 0.7)))), 160, 0.45, 0.34)[..., None] * 255)
        arr = dust.draw(arr, i / FPS)
        yield finish(arr)


SHOTS = {
    "vitac": lambda: pack_shot(vitac, 2.6, 1080, 1420, 40, (-24, 1250, 300), (-12, 380, 520), True, 0.62),
    "glow": lambda: pack_shot(glow, 2.4, 980, 1300, -40, (16, -100, 340), (8, 700, 520), False, 0.40),
    "macro": lambda: label_macro(glow, 1.4, 3000, -1750, -1000, -3.0, -0.4),
    "duo": lambda: duo(3.2),
}

if __name__ == "__main__":
    name, out = sys.argv[1], sys.argv[2]
    gen = SHOTS[name]()
    if out.endswith(".jpg"):
        frames = list(gen)
        pick = [frames[0], frames[len(frames) // 2], frames[-1]]
        sheet = Image.new("RGB", (360 * 3, 640))
        for k, f in enumerate(pick):
            sheet.paste(Image.fromarray(f).resize((360, 640)), (360 * k, 0))
        sheet.save(out)
    else:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in gen:
            p.stdin.write(f.tobytes())
        p.stdin.close()
        p.wait()
