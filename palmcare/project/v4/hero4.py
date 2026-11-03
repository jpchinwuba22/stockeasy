"""PalmCare Video 4 ("Still Water") product shots: the real N10 serum and Vitamin C moisturiser on a
pearl-stone plinth rising from a still aqua pool, with live animated water caustics on the wall, the
water and the products, a rippling reflection, expanding ripple rings, light sweeps and bloom.
Camera moves use true sub-frame motion blur. Usage: hero4.py SHOT OUT.mp4|OUT.jpg"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "../v3")
_cwd = os.getcwd()
os.chdir("../v3")  # hero3 loads its own cutouts relative to its folder
from hero3 import FPS, OH, OW, Dust, ease, ease_out, lerp, screen  # noqa: E402
from prodfx import bloom, premium  # noqa: E402
os.chdir(_cwd)

RNG = np.random.default_rng(7)
PW, PH = 1440, 2560
WATER_Y = 1390                      # far edge of the pool (wall above)
POD_X, POD_Y, POD_RX, POD_RY = 717, 1637, 390, 85   # plinth top surface on setW
POD_TOP, POD_BASE, WATERLINE = POD_Y, 1850, 1855


def tint(img, k):
    a = np.asarray(img).astype(np.float32)
    a[..., :3] *= np.array(k, np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


N10 = tint(premium(Image.open("n10_fix2.png").convert("RGBA"), spec_pos=0.30, from_right=True), (0.99, 1.0, 1.0))
_jar = Image.open("jar_cut.png").convert("RGBA")
JAR = tint(premium(_jar.crop(_jar.split()[-1].getbbox()), spec_pos=0.28, from_right=True), (1.0, 0.99, 0.975))


def caustic(w, h, t, scale, off=(0.0, 0.0), sy=1.0):
    """Tileable water-caustic pattern in [0, 1] (port of the classic shader)."""
    tau = 6.28318530718
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    px = np.mod((xs / w * scale + off[0]) * tau, tau) - 250.0
    py = np.mod((ys / w * scale * sy + off[1]) * tau, tau) - 250.0
    ix, iy = px.copy(), py.copy()
    c = np.ones_like(px)
    inten = 0.005
    for n in range(5):
        tt = t * (1.0 - 3.5 / (n + 1))
        ix, iy = px + np.cos(tt - ix) + np.sin(tt + iy), py + np.sin(tt - iy) + np.cos(tt + ix)
        c += 1.0 / np.sqrt((px / (np.sin(ix + tt) / inten)) ** 2 + (py / (np.cos(iy + tt) / inten)) ** 2)
    c = 1.17 - (c / 5) ** 1.4
    return np.clip(np.abs(c) ** 8, 0, 1.6)


def up(a, w, h, blur=0):
    im = Image.fromarray(np.clip(a * 160, 0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im).astype(np.float32) / 160


class Pool:
    """The generated pool set (setW.png), brought to life: shimmering water, drifting caustics on the
    wall, expanding ripple rings around the plinth, and the products' shadows on the plinth top."""

    def __init__(self):
        self.img = np.asarray(Image.open("setW.png").convert("RGB")).astype(np.float32)
        # pool water: between the far edge and the diagonal front ledge, minus the plinth and the lily
        wm = Image.new("L", (PW, PH), 0)
        dw = ImageDraw.Draw(wm)
        dw.polygon([(0, WATER_Y + 20), (PW, WATER_Y + 20), (PW, 2265), (0, 1945)], fill=255)
        dw.rectangle((POD_X - POD_RX - 6, POD_Y - POD_RY, POD_X + POD_RX + 6, POD_BASE), fill=0)
        dw.ellipse((POD_X - POD_RX - 6, POD_BASE - 70, POD_X + POD_RX + 6, POD_BASE + 40), fill=0)
        dw.ellipse((70, 1740, 340, 2060), fill=0)
        self.water = np.asarray(wm.filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255
        yy = np.arange(PH, dtype=np.float32)[:, None]
        self.wall = np.clip((WATER_Y - yy) / 300, 0, 1) * np.ones((1, PW), np.float32)
        self.yy, self.xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
        tm = Image.new("L", (PW, PH), 0)
        ImageDraw.Draw(tm).ellipse((POD_X - POD_RX, POD_Y - POD_RY, POD_X + POD_RX, POD_Y + POD_RY), fill=255)
        self.top = np.asarray(tm.filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255

    def plate(self, t, products):
        # water shimmer: small travelling displacement inside the water only
        dx = (3.2 * np.sin(self.yy * 0.045 + t * 2.3) + 2.0 * np.sin(self.xx * 0.03 - t * 1.4)) * self.water
        dy = (2.0 * np.sin(self.xx * 0.05 + t * 1.9) + 1.2 * np.sin(self.yy * 0.02 - t * 1.1)) * self.water
        x = np.clip(self.xx + dx, 0, PW - 1.001)
        y = np.clip(self.yy + dy, 0, PH - 1.001)
        x0, y0 = x.astype(np.int32), y.astype(np.int32)
        fx, fy = (x - x0)[..., None], (y - y0)[..., None]
        im = self.img
        rgb = (im[y0, x0] * (1 - fx) * (1 - fy) + im[y0, x0 + 1] * fx * (1 - fy)
               + im[y0 + 1, x0] * (1 - fx) * fy + im[y0 + 1, x0 + 1] * fx * fy)
        # drifting caustic light on the wall and glints on the water
        cw = up(caustic(360, 640, t * 0.5 + 23, 1.7), PW, PH, blur=3)
        k = (self.wall * 0.16 + self.water * 0.10)[..., None]
        rgb = screen(rgb, cw[..., None] * k * np.array([255, 255, 246.0]))
        img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
        lay = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for j in range(3):
            ph_ = (t * 0.30 + j / 3) % 1.0
            rx, ry = POD_RX + 40 + ph_ * 520, 100 + ph_ * 120
            al = int(70 * (1 - ph_) ** 1.6)
            d.ellipse((POD_X - rx, WATERLINE - ry, POD_X + rx, WATERLINE + ry), outline=(240, 255, 252, al), width=5)
        lay.putalpha(Image.fromarray((np.asarray(lay.split()[-1]).astype(np.float32) * self.water).astype(np.uint8)))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2)))
        for p in products:
            sh = Image.new("L", (PW, PH), 0)
            ImageDraw.Draw(sh).ellipse((p.cx - p.bw * 0.55 + p.w * 0.1, p.base - p.bw * 0.16 - 6, p.cx + p.bw * 0.55 + p.w * 0.7, p.base + 2), fill=85)
            sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(12))).astype(np.float32)
            c2 = Image.new("L", (PW, PH), 0)
            ImageDraw.Draw(c2).ellipse((p.cx - p.bw * 0.52, p.base - p.bw * 0.12 - 4, p.cx + p.bw * 0.52, p.base + 1), fill=200)
            c2 = np.asarray(c2.filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
            a = np.maximum(sh, c2) * self.top
            s = Image.new("RGBA", (PW, PH), (78, 92, 96, 0))
            s.putalpha(Image.fromarray(a.astype(np.uint8)))
            img.alpha_composite(s)
        return img.convert("RGB")


class Product:
    def __init__(self, img, cx, base_y, h):
        self.k = h / img.height
        self.x0, self.y0 = cx - img.width * self.k / 2, base_y - h
        self.w, self.h, self.cx, self.base = img.width * self.k, h, cx, base_y
        al = np.asarray(img.split()[-1])[-max(4, img.height // 25):] > 128
        cols = np.where(al.any(axis=0))[0]
        self.bw = (cols.max() - cols.min()) * self.k
        half = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
        self.levels = [(img.convert("RGBa"), 1.0), (half.convert("RGBa"), 0.5)]


POOL = Pool()


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


def sweep(mask, pos, width=120.0, angle=0.35, strength=0.5):
    u = np.arange(OW, dtype=np.float32)[None, :]
    v = np.arange(OH, dtype=np.float32)[:, None]
    return np.exp(-(((u + v * angle) - pos) / width) ** 2) * mask * strength


class Bokeh:
    def __init__(self, n=7, seed=3):
        r = np.random.default_rng(seed)
        self.p = np.column_stack([r.uniform(-100, OW + 100, n), r.uniform(OH * 0.05, OH * 0.95, n)])
        self.r = r.uniform(30, 90, n)
        self.a = r.uniform(0.10, 0.20, n)

    def draw(self, arr, off):
        q = Image.new("L", (OW // 4, OH // 4), 0)
        d = ImageDraw.Draw(q)
        for (x, y), rr, a in zip(self.p, self.r, self.a):
            x, y = ((x + off[0]) % (OW + 400) - 200) / 4, (y + off[1]) / 4
            d.ellipse((x - rr / 4, y - rr / 4, x + rr / 4, y + rr / 4), fill=int(255 * a))
        g = np.asarray(q.filter(ImageFilter.GaussianBlur(3)).resize((OW, OH), Image.BILINEAR)).astype(np.float32) / 255
        return screen(arr, g[..., None] * np.array([225, 250, 248], np.float32))


YY, XX = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = 1 - 0.08 * (((XX - OW / 2) / (OW / 2)) ** 2 + ((YY - OH / 2) / (OH / 2)) ** 2)
VEIL = (np.clip((YY / OH - 0.77) / 0.10, 0, 1) ** 1.3 * 0.40)[..., None]
PEARL = np.array([240, 249, 247], np.float32)


def finish(arr, veil):
    arr = bloom(arr, threshold=224, radius=30, amount=0.24)
    x = np.clip(arr / 255, 0, 1)
    arr = (x + 0.06 * np.sin(np.pi * x) * (x - 0.5) * 2) * 255
    if veil:
        arr = arr * (1 - VEIL) + PEARL * VEIL
    arr = arr * VIG[..., None] + RNG.normal(0, 1.5, (OH, OW))[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


def run(products, dur, cam, sweeps=((0.35, 0.95, 1),), bokeh=None, veil=True, t0=0.0, caustic_k=0.10, sharpen=False):
    dust = Dust(22)
    n = round(dur * FPS)
    cfn = lambda t: clamp_cam(*cam(t))
    dt = 1 / (n - 1)
    for i in range(n):
        t = i / (n - 1)
        plate = POOL.plate(t0 + i / FPS, products)
        c0, c1 = cfn(t), cfn(min(1.0, t + dt * 0.5))
        sp = math.hypot(c1[0] - c0[0], c1[1] - c0[1]) * OH / c0[2] + abs(c1[2] - c0[2]) / c0[2] * OH * 0.6 + abs(c1[3] - c0[3]) * 18
        ns = int(min(14, max(1, math.ceil(sp / 2.5))))
        acc, macc = 0, 0
        for k in range(ns):
            rgb, m = render(plate, products, cfn(min(1.0, t + dt * 0.5 * k / max(1, ns - 1))))
            acc, macc = acc + rgb, macc + m
        rgb, m = acc / ns, macc / ns
        # caustic light playing over the products themselves
        pc = up(caustic(270, 480, (t0 + i / FPS) * 0.55 + 11, 1.4), OW, OH, blur=2)[..., None]
        rgb = screen(rgb, pc * m[..., None] * caustic_k * np.array([255, 255, 250.0]))
        for s0, s1, dr in sweeps:
            u = min(1, max(0, (t - s0) / (s1 - s0)))
            if 0 < u < 1:
                pos = lerp(-500, OW + 1100, ease(u)) if dr > 0 else lerp(OW + 1100, -500, ease(u))
                rgb = screen(rgb, sweep(m, pos)[..., None] * 255)
        if bokeh:
            rgb = bokeh[0].draw(rgb, bokeh[1](t))
        rgb = dust.draw(rgb, i / FPS)
        out = finish(rgb, veil)
        if sharpen:
            out = np.asarray(Image.fromarray(out).filter(ImageFilter.UnsharpMask(2.2, 90, 2)))
        yield out


def hero(prod, top_frac=0.19, base_frac=0.66):
    Hh = prod.h / (base_frac - top_frac)
    return prod.base - (base_frac - 0.5) * Hh, Hh


def shot_n10():
    """Crane up from the rippling water onto N10 on the plinth, then a slow arcing push."""
    p = Product(N10, POD_X, POD_Y + 14, 760)
    cy_h, Hh_h = hero(p)

    def cam(t):
        c = ease_out(min(1, t / 0.3))
        q = ease(t)
        return lerp(POD_X - 70, POD_X, c) + lerp(0, 12, q), lerp(cy_h + 600, cy_h, c) - lerp(0, 50, q), lerp(1400, Hh_h, c) - lerp(0, 180, q), lerp(2.2, 0, c) - lerp(0, 0.5, q)
    return run([p], 2.6, cam, sweeps=((0.32, 0.9, 1),), bokeh=(Bokeh(6, 3), lambda t: (lerp(240, -60, ease_out(t)), lerp(-560, 40, ease_out(min(1, t / 0.32))))))


def shot_n10_macro():
    """Fast-braking tilt down the N10 label onto its ingredients, pool thrown soft."""
    p = Product(N10, POD_X, POD_Y + 14, 760)
    top = p.base - p.h

    def cam(t):
        e = ease_out(t)
        return p.cx, lerp(top + 0.52 * p.h, top + 0.80 * p.h, e), lerp(700, 610, e), lerp(1.6, 0, e)
    return run([p], 1.4, cam, sweeps=((0.0, 0.85, -1),), veil=False, t0=3.0, caustic_k=0.04, sharpen=True)


def shot_jar():
    """Whip truck from the left onto the moisturiser jar, then a slow push."""
    p = Product(JAR, POD_X, POD_Y + 18, 420)
    Hh_h = 1330
    cy_h = p.base - 0.14 * Hh_h

    def cam(t):
        w = ease_out(min(1, t / 0.24))
        q = ease(t)
        return lerp(POD_X - 290, POD_X, w) - lerp(0, 10, q), cy_h - lerp(0, 30, q), Hh_h - lerp(0, 150, q), lerp(-2.2, 0, w)
    return run([p], 2.6, cam, sweeps=((0.30, 0.92, -1),), bokeh=(Bokeh(5, 8), lambda t: (lerp(-900, 0, ease_out(min(1, t / 0.3))), 0)), t0=6.0)


def shot_duo():
    """Crane down from the caustic wall onto both products, then a slow push in."""
    nb = Product(N10, POD_X - 125, POD_Y + 2, 680)
    jb = Product(JAR, POD_X + 150, POD_Y + 30, 370)
    Hh_h = 1600
    cy_h = nb.base - 0.16 * Hh_h

    def cam(t):
        c = ease_out(min(1, t / 0.38))
        q = ease(t)
        return POD_X + lerp(-30, 10, q), lerp(cy_h - 700, cy_h, c), Hh_h - lerp(0, 170, q), lerp(1.4, 0, c)
    return run([nb, jb], 3.0, cam, sweeps=((0.38, 0.98, 1),), bokeh=(Bokeh(7, 11), lambda t: (lerp(0, -150, ease(t)), lerp(-700, 0, ease_out(min(1, t / 0.4))))), t0=9.0)


SHOTS = {"n10": shot_n10, "n10macro": shot_n10_macro, "jar": shot_jar, "duo": shot_duo}

if __name__ == "__main__":
    name, out = sys.argv[1], sys.argv[2]
    gen = SHOTS[name]()
    if out.endswith(".jpg"):
        frames = list(gen)
        pick = [frames[1], frames[len(frames) // 6], frames[len(frames) // 2], frames[-1]]
        sheet = Image.new("RGB", (360 * 4, 640))
        for k, f in enumerate(pick):
            sheet.paste(Image.fromarray(f).resize((360, 640), Image.LANCZOS), (360 * k, 0))
        sheet.save(out, quality=92)
    else:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in gen:
            p.stdin.write(f.tobytes())
        p.stdin.close()
        p.wait()
