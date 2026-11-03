"""Video 7 v2 — "The PalmCare Collection" as a music-led product showcase (client round: the first cut felt dull and
flat; no product explanations; products only in their real packs). Built like the reference: one product at a time,
big and centred, with the set's milk / citrus / gold-gel swirls moving around it.
  hook      lineup of every pack landing on the beat, THE PALMCARE COLLECTION
  sets      each body-care set: a wide establishing push, then a hero push-in on each bottle (camera follows the
            plate's own drift via the comp track, products stay perfectly upright), whip-blur cuts between
  packs     Vita C+, N10, DermaLuxe, GlowShield packs bursting in on gold rays, then the Vitamin C box alone on the
            citrus pedestals
  end card  the collection + "Made with healthy ingredients." + slogan, phones, address, ORDER NOW
Look: richer contrast and warmth, highlight bloom, soft vignette, a light glint sweeping across every hero, a white
flash on the section drops. Text = the product's name only.
Usage: show10.py OUT.mp4 | show10.py SHEET.jpg t1,t2,..."""
import json
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
W, H, FPS = 1080, 1920, 24
BEAT = 60 / 104


def T(b):
    return round(b * BEAT * FPS) / FPS


PLATES = {  # comp10 placements (cutout, cx, base, h) — kept in sync with comp10.CONFIGS
    "P1": [(308, 1318, 840), (768, 1415, 820)],
    "P2": [(368, 1246, 800), (702, 1358, 790)],
    "P3": [(302, 1200, 830), (712, 1322, 800)],
}
# (kind, source, src_start, start_beat, product index / None, name lines)
SHOTS = [("full", "L_hook2.mp4", 0.0, 0, None, None),
         ("wide", "P1", 0.40, 12, None, None),
         ("hero", "P1", None, 16, 0, ("Milky Hydro-Glow", "Moisturising Body Wash")),
         ("hero", "P1", None, 22, 1, ("Cacao & Collagen", "Body Lotion")),
         ("wide", "P2", 0.40, 28, None, None),
         ("hero", "P2", None, 32, 0, ("Citrus Vitamin Glow Infusion", "Body Wash")),
         ("hero", "P2", None, 38, 1, ("Molecular Glow", "Body Lotion")),
         ("wide", "P3", 0.40, 44, None, None),
         ("hero", "P3", None, 48, 0, ("Advanced Tropical Glow", "Exfoliating Lightening Body Wash")),
         ("hero", "P3", None, 54, 1, ("Dermalight", "Body Lotion")),
         ("pack", D + "v6/PS_vitac.mp4", 0.0, 60, None, ("Vita C+ Serum", "")),
         ("pack", D + "v6/PS_n10.mp4", 0.0, 64, None, ("N10 Niacinamide Serum", "")),
         ("pack", D + "v6/PS_derma.mp4", 0.0, 68, None, ("DermaLuxe Pro", "Hydrating Night Repair Serum")),
         ("pack", D + "v8/PS_glow.mp4", 0.0, 72, None, ("GlowShield", "Broad-Spectrum Daily Defense Sunscreen")),
         ("pack", "C_P9B.mp4", 1.0, 78, None, ("Vitamin C", "Face Moisturiser")),
         ("full", "L_end2.mp4", 0.0, 84, None, None)]
END_B = 102
STARTS = [T(s[3]) for s in SHOTS] + [T(END_B)]
TOTAL = STARTS[-1]
DROPS = [T(12), T(60), T(84)]
EC = T(84)

# continuous plate time: the wide + both heroes of a set run straight through the plate
for k, s in enumerate(SHOTS):
    if s[0] == "hero":
        prev = SHOTS[k - 1]
        st = prev[2] + (STARTS[k] - STARTS[k - 1])
        SHOTS[k] = (s[0], s[1], st, s[3], s[4], s[5])
TRACK = {p: [np.array(m, np.float32) for m in json.load(open(f"C_{p}_track.json"))] for p in PLATES}

# ---------- text ----------
FD = D + "fonts/"
GOLD, CREAM = (222, 182, 108), (255, 247, 235)


