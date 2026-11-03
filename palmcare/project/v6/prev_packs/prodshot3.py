"""Premium product unveil, built ONLY from the real, straight product photo (no AI bottle). The cutout is moved by
uniform scale + vertical translation only (never rotated, sheared or warped), so it stays a perfect, straight bottle
with the exact label.
Beat by beat: an anamorphic gold streak in the dark -> burst -> the camera pulls back from a label close-up to the full
bottle (motion-blurred) as it lands on a glossy pedestal with a true mirror reflection and a ring of light, while
rotating light rays, a spark burst and drifting gold flakes fill the set; a specular sweep crosses the bottle and the
pump glints. Writes OUT and OUT.json (bottle box per frame, for the label call-outs in the overlay).
Usage: prodshot3.py OUT(.mp4|.jpg) CONFIG   (CONFIG: vitac | n10 | derma)"""
import json
import math
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

W, H, FPS = 1080, 1920, 24
OUT, CFG = sys.argv[1], sys.argv[2]
A5 = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/v5/assets/"
C = {
    "vitac": dict(bottle=A5 + "vitac_real_final.png", h=1000, bg="src/S2.mp4", bg_t0=0.3, bg_speed=0.5, blur=22,
                  tint=(70, 36, 8), mix=0.55, dark=0.62, ray=(255, 196, 96), glow=(255, 180, 80), spark=(255, 220, 140),
                  floor=(64, 36, 10), rim=(240, 182, 80), dur=5.0, base=1650),
    "n10": dict(bottle=A5 + "n10_real_final.png", h=1000, bg="src/S4.mp4", bg_t0=1.0, bg_speed=0.5, blur=22,
                tint=(8, 58, 66), mix=0.55, dark=0.62, ray=(170, 240, 250), glow=(120, 220, 230), spark=(210, 250, 255),
                floor=(8, 48, 56), rim=(120, 220, 230), dur=5.0, base=1650),
    "derma": dict(bottle=A5 + "dermaluxe_box_final.png", h=1000, bg="src/S6.mp4", bg_t0=1.0, bg_speed=0.5, blur=22,
                  tint=(54, 22, 66), mix=0.55, dark=0.62, ray=(236, 190, 255), glow=(220, 150, 240), spark=(250, 220, 255),
                  floor=(44, 18, 54), rim=(214, 160, 240), dur=5.0, base=1650),
}[CFG]
N = int(C["dur"] * FPS)
rng = np.random.default_rng(11)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def c01(x):
    return min(1.0, max(0.0, x))


def eo(x):
    return 1 - (1 - c01(x)) ** 3


def eio(x):
    x = c01(x)
    return x * x * (3 - 2 * x)


# ---------- the real bottle (premultiplied float, exact) ----------
b = Image.open(C["bottle"]).convert("RGBA")
b = b.crop(b.getbbox())
B = np.asarray(b).astype(np.float32) / 255.0
PM = np.dstack([B[..., :3] * B[..., 3:4], B[..., 3]])
ASPECT = B.shape[1] / B.shape[0]


def bottle_at(scale):
    h = C["h"] * scale
    w = h * ASPECT
    r = cv2.resize(PM, (max(1, round(w)), max(1, round(h))), interpolation=cv2.INTER_AREA if scale <= 1 else cv2.INTER_CUBIC)
    return r[..., :3], np.clip(r[..., 3], 0, 1)


def place(dst, rgb, al, x0, y0, a=1.0):
    bh, bw = al.shape
    xs, ys = max(0, x0), max(0, y0)
    xe, ye = min(W, x0 + bw), min(H, y0 + bh)
    if xe <= xs or ye <= ys:
        return
    sub = dst[ys:ye, xs:xe]
    aa = al[ys - y0:ye - y0, xs - x0:xe - x0, None] * a
    dst[ys:ye, xs:xe] = rgb[ys - y0:ye - y0, xs - x0:xe - x0] * a + sub * (1 - aa)


# ---------- background frames ----------
cap = cv2.VideoCapture(C["bg"])
BG = []
for i in range(N):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int((C["bg_t0"] + i / FPS * C["bg_speed"]) * 24))
    f = cap.read()[1]
    f = cv2.GaussianBlur(cv2.resize(f, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), C["blur"])
    BG.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0)
tint = np.array(C["tint"], np.float32) / 255
vign = np.clip(1 - 0.35 * (((XX - W / 2) / (W * 0.7)) ** 2 + ((YY - H * 0.5) / (H * 0.6)) ** 2), 0.5, 1)[..., None]
ray_c, glow_c, spark_c = (np.array(C[k], np.float32) / 255 for k in ("ray", "glow", "spark"))
floor_c, rim_c = np.array(C["floor"], np.float32) / 255, np.array(C["rim"], np.float32) / 255
BASE = C["base"]
ANCHOR_Y = BASE - C["h"] * 0.42                       # pull-back centres on the label
RX, RY = np.arctan2(YY - (BASE - C["h"] * 0.62), XX - W / 2), np.hypot(XX - W / 2, YY - (BASE - C["h"] * 0.62))

