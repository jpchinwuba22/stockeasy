"""PalmCare Video 5 ("After Dark") product shots: the real Dermaluxe Pro bottle on a plum-marble plinth in a
moonlit, candlelit pool. The set is alive: drifting moonbeam, flickering candle glow, shimmering water,
slow mist and sparkles. The reveal opens in darkness and a moonbeam sweeps the bottle into view with an
anamorphic flare; a label macro follows. Usage: hero5.py SHOT OUT.mp4|OUT.jpg"""
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

RNG = np.random.default_rng(5)
PLATE = np.asarray(Image.open("setN.png").convert("RGB")).astype(np.float32)
PH, PW = PLATE.shape[:2]
POD_X, POD_Y, POD_RX, POD_RY = 590, 1190, 300, 48     # plinth top surface on setN
WATER_TOP = 1300


def tint(img, k):
    a = np.asarray(img).astype(np.float32)
    a[..., :3] *= np.array(k, np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


_dl = Image.open("dl_cut.png").convert("RGBA")
DL = tint(premium(_dl.crop(_dl.split()[-1].getbbox()), spec_pos=0.30, from_right=True), (1.0, 0.97, 0.99))


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
# water region (below the plinth's rim line), excluding the plinth body
_wm = Image.new("L", (PW, PH), 0)
_d = ImageDraw.Draw(_wm)
_d.rectangle((0, WATER_TOP, PW, PH), fill=255)
_d.ellipse((POD_X - 360, POD_Y - 60, POD_X + 360, 1530), fill=0)
WATER = np.asarray(_wm.filter(ImageFilter.GaussianBlur(20))).astype(np.float32) / 255
TOPM = Image.new("L", (PW, PH), 0)
ImageDraw.Draw(TOPM).ellipse((POD_X - POD_RX, POD_Y - POD_RY, POD_X + POD_RX, POD_Y + POD_RY), fill=255)
TOPM = np.asarray(TOPM.filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255
# candle glow centres (left) and moon centre
CANDLES = [(20, 930), (160, 1015), (40, 1130)]
MOON = (730, 410)


def plate_at(t, products, light=1.0):
    """Animated plate: water shimmer, flickering candles, drifting moonbeam and mist; product shadows/reflection."""
    dx = (2.6 * np.sin(YYp * 0.05 + t * 2.1) + 1.6 * np.sin(XXp * 0.03 - t * 1.3)) * WATER
    dy = (1.4 * np.sin(XXp * 0.045 + t * 1.7)) * WATER
    x = np.clip(XXp + dx, 0, PW - 1.001)
    y = np.clip(YYp + dy, 0, PH - 1.001)
    x0, y0 = x.astype(np.int32), y.astype(np.int32)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    im = PLATE
    rgb = (im[y0, x0] * (1 - fx) * (1 - fy) + im[y0, x0 + 1] * fx * (1 - fy) + im[y0 + 1, x0] * (1 - fx) * fy + im[y0 + 1, x0 + 1] * fx * fy)
    # candle flicker
    for k, (cx, cy) in enumerate(CANDLES):
        f = 0.5 + 0.5 * math.sin(t * (9 + k * 2.3) + k) * math.sin(t * (5.1 + k) + 2 * k)
        g = np.exp(-(((XXp - cx) / 150) ** 2 + ((YYp - cy) / 150) ** 2)) * (0.10 + 0.10 * f)
        rgb = screen(rgb, g[..., None] * np.array([255, 190, 140.0]))
    # drifting moonbeam from the upper right
    ang = math.radians(-58 + 2.5 * math.sin(t * 0.6))
    u = (XXp - 1100) * math.cos(ang) + (YYp + 100) * math.sin(ang)
    beam = np.exp(-(u / (150 + 20 * math.sin(t * 0.9))) ** 2) * np.clip((YYp + 100) / 1400, 0, 1) * 0.16
    rgb = screen(rgb, beam[..., None] * np.array([235, 225, 255.0]))
    # slow mist band above the water
    mist = np.exp(-((YYp - 1080) / 160) ** 2) * (0.5 + 0.5 * np.sin(XXp * 0.006 + t * 0.5)) * 0.10
    rgb = screen(rgb, mist[..., None] * np.array([230, 200, 225.0]))
    rgb = rgb * light
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    for p in products:
        # faint mirror reflection of the bottle on the polished plinth top
        ref = p.img.transpose(Image.FLIP_TOP_BOTTOM)
        ref = ref.resize((round(p.w), round(p.h)), Image.LANCZOS)
        ra = np.asarray(ref).astype(np.float32)
        ra[..., 3] *= np.linspace(0.32, 0.0, ra.shape[0])[:, None]
        ref = Image.fromarray(ra.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(2))
        lay = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        lay.alpha_composite(ref, (round(p.x0), round(p.base - 4)))
        la = np.asarray(lay).astype(np.float32)
        la[..., 3] *= TOPM
        img.alpha_composite(Image.fromarray(la.astype(np.uint8), "RGBA"))
        sh = Image.new("L", (PW, PH), 0)
        ImageDraw.Draw(sh).ellipse((p.cx - p.bw * 0.55 - p.w * 0.5, p.base - p.bw * 0.16 - 6, p.cx + p.bw * 0.5, p.base + 2), fill=110)
        sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(12))).astype(np.float32)
        c2 = Image.new("L", (PW, PH), 0)
        ImageDraw.Draw(c2).ellipse((p.cx - p.bw * 0.52, p.base - p.bw * 0.12 - 4, p.cx + p.bw * 0.52, p.base + 1), fill=215)
        c2 = np.asarray(c2.filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
        a = np.maximum(sh, c2) * TOPM
        s = Image.new("RGBA", (PW, PH), (25, 6, 18, 0))
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
VIG = 1 - 0.16 * (((XX - OW / 2) / (OW / 2)) ** 2 + ((YY - OH / 2) / (OH / 2)) ** 2)


class Sparkles:
    """Floating silver/rose sparkles drifting upward."""

    def __init__(self, n=40, seed=9):
        r = np.random.default_rng(seed)
        self.p = np.column_stack([r.uniform(0, OW, n), r.uniform(0, OH, n)])
        self.v = np.column_stack([r.uniform(-8, 8, n), r.uniform(-40, -12, n)])
        self.r = r.uniform(1.5, 4.5, n)
        self.ph = r.uniform(0, 6.28, n)

    def draw(self, arr, t, k=1.0):
        q = Image.new("L", (OW // 2, OH // 2), 0)
        d = ImageDraw.Draw(q)
        for (px, py), (vx, vy), rr, ph in zip(self.p, self.v, self.r, self.ph):
            x, y = ((px + vx * t) % OW) / 2, ((py + vy * t) % OH) / 2
            a = int(255 * (0.25 + 0.75 * max(0.0, math.sin(ph + t * 4))))
            d.ellipse((x - rr / 2, y - rr / 2, x + rr / 2, y + rr / 2), fill=a)
        g = np.asarray(q.filter(ImageFilter.GaussianBlur(1.2)).resize((OW, OH), Image.BILINEAR)).astype(np.float32) / 255
        return screen(arr, g[..., None] * np.array([255, 225, 240.0]) * 0.8 * k)


def flare(arr, x, y, strength):
    """Anamorphic horizontal light streak + glow at (x, y)."""
    if strength <= 0.01:
        return arr
    streak = np.exp(-((YY - y) / 7) ** 2) * np.exp(-np.abs(XX - x) / 420) * strength
    glow = np.exp(-(((XX - x) / 90) ** 2 + ((YY - y) / 90) ** 2)) * strength * 0.8
    return screen(arr, (streak + glow)[..., None] * np.array([255, 215, 235.0]))


def sweep(mask, pos, width=110.0, angle=0.35, strength=0.55):
    return np.exp(-(((XX + YY * angle) - pos) / width) ** 2) * mask * strength


def finish(arr, sharpen=False):
    arr = bloom(arr, threshold=220, radius=28, amount=0.30)
    x = np.clip(arr / 255, 0, 1)
    arr = (x + 0.08 * np.sin(np.pi * x) * (x - 0.5) * 2) * 255
    arr = arr * VIG[..., None] + RNG.normal(0, 1.6, (OH, OW))[..., None]
    out = np.clip(arr, 0, 255).astype(np.uint8)
    if sharpen:
        out = np.asarray(Image.fromarray(out).filter(ImageFilter.UnsharpMask(2.0, 80, 2)))
    return out


def run(products, dur, cam, light=lambda t: 1.0, sweeps=(), flare_fn=None, t0=0.0, sharpen=False, spark=1.0):
    n = round(dur * FPS)
    cfn = lambda t: clamp_cam(*cam(t))
    dt = 1 / (n - 1)
    sp = Sparkles()
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
        # product lit by the same light level as the set (it emerges from the dark in the reveal)
        lv = light(t)
        rgb = rgb * (1 - m[..., None]) + rgb * m[..., None] * (0.25 + 0.75 * min(1.0, lv * 1.15))
        for s0, s1, dr in sweeps:
            u = min(1, max(0, (t - s0) / (s1 - s0)))
            if 0 < u < 1:
                pos = lerp(-500, OW + 1100, ease(u)) if dr > 0 else lerp(OW + 1100, -500, ease(u))
                rgb = screen(rgb, sweep(m, pos)[..., None] * 255)
        if flare_fn:
            fx, fy, fs = flare_fn(t)
            rgb = flare(rgb, fx, fy, fs)
        rgb = sp.draw(rgb, t0 + i / FPS, spark)
        yield finish(rgb, sharpen)


def hero(prod, top_frac=0.20, base_frac=0.66):
    Hh = prod.h / (base_frac - top_frac)
    return prod.base - (base_frac - 0.5) * Hh, Hh


def shot_reveal():
    """Darkness -> a moonbeam sweeps across and the bottle is revealed with a flare, while the camera cranes
    down from the moon and pushes in."""
    p = Product(DL, POD_X, POD_Y + 14, 660)
    cy_h, Hh_h = hero(p)

    def cam(t):
        c = ease_out(min(1, t / 0.45))
        q = ease(t)
        return lerp(POD_X + 60, POD_X, c), lerp(cy_h - 520, cy_h, c) - lerp(0, 30, q), lerp(Hh_h + 260, Hh_h, c) - lerp(0, 120, q), lerp(-1.5, 0, c)

    light = lambda t: lerp(0.18, 1.0, ease(min(1, t / 0.42)))

    def fl(t):
        u = min(1, max(0, (t - 0.28) / 0.35))
        s = math.sin(math.pi * u) * 0.9
        return lerp(OW * 0.95, OW * 0.25, u), OH * 0.30, s
    return run([p], 2.8, cam, light=light, sweeps=((0.30, 0.80, -1),), flare_fn=fl)


def shot_macro():
    """Smooth tilt down the label to its key ingredients."""
    p = Product(DL, POD_X, POD_Y + 14, 660)
    top = p.base - p.h

    def cam(t):
        e = ease_out(t)
        return p.cx, lerp(top + 0.62 * p.h, top + 0.86 * p.h, e), lerp(640, 560, e), lerp(1.4, 0, e)
    return run([p], 1.6, cam, sweeps=((0.05, 0.9, 1),), t0=4.0, sharpen=True, spark=0.5)


SHOTS = {"reveal": shot_reveal, "macro": shot_macro}

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
    else:
        pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in gen:
            pr.stdin.write(f.tobytes())
        pr.stdin.close()
        pr.wait()