def text(s, f, fill, tracking=0):
    w = int(sum(f.getlength(c) for c in s) + tracking * max(0, len(s) - 1)) + 40
    a, d = f.getmetrics()
    im = Image.new("RGBA", (w, a + d + 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = 20
    for c in s:
        dr.text((x, 20), c, font=f, fill=fill + (255,))
        x += f.getlength(c) + tracking
    sh = Image.new("RGBA", im.size, (14, 7, 2, 0))
    sh.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.8)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 3))
    out.alpha_composite(im)
    return out


NAMES = {}
for s in SHOTS:
    if s[5]:
        l1, l2 = s[5]
        a = text(l1, ImageFont.truetype(FD + "Cormorant-SemiBold.ttf", 84 if len(l1) < 22 else 70), CREAM)
        b = text(l2, ImageFont.truetype(FD + "Cormorant-Italic.ttf", 50 if len(l2) < 36 else 40), GOLD) if l2 else None
        NAMES[l1] = (a, b)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def paste(dst, im, cx, cy, a):
    if a <= 0.003:
        return
    im = im.copy()
    im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    dst.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ---------- look ----------
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.30 * np.clip(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H * 0.48) / (H * 0.62)) ** 2, 0, 1.4) ** 1.3)[..., None]
_x = np.linspace(0, 1, 256)
LUT = np.clip(255 * (_x + 0.07 * np.sin(2 * np.pi * (_x - 0.5)) * 0.0 + 0.06 * np.sin(2 * np.pi * _x) * -1), 0, 255).astype(np.uint8)   # gentle S-curve