# gold flakes: (x, y, depth 0..1, size, phase, drift)
FL = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0, 1), rng.uniform(3, 9), rng.uniform(0, 6.28), rng.uniform(-50, -15))
      for _ in range(70)]
SPK = [(rng.uniform(0, 6.28), rng.uniform(500, 1500), rng.uniform(2, 5), rng.uniform(0.5, 1.1)) for _ in range(90)]


def blob(out, x, y, r, col, a):
    x0, x1, y0, y1 = int(max(0, x - 3 * r)), int(min(W, x + 3 * r)), int(max(0, y - 3 * r)), int(min(H, y + 3 * r))
    if x1 > x0 and y1 > y0:
        d = np.exp(-(((XX[y0:y1, x0:x1] - x) ** 2 + (YY[y0:y1, x0:x1] - y) ** 2) / (2 * r * r)))[..., None]
        out[y0:y1, x0:x1] = 1 - (1 - out[y0:y1, x0:x1]) * (1 - d * a * col)


def geom(t):
    """Bottle scale and top-left at time t (uniform scale about the label anchor; never rotated)."""
    sc = 1.0 + 0.85 * (1 - eo(t / 0.95)) + 0.035 * eio((t - 0.95) / (C["dur"] - 0.95))
    h = C["h"] * sc
    w = h * ASPECT
    top = ANCHOR_Y - (ANCHOR_Y - (BASE - C["h"])) * sc
    return sc, W / 2 - w / 2, top, w, h


