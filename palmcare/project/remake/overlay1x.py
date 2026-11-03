"""Video 1 'Editorial Luxe' graphics + transitions over baseR1x.mov:
- transitions at the cuts: golden light leaks, blur zoom-throughs
- kinetic captions: words land one by one as they are spoken; key words in gold serif italic
- editorial product titles at the two hero reveals (mask-wiped serif, gold rule)
- ingredient tags pinned to the still bottles, a 24H count-up, minimal benefit lines
- end card on the live packshot: logo, slogan, product names, order button and contact panel
Usage: overlay1x.py OUT.mp4 | overlay1x.py SHEET.jpg t1,t2,..."""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

os.environ.setdefault("TLMOD", "tl1x")
sys.path.insert(0, ".")
import overlayR as base  # noqa: E402
import overlay1r as o1   # noqa: E402  (glass panels, pinned tags)

tl = base.tl
_argv = sys.argv
sys.argv = [sys.argv[0], "x.jpg", "6.0"]
os.environ.setdefault("PCV", "1")
import endcardR as ec    # noqa: E402  (logo, order button, contact panel)
sys.argv = _argv
ec.PH1 = ec.text_img("0903 055 5424", ec.fp, ec.WHITE, tracking=1, shadow=0.4)
ec.PH2 = ec.text_img("0809 361 2901", ec.fp, ec.WHITE, tracking=1, shadow=0.4)
ec.PANEL = (90, 1676, 1080 - 90, 1856)     # lower than the still-image card: the bottles stand above it

W, H, FPS = 1080, 1920, 24
F = "../fonts/"
GOLD, HL, WHITE, CREAM = (226, 182, 118), (246, 197, 111), (255, 252, 246), (246, 230, 206)
c01, eo, eob, paste, shadowed, text_img = base.c01, base.eo, base.eob, base.paste, base.shadowed, base.text_img
fade = o1.fade


def font(name, size):
    return ImageFont.truetype(F + name, size)


def ease_io(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)

# ---------------- transitions ----------------


def light_leak(arr, s, x_frac, big=False):
    """Additive warm light leak: soft amber blob + a brighter core sweeping across."""
    cx = W * x_frac
    cy = H * (0.35 if big else 0.45)
    r = (900 if big else 700)
    d2 = ((XX - cx) / r) ** 2 + ((YY - cy) / (r * 1.35)) ** 2
    g = np.exp(-d2 * 2.2)[..., None]
    core = np.exp(-d2 * 9.0)[..., None]
    col = np.array([255, 176, 92], np.float32)
    add = g * col * (0.95 if big else 0.75) + core * np.array([255, 236, 200], np.float32) * (0.9 if big else 0.5)
    out = 255 - (255 - arr) * (1 - np.clip(add * s / 255, 0, 1))     # screen blend
    return out


def zoom_blur(arr, s):
    """Radial zoom blur toward the centre (strength 0..1)."""
    if s <= 0.02:
        return arr
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    acc = arr.astype(np.float32).copy()
    n = 6
    for k in range(1, n):
        z = 1 + 0.16 * s * k / n
        w, h = int(W * z), int(H * z)
        big = im.resize((w, h), Image.BILINEAR).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))
        acc += np.asarray(big).astype(np.float32)
    out = acc / n
    return out * (1 + 0.12 * s)


def apply_transitions(arr, t):
    for k, cut in enumerate(tl.CUTS, start=1):
        kind = tl.TRANS.get(k, "cut")
        dt = t - cut
        if kind in ("leak", "leak2"):
            span = 0.55 if kind == "leak2" else 0.4
            if abs(dt) < span:
                s = (1 - abs(dt) / span) ** 1.4
                arr = light_leak(arr, s, 0.15 + 0.7 * c01((dt + span) / (2 * span)), big=kind == "leak2")
        elif kind == "zoom":
            if abs(dt) < 0.22:
                arr = zoom_blur(arr, (1 - abs(dt) / 0.22) ** 1.2)
    # end: gentle fade from the last frames is not wanted (end card holds); first frame dip comes from the base
    return arr


# ---------------- kinetic captions ----------------
CAP_SANS = font("Montserrat-ExtraBold.ttf", 60)
CAP_SERIF = font("Playfair-Italic.ttf", 70)
CAP_Y = 1650
KEY = {"palmcare", "milky", "hydro-glow", "cacao", "collagen", "peptides", "niacinamide", "vitamin", "e", "hydration",
       "complex", "24-hour", "radiant", "glow", "creamy", "smooth", "soft", "hydrated", "moisture", "confidence",
       "morning", "gently", "greasy", "absorbing", "me", "skin"}
