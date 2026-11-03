"""Video 2 (redo) graphics over baseR2b.mov: calm, editorial, sunlit. Nothing shared with Video 1 or the old V2 cut:
- captions: light Jost, the spoken word in full white and the rest of the phrase softly dimmed, rising gently
- product titles: large DM Serif lines that resolve letter by letter, a fine rule and a spaced tag
- benefit call-outs: frosted-glass capsules (the picture behind is blurred and brightened), small orange dot
- ingredient constellation: fine white hexagon outlines joined by drawn lines, spaced labels
- closing words in serif italic; a slow, soft light sweep across each product reveal (no flashes)
Usage: overlay2b.py OUT.mp4 | overlay2b.py SHEET.jpg t1,t2,..."""
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import tl3 as tl

W, H, FPS = 1080, 1920, 24
F = "../../fonts/"
ORANGE, CREAM, INK, WHITE = (238, 112, 22), (255, 236, 210), (52, 34, 20), (255, 255, 255)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = "base3.mov"


def font(n, s):
    return ImageFont.truetype(F + n, s)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


def text_img(s, fnt, fill, tracking=0, pad=20):
    w = sum(fnt.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    asc, desc = fnt.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c in s:
        d.text((x, pad), c, font=fnt, fill=fill)
        x += fnt.getlength(c) + tracking
    return im


def shadow(im, blur=10, alpha=0.5, dy=3):
    sh = Image.new("RGBA", im.size, (20, 12, 6, 0))
    sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, dy))
    out.alpha_composite(im)
    return out


def fade(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.split()[-1].point(lambda v: int(v * max(0, a))))
    return im


