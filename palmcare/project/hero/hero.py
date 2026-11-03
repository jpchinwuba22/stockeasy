"""PalmCare Video 1 product hero: real bottle cutouts composited on an AI set,
with eased camera moves, light sweeps, contact shadows, dust motes and grain."""
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageFilter

FPS = 24
OW, OH = 1080, 1920
RNG = np.random.default_rng(7)

plate = Image.open("backdrop.png").convert("RGB")
milky = Image.open("milky_cut.png").convert("RGBA")
cacao = Image.open("cacao_cut.png").convert("RGBA")
milky = milky.crop(milky.split()[-1].getbbox())
cacao = cacao.crop(cacao.split()[-1].getbbox())


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * t * (t * (6 * t - 15) + 10)  # smootherstep


def lerp(a, b, t):
    return a + (b - a) * t


def grade_bottle(img, warm=(1.04, 0.985, 0.90), light_from_left=True):
    """Warm the white plastic to match the golden set and add directional falloff."""
    a = np.asarray(img).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3:]
    rgb = rgb * np.array(warm, np.float32)
    w = rgb.shape[1]
    ramp = np.linspace(1.10, 0.86, w, dtype=np.float32) if light_from_left else np.linspace(0.86, 1.10, w, dtype=np.float32)
    rgb = rgb * ramp[None, :, None]
    h = rgb.shape[0]
    ao = np.ones(h, np.float32)
    k = max(1, int(h * 0.07))
    ao[-k:] = np.linspace(1.0, 0.80, k)
    rgb = rgb * ao[:, None, None] + (1 - ao[:, None, None]) * np.array([120, 70, 40], np.float32) * 0.6
    # soft warm rim light on the lit edge
    al = img.split()[-1]
    inner = al.filter(ImageFilter.MinFilter(9))
    edge = np.asarray(ImageChops.subtract(al, inner)).astype(np.float32) / 255.0
    edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255.0
    side = np.linspace(1.0, 0.0, w, dtype=np.float32)[None, :] ** 2
    rim = (edge * side)[..., None] * np.array([255, 226, 180], np.float32) * 0.55
    rgb = 255 - (255 - rgb) * (255 - rim) / 255  # screen
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8), "RGBA")


def sweep(mask, xw, yw, pos, width=220.0, angle=0.35, strength=0.30):
    """Diagonal light band in world coords, limited to the bottle mask (output-sized arrays)."""
    d = (xw + yw * angle) - pos
    band = np.exp(-(d / width) ** 2)
    return band * mask * strength


class Motes:
    def __init__(self, n, w, h):
        self.p = np.column_stack([RNG.uniform(0, w, n), RNG.uniform(0, h, n)])
        self.r = RNG.uniform(3, 11, n)
        self.a = RNG.uniform(0.05, 0.22, n)
        self.v = np.column_stack([RNG.uniform(-6, 6, n), RNG.uniform(-22, -8, n)])

    def draw(self, arr, t, shift_x, shift_y, parallax):
        h, w = arr.shape[:2]
        yy, xx = np.mgrid[0:h:4, 0:w:4]
        acc = np.zeros(xx.shape, np.float32)
        for (px, py), r, a, (vx, vy) in zip(self.p, self.r, self.a, self.v):
            x = (px + vx * t - shift_x * parallax) % w
            y = (py + vy * t - shift_y * parallax) % h
            acc += a * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2 * (r * 2.2) ** 2)))
        acc = np.asarray(Image.fromarray(np.clip(acc * 255, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32) / 255
        glow = acc[..., None] * np.array([255, 236, 205], np.float32)
        return 255 - (255 - arr) * (255 - glow) / 255


def finish(arr, frame_idx):
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vig = 1 - 0.16 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) ** 1.3
    arr = arr * np.clip(vig, 0.6, 1)[..., None]
    arr = arr + RNG.normal(0, 2.4, arr.shape[:2])[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


# ---------- world for the wide pedestal shot ----------
S = 2048 / plate.height
world = plate.resize((round(plate.width * S), 2048), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2))
WW, WH = world.size
ped_cx, ped_top = 1884, 1511

def place(img, height):
    s = height / img.height
    return grade_bottle(img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS))

wash_w = place(milky, 900)
lot_w = place(cacao, 720)
placements = [(wash_w, ped_cx - 150, ped_top - 38), (lot_w, ped_cx + 150, ped_top + 6)]  # (img, center x, bottom y)

world_rgba = world.convert("RGBA")
mask_world = Image.new("L", world.size, 0)
for img, cx, by in placements:
    x0, y0 = round(cx - img.width / 2), round(by - img.height)
    al = img.split()[-1]
    # cast shadow: flatten the silhouette onto the stone, pushed right and back (key light from left)
    sh_h = max(1, round(img.height * 0.16))
    sh = al.resize((img.width, sh_h)).transform((img.width + 260, sh_h), Image.AFFINE, (1, -1.4, 0, 0, 1, 0)).filter(ImageFilter.GaussianBlur(14))
    shadow = Image.new("RGBA", sh.size, (60, 38, 22, 0))
    shadow.putalpha(sh.point(lambda v: int(v * 0.38)))
    world_rgba.alpha_composite(shadow, (x0 + 10, by - sh_h + 6))
    # contact shadow
    cs = Image.new("L", (img.width + 60, 60), 0)
    cs.paste(255, (24, 24, img.width + 40, 36))
    cs = cs.filter(ImageFilter.GaussianBlur(7))
    cshadow = Image.new("RGBA", cs.size, (34, 20, 12, 0))
    cshadow.putalpha(cs.point(lambda v: int(v * 0.85)))
    world_rgba.alpha_composite(cshadow, (x0 - 24, by - 34))
    wide = Image.new("L", (img.width + 200, 120), 0)
    wide.paste(255, (90, 50, img.width + 140, 70))
    wide = wide.filter(ImageFilter.GaussianBlur(30))
    wshadow = Image.new("RGBA", wide.size, (50, 30, 18, 0))
    wshadow.putalpha(wide.point(lambda v: int(v * 0.45)))
    world_rgba.alpha_composite(wshadow, (x0 - 70, by - 64))