CHUNKS = tl.caption_chunks()
_word = {}


def is_key(w):
    return w.lower().strip(".,…") in KEY


def word_img(w):
    if w in _word:
        return _word[w]
    if is_key(w):
        # gold-gradient serif italic over a dark outline
        im = text_img(w, CAP_SERIF, (30, 16, 6), pad=24, stroke=3, stroke_fill=(30, 16, 6, 255)).copy()
        top = np.asarray(text_img(w, CAP_SERIF, (255, 255, 255), pad=24)).astype(np.float32)
        g = np.linspace(0, 1, top.shape[0])[:, None, None]
        top[..., :3] = np.array((255, 236, 196), np.float32) * (1 - g) + np.array((226, 160, 80), np.float32) * g
        im.alpha_composite(Image.fromarray(top.astype(np.uint8), "RGBA"))
        base_y = 6          # serif sits slightly lower to share the baseline
    else:
        im = text_img(w, CAP_SANS, WHITE, pad=24, stroke=3, stroke_fill=(24, 12, 4, 255))
        base_y = 0
    im = shadowed(im, blur=12, alpha=0.8, dy=4)
    _word[w] = (im, base_y)
    return _word[w]


def chunk_layout(ci):
    words = [w[0] for w in CHUNKS[ci]]
    ims = [word_img(w) for w in words]
    gap = 2
    widths = [im.width - 48 for im, _ in ims]
    total = sum(widths) + 16 * (len(words) - 1)
    scale = min(1.0, 1000 / total)
    x = W / 2 - total * scale / 2
    pos = []
    for (im, by), w in zip(ims, widths):
        pos.append((x + w * scale / 2, by))
        x += (w + 16) * scale
    return ims, pos, scale


def caption_band(img, a):
    if a <= 0:
        return
    band = np.clip((YY[1380:, :1] - 1380) / 380, 0, 1) ** 1.2 * 0.5 * a
    layer = np.zeros((H - 1380, W, 4), np.uint8)
    layer[..., :3] = (18, 10, 4)
    layer[..., 3] = (band * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(layer, "RGBA"), (0, 1380))


def draw_captions(img, t):
    if t >= tl.CAPTION_UNTIL - 0.05:
        return
    for ci, ch in enumerate(CHUNKS):
        s, e = ch[0][1] - 0.06, ch[-1][2]
        nxt = CHUNKS[ci + 1][0][1] - 0.08 if ci + 1 < len(CHUNKS) else e + 0.6
        e_out = min(e + 0.5, nxt)
        cut = next((c for c in tl.CUTS if c > e), None)
        if cut is not None and cut < e_out:     # a finished line never spills into the next shot
            e_out = cut - 0.01
        if not (s <= t < e_out):
            continue
        out = c01((t - (e_out - 0.14)) / 0.14)
        caption_band(img, eo((t - s) / 0.2) * (1 - out))
        ims, pos, sc = chunk_layout(ci)
        for k, ((im, by), (cx, _), (w, ws, we)) in enumerate(zip(ims, pos, ch)):
            p = eo((t - (ws - 0.05)) / 0.2)
            if p <= 0:
                continue
            pop = 1 + 0.06 * math.sin(math.pi * c01((t - ws) / 0.3)) if is_key(w) else 1
            paste(img, im, cx, CAP_Y + by + (1 - p) * 18 - out * 10, p * (1 - out), sc * pop)


# ---------------- editorial product titles ----------------
_title = {}


def title_parts(k):
    if k in _title:
        return _title[k]
    pre, l1, l2, sub = tl.EDIT_TITLES[k][:4]
    a = text_img(pre, font("Montserrat-SemiBold.ttf", 26), GOLD, tracking=10, pad=10)
    big = font("Cormorant-SemiBold.ttf", 108)
    b1 = shadowed(text_img(l1, big, WHITE, pad=14), blur=14, alpha=0.6, dy=3)
    b2 = shadowed(text_img(l2, font("Playfair-Italic.ttf", 94), HL, pad=14), blur=14, alpha=0.6, dy=3)
    c = shadowed(text_img(sub, font("Montserrat-Bold.ttf", 27), CREAM, tracking=7, pad=10), blur=8, alpha=0.6, dy=2)
    _title[k] = (a, b1, b2, c)
    return _title[k]


def wipe_up(im, p):
    """Reveal from the bottom edge upward (text rising out of a mask)."""
    if p >= 0.999:
        return im, 0
    h = im.height
    off = int((1 - p) * h * 0.6)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(im, (0, off))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rectangle((0, 0, im.width, h), fill=int(255 * min(1, p * 1.5)))
    out.putalpha(Image.fromarray(np.minimum(np.asarray(out.split()[-1]), np.asarray(m))))
    return out, 0