def paste(dst, im, cx, cy, a=1.0):
    if a > 0.003:
        dst.alpha_composite(fade(im, a), (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


# ---------------- soft light sweep over the reveals ----------------
def sweep(arr, t):
    return arr          # the product shots carry their own light sweep
    for r in tl.REVEALS:
        p = (t - (r + 0.9)) / 1.6
        if 0 <= p <= 1:
            pos = -500 + eio(p) * (W + H * 0.45 + 1000)
            d = (XX + YY * 0.45) - pos
            band = np.exp(-(d / 150) ** 2) * math.sin(math.pi * p) * 46
            arr = 255 - (255 - arr) * (1 - band[..., None] / 255 * np.array([1.0, 0.94, 0.82]))
    return arr


# ---------------- captions ----------------
CAP_F = font("Jost-Medium.ttf", 52)
CAP_Y = 1610
CHUNKS = tl.caption_chunks()
WORD_SPANS = [(s, e) for _, s, e in tl.WORDS]
_cw = {}
_g = np.clip((np.arange(H) - 1380) / 420, 0, 1) ** 1.6 * 0.42
SCRIM = Image.fromarray(np.dstack([np.full((H, W), 25, np.uint8), np.full((H, W), 16, np.uint8), np.full((H, W), 8, np.uint8),
                                   np.repeat((_g * 255).astype(np.uint8)[:, None], W, 1)]), "RGBA")


def word_im(w, a):
    key = (w, a)
    if key not in _cw:
        _cw[key] = text_img(w, CAP_F, WHITE + (a,), tracking=1, pad=0)
    return _cw[key]


def draw_captions(img, t):
    if t >= tl.CAPTION_UNTIL or any(a <= t < b for a, b in tl.PRODUCT_SPANS) or any(s - 0.1 <= t < e for s, e in WORD_SPANS) or any(s - 0.1 <= t < e for *_, s, e in tl.TITLES):
        return
    for ci, ch in enumerate(CHUNKS):
        s, e = ch[0][1] - 0.12, ch[-1][2]
        nxt = CHUNKS[ci + 1][0][1] - 0.15 if ci + 1 < len(CHUNKS) else e + 0.9
        e_out = min(e + 0.7, nxt)
        if not (s <= t < e_out):
            continue
        a = eo((t - s) / 0.3) * (1 - c01((t - (e_out - 0.25)) / 0.25))
        dy = (1 - eo((t - s) / 0.45)) * 18
        words = [w for w, _, _ in ch]
        sp = CAP_F.getlength(" ") + 2
        ims = []
        for w, ws, we in ch:
            lit = 255 if t >= ws - 0.04 else 170
            ims.append(word_im(w, lit))
        total = sum(i.width for i in ims) + sp * (len(ims) - 1)
        asc, desc = CAP_F.getmetrics()
        layer = Image.new("RGBA", (int(total) + 60, asc + desc + 40), (0, 0, 0, 0))
        x = 30
        for im in ims:
            layer.alpha_composite(im, (int(x), 20))
            x += im.width + sp
        layer = shadow(shadow(layer, blur=14, alpha=0.55, dy=0), blur=4, alpha=0.5, dy=1)
        img.alpha_composite(fade(SCRIM, a))
        paste(img, layer, W / 2, CAP_Y + dy, a)
        _ = words


# ---------------- product titles ----------------
T_F = font("DMSerifDisplay.ttf", 116)
TAG_F = font("Jost-Bold.ttf", 28)


TITLE_Y = [150, 150]
TITLE_COL = [(INK, ORANGE, 0.0), (INK, ORANGE, 0.0)]      # light-on-scrim low, dark editorial on the bright prism set


def draw_titles(img, t):
    for (l1, l2, tag, s, e), ty, (tc, gc, sha) in zip(tl.TITLES, TITLE_Y, TITLE_COL):
        if not (s <= t < e):
            continue
        out = c01((t - (e - 0.45)) / 0.45)
        layer = Image.new("RGBA", (W, 520), (0, 0, 0, 0))
        y = 40
        for j, line in enumerate((l1, l2)):
            x = W / 2 - T_F.getlength(line) / 2
            for k, ch in enumerate(line):
                q = eo((t - s - 0.12 * j - 0.035 * k) / 0.5)
                if q > 0:
                    ci = text_img(ch, T_F, tc + (int(255 * q),), pad=0)
                    layer.alpha_composite(ci, (int(x), int(y + (1 - q) * 14)))
                x += T_F.getlength(ch)
            y += 122
        rp = eo((t - s - 0.5) / 0.6)
        if rp > 0:
            ImageDraw.Draw(layer).line((W / 2 - 120 * rp, y + 34, W / 2 + 120 * rp, y + 34), fill=tc + (220,), width=2)
        ta = eo((t - s - 0.7) / 0.5)
        if ta > 0:
            ti = text_img(tag, TAG_F, gc + (255,), tracking=7, pad=0)
            layer.alpha_composite(fade(ti, ta), (int(W / 2 - ti.width / 2), int(y + 62)))
        if ty > 1000:
            img.alpha_composite(fade(SCRIM, (1 - out) * eo((t - s) / 0.5)))
        img.alpha_composite(fade(shadow(layer, blur=16, alpha=sha, dy=3), 1 - out), (0, ty))


# ---------------- frosted benefit capsules ----------------
PILL_F = font("Jost-SemiBold.ttf", 38)
_pt = {}


def draw_pills(img, t):
    for kind, text, s, e, cy in tl.PILLS:
        if not (s <= t < e):
            continue
        if text not in _pt:
            _pt[text] = text_img(text, PILL_F, INK + (255,), tracking=1, pad=0)
        ti = _pt[text]
        w, h = ti.width + 120, 92
        a = eo((t - s) / 0.4) * (1 - c01((t - (e - 0.3)) / 0.3))
        dy = (1 - eo((t - s) / 0.5)) * 20
        x0, y0 = int(W / 2 - w / 2), int(cy - h / 2 + dy)
        bg = img.crop((x0 - 30, y0 - 30, x0 + w + 30, y0 + h + 30)).filter(ImageFilter.GaussianBlur(18))
        bg = Image.blend(bg.convert("RGB"), Image.new("RGB", bg.size, (255, 250, 244)), 0.62).convert("RGBA")
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=255)
        cap = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        cap.paste(bg.crop((30, 30, 30 + w, 30 + h)), (0, 0), m)
        d = ImageDraw.Draw(cap)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, outline=WHITE + (235,), width=2)
        d.ellipse((34, h / 2 - 9, 52, h / 2 + 9), fill=ORANGE + (255,))
        cap.alpha_composite(ti, (72, int(h / 2 - ti.height / 2 - 3)))
        lay = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
        sh = Image.new("RGBA", lay.size, (60, 40, 20, 0))
        sm = Image.new("L", lay.size, 0)
        ImageDraw.Draw(sm).rounded_rectangle((30, 36, 30 + w, 36 + h), radius=h // 2, fill=70)
        sh.putalpha(sm.filter(ImageFilter.GaussianBlur(14)))
        lay.alpha_composite(sh)
        lay.alpha_composite(cap, (30, 30))
        img.alpha_composite(fade(lay, a), (x0 - 30, y0 - 30))


# ---------------- ingredient constellation ----------------
MOL_F = font("Jost-SemiBold.ttf", 29)


def hexagon(cx, cy, r, rot=0.0):
    return [(cx + r * math.cos(math.radians(60 * k + 30) + rot), cy + r * math.sin(math.radians(60 * k + 30) + rot)) for k in range(7)]


def draw_molecule(img, t):
    nodes, t_end = tl.MOLECULE
    if not (nodes[0][1] <= t < t_end):
        return
    out = c01((t - (t_end - 0.4)) / 0.4)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    shown = [(lab, s, p) for lab, s, p in nodes if t >= s]
    g = np.asarray(img.convert("L"), np.float32)
    lum = np.mean([g[max(0, cy - 60):cy + 140, max(0, cx - 160):cx + 160].mean() for _, _, (cx, cy) in shown])
    C = INK if lum > 175 else WHITE
    for (_, _, pa), (_, sb, pb) in zip(shown[:-1], shown[1:]):
        q = eio((t - sb) / 0.6)
        d.line((pa[0], pa[1], pa[0] + (pb[0] - pa[0]) * q, pa[1] + (pb[1] - pa[1]) * q), fill=C + (170,), width=2)
    for lab, s, (cx, cy) in shown:
        u = t - s
        q = eo(u / 0.6)
        r = 40 + 8 * q
        d.line(hexagon(cx, cy, r, u * 0.25), fill=C + (int(240 * q),), width=3)
        d.line(hexagon(cx, cy, r * 0.62, -u * 0.25), fill=C + (int(130 * q),), width=2)
        rr = 7 + 2 * math.sin(u * 3)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=ORANGE + (int(255 * q),))
        pa = eo((u - 0.25) / 0.5)
        if pa > 0:
            ti = text_img(lab, MOL_F, C + (255,), tracking=5, pad=0)
            lx = min(max(cx - ti.width / 2, 40), W - 40 - ti.width)
            layer.alpha_composite(fade(ti, pa), (int(lx), int(cy + 72 + (1 - pa) * 12)))
    img.alpha_composite(fade(shadow(layer, blur=12, alpha=0.6 if C == WHITE else 0.0, dy=2), 1 - out))


