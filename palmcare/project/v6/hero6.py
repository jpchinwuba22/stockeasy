"""PalmCare Video 6 ("Tropical Glow") product shots: the real Advanced Tropical Glow and Dermalight bottles on a
travertine plinth in a still tropical pool at sunrise. The set is alive: shimmering water, drifting caustic light
on the wall, slow sun rays and floating gold dust. Usage: hero6.py SHOT OUT.mp4|OUT.jpg"""
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

RNG = np.random.default_rng(6)
PLATE = np.asarray(Image.open("setT.png").convert("RGB")).astype(np.float32)
PH, PW = PLATE.shape[:2]
POD_X, POD_Y, POD_RX, POD_RY = 577, 1402, 410, 38     # plinth top surface on setT
WATER_TOP = 1590


def tint(img, k):
    a = np.asarray(img).astype(np.float32)
    a[..., :3] *= np.array(k, np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def load(path):
    im = Image.open(path).convert("RGBA")
    return tint(premium(im.crop(im.split()[-1].getbbox()), spec_pos=0.30, from_right=True), (1.0, 0.975, 0.94))


TROP = load("../group/trop_cut.png")
DERM = load("../group/dermalight_cut.png")


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
_wm = Image.new("L", (PW, PH), 0)
_d = ImageDraw.Draw(_wm)
_d.rectangle((0, WATER_TOP, PW, 1880), fill=255)
_d.ellipse((POD_X - 430, 1330, POD_X + 430, 1660), fill=0)
WATER = np.asarray(_wm.filter(ImageFilter.GaussianBlur(24))).astype(np.float32) / 255
WALL = np.clip((1250 - YYp) / 200, 0, 1)
TOPM = Image.new("L", (PW, PH), 0)
ImageDraw.Draw(TOPM).ellipse((POD_X - POD_RX, POD_Y - POD_RY, POD_X + POD_RX, POD_Y + POD_RY), fill=255)
TOPM = np.asarray(TOPM.filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255


def plate_at(t, products, light=1.0):
    """Animated plate: water shimmer, drifting wall caustics and sun rays; product shadows and reflections."""
    dx = (2.4 * np.sin(YYp * 0.06 + t * 2.0) + 1.5 * np.sin(XXp * 0.028 - t * 1.4)) * WATER
    dy = (1.2 * np.sin(XXp * 0.05 + t * 1.6)) * WATER
    x = np.clip(XXp + dx, 0, PW - 1.001)
    y = np.clip(YYp + dy, 0, PH - 1.001)
    x0, y0 = x.astype(np.int32), y.astype(np.int32)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    im = PLATE
    rgb = (im[y0, x0] * (1 - fx) * (1 - fy) + im[y0, x0 + 1] * fx * (1 - fy) + im[y0 + 1, x0] * (1 - fx) * fy + im[y0 + 1, x0 + 1] * fx * fy)
    # caustic light dancing on the wall (reflected from the pool)
    c = (np.sin(XXp * 0.021 + YYp * 0.008 + t * 1.3) * np.sin(XXp * 0.013 - YYp * 0.017 - t * 1.05)
         + np.sin(XXp * 0.031 - YYp * 0.011 + t * 0.9) * 0.6)
    caus = np.clip(c - 0.75, 0, None) * WALL * 0.22
    rgb = screen(rgb, caus[..., None] * np.array([255, 236, 200.0]))
    # slow sun rays from the upper right
    ang = math.radians(-35 + 2.0 * math.sin(t * 0.5))
    u = (XXp - 1300) * math.cos(ang) + (YYp + 200) * math.sin(ang)
    rays = (0.5 + 0.5 * np.sin(u * 0.012 + t * 0.35)) ** 6 * np.clip(1 - YYp / 1700, 0, 1) * 0.12
    rgb = screen(rgb, rays[..., None] * np.array([255, 228, 180.0]))
    rgb = rgb * light
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    for p in products:
        # soft reflection of the bottle on the polished stone top
        ref = p.img.transpose(Image.FLIP_TOP_BOTTOM).resize((round(p.w), round(p.h)), Image.LANCZOS)
        ra = np.asarray(ref).astype(np.float32)
        ra[..., 3] *= np.linspace(0.22, 0.0, ra.shape[0])[:, None]
        ref = Image.fromarray(ra.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(3))
        lay = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        lay.alpha_composite(ref, (round(p.x0), round(p.base - 4)))
        la = np.asarray(lay).astype(np.float32)
        la[..., 3] *= TOPM
        img.alpha_composite(Image.fromarray(la.astype(np.uint8), "RGBA"))
        # key light is high on the right: a soft shadow falls back-left plus tight contact occlusion
        sh = Image.new("L", (PW, PH), 0)
        ImageDraw.Draw(sh).ellipse((p.cx - p.bw * 1.25, p.base - p.bw * 0.22 - 4, p.cx + p.bw * 0.35, p.base + 3), fill=105)
        sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(14))).astype(np.float32)
        c2 = Image.new("L", (PW, PH), 0)
        ImageDraw.Draw(c2).ellipse((p.cx - p.bw * 0.52, p.base - p.bw * 0.10 - 4, p.cx + p.bw * 0.52, p.base + 2), fill=245)
        c2 = np.asarray(c2.filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
        a = np.maximum(sh, c2) * TOPM
        s = Image.new("RGBA", (PW, PH), (70, 45, 22, 0))
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
    hw, hh = Hh * OW / OH / 2 * (1 + abs(rot) * 0.03), Hh / 2 * (1 + abs(rot) * 0.01)
    return min(max(cx, hw), PW - hw), min(max(cy, hh), PH - hh), Hh, rot


YY, XX = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = 1 - 0.13 * (((XX - OW / 2) / (OW / 2)) ** 2 + ((YY - OH / 2) / (OH / 2)) ** 2)


class Dust:
    """Floating golden dust motes drifting upward in the sun."""

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


def run(products, dur, cam, light=lambda t: 1.0, sweeps=(), flare_fn=None, t0=0.0, sharpen=False, dust=1.0):
    n = round(dur * FPS)
    cfn = lambda t: clamp_cam(*cam(t))
    dt = 1 / (n - 1)
    dd = Dust()
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
        for s0, s1, dr in sweeps:
            u = min(1, max(0, (t - s0) / (s1 - s0)))
            if 0 < u < 1:
                pos = lerp(-500, OW + 1100, ease(u)) if dr > 0 else lerp(OW + 1100, -500, ease(u))
                rgb = screen(rgb, sweep(m, pos)[..., None] * 255)
        if flare_fn:
            fx, fy, fs = flare_fn(t)
            rgb = flare(rgb, fx, fy, fs)
        rgb = dd.draw(rgb, t0 + i / FPS, dust)
        yield finish(rgb, sharpen)


def hero(prod, top_frac=0.25, base_frac=0.73):
    Hh = prod.h / (base_frac - top_frac)
    return prod.base - (base_frac - 0.5) * Hh, Hh


def shot_trop():
    """Crane up from the pool (frangipani and water) to the bottle; a sunbeam sweeps across the label with a
    warm flare and the camera settles into a slow push-in so the label holds sharp."""
    p = Product(TROP, POD_X, POD_Y + 8, 800)
    cy_h, Hh_h = hero(p)

    def cam(t):
        c = ease_out(min(1, t / 0.5))
        q = ease(t)
        return lerp(POD_X - 40, POD_X, c), lerp(cy_h + 420, cy_h, c) - lerp(0, 18, q), lerp(Hh_h - 180, Hh_h, c) - lerp(0, 70, q), lerp(1.2, 0, c)

    def fl(t):
        u = min(1, max(0, (t - 0.25) / 0.4))
        return lerp(OW * 0.95, OW * 0.2, u), OH * 0.30, math.sin(math.pi * u) * 0.8
    return run([p], 2.8, cam, sweeps=((0.28, 0.78, -1),), flare_fn=fl)


def shot_derm():
    """Lateral glide with a gentle roll that lands square on the bottle, a light sweep and a soft push-in."""
    p = Product(DERM, POD_X, POD_Y + 8, 700)
    cy_h, Hh_h = hero(p, 0.27, 0.73)

    def cam(t):
        c = ease_out(min(1, t / 0.55))
        q = ease(t)
        return lerp(POD_X + 300, POD_X, c), cy_h - lerp(0, 14, q), lerp(Hh_h + 160, Hh_h, c) - lerp(0, 60, q), lerp(-2.2, 0, c)

    def fl(t):
        u = min(1, max(0, (t - 0.3) / 0.4))
        return lerp(OW * 0.1, OW * 0.85, u), OH * 0.32, math.sin(math.pi * u) * 0.7
    return run([p], 2.8, cam, sweeps=((0.3, 0.8, 1),), flare_fn=fl, t0=3.0)


def duo_products():
    return [Product(TROP, POD_X - 150, POD_Y + 4, 760), Product(DERM, POD_X + 175, POD_Y + 16, 640)]


def shot_duo():
    ps = duo_products()

    def cam(t):
        q = ease(t)
        return POD_X + 12, lerp(1150, 1130, q), lerp(1780, 1660, q), 0.0
    return run(ps, 1.6, cam, sweeps=((0.1, 0.9, 1),), t0=6.0)


SHOTS = {"trop": shot_trop, "derm": shot_derm, "duo": shot_duo}

if __name__ == "__main__":
    name, out = sys.argv[1], sys.argv[2]
    gen = SHOTS[name]()
    if out.endswith(".jpg"):
        frames = list(gen)
        pick = [frames[2], frames[len(frames) // 4], frames[len(frames) // 2], frames[-1]]
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