def draw_titles(img, t):
    for k, (pre, l1, l2, sub, s, e, x0, y0) in enumerate(tl.EDIT_TITLES):
        if not (s <= t < e):
            continue
        a, b1, b2, c = title_parts(k)
        u = t - s
        out = c01((t - (e - 0.35)) / 0.35)
        al = 1 - eo(out)
        dy = -eo(out) * 30
        # soft top shade for legibility
        sh = np.clip((480 + y0 - YY[:700 + y0, :1]) / 480, 0, 1) ** 1.6 * 0.45 * eo(u / 0.4) * al
        layer = np.zeros((700 + y0, W, 4), np.uint8)
        layer[..., :3] = (20, 11, 4)
        layer[..., 3] = (sh * 255).astype(np.uint8)
        img.alpha_composite(Image.fromarray(layer, "RGBA"))
        pa = eo(u / 0.35)
        img.alpha_composite(fade(a, pa * al), (int(x0 - 10 + (1 - pa) * -20), int(y0 + dy)))
        for im, yy, d0 in ((b1, y0 + 30, 0.12), (b2, y0 + 136, 0.3)):
            p = eo((u - d0) / 0.55)
            if p > 0:
                w_, _ = wipe_up(im, p)
                img.alpha_composite(fade(w_, al), (int(x0 - 14), int(yy + dy)))
        lp = eo((u - 0.55) / 0.5)
        if lp > 0:
            d = ImageDraw.Draw(img)
            d.line((x0, y0 + 262 + dy, x0 + 460 * lp, y0 + 262 + dy), fill=GOLD + (int(230 * al),), width=3)
        pc = eo((u - 0.75) / 0.4)
        if pc > 0:
            img.alpha_composite(fade(c, pc * al), (int(x0 - 10), int(y0 + 272 + dy + (1 - pc) * 12)))


# ---------------- 24H count-up ----------------


def draw_count(img, t):
    if not getattr(tl, "COUNT", None):
        return
    s, e, cx, cy = tl.COUNT
    if not (s <= t < e):
        return
    u = t - s
    out = c01((t - (e - 0.3)) / 0.3)
    al = eo(u / 0.25) * (1 - eo(out))
    n = int(round(24 * eo(u / 1.0)))
    num = shadowed(text_img(f"{n}", font("Playfair-Italic.ttf", 210), HL, pad=20), blur=16, alpha=0.7, dy=4)
    hr = shadowed(text_img("HR", font("Montserrat-ExtraBold.ttf", 54), WHITE, tracking=4, pad=10), blur=10, alpha=0.7)
    lab = shadowed(text_img("DEEP MOISTURE", font("Montserrat-Bold.ttf", 30), CREAM, tracking=8, pad=10), blur=8, alpha=0.7)
    ref = text_img("24", font("Playfair-Italic.ttf", 210), HL, pad=20)       # fixed width so digits do not jitter
    x = cx - (ref.width + hr.width) / 2
    sc = 0.85 + 0.15 * eob(u / 0.4)
    paste(img, num, x + ref.width / 2, cy, al, sc)
    paste(img, hr, x + ref.width + hr.width / 2 - 10, cy + 40, al)
    lp = eo((u - 0.3) / 0.4)
    d = ImageDraw.Draw(img)
    if lp > 0:
        d.line((cx - 200 * lp, cy + 130, cx + 200 * lp, cy + 130), fill=GOLD + (int(220 * al),), width=2)
    paste(img, lab, cx, cy + 165, al * eo((u - 0.4) / 0.4))


# ---------------- minimal benefit lines ----------------
_ben = {}


def draw_benefits(img, t):
    for title, s, e, cx, cy in getattr(tl, "BENEFITS", []):
        if not (s <= t < e):
            continue
        if title not in _ben:
            _ben[title] = shadowed(text_img(title, font("Montserrat-ExtraBold.ttf", 40), WHITE, tracking=6, pad=12),
                                   blur=12, alpha=0.85, dy=3)
        im = _ben[title]
        u = t - s
        out = c01((t - (e - 0.3)) / 0.3)
        al = 1 - eo(out)
        p = eo(u / 0.45)
        d = ImageDraw.Draw(img)
        half = im.width / 2 + 20
        d.line((cx - half * p, cy - 44, cx + half * p, cy - 44), fill=GOLD + (int(230 * al),), width=2)
        d.line((cx - half * p, cy + 44, cx + half * p, cy + 44), fill=GOLD + (int(230 * al),), width=2)
        # sparkle at the line ends
        for sx in (cx - half * p, cx + half * p):
            r = 7 * p
            d.polygon([(sx, cy - 44 - r), (sx + r * 0.3, cy - 44), (sx, cy - 44 + r), (sx - r * 0.3, cy - 44)], fill=HL + (int(255 * al),))
        paste(img, im, cx, cy + (1 - eo((u - 0.15) / 0.4)) * 16, eo((u - 0.15) / 0.35) * al)