def frame(i):
    t = i / FPS
    bg = BG[i] * (1 - C["mix"]) + tint * C["mix"]
    bg = bg * C["dark"] * vign
    lift = eo((t - 0.15) / 0.6)
    out = bg * (0.25 + 0.75 * lift)
    # rotating volumetric rays behind the bottle
    ri = eo((t - 0.25) / 0.8)
    if ri > 0:
        rays = (0.5 + 0.5 * np.cos(RX * 14 + t * 0.35)) ** 10 * np.exp(-RY / 900) * 0.55 * ri
        rays += (0.5 + 0.5 * np.cos(RX * 7 - t * 0.2)) ** 6 * np.exp(-RY / 600) * 0.25 * ri
        out = 1 - (1 - out) * (1 - rays[..., None] * ray_c)
    # anamorphic streak (first beat)
    if t < 0.9:
        s = math.sin(math.pi * c01(t / 0.9))
        streak = np.exp(-((YY - ANCHOR_Y) / 9) ** 2) * np.exp(-((XX - W / 2) / (60 + 900 * eo(t / 0.4))) ** 2) * s
        out = 1 - (1 - out) * (1 - streak[..., None] * np.array([1.0, 0.85, 0.55]))
    # glossy pedestal floor
    fa = eo((t - 0.55) / 0.5)
    if fa > 0:
        fm = np.clip((YY - BASE) / 6 + 0.5, 0, 1) * np.exp(-((XX - W / 2) / 900) ** 2)
        out = out * (1 - fm[..., None] * 0.75 * fa) + floor_c * fm[..., None] * 0.75 * fa
        rim = np.exp(-(((XX - W / 2) / 420) ** 2 + ((YY - BASE) / 40) ** 2) * 1.0)
        wq = c01((t - 0.9) / 0.9)                           # light ring spreading out from the landing
        ring = np.exp(-((np.sqrt((XX - W / 2) ** 2 + ((YY - BASE) * 6.5) ** 2) - (180 + 520 * eo(wq))) / 16) ** 2) * (1 - wq) * (wq > 0)
        ring = ring + np.exp(-((np.sqrt((XX - W / 2) ** 2 + ((YY - BASE) * 6.5) ** 2) - 300) / 10) ** 2) * 0.35
        out = 1 - (1 - out) * (1 - (rim * 0.25 + ring * 0.6)[..., None] * rim_c * fa)
    # bottle (with motion blur during the pull-back) + mirror reflection
    subs = 4 if t < 0.95 else 1
    acc_rgb, acc_a = np.zeros((H, W, 3), np.float32), np.zeros((H, W), np.float32)
    box = None
    for k in range(subs):
        tt = t - k * (0.6 / FPS) / max(1, subs - 1) if subs > 1 else t
        sc, x0, y0, w, h = geom(max(0.0, tt))
        rgb, al = bottle_at(sc)
        lay_rgb, lay_a = np.zeros((H, W, 3), np.float32), np.zeros((H, W), np.float32)
        bh, bw = al.shape
        X0, Y0 = int(round(x0)), int(round(y0))
        xs, ys, xe, ye = max(0, X0), max(0, Y0), min(W, X0 + bw), min(H, Y0 + bh)
        if xe > xs and ye > ys:
            lay_rgb[ys:ye, xs:xe] = rgb[ys - Y0:ye - Y0, xs - X0:xe - X0]
            lay_a[ys:ye, xs:xe] = al[ys - Y0:ye - Y0, xs - X0:xe - X0]
        acc_rgb += lay_rgb / subs
        acc_a += lay_a / subs
        if k == 0:
            box = (x0, y0, w, h, sc)
    ba = c01(t / 0.12)
    # warm glow behind the bottle
    g = cv2.GaussianBlur(acc_a, (0, 0), 70) * 0.6 * ba
    out = 1 - (1 - out) * (1 - g[..., None] * glow_c)
    if fa > 0:                                            # reflection: mirrored copy below the base, fading out
        sc, x0, y0, w, h = box
        if y0 + h >= BASE - 2:
            rgb, al = bottle_at(sc)
            rf_rgb, rf_a = rgb[::-1], al[::-1]
            fadev = np.clip(1 - np.arange(rf_a.shape[0]) / 300, 0, 1) ** 1.7 * 0.45 * fa
            place(out, rf_rgb * fadev[:, None, None], rf_a * fadev[:, None], int(round(x0)), int(round(y0 + h)))
    out = acc_rgb * ba + out * (1 - acc_a[..., None] * ba)
    # spark burst at the landing
    u = t - 0.2
    if 0 < u < 1.3:
        cx, cy = W / 2, ANCHOR_Y
        for ang, spd, sz, life in SPK:
            if u > life:
                continue
            r = spd * eo(u / 0.8) * 0.8
            blob(out, cx + math.cos(ang) * r, cy + math.sin(ang) * r * 0.9 + 140 * u * u, sz * (1 - u / life * 0.5), spark_c, (1 - u / life) * 0.95)
    # drifting gold flakes (depth: far ones small and soft, near ones big bokeh)
    for x, y, z, sz, ph, vy in FL:
        yy = (y + vy * t * (0.5 + z)) % H
        xx = x + 18 * math.sin(ph + t * 0.8)
        tw = 0.5 + 0.5 * math.sin(ph * 3 + t * 4.0)
        r = sz * (0.6 + 2.6 * z ** 3)
        blob(out, xx, yy, r, spark_c, (0.25 + 0.55 * tw) * (0.35 if z > 0.85 else 1) * lift)
    # specular sweep across the bottle (1.3-2.3 s) and a pump glint
    sc, x0, y0, w, h = box
    q = (t - 1.3) / 1.0
    if 0 < q < 1:
        pos = -400 + eio(q) * (w + h * 0.5 + 800)
        band = np.exp(-((((XX - x0) + (YY - y0) * 0.5) - pos) / 60) ** 2) * math.sin(math.pi * q)
        out = 1 - (1 - out) * (1 - (band * acc_a * 0.6)[..., None])
    gq = (t - 2.5) / 0.6
    if 0 < gq < 1:
        s = math.sin(math.pi * gq)
        gx, gy = x0 + w * 0.62, y0 + h * 0.03
        star = (np.exp(-((XX - gx) / 3) ** 2 - ((YY - gy) / (60 * s + 1)) ** 2) + np.exp(-((YY - gy) / 3) ** 2 - ((XX - gx) / (60 * s + 1)) ** 2)) * s
        out = 1 - (1 - out) * (1 - star[..., None] * 0.9)
        blob(out, gx, gy, 10 * s + 1, np.array([1, 1, 1], np.float32), 0.8 * s)
    return np.clip(out * 255, 0, 255).astype(np.uint8), [round(v, 2) for v in box]


if __name__ == "__main__":
    if OUT.endswith(".jpg"):
        ims = [Image.fromarray(frame(int(t * FPS))[0]) for t in (0.1, 0.3, 0.6, 1.0, 1.8, 2.7, 4.8)]
        sheet = Image.new("RGB", (360 * len(ims), 640))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((360, 640), Image.LANCZOS), (360 * k, 0))
        sheet.save(OUT, quality=92)
        Image.fromarray(frame(int(3.0 * FPS))[0]).save(OUT.replace(".jpg", "_full.png"))
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    boxes = []
    for i in range(N):
        fr, box = frame(i)
        boxes.append(box)
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    json.dump({"boxes": boxes}, open(OUT.rsplit(".", 1)[0] + ".json", "w"))
    print("frames", N)
