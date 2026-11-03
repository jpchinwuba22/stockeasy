"""PalmCare Video 3 product unveiling, premium version: the real products (clean edges, studio-white
finish, gloss, rim light) standing on a styled sunlit travertine set (arch, palm shadows, oranges).
Camera: crane-ups, whip trucks and a pull-out with true sub-frame motion blur (no ghosting), rack
focus on the set, out-of-focus foreground leaf and bokeh for depth, light sweeps and bloom.
Usage: hero3c.py SHOT OUT.mp4|OUT.jpg"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from hero3 import FPS, GOBO, OH, OW, Dust, ease, ease_out, glow, gobo_mask, lerp, screen
from prodfx import bloom, premium

RNG = np.random.default_rng(41)
PLATE = Image.open("setA.png").convert("RGB")
PW, PH = PLATE.size
POD_X, POD_Y, POD_RX, POD_RY = 586, 1410, 281, 31  # podium top surface (centre, radii) on setA


def warm(img, k=(1.0, 0.975, 0.93)):
    a = np.asarray(img).astype(np.float32)
    a[..., :3] *= np.array(k, np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


VITAC = warm(premium(Image.open("vitac_fix.png").convert("RGBA"), spec_pos=0.30, from_right=True))
GLOW = warm(premium(glow, spec_pos=0.30, from_right=True))


class Product:
    """A product cutout in plate coordinates, kept premultiplied at full and half resolution."""

    def __init__(self, img, cx, base_y, h):
        self.k = h / img.height  # plate px per source px
        self.x0, self.y0 = cx - img.width * self.k / 2, base_y - h
        self.w, self.h, self.cx, self.base = img.width * self.k, h, cx, base_y
        al = np.asarray(img.split()[-1])[-max(4, img.height // 25):] > 128
        cols = np.where(al.any(axis=0))[0]
        self.bw = (cols.max() - cols.min()) * self.k  # width of the foot that touches the podium
        half = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
        self.levels = [(img.convert("RGBa"), 1.0), (half.convert("RGBa"), 0.5)]


class Set:
    def __init__(self, products, flip=False, title_veil=True):
        plate = PLATE.transpose(Image.FLIP_LEFT_RIGHT) if flip else PLATE.copy()
        plate = plate.convert("RGBA")
        pod_x = PW - POD_X if flip else POD_X
        # contact + soft cast shadows, clipped to the podium's top surface
        top = Image.new("L", (PW, PH), 0)
        ImageDraw.Draw(top).ellipse((pod_x - POD_RX, POD_Y - POD_RY, pod_x + POD_RX, POD_Y + POD_RY + 6), fill=255)
        for p in products:
            sh = Image.new("L", (PW, PH), 0)
            d = ImageDraw.Draw(sh)
            d.ellipse((p.cx - p.bw * 0.55, p.base - p.bw * 0.16 - 6, p.cx + p.bw * 0.55 + p.w * 0.7, p.base + 2), fill=100)
            sh = sh.filter(ImageFilter.GaussianBlur(10))
            c = Image.new("L", (PW, PH), 0)
            ImageDraw.Draw(c).ellipse((p.cx - p.bw * 0.52, p.base - p.bw * 0.12 - 4, p.cx + p.bw * 0.52, p.base + 1), fill=200)
            c = c.filter(ImageFilter.GaussianBlur(4))
            a = np.maximum(np.asarray(sh), np.asarray(c)).astype(np.float32) * (np.asarray(top) / 255.0)
            layer = Image.new("RGBA", (PW, PH), (110, 66, 36, 0))
            layer.putalpha(Image.fromarray(a.astype(np.uint8)))
            plate.alpha_composite(layer)
        plate = plate.convert("RGB")
        self.sharp = plate.filter(ImageFilter.GaussianBlur(1.4))  # also hides the generator's faint grid texture
        self.soft = plate.filter(ImageFilter.GaussianBlur(9))
        self.products = products
        self.veil = title_veil

    def render(self, cam, focus):
        """One exposure: cam = (cx, cy, Hh, rot_deg) in plate px. focus 1 = set sharp, 0 = set soft."""
        cx, cy, Hh, rot = cam
        s, r = Hh / OH, math.radians(rot)
        a, b, d, e = s * math.cos(r), -s * math.sin(r), s * math.sin(r), s * math.cos(r)
        ox, oy = cx - a * OW / 2 - b * OH / 2, cy - d * OW / 2 - e * OH / 2
        co = (a, b, ox, d, e, oy)
        bg = np.asarray(self.sharp.transform((OW, OH), Image.AFFINE, co, Image.BICUBIC)).astype(np.float32)
        if focus < 0.999:
            soft = np.asarray(self.soft.transform((OW, OH), Image.AFFINE, co, Image.BILINEAR)).astype(np.float32)
            bg = soft + (bg - soft) * focus
        mask = np.zeros((OH, OW), np.float32)
        for p in self.products:
            disp = s / p.k  # source px per output px
            img, f = p.levels[1] if disp > 1.7 else p.levels[0]
            pc = tuple(v / p.k * f for v in (a, b, ox - p.x0, d, e, oy - p.y0))
            lay = np.asarray(img.transform((OW, OH), Image.AFFINE, pc, Image.BICUBIC)).astype(np.float32)
            al = lay[..., 3:] / 255
            bg = bg * (1 - al) + lay[..., :3]
            mask = np.maximum(mask, al[..., 0])
        return np.clip(bg, 0, 255), mask

    def expose(self, cam_fn, t, dt, focus):
        """Average sub-frame exposures across a 180-degree shutter; sample count follows image speed."""
        c0, c1 = cam_fn(t), cam_fn(min(1.0, t + dt * 0.5))
        sp = math.hypot(c1[0] - c0[0], c1[1] - c0[1]) * OH / c0[2]
        sp += abs(c1[2] - c0[2]) / c0[2] * OH * 0.6 + abs(c1[3] - c0[3]) * 18
        n = int(min(14, max(1, math.ceil(sp / 2.5))))
        acc, macc = 0, 0
        for k in range(n):
            tk = t + (dt * 0.5) * (k / max(1, n - 1)) if n > 1 else t
            rgb, m = self.render(cam_fn(min(1.0, tk)), focus)
            acc, macc = acc + rgb, macc + m
        return acc / n, macc / n


def clamp_cam(cx, cy, Hh, rot):
    hw, hh = Hh * OW / OH / 2 * (1 + abs(rot) * 0.03), Hh / 2 * (1 + abs(rot) * 0.01)
    return min(max(cx, hw), PW - hw), min(max(cy, hh), PH - hh), Hh, rot


def leaf_layer(angle, scale):
    """Out-of-focus foreground palm leaf at quarter resolution (RGBA)."""
    g = GOBO.rotate(angle, Image.BICUBIC, expand=True)
    sz = round(OH / 4 * scale)
    g = g.resize((sz, sz), Image.BILINEAR).filter(ImageFilter.GaussianBlur(7))
    lay = Image.new("RGBA", g.size, (84, 60, 30, 0))
    lay.putalpha(g.point(lambda v: min(255, int(v * 1.25))))
    return lay


def fg_composite(arr, leaf, pos, alpha=0.93):
    q = Image.new("RGBA", (OW // 4, OH // 4), (0, 0, 0, 0))
    q.paste(leaf, (round(pos[0] / 4 - leaf.width / 2), round(pos[1] / 4 - leaf.height / 2)), leaf)
    q = np.asarray(q.resize((OW, OH), Image.BILINEAR)).astype(np.float32)
    al = q[..., 3:] / 255 * alpha
    return arr * (1 - al) + q[..., :3] * al


class Bokeh:
    """Soft warm out-of-focus light orbs in the foreground, moving with parallax."""

    def __init__(self, n=6, seed=3):
        r = np.random.default_rng(seed)
        self.p = np.column_stack([r.uniform(-100, OW + 100, n), r.uniform(OH * 0.05, OH * 0.95, n)])
        self.r = r.uniform(35, 95, n)
        self.a = r.uniform(0.10, 0.22, n)

    def draw(self, arr, off):
        q = Image.new("L", (OW // 4, OH // 4), 0)
        d = ImageDraw.Draw(q)
        for (x, y), rr, a in zip(self.p, self.r, self.a):
            x, y = ((x + off[0]) % (OW + 400) - 200) / 4, (y + off[1]) / 4
            d.ellipse((x - rr / 4, y - rr / 4, x + rr / 4, y + rr / 4), fill=int(255 * a))
        g = np.asarray(q.filter(ImageFilter.GaussianBlur(3)).resize((OW, OH), Image.BILINEAR)).astype(np.float32) / 255
        return screen(arr, g[..., None] * np.array([255, 226, 180], np.float32))


def sweep(mask, pos, width=120.0, angle=0.35, strength=0.50):
    u = np.arange(OW, dtype=np.float32)[None, :]
    v = np.arange(OH, dtype=np.float32)[:, None]
    return np.exp(-(((u + v * angle) - pos) / width) ** 2) * mask * strength


YY = np.mgrid[0:OH, 0:OW][0].astype(np.float32)
XX = np.mgrid[0:OH, 0:OW][1].astype(np.float32)
VIG = 1 - 0.07 * (((XX - OW / 2) / (OW / 2)) ** 2 + ((YY - OH / 2) / (OH / 2)) ** 2)
VEIL = (np.clip((YY / OH - 0.77) / 0.10, 0, 1) ** 1.3 * 0.42)[..., None]
IVORY = np.array([251, 242, 229], np.float32)


def finish(arr, veil):
    arr = bloom(arr, threshold=226, radius=30, amount=0.26)
    x = np.clip(arr / 255, 0, 1)
    x = x + 0.06 * np.sin(np.pi * x) * (x - 0.5) * 2  # crisp S-curve
    arr = x * 255
    if veil:
        arr = arr * (1 - VEIL) + IVORY * VEIL
    arr = arr * VIG[..., None] + RNG.normal(0, 1.5, (OH, OW))[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


def run(st, dur, cam, focus=lambda t: 1.0, sweeps=((0.35, 0.95, 1),), gobo=None, leaf=None, bokeh=None):
    """cam(t) -> (cx, cy, Hh, rot). leaf(t) -> (layer, (x, y)) or None. bokeh(t) -> offset or None."""
    dust = Dust(24)
    n = round(dur * FPS)
    cfn = lambda t: clamp_cam(*cam(t))
    dt = 1 / (n - 1)
    for i in range(n):
        t = i / (n - 1)
        rgb, m = st.expose(cfn, t, dt, focus(t))
        if gobo:
            rgb = rgb * (1 - 0.11 * gobo(t)[..., None])
        for t0, t1, dr in sweeps:
            u = min(1, max(0, (t - t0) / (t1 - t0)))
            if 0 < u < 1:
                pos = lerp(-500, OW + 1100, ease(u)) if dr > 0 else lerp(OW + 1100, -500, ease(u))
                rgb = screen(rgb, sweep(m, pos)[..., None] * 255)
        if bokeh:
            rgb = bokeh[0].draw(rgb, bokeh[1](t))
        rgb = dust.draw(rgb, i / FPS)
        if leaf:
            lf = leaf(t)
            if lf:
                rgb = fg_composite(rgb, *lf)
        yield finish(rgb, st.veil)


def gobo_drift(a0, a1, x0, x1, y0, y1):
    return lambda t: gobo_mask(lerp(a0, a1, t), lerp(x0, x1, t), lerp(y0, y1, t), 1.3, 16)


# Hero framing helper: product top at `top_frac` of frame height, podium surface at `base_frac`.
def hero(prod, top_frac=0.19, base_frac=0.67):
    Hh = prod.h / (base_frac - top_frac)
    return prod.base - (base_frac - 0.5) * Hh, Hh


def shot_vitac():
    """Out-of-focus leaf wipes off as the camera cranes up from the oranges onto Vita C+, then a slow arcing push."""
    p = Product(VITAC, POD_X, POD_Y + 20, 640)
    st = Set([p])
    cy_h, Hh_h = hero(p)
    lf = leaf_layer(-35, 1.9)

    def cam(t):
        c = ease_out(min(1, t / 0.26))
        q = ease(t)
        Hh = lerp(1150, Hh_h, c) - lerp(0, 150, q)
        return lerp(POD_X + 70, POD_X, c) + lerp(0, -12, q), lerp(cy_h + 430, cy_h, c) - lerp(0, 40, q), Hh, lerp(-2.5, 0, c) + lerp(0, 0.6, q)

    leaf = lambda t: (lf, (lerp(OW * 0.45, -OW * 0.9, ease_out(min(1, t / 0.24))), OH * 0.55)) if t < 0.25 else None
    return run(st, 2.6, cam, focus=lambda t: lerp(0.35, 1.0, ease_out(min(1, t / 0.4))),
               sweeps=((0.32, 0.90, 1),), gobo=gobo_drift(-24, -14, 1150, 420, 300, 440), leaf=leaf,
               bokeh=(Bokeh(6, 3), lambda t: (lerp(260, -80, ease_out(t)), lerp(-520, 60, ease_out(min(1, t / 0.3))))))


def shot_glow_reveal():
    """Opens inside the palm logo of the tube and pulls out fast, racking the set into focus."""
    p = Product(GLOW, PW - POD_X, POD_Y + 18, 620)
    st = Set([p], flip=True, title_veil=False)
    cy_h, Hh_h = hero(p)
    logo_y = p.base - p.h * 0.62

    def cam(t):
        z = ease_out(min(1, t / 0.55))
        Hh = lerp(330, Hh_h, z) - lerp(0, 50, ease(t))
        return p.cx, lerp(logo_y, cy_h, z), Hh, lerp(3, 0, z)
    return run(st, 1.8, cam, focus=lambda t: lerp(0.0, 1.0, ease(min(1, t / 0.6))),
               sweeps=((0.45, 1.0, -1),), gobo=gobo_drift(16, 9, -100, 520, 400, 520))


def shot_glow():
    """Whip truck from the right past a foreground leaf onto Glowshield, then a slow push."""
    p = Product(GLOW, PW - POD_X, POD_Y + 18, 620)
    st = Set([p], flip=True)
    cy_h, Hh_h = hero(p)
    lf = leaf_layer(150, 1.7)

    def cam(t):
        w = ease_out(min(1, t / 0.24))
        q = ease(t)
        return lerp(p.cx + 210, p.cx, w) + lerp(0, 10, q), cy_h - lerp(0, 30, q), Hh_h - lerp(0, 140, q), lerp(2.2, 0, w)

    leaf = lambda t: (lf, (lerp(OW * 0.6, OW * 1.9, ease_out(min(1, t / 0.22))), OH * 0.42)) if t < 0.23 else None
    return run(st, 2.4, cam, sweeps=((0.30, 0.92, -1),), gobo=gobo_drift(18, 9, -120, 700, 340, 520), leaf=leaf,
               bokeh=(Bokeh(5, 8), lambda t: (lerp(900, 0, ease_out(min(1, t / 0.3))), 0)))


def shot_macro():
    """Smooth, fast-braking tilt down the label onto 'SPF 50+ PA++++' with the set thrown soft."""
    p = Product(GLOW, PW - POD_X, POD_Y + 18, 620)
    st = Set([p], flip=True, title_veil=False)
    top = p.base - p.h

    def cam(t):
        e = ease_out(t)
        return p.cx, lerp(top + 0.55 * p.h, top + 0.79 * p.h, e), lerp(560, 500, e), lerp(-1.8, 0, e)
    return run(st, 1.4, cam, focus=lambda t: 0.15, sweeps=((0.0, 0.85, -1),), gobo=gobo_drift(-18, -10, 300, 820, 700, 1100))


def shot_duo():
    """Crane down from the sunlit arch onto both products on the podium, then a slow push in."""
    vb = Product(VITAC, POD_X - 96, POD_Y + 12, 560)
    gb = Product(GLOW, POD_X + 114, POD_Y + 24, 520)
    st = Set([vb, gb])
    Hh_h = 1330
    cy_h = vb.base - 0.17 * Hh_h
    lf = leaf_layer(20, 2.0)

    def cam(t):
        c = ease_out(min(1, t / 0.38))
        q = ease(t)
        return POD_X + lerp(-40, 10, q), lerp(cy_h - 560, cy_h, c), Hh_h - lerp(0, 150, q), lerp(1.5, 0, c)

    leaf = lambda t: (lf, (OW * 0.02 - lerp(0, OW * 0.5, ease_out(min(1, t / 0.4))), lerp(OH * 0.25, OH * 1.2, ease_out(min(1, t / 0.4))))) if t < 0.4 else None
    return run(st, 3.2, cam, sweeps=((0.38, 0.98, 1),), gobo=gobo_drift(-28, -16, 900, 360, 480, 700), leaf=leaf,
               bokeh=(Bokeh(7, 11), lambda t: (lerp(0, -160, ease(t)), lerp(-700, 0, ease_out(min(1, t / 0.4))))))


SHOTS = {"vitac": shot_vitac, "glowrev": shot_glow_reveal, "glow": shot_glow, "macro": shot_macro, "duo": shot_duo}

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
