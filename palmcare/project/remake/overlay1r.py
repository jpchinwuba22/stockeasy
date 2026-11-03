"""Video 1 lock-down graphics over baseR1r.mov: opening title, BOLD word-highlighted captions, a frosted-glass
product spotlight that pops up at each reveal (real product photo, name, category, three key benefits), ingredient
call-outs pointing at the real label on the locked shots, and benefit explainer pop-ups.
Usage: overlay1r.py OUT.mp4|OUT.png [START END | T]"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

os.environ.setdefault("TLMOD", "tl1r")
sys.path.insert(0, ".")
import overlayR as base  # noqa: E402  (opening title + helpers)

tl = base.tl
W, H, FPS = 1080, 1920, 24
F = "../fonts/"
GOLD, HL, WHITE, CREAM, INK = (226, 182, 118), (246, 197, 111), (255, 252, 246), (246, 230, 206), (30, 17, 7)
c01, eo, eob, paste, shadowed, text_img = base.c01, base.eo, base.eob, base.paste, base.shadowed, base.text_img


def font(name, size):
    return ImageFont.truetype(F + name, size)


def glass(img, box, radius, tint=(30, 17, 7), amount=0.58, blur=22):
    """Frosted panel: the frame behind it blurred and tinted, rounded, with a fine gold rim."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return None
    crop = img.crop((x0, y0, x1, y1)).convert("RGB").filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(crop).astype(np.float32)
    a = a * (1 - amount) + np.array(tint, np.float32) * amount
    panel = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    m = Image.new("L", panel.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, panel.width - 1, panel.height - 1), radius=radius, fill=255)
    panel.putalpha(m)
    d = ImageDraw.Draw(panel)
    d.rounded_rectangle((1, 1, panel.width - 2, panel.height - 2), radius=radius, outline=GOLD + (230,), width=2)
    # soft top sheen
    sh = Image.new("L", panel.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((6, 4, panel.width - 7, panel.height // 3), radius=radius, fill=26)
    sheen = Image.new("RGBA", panel.size, (255, 244, 224, 0))
    sheen.putalpha(Image.fromarray(np.minimum(np.asarray(sh.filter(ImageFilter.GaussianBlur(12))), np.asarray(m))))
    panel.alpha_composite(sheen)
    return panel, (x0, y0)


def drop_shadow(img, box, radius, alpha=0.45, blur=26, dy=14):
    x0, y0, x1, y1 = [int(v) for v in box]
    pad = blur * 2
    m = Image.new("L", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), 0)
    ImageDraw.Draw(m).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), radius=radius, fill=int(255 * alpha))
    s = Image.new("RGBA", m.size, (0, 0, 0, 0))
    s.putalpha(m.filter(ImageFilter.GaussianBlur(blur)))
    img.alpha_composite(s, (x0 - pad, y0 - pad + dy))


def fade(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.split()[-1].point(lambda v: int(v * a)))
    return im


# ---------- bold captions ----------
CAP_FONT = font("Montserrat-ExtraBold.ttf", 62)
CAP_Y = 1640
CAP_MAX = 960
CHUNKS = tl.caption_chunks()
KEYWORDS = {"palmcare", "milky", "hydro-glow", "cacao", "collagen", "peptides,", "niacinamide,", "vitamin", "e…",
            "hydration", "24-hour", "radiant", "glow."}
_cap = {}


def _lines(words):
    sp = CAP_FONT.getlength(" ")
    wid = [CAP_FONT.getlength(w) for w in words]
    if sum(wid) + sp * (len(words) - 1) <= CAP_MAX or len(words) < 2:
        return [list(range(len(words)))]
    best = None
    for k in range(1, len(words)):
        a = sum(wid[:k]) + sp * (k - 1)
        b = sum(wid[k:]) + sp * (len(words) - k - 1)
        if best is None or max(a, b) < best[0]:
            best = (max(a, b), k)
    k = best[1]
    return [list(range(k)), list(range(k, len(words)))]