# ---------------- closing words ----------------
WORD_F = font("DMSerifDisplay-Italic.ttf", 132)
_wi = {}


def draw_words(img, t):
    for text, s, e in tl.WORDS:
        if not (s - 0.05 <= t < e):
            continue
        if text not in _wi:
            _wi[text] = shadow(text_img(text, WORD_F, WHITE + (255,), pad=30), blur=18, alpha=0.55, dy=3)
        a = eo((t - s + 0.05) / 0.45) * (1 - c01((t - (e - 0.3)) / 0.3))
        paste(img, _wi[text], W / 2, 1470 + (1 - eo((t - s) / 0.6)) * 16, a)


# ---------------- energy: punch-in on every cut, bright flash on each reveal ----------------
def energy(arr, t):
    for c in tl.CUTS:
        p = (t - c) / 0.4
        if 0 <= p < 1 and c < tl.EC_START - 0.01:
            z = 1 + 0.055 * (1 - eo(p))
            h, w = arr.shape[:2]
            ch, cw = int(round(h / z)), int(round(w / z))
            y0, x0 = (h - ch) // 2, (w - cw) // 2
            arr = cv2.resize(arr[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_CUBIC)
            break
    for r in list(tl.REVEALS) + [tl.EC_START]:
        p = (t - r) / 0.32
        if 0 <= p < 1:
            arr = arr + (255 - arr) * 0.8 * (1 - p) ** 2
    return arr


def compose(frame, t):
    arr = sweep(energy(frame.astype(np.float32), t), t)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    draw_titles(img, t)
    draw_pills(img, t)
    draw_molecule(img, t)
    draw_words(img, t)
    draw_captions(img, t)
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]
    if out.endswith((".jpg", ".png")):
        ts = [float(x) for x in sys.argv[2].split(",")]
        ims = []
        for t in ts:
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", BASE, "-frames:v", "1", "-f", "rawvideo",
                                 "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            ims.append(Image.fromarray(compose(np.frombuffer(fr, np.uint8).reshape(H, W, 3), t)))
        sheet = Image.new("RGB", (432 * len(ims), 768))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((432, 768), Image.LANCZOS), (432 * k, 0))
        sheet.save(out, quality=90)
        sys.exit()
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", BASE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", BASE, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "15", "-preset", "slow",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out],
                          stdin=subprocess.PIPE)
    i = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        wr.stdin.write(compose(np.frombuffer(buf, np.uint8).reshape(H, W, 3), i / FPS).tobytes())
        i += 1
    wr.stdin.close()
    wr.wait()
    print("frames", i)
