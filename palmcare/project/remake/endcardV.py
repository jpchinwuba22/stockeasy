"""PalmCare end card over a real product frame from the video (label-corrected), instead of a built set:
slow push-in on the still, golden dust, a flare, the gold hairline frame drawing on, shimmering logo, product
tagline, the "Pamper your skin with PalmCare." headline, pulsing ORDER NOW button and the contact panel
(phones in the client's order). Run from remake/.
Usage: endcardV.py STILL.png OUT.mp4|OUT.jpg TAGLINE [SECONDS]"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

STILL, OUT, TAGLINE = sys.argv[1], sys.argv[2], sys.argv[3]
DUR = float(sys.argv[4]) if len(sys.argv) > 4 else 7.0
os.environ.setdefault("PCV", "1")
sys.argv = [sys.argv[0], "x.jpg", str(DUR)]
sys.path.insert(0, ".")
import endcardR as ec  # noqa: E402  (reuses its typography, button, frame and panel)

h = ec.h
OW, OH, FPS = ec.OW, ec.OH, ec.FPS
F = ec.F
# client's own order of the numbers
ec.PH1, ec.PH2 = ec.text_img("0903 055 5424", ec.fp, ec.WHITE, tracking=1, shadow=0.4), ec.text_img("0809 361 2901", ec.fp, ec.WHITE, tracking=1, shadow=0.4)
ec.INK = (40, 22, 10)
TAG = ec.text_img(TAGLINE, ImageFont.truetype(F + "Jost-Medium.ttf", 26), ec.WHITE, tracking=6)
L1 = ec.text_img("Pamper your skin", ImageFont.truetype(F + "Cormorant-Italic.ttf", 98), ec.WHITE)
L2 = ec.gradient_text("with PalmCare.", ImageFont.truetype(F + "Cormorant-Italic.ttf", 122), (255, 240, 214), (214, 150, 74))
BG = np.asarray(Image.open(STILL).convert("RGB").resize((OW, OH), Image.LANCZOS)).astype(np.float32)
YY, XX = h.YY, h.XX
TOPDARK = np.clip((620 - YY) / 620, 0, 1) ** 1.3 * 0.72
BOTDARK = np.clip((YY - 1430) / 300, 0, 1) ** 1.1 * 0.86
DUST = h.Dust(44, 31)
c01, eo, eob, paste = ec.c01, ec.eo, ec.eob, ec.paste


def background(t):
    q = t / DUR
    s = 1.0 + 0.035 * h.ease(q)
    cx, cy = OW / 2, 1000
    # inverse map for a centred zoom
    im = Image.fromarray(BG.astype(np.uint8))
    a = 1 / s
    im = im.transform((OW, OH), Image.AFFINE, (a, 0, cx - a * cx, 0, a, cy - a * cy), Image.BICUBIC)
    return np.asarray(im).astype(np.float32)


def frame(i):
    t = i / FPS
    rgb = background(t)
    fl = math.sin(math.pi * c01((t - 0.1) / 0.8)) * 0.7
    rgb = h.flare(rgb, OW * (0.92 - 0.6 * c01((t - 0.1) / 0.8)), 760, fl)
    rgb = DUST.draw(rgb, t, 0.9)
    k = (TOPDARK + BOTDARK)[..., None]
    rgb = rgb * (1 - k) + np.array(ec.INK, np.float32) * k
    rgb = h.bloom(rgb, threshold=230, radius=26, amount=0.2)
    rgb = rgb * h.VIG[..., None]
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    ec.draw_frame(img, t)
    al = eo((t - 0.4) / 0.6)
    paste(img, ec.shimmer(ec.LOGO, c01((t - 1.2) / 1.0), 40), OW / 2, 50 + (1 - al) * 14, al)
    paste(img, ec.SUB, OW / 2, 168 + (1 - al) * 10, al * 0.9)
    at = eo((t - 0.75) / 0.5)
    paste(img, TAG, OW / 2, 206 + (1 - at) * 12, at)
    d = ImageDraw.Draw(img)
    room = (OW - 2 * ec.FRAME_IN - TAG.width) / 2 - 40
    rl = min(80, room) * eo((t - 0.85) / 0.6)
    if rl > 1:
        yy = 206 + TAG.height / 2 + 2
        hw = TAG.width / 2 - 6
        d.line((OW / 2 - hw - 14 - rl, yy, OW / 2 - hw - 14, yy), fill=ec.GOLD + (230,), width=2)
        d.line((OW / 2 + hw + 14, yy, OW / 2 + hw + 14 + rl, yy), fill=ec.GOLD + (230,), width=2)
    a1 = eo((t - 1.0) / 0.55)
    paste(img, L1, OW / 2, 262 + (1 - a1) * 30, a1)
    a2 = eo((t - 1.25) / 0.6)
    paste(img, ec.shimmer(L2, c01((t - 2.2) / 0.9)), OW / 2, 352 + (1 - a2) * 40, a2)
    bt = c01((t - 1.9) / 0.45)
    if bt > 0:
        pulse = 0.55 + 0.45 * (0.5 + 0.5 * math.sin((t - 2.3) * 2 * math.pi / 1.1)) if t > 2.3 else 0.5
        sc = eob(bt) * (1 + 0.025 * math.sin(max(0, t - 2.3) * 2 * math.pi / 1.1))
        b = ec.button(sc, pulse)
        if b:
            paste(img, b, OW / 2, 1500 - (b.height - 112 * sc) / 2, min(1, bt * 1.5))
    ec.draw_panel(img, rgb, t)
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    fl_in = c01(1 - t / 0.3)
    if fl_in > 0:
        arr = arr * (1 - fl_in) + np.array([255, 240, 214.0]) * fl_in
    arr = arr + h.RNG.normal(0, 1.4, (OH, OW))[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    n = round(DUR * FPS)
    if OUT.endswith(".jpg"):
        picks = [int(n * f) for f in (0.08, 0.25, 0.45, 0.98)]
        sheet = Image.new("RGB", (360 * 4, 640))
        for k, i in enumerate(picks):
            sheet.paste(Image.fromarray(frame(i)).resize((360, 640), Image.LANCZOS), (360 * k, 0))
        sheet.save(OUT, quality=92)
        Image.fromarray(frame(n - 1)).save(OUT.replace(".jpg", "_last.png"))
    else:
        pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
        for i in range(n):
            pr.stdin.write(frame(i).tobytes())
        pr.stdin.close()
        pr.wait()