# ---------------- end card on the live packshot ----------------
SLOGAN1 = shadowed(text_img("Pamper your skin", font("Playfair-Italic.ttf", 92), WHITE, pad=16), blur=14, alpha=0.7, dy=3)
SLOGAN2 = ec.gradient_text("with PalmCare.", font("Cormorant-SemiBold.ttf", 118), (255, 240, 214), (214, 150, 74))
_nm = {}


def name_tag(s):
    if s not in _nm:
        _nm[s] = shadowed(text_img(s, font("Montserrat-Bold.ttf", 24), CREAM, tracking=5, pad=8), blur=8, alpha=0.8, dy=2)
    return _nm[s]


def draw_endcard(img, t, rgb):
    s = tl.EC_START
    if t < s:
        return
    u = t - s
    # darken the top for the type and the bottom for the panel
    k = (np.clip((560 - YY) / 560, 0, 1) ** 1.3 * 0.62 + np.clip((YY - 1540) / 220, 0, 1) ** 1.1 * 0.82)[..., None]
    k = k * eo(u / 0.6)
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    arr = arr * (1 - k) + np.array([34, 19, 8], np.float32) * k
    img.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA"))
    ec.draw_frame(img, u)
    al = eo((u - 0.3) / 0.6)
    paste(img, ec.shimmer(ec.LOGO, c01((u - 1.0) / 1.0), 40), W / 2, 96 + (1 - al) * 14, al)
    paste(img, ec.SUB, W / 2, 178, al * 0.9)
    a1 = eo((u - 0.8) / 0.55)
    paste(img, SLOGAN1, W / 2, 262 + (1 - a1) * 26, a1)
    a2 = eo((u - 1.05) / 0.6)
    paste(img, ec.shimmer(SLOGAN2, c01((u - 2.0) / 0.9)), W / 2, 368 + (1 - a2) * 34, a2)
    # product names under each bottle's pump
    for txt, (x, y), d0 in getattr(tl, "EC_TAGS", []):
        p = eo((u - d0) / 0.5)
        if p > 0:
            paste(img, name_tag(txt), x, y + (1 - p) * 10, p)
    bt = 0     # no button: the bottles fill the lower frame; the contact panel carries the call to action
    if bt > 0:
        pulse = 0.55 + 0.45 * (0.5 + 0.5 * math.sin((u - 2.6) * 2 * math.pi / 1.1)) if u > 2.6 else 0.5
        sc = eob(bt) * (1 + 0.025 * math.sin(max(0, u - 2.6) * 2 * math.pi / 1.1))
        b = ec.button(sc, pulse)
        if b:
            paste(img, b, W / 2, 1628 - (b.height - 112 * sc) / 2, min(1, bt * 1.5))
    ec.draw_panel(img, rgb, u)


def draw_opener(img, t):
    """Quiet brand mark over the wake-up shot."""
    if True:            # the brand gets its moment on the end card; nothing over her stretch
        return
    a = eo((t - 0.3) / 0.6) * (1 - c01((t - 2.35) / 0.4))
    paste(img, ec.shimmer(ec.LOGO, c01((t - 0.8) / 1.2), 40), W / 2, 150, a, 0.62)
    paste(img, ec.SUB, W / 2, 205, a * 0.85, 0.9)


def compose(frame, t):
    arr = frame.astype(np.float32)
    arr = apply_transitions(arr, t)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    draw_opener(img, t)
    o1.draw_tags(img, t)
    draw_count(img, t)
    draw_benefits(img, t)
    draw_titles(img, t)
    draw_captions(img, t)
    draw_endcard(img, t, arr)
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]
    BASE = os.environ.get("BASE", f"baseR{tl.V}.mov")
    if out.endswith(".jpg") or out.endswith(".png"):
        ts = [float(x) for x in sys.argv[2].split(",")]
        ims = []
        for t in ts:
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", BASE, "-frames:v", "1", "-f", "rawvideo",
                                 "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            ims.append(Image.fromarray(compose(np.frombuffer(fr, np.uint8).reshape(H, W, 3), t)))
        sheet = Image.new("RGB", (540 * len(ims), 960))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((540, 960), Image.LANCZOS), (540 * k, 0))
        sheet.save(out, quality=92)
        sys.exit()
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", BASE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", BASE, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
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
