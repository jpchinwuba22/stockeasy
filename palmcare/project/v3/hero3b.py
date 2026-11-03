"""PalmCare Video 3 product unveiling, bright high-key version: real bottle cutouts in a luminous
ivory-peach studio, swift camera moves (whip-ins, pull-out reveal, crane-down) with motion blur that
settle into slow pushes, soft palm-shadow gobo and light sweeps. Usage: hero3b.py SHOT OUT.mp4|OUT.jpg"""
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from hero3 import FPS, OH, OW, Dust, ease, ease_out, glow, gobo_mask, grade, lerp, screen, vitac

RNG = np.random.default_rng(31)
TOP, MID, LOW = np.array([253, 241, 227.0]), np.array([248, 222, 196.0]), np.array([236, 200, 168.0])


def bright_bg(w, h, floor_frac=0.78, glow_x=0.6):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = (yy / h)[..., None]
    bg = np.where(v < 0.5, TOP + (MID - TOP) * (v / 0.5), MID + (LOW - MID) * ((v - 0.5) / 0.5))
    d = np.sqrt(((xx - w * glow_x) / w) ** 2 + ((yy - h * 0.38) / h * 0.8) ** 2)[..., None]
    bg = bg + np.clip(0.55 - d, 0, 1) * np.array([20, 16, 10.0])
    floor = (yy > h * floor_frac)[..., None]
    bg = np.where(floor, bg * 0.93, bg)
    return np.clip(bg + np.exp(-((yy - h * floor_frac) / 18) ** 2)[..., None] * 10, 0, 255)


def light_grade(img, key_from_right=True):
    """Bright, neutral-warm grade for the products in a high-key set."""
    return grade(img, warm=(1.02, 0.995, 0.965), key_from_right=key_from_right)