def caption_img(ci, hi, pop):
    """Chunk ci, word hi active (gold, lifted); pop 0..1 scales the active word in."""
    key = (ci, hi, round(pop, 1))
    if key in _cap:
        return _cap[key]
    words = [w[0] for w in CHUNKS[ci]]
    sp = CAP_FONT.getlength(" ")
    asc, desc = CAP_FONT.getmetrics()
    lh = asc + desc - 4
    lines = _lines(words)
    tw = max(sum(CAP_FONT.getlength(words[k]) for k in ln) + sp * (len(ln) - 1) for ln in lines)
    pad = 40
    im = Image.new("RGBA", (int(tw) + 2 * pad, lh * len(lines) + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for li, ln in enumerate(lines):
        lw = sum(CAP_FONT.getlength(words[k]) for k in ln) + sp * (len(ln) - 1)
        x = pad + (tw - lw) / 2
        y = pad + li * lh
        for k in ln:
            w = words[k]
            kw = w.lower().strip(".,…") in {x.strip(".,…") for x in KEYWORDS}
            fill = HL if k == hi else (CREAM if kw else WHITE)
            lift = -6 * pop if k == hi else 0
            d.text((x, y + lift), w, font=CAP_FONT, fill=fill, stroke_width=4, stroke_fill=(22, 12, 4, 255))
            x += CAP_FONT.getlength(w) + sp
    out = shadowed(im, blur=14, alpha=0.85, dy=5)
    _cap[key] = out
    return out


def hidden_by_spotlight(t):
    return any(s - 0.1 <= t < e + 0.05 for *_, s, e, _y in tl.SPOTLIGHT)


def draw_captions(img, t):
    if hidden_by_spotlight(t):
        return
    for ci, ch in enumerate(CHUNKS):
        s, e = ch[0][1] - 0.08, ch[-1][2]
        nxt = CHUNKS[ci + 1][0][1] - 0.1 if ci + 1 < len(CHUNKS) else e + 0.6
        e_out = min(e + 0.45, nxt + 0.02)
        if not (s <= t < e_out):
            continue
        hi, pop = -1, 0.0
        for k, (_, ws, we) in enumerate(ch):
            if ws - 0.04 <= t < (ch[k + 1][1] - 0.04 if k + 1 < len(ch) else we + 0.2):
                hi, pop = k, eob((t - ws + 0.04) / 0.18)
        a = eo((t - s) / 0.12) * (1 - c01((t - (e_out - 0.12)) / 0.12))
        sc = 0.86 + 0.14 * eob((t - s) / 0.24)
        paste(img, caption_img(ci, hi, pop), W / 2, CAP_Y, a, sc)


# ---------- product spotlight pop-up ----------
SP_W, SP_H, SP_R = 980, 430, 40
_sp = {}


def sp_parts(k):
    if k in _sp:
        return _sp[k]
    path, l1, l2, cat, bullets = tl.SPOTLIGHT[k][:5]
    prod = Image.open(path).convert("RGBA")
    ph = 390
    prod = prod.resize((round(prod.width * ph / prod.height), ph), Image.LANCZOS)
    # product shadow + warm glow behind it
    glow = Image.new("L", (prod.width + 160, ph + 120), 0)
    ImageDraw.Draw(glow).ellipse((20, 40, glow.width - 20, glow.height - 20), fill=120)
    gl = Image.new("RGBA", glow.size, (255, 196, 120, 0))
    gl.putalpha(glow.filter(ImageFilter.GaussianBlur(40)))
    prod = shadowed(prod, blur=10, alpha=0.6, dy=6)
    pc = text_img("PALMCARE", font("Montserrat-Bold.ttf", 24), GOLD, tracking=9, pad=0)
    n1 = shadowed(text_img(l1, font("Cormorant-SemiBold.ttf", 76), WHITE, pad=0), blur=8, alpha=0.6, dy=2)
    n2 = shadowed(text_img(l2, font("Cormorant-SemiBold.ttf", 76), HL, pad=0), blur=8, alpha=0.6, dy=2)
    ct = text_img(cat, font("Montserrat-Bold.ttf", 25), CREAM, tracking=4, pad=0)
    bl = [text_img(b, font("Montserrat-SemiBold.ttf", 27), WHITE, pad=0) for b in bullets]
    _sp[k] = (prod, gl, pc, n1, n2, ct, bl)
    return _sp[k]


def draw_spotlight(img, t):
    for k, (path, l1, l2, cat, bullets, s, e, yc) in enumerate(tl.SPOTLIGHT):
        if not (s <= t < e):
            continue
        prod, gl, pc, n1, n2, ct, bl = sp_parts(k)
        u = t - s
        ain = eob(u / 0.5)
        out = c01((t - (e - 0.3)) / 0.3)
        a = c01(u / 0.2) * (1 - eo(out))
        sc = 0.82 + 0.18 * ain
        cw, chh = SP_W * sc, SP_H * sc
        cx, cy = W / 2, yc + (1 - eo(u / 0.45)) * 70 + eo(out) * 40
        box = (cx - cw / 2, cy - chh / 2, cx + cw / 2, cy + chh / 2)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        drop_shadow(layer, box, SP_R, alpha=0.5)
        g = glass(img, box, int(SP_R * sc))
        if g is None:
            continue
        panel, (px, py) = g
        layer.alpha_composite(panel, (px, py))
        # contents laid out in card coordinates (unscaled), then scaled with the card
        card = Image.new("RGBA", (SP_W, SP_H), (0, 0, 0, 0))
        pu = eob((u - 0.12) / 0.5)
        card.alpha_composite(gl, (int(150 - gl.width / 2), int(SP_H / 2 - gl.height / 2)))
        pimg = fade(prod, c01((u - 0.12) / 0.2))
        card.alpha_composite(pimg, (int(150 - pimg.width / 2), int(SP_H - 18 - pimg.height + (1 - pu) * 90)))
        tx = 300
        items = [(pc, 46, 0.25), (n1, 74, 0.32), (n2, 146, 0.40), (ct, 238, 0.50)]
        for im, y, d0 in items:
            p = eo((u - d0) / 0.35)
            if p > 0:
                card.alpha_composite(fade(im, p), (int(tx + (1 - p) * 30), y))
        dd = ImageDraw.Draw(card)
        lp = eo((u - 0.55) / 0.4)
        if lp > 0:
            dd.line((tx, 284, tx + 600 * lp, 284), fill=GOLD + (220,), width=2)
        for j, b in enumerate(bl):
            p = eo((u - 0.65 - j * 0.16) / 0.3)
            if p > 0:
                y = 304 + j * 40
                r = 6
                dd.ellipse((tx + 2, y + 13 - r, tx + 2 + 2 * r, y + 13 + r), fill=HL + (int(255 * p),))
                card.alpha_composite(fade(b, p), (int(tx + 26 + (1 - p) * 20), y))
        # one light sweep across the card
        sw = c01((u - 0.9) / 0.7)
        if 0 < sw < 1:
            band = Image.new("L", (SP_W, SP_H), 0)
            bx = -200 + (SP_W + 400) * sw
            ImageDraw.Draw(band).polygon([(bx, 0), (bx + 90, 0), (bx - 30, SP_H), (bx - 120, SP_H)], fill=60)
            sweep = Image.new("RGBA", (SP_W, SP_H), (255, 240, 210, 0))
            mask = Image.new("L", (SP_W, SP_H), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, SP_W - 1, SP_H - 1), radius=SP_R, fill=255)
            sweep.putalpha(Image.fromarray(np.minimum(np.asarray(band.filter(ImageFilter.GaussianBlur(18))), np.asarray(mask))))
            card.alpha_composite(sweep)
        if abs(sc - 1) > 0.002:
            card = card.resize((round(SP_W * sc), round(SP_H * sc)), Image.BICUBIC)
        layer.alpha_composite(card, (int(round(cx - card.width / 2)), int(round(cy - card.height / 2))))
        img.alpha_composite(fade(layer, a))


# ---------- ingredient call-outs (locked shots) ----------
TAG_T = font("Montserrat-ExtraBold.ttf", 34)
TAG_S = font("Montserrat-SemiBold.ttf", 24)
_tag = {}


def stack(ims, gap):
    out = Image.new("RGBA", (max(i.width for i in ims), sum(i.height for i in ims) + gap * (len(ims) - 1)), (0, 0, 0, 0))
    y = 0
    for i in ims:
        out.alpha_composite(i, (0, y))
        y += i.height + gap
    return out


def tag_img(title, line):
    if (title, line) in _tag:
        return _tag[(title, line)]
    a = stack([text_img(x, TAG_T, WHITE, tracking=2, pad=0) for x in title.split("\n")], 2)
    b = stack([text_img(x, TAG_S, CREAM, pad=0) for x in line.split("\n")], 2)
    w, h = max(a.width, b.width) + 56, a.height + b.height + 40
    _tag[(title, line)] = (a, b, w, h)
    return _tag[(title, line)]


def draw_tags(img, t):
    for title, line, s, e, (ax, ay), (tx, ty) in tl.TAGS:
        if not (s <= t < e):
            continue
        u = t - s
        out = 1 - c01((t - (e - 0.25)) / 0.25)
        a, b, w, h = tag_img(title, line)
        d = ImageDraw.Draw(img)
        # anchor dot with a pulse ring on the label
        ring = c01((u % 1.2) / 0.8)
        rr = 7 + 9 * ring
        d.ellipse((ax - rr, ay - rr, ax + rr, ay + rr), outline=HL + (int(200 * (1 - ring) * out),), width=3)
        d.ellipse((ax - 6, ay - 6, ax + 6, ay + 6), fill=HL + (int(255 * out),), outline=(40, 22, 8, int(200 * out)), width=2)
        # leader line draws out to the tag
        lp = eo(u / 0.3)
        ex = tx - w / 2 if tx > ax else tx + w / 2
        mx, my = ax + (ex - ax) * lp, ay + (ty - ay) * lp
        d.line((ax, ay, mx, my), fill=(40, 22, 8, int(120 * out)), width=6)
        d.line((ax, ay, mx, my), fill=HL + (int(255 * out),), width=3)
        p = eob((u - 0.22) / 0.4)
        if p > 0:
            box = (tx - w / 2, ty - h / 2, tx + w / 2, ty + h / 2)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            drop_shadow(layer, box, 24, alpha=0.4, blur=18, dy=8)
            g = glass(img, box, 24, amount=0.62)
            if g:
                layer.alpha_composite(g[0], g[1])
                layer.alpha_composite(a, (int(tx - w / 2 + 28), int(ty - h / 2 + 16)))
                layer.alpha_composite(b, (int(tx - w / 2 + 28), int(ty - h / 2 + 22 + a.height)))
            sc = 0.7 + 0.3 * p
            if abs(sc - 1) > 0.002:
                # scale about the tag centre
                cx0, cy0 = tx, ty
                layer = layer.transform((W, H), Image.AFFINE, (1 / sc, 0, cx0 - cx0 / sc, 0, 1 / sc, cy0 - cy0 / sc), Image.BICUBIC)
            img.alpha_composite(fade(layer, c01((u - 0.22) / 0.15) * out))


# ---------- benefit explainers ----------
POP_T = font("Montserrat-ExtraBold.ttf", 42)
POP_S = font("Montserrat-SemiBold.ttf", 29)
_pop = {}


def icon(kind, r=34):
    im = Image.new("RGBA", (2 * r + 8, 2 * r + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = r + 4
    d.ellipse((4, 4, 4 + 2 * r, 4 + 2 * r), fill=(184, 124, 44, 255), outline=HL + (255,), width=2)
    ink = (255, 250, 240, 255)
    if kind == "drop":
        pts = [(c + 13 * math.sin(a) * (1 - math.cos(a)) / 1.4, c + 4 - 15 * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 40)]
        d.polygon(pts, fill=ink)
    elif kind == "sparkle":
        for (sx, sy, s) in ((c - 3, c + 2, 17), (c + 13, c - 12, 7)):
            d.polygon([(sx, sy - s), (sx + s * 0.25, sy - s * 0.25), (sx + s, sy), (sx + s * 0.25, sy + s * 0.25), (sx, sy + s),
                       (sx - s * 0.25, sy + s * 0.25), (sx - s, sy), (sx - s * 0.25, sy - s * 0.25)], fill=ink)
    elif kind == "clock":
        d.ellipse((c - 17, c - 17, c + 17, c + 17), outline=ink, width=4)
        d.line((c, c, c, c - 11), fill=ink, width=4)
        d.line((c, c, c + 8, c + 5), fill=ink, width=4)
    elif kind == "leaf":
        # lens-shaped leaf tilted 40 degrees, with a midrib and a short stem
        ca, sa = math.cos(math.radians(-40)), math.sin(math.radians(-40))
        pts = [(-19 + 38 * u, 11 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 20)]
        pts += [(19 - 38 * u, -11 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 20)]
        rot = [(c + x * ca - y * sa, c + x * sa + y * ca) for x, y in pts]
        d.polygon(rot, fill=ink)
        p0, p1 = (c - 15 * ca, c - 15 * sa), (c + 15 * ca, c + 15 * sa)
        d.line((p0, p1), fill=(184, 124, 44, 255), width=3)
        d.line(((c - 19 * ca, c - 19 * sa), (c - 25 * ca, c - 25 * sa)), fill=ink, width=3)
    return im


def pop_parts(title, line, kind):
    key = (title, line, kind)
    if key not in _pop:
        a = text_img(title, POP_T, WHITE, tracking=2, pad=0)
        b = text_img(line, POP_S, CREAM, pad=0)
        ic = icon(kind)
        w = max(a.width, b.width) + ic.width + 100
        h = a.height + b.height + 52
        _pop[key] = (a, b, ic, w, h)
    return _pop[key]


def draw_pops(img, t):
    for title, line, kind, s, e, yc in tl.POPS:
        if not (s <= t < e):
            continue
        u = t - s
        a, b, ic, w, h = pop_parts(title, line, kind)
        out = c01((t - (e - 0.25)) / 0.25)
        p = eob(u / 0.42)
        sc = 0.72 + 0.28 * p
        alpha = c01(u / 0.15) * (1 - eo(out))
        cx, cy = W / 2, yc + eo(out) * 20
        box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        drop_shadow(layer, box, h // 2, alpha=0.4, blur=20, dy=10)
        g = glass(img, box, h // 2, amount=0.6)
        if g is None:
            continue
        layer.alpha_composite(g[0], g[1])
        ip = eob((u - 0.1) / 0.4)
        ici = ic.rotate((1 - ip) * 90, resample=Image.BICUBIC) if ip < 1 else ic
        layer.alpha_composite(fade(ici, c01((u - 0.1) / 0.2)), (int(box[0] + 26), int(cy - ic.height / 2)))
        tx = box[0] + 26 + ic.width + 26
        ta = eo((u - 0.18) / 0.3)
        layer.alpha_composite(fade(a, ta), (int(tx + (1 - ta) * 24), int(box[1] + 20)))
        tb = eo((u - 0.3) / 0.3)
        layer.alpha_composite(fade(b, tb), (int(tx + (1 - tb) * 24), int(box[1] + 30 + a.height)))
        if abs(sc - 1) > 0.002:
            layer = layer.transform((W, H), Image.AFFINE, (1 / sc, 0, cx - cx / sc, 0, 1 / sc, cy - cy / sc), Image.BICUBIC)
        img.alpha_composite(fade(layer, alpha))


def compose(frame, t):
    img = Image.fromarray(frame).convert("RGBA")
    base.draw_opener(img, t)
    draw_tags(img, t)
    draw_pops(img, t)
    draw_spotlight(img, t)
    draw_captions(img, t)
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]
    BASE = os.environ.get("BASE", f"baseR{tl.V}.mov")
    if out.endswith(".png") or out.endswith(".jpg"):
        ts = [float(x) for x in sys.argv[2].split(",")]
        ims = []
        for t in ts:
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", BASE, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                capture_output=True).stdout
            ims.append(Image.fromarray(compose(np.frombuffer(fr, np.uint8).reshape(H, W, 3), t)))
        sheet = Image.new("RGB", (540 * len(ims), 960))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((540, 960), Image.LANCZOS), (540 * k, 0))
        sheet.save(out, quality=92)
        sys.exit()
    t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    t1 = float(sys.argv[3]) if len(sys.argv) > 3 else tl.TOTAL
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(t1 - t0), "-i", BASE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-ss", str(t0), "-t", str(t1 - t0), "-i", BASE, "-map", "0:v", "-map", "1:a",
                           "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                           "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    i = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        wr.stdin.write(compose(f, t0 + i / FPS).tobytes())
        i += 1
    wr.stdin.close()
    wr.wait()
    print("frames", i)