for img, cx, by in placements:
    x0, y0 = round(cx - img.width / 2), round(by - img.height)
    world_rgba.alpha_composite(img, (x0, y0))
    mask_world.paste(img.split()[-1], (x0, y0), img.split()[-1])
world_rgb = world_rgba.convert("RGB")


def render_window(src_rgb, src_mask, cx, cy, H):
    Wd = H * OW / OH
    box = (cx - Wd / 2, cy - H / 2, cx + Wd / 2, cy + H / 2)
    rgb = np.asarray(src_rgb.transform((OW, OH), Image.EXTENT, box, Image.BICUBIC)).astype(np.float32)
    m = np.asarray(src_mask.transform((OW, OH), Image.EXTENT, box, Image.BILINEAR)).astype(np.float32) / 255
    u = np.linspace(box[0], box[2], OW, dtype=np.float32)[None, :]
    v = np.linspace(box[1], box[3], OH, dtype=np.float32)[:, None]
    return rgb, m, u, v


def shot_wide(dur):
    motes = Motes(26, OW, OH)
    n = round(dur * FPS)
    for i in range(n):
        t = i / (n - 1)
        e = ease(t)
        H = lerp(1650, 1900, e)
        cx = lerp(1250, ped_cx, e)
        cy = ped_top + 0.5 * H - 0.72 * H
        rgb, m, u, v = render_window(world_rgb, mask_world, cx, cy, H)
        pos = lerp(1300, 2700, ease(min(1, max(0, (t - 0.35) / 0.65))))
        s = sweep(m, u, v, pos, width=180, strength=0.33)[..., None]
        rgb = 255 - (255 - rgb) * (1 - s)
        rgb = motes.draw(rgb, i / FPS, cx - 1250, 0, 1.35)
        yield finish(rgb, i)


def shot_macro(bottle, dur, Hb, y_from, y_to, x_off, rot_from, rot_to, sweep_dir, bg_x):
    big = grade_bottle(bottle.resize((round(bottle.width * Hb / bottle.height), Hb), Image.LANCZOS))
    big = big.filter(ImageFilter.UnsharpMask(2, 70, 2))
    bg = plate.crop((bg_x, 250, bg_x + 640, 1138)).resize((OW + 200, OH + 200), Image.BICUBIC).filter(ImageFilter.GaussianBlur(26))
    motes = Motes(18, OW, OH)
    n = round(dur * FPS)
    for i in range(n):
        t = i / (n - 1)
        e = ease(t)
        canvas = bg.crop((round(100 + 60 * (e - 0.5)), 100, round(100 + 60 * (e - 0.5)) + OW, 100 + OH)).convert("RGBA")
        rot = lerp(rot_from, rot_to, e)
        b = big.rotate(rot, Image.BICUBIC, expand=True)
        y = lerp(y_from, y_to, e)
        x = (OW - b.width) / 2 + x_off
        canvas.alpha_composite(b.crop((round(-x), round(-y), round(-x) + OW, round(-y) + OH)))
        rgb = np.asarray(canvas.convert("RGB")).astype(np.float32)
        m = np.asarray(b.split()[-1].crop((round(-x), round(-y), round(-x) + OW, round(-y) + OH))).astype(np.float32) / 255
        u = np.arange(OW, dtype=np.float32)[None, :]
        v = np.arange(OH, dtype=np.float32)[:, None]
        pos = lerp(-400, OW + 1400, t) if sweep_dir > 0 else lerp(OW + 1400, -400, t)
        s = sweep(m, u, v, pos, width=170, angle=0.45, strength=0.28)[..., None]
        rgb = 255 - (255 - rgb) * (1 - s)
        rgb = motes.draw(rgb, i / FPS, 0, y, 0.25)
        yield finish(rgb, i)


def shots():
    # 1. Milky Hydro-Glow label macro: tilt down the label from the logo to the milk swirl
    yield from shot_macro(milky, 1.9, 2500, -260, -760, 170, 3.0, 1.2, +1, 150)
    # 2. Cacao & Collagen macro: rise up the label to the brand name, opposite roll
    yield from shot_macro(cacao, 1.9, 2600, -1000, -480, -170, -2.6, -1.0, -1, 950)
    # 3. Wide reveal: truck right off the palm shadows, pull back onto the duo on the pedestal
    yield from shot_wide(3.4)


if __name__ == "__main__":
    out = sys.argv[1]
    if out.endswith(".jpg"):  # test frames: sheet of chosen frame indices
        idx = set(int(x) for x in sys.argv[2].split(","))
        frames = []
        for k, f in enumerate(shots()):
            if k in idx:
                Image.fromarray(f).save(f"test_{k}.jpg", quality=92)
                frames.append(Image.fromarray(f).resize((270, 480)))
            if k >= max(idx):
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