def finish(arr):
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    vig = 1 - 0.06 * (((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH / 2) / (OH / 2)) ** 2)
    arr = arr * vig[..., None] + RNG.normal(0, 1.6, (OH, OW))[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


def motion_blur(arr, vx, vy, taps=7):
    """Directional blur along the frame's camera velocity (px/frame)."""
    if abs(vx) + abs(vy) < 1.5:
        return arr
    acc = np.zeros_like(arr)
    for k in range(taps):
        f = (k / (taps - 1) - 0.5) * 0.9
        acc += np.roll(np.roll(arr, int(round(vx * f)), axis=1), int(round(vy * f)), axis=0)
    return acc / taps


def zoom_blur(arr, rate, taps=5):
    """Radial blur for fast zooms (rate = relative scale change per frame)."""
    if abs(rate) < 0.01:
        return arr
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    acc = np.zeros_like(arr)
    for k in range(taps):
        s = 1 + abs(rate) * (k / (taps - 1)) * 0.9
        w, h = round(OW * s), round(OH * s)
        r = im.resize((w, h), Image.BILINEAR)
        acc += np.asarray(r.crop(((w - OW) // 2, (h - OH) // 2, (w - OW) // 2 + OW, (h - OH) // 2 + OH))).astype(np.float32)
    return acc / taps


def compose_product(bottle, H, key_from_right):
    """Bright seamless frame with one product standing on the floor line, plus reflection and shadows."""
    g = light_grade(bottle, key_from_right).filter(ImageFilter.UnsharpMask(2, 60, 2))
    b = g.resize((round(g.width * H / g.height), round(H)), Image.LANCZOS)
    return b


class Stage:
    """A wide bright world with products placed; the camera crops a 9:16 window from it."""

    def __init__(self, items, W=1800, Hh=3200, floor_frac=0.80, plinth=None):
        self.W, self.H = W, Hh
        world = Image.fromarray(bright_bg(W, Hh, floor_frac).astype(np.uint8)).convert("RGBA")
        mask = Image.new("L", (W, Hh), 0)
        floor_y = Hh * floor_frac
        if plinth:
            cx, top, rw, depth = plinth
            self._plinth(world, cx, top, rw, depth)
        for b, cx, by in items:
            x0, y0 = round(cx - b.width / 2), round(by - b.height)
            sh = Image.new("L", (b.width + 500, 200), 0)
            ImageDraw.Draw(sh).ellipse((170, 70, b.width + 330, 130), fill=170)
            s = Image.new("RGBA", sh.size, (120, 70, 40, 0))
            s.putalpha(sh.filter(ImageFilter.GaussianBlur(34)))
            world.alpha_composite(s, (x0 - 300, round(by - 105)))
            cs = Image.new("L", (b.width + 60, 60), 0)
            ImageDraw.Draw(cs).ellipse((16, 22, b.width + 44, 40), fill=210)
            c = Image.new("RGBA", cs.size, (90, 50, 26, 0))
            c.putalpha(cs.filter(ImageFilter.GaussianBlur(7)))
            world.alpha_composite(c, (x0 - 30, round(by - 34)))
            if not plinth:
                ref = b.transpose(Image.FLIP_TOP_BOTTOM)
                fade = np.linspace(0.30, 0.0, ref.height, dtype=np.float32) ** 1.5
                ref.putalpha(Image.fromarray((np.asarray(ref.split()[-1]).astype(np.float32) * fade[:, None]).astype(np.uint8)))
                world.alpha_composite(ref.filter(ImageFilter.GaussianBlur(3)), (x0, round(by)))
            world.alpha_composite(b, (x0, y0))
            mask.paste(b.split()[-1], (x0, y0), b.split()[-1])
        self.rgb, self.mask, self.floor_y = world.convert("RGB"), mask, floor_y

    def _plinth(self, world, cx, top, rw, depth):
        """Ivory travertine cylinder drawn in perspective (top ellipse + shaded side)."""
        eh = rw * 0.22
        side = Image.new("RGBA", (round(rw * 2), round(depth + eh)), (0, 0, 0, 0))
        sa = np.zeros((side.height, side.width, 4), np.float32)
        xs = np.linspace(-1, 1, side.width, dtype=np.float32)
        shade = 0.80 + 0.17 * (xs + 1) / 2 - 0.10 * xs ** 8
        col = np.array([238, 226, 210.0])
        sa[..., :3] = col * shade[None, :, None] + RNG.normal(0, 3, (side.height, side.width, 1))
        sa[..., 3] = 255
        side = Image.fromarray(np.clip(sa, 0, 255).astype(np.uint8), "RGBA")
        m = Image.new("L", side.size, 0)
        dm = ImageDraw.Draw(m)
        dm.rectangle((0, eh / 2, side.width, depth + eh / 2), fill=255)
        dm.ellipse((0, depth, side.width, depth + eh), fill=255)
        side.putalpha(m)
        sh = Image.new("L", (side.width + 400, 220), 0)
        ImageDraw.Draw(sh).ellipse((120, 70, side.width + 280, 160), fill=160)
        s = Image.new("RGBA", sh.size, (120, 70, 40, 0))
        s.putalpha(sh.filter(ImageFilter.GaussianBlur(40)))
        world.alpha_composite(s, (round(cx - rw - 260), round(top + depth - 40)))
        world.alpha_composite(side, (round(cx - rw), round(top - eh / 2)))
        topi = Image.new("RGBA", (round(rw * 2), round(eh)), (0, 0, 0, 0))
        ImageDraw.Draw(topi).ellipse((0, 0, topi.width, topi.height), fill=(250, 243, 233, 255))
        world.alpha_composite(topi, (round(cx - rw), round(top - eh / 2)))

    def window(self, cx, cy, Hh):
        Wd = Hh * OW / OH
        box = (cx - Wd / 2, cy - Hh / 2, cx + Wd / 2, cy + Hh / 2)
        rgb = np.asarray(self.rgb.transform((OW, OH), Image.EXTENT, box, Image.BICUBIC)).astype(np.float32)
        m = np.asarray(self.mask.transform((OW, OH), Image.EXTENT, box, Image.BILINEAR)).astype(np.float32) / 255
        return rgb, m


def sweep(mask, pos, width=160.0, angle=0.45, strength=0.38):
    u = np.arange(OW, dtype=np.float32)[None, :]
    v = np.arange(OH, dtype=np.float32)[:, None]
    return np.exp(-(((u + v * angle) - pos) / width) ** 2) * mask * strength


def run(stage, dur, cam, gobo=None, sweep_t=(0.35, 1.0), sweep_dir=1, zoom_fast=False):
    """cam(t) -> (cx, cy, Hh) in world px. Motion/zoom blur is derived from the camera's speed."""
    dust = Dust(30)
    n = round(dur * FPS)
    prev = cam(0.0)
    for i in range(n):
        t = i / (n - 1)
        cx, cy, Hh = cam(t)
        rgb, m = stage.window(cx, cy, Hh)
        if gobo:
            gm = gobo(t)
            rgb = rgb * (1 - 0.16 * gm[..., None])
        st = min(1, max(0, (t - sweep_t[0]) / (sweep_t[1] - sweep_t[0])))
        pos = lerp(-600, OW + 1700, ease(st)) if sweep_dir > 0 else lerp(OW + 1700, -600, ease(st))
        rgb = screen(rgb, sweep(m, pos)[..., None] * 255)
        scale = OH / Hh
        vx, vy = (prev[0] - cx) * scale, (prev[1] - cy) * scale
        rgb = motion_blur(rgb, vx, vy)
        if zoom_fast:
            rgb = zoom_blur(rgb, (prev[2] - Hh) / Hh)
        prev = (cx, cy, Hh)
        rgb = dust.draw(rgb, i / FPS)
        yield finish(rgb)


def gobo_drift(a0, a1, x0, x1, y0, y1):
    return lambda t: gobo_mask(lerp(a0, a1, t), lerp(x0, x1, t), lerp(y0, y1, t), 1.2, 14)


def shot_vitac():
    """Whip-in from the left, landing on the bottle, then a slow push as light sweeps across."""
    b = compose_product(vitac, 1300, True)
    st = Stage([(b, 1800, 3200 * 0.80)], W=3600)
    fy = 3200 * 0.80

    def cam(t):
        w = ease_out(min(1, t / 0.22))
        p = ease(t)
        Hh = lerp(1900, 1650, p)
        return lerp(650, 1800, w) + lerp(0, 20, p), fy - 0.32 * Hh, Hh
    return run(st, 2.6, cam, gobo_drift(-20, -12, 1100, 300, 300, 420), (0.30, 0.95), 1)


def shot_glow_reveal():
    """Starts inside the palm logo of the tube and pulls out fast to reveal the whole tube."""
    b = compose_product(glow, 1250, False)
    st = Stage([(b, 900, 3200 * 0.80)])
    fy = 3200 * 0.80
    logo_y = fy - 1250 * 0.62

    def cam(t):
        z = ease_out(min(1, t / 0.55))
        Hh = lerp(330, 1820, z) + lerp(0, -60, ease(t))
        cy = lerp(logo_y, fy - 0.33 * Hh, z)
        return 900, cy, Hh
    return run(st, 1.8, cam, gobo_drift(14, 8, -100, 500, 400, 520), (0.45, 1.0), -1, zoom_fast=True)


def shot_glow():
    """Whip-in from the right onto the tube, slow push and a counter light sweep."""
    b = compose_product(glow, 1250, False)
    st = Stage([(b, 1800, 3200 * 0.80)], W=3600)
    fy = 3200 * 0.80

    def cam(t):
        w = ease_out(min(1, t / 0.22))
        p = ease(t)
        Hh = lerp(1800, 1600, p)
        return lerp(2950, 1800, w) - lerp(0, 20, p), fy - 0.33 * Hh, Hh
    return run(st, 2.4, cam, gobo_drift(16, 8, -100, 700, 340, 520), (0.30, 0.95), -1)


def shot_macro():
    """Fast tilt down the Glowshield label that brakes onto 'SPF 50+ PA++++'."""
    b = compose_product(glow, 3100, False)
    st = Stage([(b, 900, 4200)], W=1800, Hh=4600, floor_frac=0.93)
    top = 4200 - 3100

    def cam(t):
        e = ease_out(t)
        return 900, lerp(top + 900, top + 2150, e), 1500
    return run(st, 1.4, cam, gobo_drift(-18, -10, 300, 820, 700, 1100), (0.0, 0.8), -1)


def shot_duo():
    """Crane down onto both products on an ivory plinth, then a slow push in."""
    vb = compose_product(vitac, 760, True)
    gb = compose_product(glow, 700, False)
    W, Hh0 = 1800, 3200
    top = 2050
    st = Stage([(vb, 760, top + 6), (gb, 1060, top + 34)], W, Hh0, floor_frac=0.86, plinth=(905, top + 20, 480, 300))

    def cam(t):
        c = ease_out(min(1, t / 0.4))
        p = ease(t)
        Hh = lerp(2050, 1650, p)
        return 905 + lerp(-30, 20, p), lerp(top - 1000, top - 0.18 * Hh, c), Hh
    return run(st, 3.2, cam, gobo_drift(-28, -14, 900, 380, 480, 700), (0.35, 1.0), 1)


SHOTS = {"vitac": shot_vitac, "glowrev": shot_glow_reveal, "glow": shot_glow, "macro": shot_macro, "duo": shot_duo}

if __name__ == "__main__":
    name, out = sys.argv[1], sys.argv[2]
    gen = SHOTS[name]()
    if out.endswith(".jpg"):
        frames = list(gen)
        pick = [frames[1], frames[len(frames) // 4], frames[len(frames) // 2], frames[-1]]
        sheet = Image.new("RGB", (270 * 4, 480))
        for k, f in enumerate(pick):
            sheet.paste(Image.fromarray(f).resize((270, 480)), (270 * k, 0))
        sheet.save(out)
    else:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in gen:
            p.stdin.write(f.tobytes())
        p.stdin.close()
        p.wait()
