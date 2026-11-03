"""Video 6 graphics pass over base6.mov: animated opening title, product-name titles on the reveals,
word-highlighted subtitles that follow the narrator, and pop-up benefit chips. Writes the final mp4.
Usage: overlay6.py OUT.mp4 [START END]  (START/END renders a preview range)"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, ".")
import timeline6 as tl  # noqa: E402

W, H, FPS = 1080, 1920, 24
F = "../fonts/"
GOLD, HL, WHITE, INK, BROWN = (226, 182, 118), (246, 197, 111), (255, 252, 246), (48, 28, 10), (112, 64, 16)
CAP_FONT = ImageFont.truetype(F + "Jost-Medium.ttf", 50)
CAP_Y = 1548


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eob(x):
    x = c01(x)
    c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def shadowed(im, blur=9, alpha=0.75, colour=(0, 0, 0), dy=3):
    sh = Image.new("RGBA", im.size, colour + (0,))
    sh.putalpha(im.split()[-1].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, dy))
    out.alpha_composite(im)
    return out


def text_img(s, font, fill, tracking=0, pad=30, stroke=0, stroke_fill=None):
    w = sum(font.getlength(c) for c in s) + tracking * max(0, len(s) - 1)
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (int(w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c in s:
        d.text((x, pad), c, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += font.getlength(c) + tracking
    return im


def paste(dst, im, cx, y, alpha=1.0, scale=1.0):
    if im is None or alpha <= 0.002:
        return
    if abs(scale - 1) > 0.002:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        im = im.copy()
        im.putalpha(im.split()[-1].point(lambda v: int(v * alpha)))
    dst.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(y - im.height / 2))))


# ---------- subtitles ----------
CHUNKS = tl.caption_chunks()
_cap_cache = {}


def caption_img(ci, hi):
    """Chunk ci with word hi highlighted (-1: none)."""
    key = (ci, hi)
    if key in _cap_cache:
        return _cap_cache[key]
    words = [w[0] for w in CHUNKS[ci]]
    sp = CAP_FONT.getlength(" ")
    widths = [CAP_FONT.getlength(w) for w in words]
    tw = sum(widths) + sp * (len(words) - 1)
    asc, desc = CAP_FONT.getmetrics()
    pad = 30
    im = Image.new("RGBA", (int(tw) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for k, (w, ww) in enumerate(zip(words, widths)):
        d.text((x, pad), w, font=CAP_FONT, fill=HL if k == hi else WHITE, stroke_width=2, stroke_fill=(20, 10, 4, 140))
        x += ww + sp
    out = shadowed(im, blur=10, alpha=0.8, dy=3)
    _cap_cache[key] = out
    return out


def draw_captions(img, t):
    for ci, ch in enumerate(CHUNKS):
        s, e = ch[0][1] - 0.08, ch[-1][2]
        nxt = CHUNKS[ci + 1][0][1] - 0.1 if ci + 1 < len(CHUNKS) else e + 0.6
        e_out = min(e + 0.45, nxt)
        if not (s <= t < e_out + 0.15):
            continue
        hi = -1
        for k, (_, ws, we) in enumerate(ch):
            if ws - 0.04 <= t < (ch[k + 1][1] - 0.04 if k + 1 < len(ch) else we + 0.2):
                hi = k
        a = eo((t - s) / 0.14) * (1 - c01((t - e_out) / 0.15))
        paste(img, caption_img(ci, hi), W / 2, CAP_Y + (1 - eo((t - s) / 0.18)) * 12, a)


# ---------- pop-up chips ----------
CHIP_FONT = ImageFont.truetype(F + "Jost-Medium.ttf", 32)
_chip_cache = {}


def chip_img(label):
    if label in _chip_cache:
        return _chip_cache[label]
    t = text_img(label, CHIP_FONT, WHITE, tracking=5, pad=0)
    hh, star = 76, 26
    w = t.width + 2 * 34 + star + 16
    pad = 40
    im = Image.new("RGBA", (w + 2 * pad, hh + 2 * pad), (0, 0, 0, 0))
    g = Image.new("L", im.size, 0)
    ImageDraw.Draw(g).rounded_rectangle((pad, pad, pad + w, pad + hh), radius=hh // 2, fill=150)
    glow = Image.new("RGBA", im.size, (255, 190, 100, 0))
    glow.putalpha(g.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + hh), radius=hh // 2, fill=(28, 16, 6, 175), outline=GOLD + (255,), width=2)
    # four-point sparkle
    cx, cy, r = pad + 34 + star / 2, pad + hh / 2, star / 2
    d.polygon([(cx, cy - r), (cx + r * 0.28, cy - r * 0.28), (cx + r, cy), (cx + r * 0.28, cy + r * 0.28),
               (cx, cy + r), (cx - r * 0.28, cy + r * 0.28), (cx - r, cy), (cx - r * 0.28, cy - r * 0.28)], fill=HL)
    im.alpha_composite(t, (int(pad + 34 + star + 16), int(pad + (hh - t.height) / 2 - 2)))
    _chip_cache[label] = im
    return im


def draw_chips(img, t):
    for label, s, e in tl.CHIPS:
        if s <= t < e:
            sc = 0.55 + 0.45 * eob((t - s) / 0.38)
            a = eo((t - s) / 0.15) * (1 - c01((t - (e - 0.22)) / 0.22))
            paste(img, chip_img(label), W / 2, 1405, a, sc)


# ---------- product titles ----------
_title_cache = {}


def title_parts(name, sub):
    if name in _title_cache:
        return _title_cache[name]
    badge_t = text_img("NEW", ImageFont.truetype(F + "Jost-Medium.ttf", 26), WHITE, tracking=8, pad=0)
    bw, bh = badge_t.width + 44, 46
    badge = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    ImageDraw.Draw(badge).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=bh // 2, fill=(184, 124, 44, 235))
    badge.alpha_composite(badge_t, ((bw - badge_t.width) // 2, (bh - badge_t.height) // 2 - 2))
    nm = shadowed(text_img(name, ImageFont.truetype(F + "Jost-Medium.ttf", 54 if len(name) > 14 else 64), INK, tracking=6),
                  blur=12, alpha=0.55, colour=(255, 246, 228), dy=0)
    sb = shadowed(text_img(sub, ImageFont.truetype(F + "Cormorant-SemiBold.ttf", 60), BROWN), blur=10, alpha=0.95,
                  colour=(255, 248, 232), dy=0)
    halo = Image.new("L", (W, 420), 0)
    ImageDraw.Draw(halo).ellipse((W / 2 - 470, 60, W / 2 + 470, 360), fill=150)
    hl = Image.new("RGBA", halo.size, (255, 246, 226, 0))
    hl.putalpha(halo.filter(ImageFilter.GaussianBlur(60)))
    _title_cache[name] = (badge, nm, sb, hl)
    return _title_cache[name]


def draw_titles(img, t):
    for name, sub, s, e in tl.TITLES:
        if not (s <= t < e):
            continue
        badge, nm, sb, hl = title_parts(name, sub)
        out = 1 - c01((t - (e - 0.25)) / 0.25)
        paste(img, hl, W / 2, 200, eo((t - s - 0.2) / 0.5) * out)
        paste(img, badge, W / 2, 128, eo((t - s - 0.25) / 0.3) * out, 0.6 + 0.4 * eob((t - s - 0.25) / 0.35))
        a = eo((t - s - 0.4) / 0.45)
        # name: letter-spaced reveal by a widening clip mask
        if a > 0:
            reveal = nm.copy()
            m = Image.new("L", reveal.size, 0)
            half = reveal.width / 2 * eo((t - s - 0.4) / 0.6)
            ImageDraw.Draw(m).rectangle((reveal.width / 2 - half, 0, reveal.width / 2 + half, reveal.height), fill=255)
            reveal.putalpha(Image.fromarray(np.minimum(np.asarray(reveal.split()[-1]), np.asarray(m.filter(ImageFilter.GaussianBlur(14))))))
            paste(img, reveal, W / 2, 205, a * out)
        paste(img, sb, W / 2, 282 + (1 - eo((t - s - 0.7) / 0.45)) * 16, eo((t - s - 0.7) / 0.45) * out)


# ---------- opening title ----------
OP_TAG = shadowed(text_img("PALMCARE  PRESENTS", ImageFont.truetype(F + "Jost-Medium.ttf", 28), WHITE, tracking=9), alpha=0.6)
_op_font = ImageFont.truetype(F + "Cormorant-Italic.ttf", 150)
OP_WORD = "Tropical Glow"


def draw_opener(img, t):
    s, e = tl.OPENER
    if not (s <= t < e):
        return
    out = 1 - c01((t - (e - 0.3)) / 0.3)
    paste(img, OP_TAG, W / 2, 300, eo((t - s) / 0.4) * out)
    # letter-by-letter rise with a cream-to-gold gradient
    widths = [_op_font.getlength(c) for c in OP_WORD]
    x = W / 2 - sum(widths) / 2
    for k, (ch, cw) in enumerate(zip(OP_WORD, widths)):
        if ch != " ":
            p = eo((t - s - 0.25 - k * 0.045) / 0.45)
            if p > 0:
                li = _letter(ch)
                paste(img, li, x + cw / 2, 420 + (1 - p) * 36, p * out)
        x += cw


_letters = {}


def _letter(ch):
    if ch in _letters:
        return _letters[ch]
    im = text_img(ch, _op_font, (255, 255, 255), pad=40)
    a = np.asarray(im).astype(np.float32)
    g = np.linspace(0, 1, a.shape[0])[:, None, None]
    a[..., :3] = np.array((255, 246, 230), np.float32) * (1 - g) + np.array((232, 178, 96), np.float32) * g
    _letters[ch] = shadowed(Image.fromarray(a.astype(np.uint8), "RGBA"), blur=12, alpha=0.65, dy=4)
    return _letters[ch]


def compose(frame, t):
    img = Image.fromarray(frame).convert("RGBA")
    draw_opener(img, t)
    draw_titles(img, t)
    draw_chips(img, t)
    draw_captions(img, t)
    return np.asarray(img.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]
    t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    t1 = float(sys.argv[3]) if len(sys.argv) > 3 else tl.TOTAL
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(t1 - t0), "-i", "base6.mov", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-ss", str(t0), "-t", str(t1 - t0), "-i", "base6.mov", "-map", "0:v", "-map", "1:a",
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
