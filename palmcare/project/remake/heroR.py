"""PalmCare Videos 1-3 (remake) product reveals: the real product cutouts on a premium set per video, with a living
set (steam / water shimmer and caustics / swaying palm shadows), a light burst on the unveil, a light sweep across
the label, an anamorphic flare, a glint, golden dust and a motion-blurred camera move.
The video is chosen with the PCV environment variable (1, 2 or 3).  Usage: heroR.py SHOT OUT.mp4|OUT.jpg  (SHOT a|b)"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "../v3")
_cwd = os.getcwd()
os.chdir("../v3")  # hero3 loads its own cutouts relative to its folder
from hero3 import FPS, OH, OW, ease, ease_out, lerp, screen  # noqa: E402
from prodfx import bloom, premium  # noqa: E402
os.chdir(_cwd)

V = int(os.environ.get("PCV", "1"))
# plate, plinth top (x, y, rx, ry), shadow colour, product tint, set effects, products (cutout, hero h, duo dx, duo dy, duo h)
CFG = {
    1: dict(plate="set1.png", pod=(578, 1403, 370, 46), shade=(78, 52, 32), tint=(1.0, 0.97, 0.925),
            fx={"steam"}, rays=(1250, -250, -38), ray_col=(255, 232, 196),
            prods=[("../hero/milky_cut.png", 800, -135, 2, 630), ("../hero/cacao_cut.png", 780, 150, 14, 545)]),
    2: dict(plate="set2.png", pod=(583, 1192, 440, 60), shade=(120, 78, 46), tint=(1.0, 0.975, 0.945),
            fx={"water", "caustics"}, rays=(1350, -250, -35), ray_col=(255, 226, 176),
            prods=[("../v2/citrus_cut.png", 800, -160, 4, 730), ("../v2/molecular_cut.png", 780, 175, 16, 650)]),
    3: dict(plate="set3.png", pod=(588, 1453, 470, 46), shade=(104, 50, 16), tint=(1.0, 0.955, 0.895),
            fx={"sway"}, rays=(1350, -300, -32), ray_col=(255, 214, 150),
            prods=[("../v3/vitac_fix.png", 760, -150, 4, 600), ("../v3/glowshield_cut.png", 700, 160, 14, 520)]),
}[V]

RNG = np.random.default_rng(6 + V)
PLATE = np.asarray(Image.open(CFG["plate"]).convert("RGB")).astype(np.float32)
PH, PW = PLATE.shape[:2]
POD_X, POD_Y, POD_RX, POD_RY = CFG["pod"]


def tint(img, k):
    a = np.asarray(img).astype(np.float32)
    a[..., :3] *= np.array(k, np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def load(path):
    im = Image.open(path).convert("RGBA")
    return tint(premium(im.crop(im.split()[-1].getbbox()), spec_pos=0.30, from_right=True), CFG["tint"])


IMGS = [load(p[0]) for p in CFG["prods"]]


class Product:
    def __init__(self, img, cx, base_y, h):
        self.k = h / img.height
        self.x0, self.y0 = cx - img.width * self.k / 2, base_y - h
        self.w, self.h, self.cx, self.base = img.width * self.k, h, cx, base_y
        al = np.asarray(img.split()[-1])[-max(4, img.height // 25):] > 128
        cols = np.where(al.any(axis=0))[0]
        self.bw = (cols.max() - cols.min()) * self.k
        self.img = img
        half = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
        self.levels = [(img.convert("RGBa"), 1.0), (half.convert("RGBa"), 0.5)]


YYp, XXp = np.mgrid[0:PH, 0:PW].astype(np.float32)
FX = CFG["fx"]
if "water" in FX:   # V2: the shallow pool in front of and around the plinth
    _wm = Image.new("L", (PW, PH), 0)
    _d = ImageDraw.Draw(_wm)
    _d.rectangle((0, 1395, PW, PH), fill=255)
    _d.rectangle((POD_X - POD_RX - 8, 0, POD_X + POD_RX + 8, 1478), fill=0)
    DISP = np.asarray(_wm.filter(ImageFilter.GaussianBlur(20))).astype(np.float32) / 255
    WALL = np.clip((1130 - YYp) / 160, 0, 1)
elif "sway" in FX:  # V3: palm shadows on the wall sway in the breeze (wall only, never the plinth)
    _wm = Image.new("L", (PW, PH), 0)
    _d = ImageDraw.Draw(_wm)
    _d.rectangle((0, 0, PW, 1380), fill=255)
    _d.ellipse((POD_X - POD_RX - 60, 1330, POD_X + POD_RX + 60, 1700), fill=0)
    DISP = np.asarray(_wm.filter(ImageFilter.GaussianBlur(40))).astype(np.float32) / 255
    WALL = None
else:
    DISP, WALL = None, None
if "steam" in FX:   # V1: a soft rising steam texture, tiled vertically
    _n = RNG.normal(0, 1, (PH // 8, PW // 8)).astype(np.float32)
    _n = np.asarray(Image.fromarray(((_n - _n.min()) / np.ptp(_n) * 255).astype(np.uint8)).resize((PW, PH), Image.BICUBIC)
                    .filter(ImageFilter.GaussianBlur(60))).astype(np.float32) / 255
    STEAM = np.clip((_n - 0.47) * 6, 0, 1)
    STEAM_M = np.clip((1450 - YYp) / 500, 0, 1) * np.clip(YYp / 300, 0, 1)
TOPM = Image.new("L", (PW, PH), 0)
ImageDraw.Draw(TOPM).ellipse((POD_X - POD_RX, POD_Y - POD_RY, POD_X + POD_RX, POD_Y + POD_RY), fill=255)
TOPM = np.asarray(TOPM.filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255


def plate_at(t, products, light=1.0):
    """Animated plate for the video's set; product shadows and reflections on the plinth top."""
    rgb = PLATE
    if DISP is not None:
        if "water" in FX:
            dx = (2.4 * np.sin(YYp * 0.06 + t * 2.0) + 1.5 * np.sin(XXp * 0.028 - t * 1.4)) * DISP
            dy = (1.2 * np.sin(XXp * 0.05 + t * 1.6)) * DISP
        else:
            dx = (3.2 * np.sin(YYp * 0.004 + t * 0.9) + 1.6 * np.sin(XXp * 0.006 - t * 1.3 + YYp * 0.003)) * DISP
            dy = (1.4 * np.sin(XXp * 0.005 + t * 0.7)) * DISP
        x = np.clip(XXp + dx, 0, PW - 1.001)
        y = np.clip(YYp + dy, 0, PH - 1.001)
        x0, y0 = x.astype(np.int32), y.astype(np.int32)
        fx, fy = (x - x0)[..., None], (y - y0)[..., None]
        im = PLATE
        rgb = (im[y0, x0] * (1 - fx) * (1 - fy) + im[y0, x0 + 1] * fx * (1 - fy) + im[y0 + 1, x0] * (1 - fx) * fy + im[y0 + 1, x0 + 1] * fx * fy)
    if "caustics" in FX:
        c = (np.sin(XXp * 0.021 + YYp * 0.008 + t * 1.3) * np.sin(XXp * 0.013 - YYp * 0.017 - t * 1.05)
             + np.sin(XXp * 0.031 - YYp * 0.011 + t * 0.9) * 0.6)
        rgb = screen(rgb, (np.clip(c - 0.75, 0, None) * WALL * 0.24)[..., None] * np.array([255, 240, 214.0]))
    if "steam" in FX:
        sy = (YYp + t * 55) % PH
        st = STEAM[sy.astype(np.int32), ((XXp + 12 * np.sin(YYp * 0.004 + t * 0.6)) % PW).astype(np.int32)]
        rgb = screen(rgb, (st * STEAM_M * 0.16)[..., None] * np.array([255, 246, 236.0]))
    ox, oy, ad = CFG["rays"]
    ang = math.radians(ad + 2.0 * math.sin(t * 0.5))
    u = (XXp - ox) * math.cos(ang) + (YYp - oy) * math.sin(ang)
    rays = (0.5 + 0.5 * np.sin(u * 0.012 + t * 0.35)) ** 6 * np.clip(1 - YYp / 1750, 0, 1) * 0.13
    rgb = screen(rgb, rays[..., None] * np.array(CFG["ray_col"], np.float64))
    rgb = rgb * light
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    for p in products:
        ref = p.img.transpose(Image.FLIP_TOP_BOTTOM).resize((round(p.w), round(p.h)), Image.LANCZOS)
        ra = np.asarray(ref).astype(np.float32)
        ra[..., 3] *= np.linspace(0.2, 0.0, ra.shape[0])[:, None]
        ref = Image.fromarray(ra.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(3))
        lay = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        lay.alpha_composite(ref, (round(p.x0), round(p.base - 4)))
        la = np.asarray(lay).astype(np.float32)
        la[..., 3] *= TOPM
        img.alpha_composite(Image.fromarray(la.astype(np.uint8), "RGBA"))
        sh = Image.new("L", (PW, PH), 0)
        ImageDraw.Draw(sh).ellipse((p.cx - p.bw * 1.25, p.base - p.bw * 0.22 - 4, p.cx + p.bw * 0.35, p.base + 3), fill=105)
        sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(14))).astype(np.float32)
        c2 = Image.new("L", (PW, PH), 0)
        ImageDraw.Draw(c2).ellipse((p.cx - p.bw * 0.52, p.base - p.bw * 0.10 - 4, p.cx + p.bw * 0.52, p.base + 2), fill=245)
        c2 = np.asarray(c2.filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
        a = np.maximum(sh, c2) * TOPM
        s = Image.new("RGBA", (PW, PH), CFG["shade"] + (0,))
        s.putalpha(Image.fromarray(a.astype(np.uint8)))
        img.alpha_composite(s)
    return img.convert("RGB")


def render(plate, products, cam):
    cx, cy, Hh, rot = cam
    s, r = Hh / OH, math.radians(rot)
    a, b, d, e = s * math.cos(r), -s * math.sin(r), s * math.sin(r), s * math.cos(r)
    ox, oy = cx - a * OW / 2 - b * OH / 2, cy - d * OW / 2 - e * OH / 2
    bg = np.asarray(plate.transform((OW, OH), Image.AFFINE, (a, b, ox, d, e, oy), Image.BICUBIC)).astype(np.float32)
    mask = np.zeros((OH, OW), np.float32)
    for p in products:
        img, f = p.levels[1] if s / p.k > 1.7 else p.levels[0]
        pc = tuple(v / p.k * f for v in (a, b, ox - p.x0, d, e, oy - p.y0))
        lay = np.asarray(img.transform((OW, OH), Image.AFFINE, pc, Image.BICUBIC)).astype(np.float32)
        al = lay[..., 3:] / 255
        bg = bg * (1 - al) + lay[..., :3]
        mask = np.maximum(mask, al[..., 0])
    return np.clip(bg, 0, 255), mask


def clamp_cam(cx, cy, Hh, rot):
    Hh = min(Hh, PH / (1 + abs(rot) * 0.01))
    hw, hh = Hh * OW / OH / 2 * (1 + abs(rot) * 0.03), Hh / 2 * (1 + abs(rot) * 0.01)
    return min(max(cx, hw), PW - hw), min(max(cy, hh), PH - hh), Hh, rot


YY, XX = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = 1 - 0.13 * (((XX - OW / 2) / (OW / 2)) ** 2 + ((YY - OH / 2) / (OH / 2)) ** 2)


class Dust:
    """Floating golden dust motes drifting upward in the light."""

    def __init__(self, n=46, seed=11):
        r = np.random.default_rng(seed)
        self.p = np.column_stack([r.uniform(0, OW, n), r.uniform(0, OH, n)])
        self.v = np.column_stack([r.uniform(-10, 10, n), r.uniform(-34, -10, n)])
        self.r = r.uniform(1.5, 4.5, n)
        self.ph = r.uniform(0, 6.28, n)

    def draw(self, arr, t, k=1.0):
        q = Image.new("L", (OW // 2, OH // 2), 0)
        d = ImageDraw.Draw(q)
        for (px, py), (vx, vy), rr, ph in zip(self.p, self.v, self.r, self.ph):
            x, y = ((px + vx * t) % OW) / 2, ((py + vy * t) % OH) / 2
            a = int(255 * (0.25 + 0.75 * max(0.0, math.sin(ph + t * 3))))
            d.ellipse((x - rr / 2, y - rr / 2, x + rr / 2, y + rr / 2), fill=a)
        g = np.asarray(q.filter(ImageFilter.GaussianBlur(1.2)).resize((OW, OH), Image.BILINEAR)).astype(np.float32) / 255
        return screen(arr, g[..., None] * np.array([255, 226, 170.0]) * 0.75 * k)


def flare(arr, x, y, strength):
    """Warm anamorphic streak + glow at (x, y)."""
    if strength <= 0.01:
        return arr
    streak = np.exp(-((YY - y) / 7) ** 2) * np.exp(-np.abs(XX - x) / 420) * strength
    glow = np.exp(-(((XX - x) / 100) ** 2 + ((YY - y) / 100) ** 2)) * strength * 0.8
    return screen(arr, (streak + glow)[..., None] * np.array([255, 222, 170.0]))


def glint(arr, x, y, strength):
    """Four-point star glint (a catch-light popping on the pack)."""
    if strength <= 0.01:
        return arr
    dx, dy = np.abs(XX - x), np.abs(YY - y)
    star = (np.exp(-(dy / 2.5) ** 2) * np.exp(-dx / 90) + np.exp(-(dx / 2.5) ** 2) * np.exp(-dy / 90)
            + np.exp(-((dx ** 2 + dy ** 2) / 18 ** 2)) * 0.9)
    return screen(arr, (star * strength)[..., None] * np.array([255, 246, 228.0]))


ANG = np.arctan2(YY - OH * 0.47, XX - OW / 2)
RAD = np.hypot(YY - OH * 0.47, XX - OW / 2)


def burst(arr, mask, t, strength):
    """Radial light burst behind the product at the moment of the unveil (behind = outside the product mask)."""
    if strength <= 0.01:
        return arr
    rays = (0.5 + 0.5 * np.cos(ANG * 18 + t * 1.6)) ** 10 * 0.8 + (0.5 + 0.5 * np.cos(ANG * 7 - t * 1.1)) ** 6 * 0.5
    fall = np.exp(-RAD / 520) * np.clip(RAD / 160, 0, 1)
    core = np.exp(-(RAD / 380) ** 2) * 0.55
    v = (rays * fall + core) * (1 - mask) * strength
    return screen(arr, v[..., None] * np.array([255, 232, 190.0]))


def sweep(mask, pos, width=110.0, angle=0.35, strength=0.5):
    return np.exp(-(((XX + YY * angle) - pos) / width) ** 2) * mask * strength


def finish(arr, sharpen=False):
    arr = bloom(arr, threshold=226, radius=28, amount=0.26)
    x = np.clip(arr / 255, 0, 1)
    arr = (x + 0.07 * np.sin(np.pi * x) * (x - 0.5) * 2) * 255
    arr = arr * VIG[..., None] + RNG.normal(0, 1.4, (OH, OW))[..., None]
    out = np.clip(arr, 0, 255).astype(np.uint8)
    if sharpen:
        out = np.asarray(Image.fromarray(out).filter(ImageFilter.UnsharpMask(2.0, 70, 2)))
    return out


def run(products, dur, cam, light=lambda t: 1.0, sweeps=(), flare_fn=None, t0=0.0, sharpen=False, dust=1.0,
        burst_fn=None, glint_fn=None):
    n = round(dur * FPS)
    cfn = lambda t: clamp_cam(*cam(t))
    dt = 1 / (n - 1)
    dd = Dust(seed=11 + V)
    for i in range(n):
        t = i / (n - 1)
        plate = plate_at(t0 + i / FPS, products, light(t))
        c0, c1 = cfn(t), cfn(min(1.0, t + dt * 0.5))
        spd = math.hypot(c1[0] - c0[0], c1[1] - c0[1]) * OH / c0[2] + abs(c1[2] - c0[2]) / c0[2] * OH * 0.6 + abs(c1[3] - c0[3]) * 18
        ns = int(min(14, max(1, math.ceil(spd / 2.5))))
        acc, macc = 0, 0
        for k in range(ns):
            rgb, m = render(plate, products, cfn(min(1.0, t + dt * 0.5 * k / max(1, ns - 1))))
            acc, macc = acc + rgb, macc + m
        rgb, m = acc / ns, macc / ns
        if burst_fn:
            rgb = burst(rgb, m, t0 + i / FPS, burst_fn(t))
        for s0, s1, dr in sweeps:
            u = min(1, max(0, (t - s0) / (s1 - s0)))
            if 0 < u < 1:
                pos = lerp(-500, OW + 1100, ease(u)) if dr > 0 else lerp(OW + 1100, -500, ease(u))
                rgb = screen(rgb, sweep(m, pos)[..., None] * 255)
        if flare_fn:
            rgb = flare(rgb, *flare_fn(t))
        if glint_fn:
            rgb = glint(rgb, *glint_fn(t))
        rgb = dd.draw(rgb, t0 + i / FPS, dust)
        yield finish(rgb, sharpen)


def hero(prod, top_frac=0.25, base_frac=0.73):
    Hh = prod.h / (base_frac - top_frac)
    return prod.base - (base_frac - 0.5) * Hh, Hh


def pulse(t, at, width):
    """0 -> 1 -> 0 bump centred on `at`."""
    u = (t - at) / width
    return math.exp(-u * u * 4) if abs(u) < 1.2 else 0.0


def shoulder(p, cy, Hh, side=1):
    """Output position of the pack's upper shoulder (where the glint pops) in a centred hero frame."""
    s = OH / Hh
    return OW / 2 + side * p.bw * 0.36 * s, OH / 2 + (p.base - p.h * 0.62 - cy) * s


def shot_a():
    """Crane up from the set to the first product: light burst on the unveil, a sweep across the label with a warm
    flare, a glint on the shoulder, then a slow settle and push-in so the label holds sharp."""
    path, h, *_ = CFG["prods"][0]
    p = Product(IMGS[0], POD_X, POD_Y + 8, h)
    cy_h, Hh_h = hero(p)
    gx, gy = shoulder(p, cy_h - 18, Hh_h - 70, 1)

    def cam(t):
        c = ease_out(min(1, t / 0.5))
        q = ease(t)
        return lerp(POD_X - 40, POD_X, c), lerp(cy_h + 420, cy_h, c) - lerp(0, 18, q), lerp(Hh_h - 180, Hh_h, c) - lerp(0, 70, q), lerp(1.2, 0, c)

    def fl(t):
        u = min(1, max(0, (t - 0.25) / 0.4))
        return lerp(OW * 0.95, OW * 0.2, u), OH * 0.30, math.sin(math.pi * u) * 0.8
    return run([p], 2.8, cam, sweeps=((0.28, 0.78, -1),), flare_fn=fl, light=lambda t: lerp(0.88, 1.0, ease_out(min(1, t / 0.4))),
               burst_fn=lambda t: 0.75 * pulse(t, 0.22, 0.45) + 0.12 * min(1, t / 0.3),
               glint_fn=lambda t: (gx, gy, 0.9 * pulse(t, 0.74, 0.18)))


def shot_b():
    """Lateral glide with a gentle roll that lands square on the second product, burst, sweep, glint, push-in."""
    path, h, *_ = CFG["prods"][1]
    p = Product(IMGS[1], POD_X, POD_Y + 8, h)
    cy_h, Hh_h = hero(p, 0.27, 0.73)
    gx, gy = shoulder(p, cy_h - 14, Hh_h - 60, -1)

    def cam(t):
        c = ease_out(min(1, t / 0.55))
        q = ease(t)
        return lerp(POD_X + 300, POD_X, c), cy_h - lerp(0, 14, q), lerp(Hh_h + 160, Hh_h, c) - lerp(0, 60, q), lerp(-2.2, 0, c)

    def fl(t):
        u = min(1, max(0, (t - 0.3) / 0.4))
        return lerp(OW * 0.1, OW * 0.85, u), OH * 0.32, math.sin(math.pi * u) * 0.7
    return run([p], 2.8, cam, sweeps=((0.3, 0.8, 1),), flare_fn=fl, t0=3.0, light=lambda t: lerp(0.88, 1.0, ease_out(min(1, t / 0.4))),
               burst_fn=lambda t: 0.75 * pulse(t, 0.25, 0.45) + 0.12 * min(1, t / 0.3),
               glint_fn=lambda t: (gx, gy, 0.9 * pulse(t, 0.78, 0.18)))


def duo_products():
    (_, _, dx1, dy1, h1), (_, _, dx2, dy2, h2) = CFG["prods"]
    return [Product(IMGS[0], POD_X + dx1, POD_Y + dy1, h1), Product(IMGS[1], POD_X + dx2, POD_Y + dy2, h2)]


SHOTS = {"a": shot_a, "b": shot_b}

if __name__ == "__main__":
    name, out = sys.argv[1], sys.argv[2]
    gen = SHOTS[name]()
    if out.endswith(".jpg"):
        frames = list(gen)
        pick = [frames[2], frames[len(frames) // 5], frames[len(frames) // 2], frames[-1]]
        sheet = Image.new("RGB", (360 * 4, 640))
        for k, f in enumerate(pick):
            sheet.paste(Image.fromarray(f).resize((360, 640), Image.LANCZOS), (360 * k, 0))
        sheet.save(out, quality=92)
        Image.fromarray(frames[-1]).save(out.replace(".jpg", "_last.png"))
    else:
        pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in gen:
            pr.stdin.write(f.tobytes())
        pr.stdin.close()
        pr.wait()