def grade(fr, kind):
    """S-curve contrast, a touch more colour and warmth, highlight bloom, vignette."""
    x = cv2.LUT(fr, LUT).astype(np.float32)
    g = x.mean(2, keepdims=True)
    x = g + (x - g) * (1.10 if kind != "full" else 1.04)
    x *= np.array([0.985, 1.0, 1.035], np.float32)             # BGR warm
    hi = np.clip(x - 175, 0, 255)
    small = cv2.resize(hi, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
    bloom = cv2.resize(cv2.GaussianBlur(small, (0, 0), 7), (W, H), interpolation=cv2.INTER_LINEAR)
    x = 255 - (255 - x) * (1 - bloom / 255 * 0.55)
    if kind != "full":
        x *= VIG
    return x


def glint(x, u):
    """A soft diagonal light glint sweeping across the hero, 0..0.7 s after the cut."""
    if not 0 <= u < 0.7:
        return x
    p = -0.3 + 1.6 * eio(u / 0.7)
    d = (XX[::4, ::4] / W * 0.8 + YY[::4, ::4] / H * 0.6) - p
    band = np.exp(-(d / 0.05) ** 2) * 0.32 * math.sin(math.pi * c01(u / 0.7))
    m = cv2.resize(band.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return 255 - (255 - x) * (1 - m * np.array([0.9, 0.97, 1.0], np.float32))


# ---------- sources ----------
def reader(src, st, dur):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{st:.4f}", "-i", src, "-t", f"{dur + 0.2:.4f}", "-vf",
                          f"fps={FPS},scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         stdout=subprocess.PIPE)
    last = None
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            while True:
                yield last
        last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        yield last


def crop_zoom(fr, cx, cy, z):
    cw, ch = W / z, H / z
    cx = min(max(cx, cw / 2), W - cw / 2)
    cy = min(max(cy, ch / 2), H - ch / 2)
    M = np.float32([[z, 0, -(cx - cw / 2) * z], [0, z, -(cy - ch / 2) * z]])
    return cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def shot_frame(k, fr, u, dur):
    kind, src, st, _, pi, _ = SHOTS[k]
    p = u / dur
    if kind == "wide":
        return crop_zoom(fr, W / 2, H * 0.55, 1.0 + 0.07 * eio(p))
    if kind == "hero":
        fi = min(len(TRACK[src]) - 1, int(round((st + u) * FPS)))
        M = TRACK[src][fi]
        cx, base, h = PLATES[src][pi]
        ax, ay = M @ np.array([cx, base, 1.0], np.float32)
        sc = float(np.sqrt(abs(np.linalg.det(M[:, :2]))))
        z0 = H / (h * sc * 1.42)
        z = z0 * (1.0 + 0.07 * eio(p))
        return crop_zoom(fr, ax, ay - h * sc * 0.47, z)
    if kind == "pack":
        return crop_zoom(fr, W / 2, H * 0.47, 1.0 + 0.06 * eio(p))
    return fr


def transitions(x, t):
    for c in STARTS[1:-1]:                                  # whip blur through every cut
        u = t - c
        if -0.07 < u < 0.07:
            s = 1 - abs(u) / 0.07
            k = int(4 + 70 * s) | 1
            ker = np.full((1, k), 1.0 / k, np.float32)
            x = cv2.filter2D(x, -1, ker)
    for c in DROPS:                                         # white flash on the section drops
        u = t - c
        if 0 <= u < 0.35:
            x = x + (255 - x) * 0.55 * (1 - u / 0.35) ** 2
    return x


def names(img, t, k):
    kind, _, _, _, _, nm = SHOTS[k]
    if not nm:
        return
    s, e = STARTS[k] + 0.25, STARTS[k + 1] - 0.05
    a = c01((t - s) / 0.3) * (1 - c01((t - (e - 0.25)) / 0.25))
    if a <= 0:
        return
    im1, im2 = NAMES[nm[0]]
    u = t - s
    y = 1690 if kind == "hero" else 300                      # packs fill the lower frame: their name sits up top
    ImageDraw.Draw(img).line((W / 2 - 120 * eo(u / 0.5), y - 72, W / 2 + 120 * eo(u / 0.5), y - 72), fill=GOLD + (int(255 * a),), width=2)
    paste(img, im1, W / 2, y - 12 + 14 * (1 - eo(u / 0.45)), a)
    if im2 is not None:
        paste(img, im2, W / 2, y + 60 + 14 * (1 - eo((u - 0.1) / 0.45)), a * c01((u - 0.1) / 0.3))


SCRIM = np.clip((YY[:, :1] - 1450) / 470, 0, 1) ** 1.5
TOPSCRIM = np.clip((520 - YY[:, :1]) / 520, 0, 1) ** 1.3


def render(t_list=None):
    out_frames = {}
    n_total = int(round(TOTAL * FPS))
    want = None if t_list is None else {int(round(t * FPS)) for t in t_list}
    for k in range(len(SHOTS)):
        kind, src, st, _, _, _ = SHOTS[k]
        a, b = int(round(STARTS[k] * FPS)), int(round(STARTS[k + 1] * FPS))
        if want is not None and not any(a <= w < b for w in want):
            continue
        path = f"C_{src}.mp4" if src in PLATES else src
        dur = (b - a) / FPS
        rd = reader(path, st, dur)
        for i in range(a, b):
            fr = next(rd)
            if want is not None and i not in want:
                continue
            t = i / FPS
            u = t - STARTS[k]
            x = grade(shot_frame(k, fr, u, dur), kind)
            if kind in ("hero", "pack"):
                x = glint(x, u - 0.1)
                if SHOTS[k][5]:
                    x = x * (1 - (SCRIM if kind == "hero" else TOPSCRIM)[..., None] * 0.5)
            x = transitions(x, t)
            img = Image.fromarray(cv2.cvtColor(np.clip(x, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)).convert("RGBA")
            names(img, t, k)
            rgb = np.asarray(img.convert("RGB"))
            yield i, rgb
    return n_total


if __name__ == "__main__":
    out = sys.argv[1]
    if out.endswith(".jpg"):
        ts = [float(x) for x in sys.argv[2].split(",")]
        got = dict(render(ts))
        ims = [Image.fromarray(got[int(round(t * FPS))]).resize((300, 533), Image.LANCZOS) for t in ts]
        sheet = Image.new("RGB", (300 * len(ims), 533))
        for j, im in enumerate(ims):
            sheet.paste(im, (300 * j, 0))
        sheet.save(out, quality=90)
        sys.exit()
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = 0
    for i, rgb in render():
        wr.stdin.write(rgb.tobytes())
        n += 1
    wr.stdin.close()
    wr.wait()
    print("frames", n, "TOTAL", TOTAL)
