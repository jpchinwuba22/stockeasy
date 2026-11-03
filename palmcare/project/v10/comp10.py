"""Collection video: place the REAL product cut-outs onto a Flow set plate (empty pedestals), locked to the plate's
camera drift (ECC affine tracking on the static set, milk/splash areas ignored), with soft contact shadows, a warm light
match from the set's sunlight, and gentle light wrap. Products are only ever uniformly scaled and moved with the set.
Usage: comp10.py PLATE.mp4 CONFIG OUT(.mp4|.jpg)"""
import json
import subprocess
import sys

import cv2
import numpy as np

W, H, FPS = 1080, 1920, 24
D = "/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/"
PLATE, CFG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

# product placements per plate: (cut-out, centre x, base y, height) in 1080x1920 plate coordinates
CONFIGS = {
    "P1": dict(track=(0, 1240, 1080, 1700), items=[("straight/out/milky.png", 308, 1318, 840),
                                                   ("straight/out/cacao.png", 768, 1415, 820)],
               light=(1.0, 0.97, 0.90), side=1),
    "P2": dict(track=(0, 1260, 1080, 1750), items=[("v3/assets/citrus_cut.png", 368, 1246, 800),
                                                   ("v3/assets/molecular_cut.png", 702, 1358, 790)],
               light=(1.0, 0.97, 0.90), side=-1),
    "P3": dict(track=(0, 1220, 1080, 1700), items=[("v4/assets/tropical_cut.png", 302, 1200, 830),
                                                   ("v4/assets/dermalight_cut.png", 712, 1322, 800)],
               light=(1.0, 0.96, 0.86), side=1),
    "P9": dict(track=(0, 1150, 1080, 1800), items=[("v9/box_straight.png", 728, 1126, 372),
                                                   ("v9/jar_cut.png", 418, 1312, 318)],
               light=(1.0, 0.97, 0.91), side=-1),
    "P9B": dict(track=(0, 1150, 1080, 1800), items=[("v9/box_straight.png", 511, 1316, 470)],
                light=(1.0, 0.97, 0.91), side=-1),
    "PA": dict(track=(0, 1150, 1080, 1850), items=[("v9/jar_cut.png", 511, 1318, 424)],
               light=(1.0, 0.98, 0.94), side=-1),
}
C = CONFIGS[CFG]


def load(p, h):
    im = cv2.imread(D + p, cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    ys, xs = np.nonzero(im[..., 3] > 8)
    im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    w = round(im.shape[1] * h / im.shape[0])
    im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    rgb = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2RGB)
    # light match: warm the product toward the set's sunlight and shade the side away from the window
    rgb = rgb * np.array(C["light"], np.float32)
    g = np.linspace(-1, 1, w)[None, :, None] * C["side"]
    rgb = rgb * (1 + 0.06 * g)
    return np.dstack([np.clip(rgb, 0, 1) * im[..., 3:4], im[..., 3:4]])


ITEMS = [(load(p, h), cx, by) for p, cx, by, h in C["items"]]


def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            return
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)


def track(fr0, fr, mask, init=None):
    """Affine warp mapping frame-0 coordinates to this frame, estimated on the static counter / pedestals.
    Coarse-to-fine (quarter, half, full resolution), seeded with the previous frame's warp so larger camera moves hold."""
    a0 = cv2.cvtColor(fr0, cv2.COLOR_RGB2GRAY).astype(np.float32)
    b0 = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY).astype(np.float32)
    M = (np.eye(2, 3, dtype=np.float32) if init is None else np.array(init, np.float32)).copy()
    for sc in (0.25, 0.5, 1.0):
        a = cv2.GaussianBlur(cv2.resize(a0, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA), (0, 0), 1.0)
        b = cv2.GaussianBlur(cv2.resize(b0, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA), (0, 0), 1.0)
        m = cv2.resize(mask, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_NEAREST)
        Ms = M.copy()
        Ms[:, 2] *= sc
        try:
            _, Ms = cv2.findTransformECC(a, b, Ms, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-6), m, 3)
            M = Ms.copy()
            M[:, 2] /= sc
        except cv2.error:
            pass
    return M


def comp(frame, M):
    out = frame.astype(np.float32) / 255
    for pm, cx, by in ITEMS:
        h, w = pm.shape[:2]
        x0, y0 = cx - w / 2, by - h
        # contact shadow on the pedestal top (soft ellipse), placed in frame-0 coords then warped with the set
        sh = np.zeros((H, W), np.float32)
        cv2.ellipse(sh, (int(cx + 14 * C["side"] * -1), int(by - 4)), (int(w * 0.62), int(w * 0.13)), 0, 0, 360, 1.0, -1)
        sh = cv2.GaussianBlur(sh, (0, 0), 14) * 0.55
        sh = cv2.warpAffine(sh, M, (W, H), flags=cv2.INTER_LINEAR)
        # the product follows the set by UNIFORM scale + translation only (never rotated, sheared or bent):
        # its base anchor goes where the set moved it, its size by the set's mean scale
        ax, ay = M @ np.array([cx, by, 1.0], np.float32)
        sc = float(np.sqrt(abs(np.linalg.det(M[:, :2]))))
        pw, ph = max(1, round(w * sc)), max(1, round(h * sc))
        pms = cv2.resize(pm, (pw, ph), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
        layer = np.zeros((H, W, 4), np.float32)
        xs, ys = int(round(ax - pw / 2)), int(round(ay - ph))
        xa, ya, xb, yb = max(0, xs), max(0, ys), min(W, xs + pw), min(H, ys + ph)
        if xb > xa and yb > ya:
            layer[ya:yb, xa:xb] = pms[ya - ys:yb - ys, xa - xs:xb - xs]
        out *= (1 - sh[..., None] * np.array([0.55, 0.62, 0.72], np.float32))
        # light wrap: the set's light bleeds a touch onto the product edges
        al = layer[..., 3]
        edge = np.clip(cv2.GaussianBlur(al, (0, 0), 3) - al * 0.7, 0, 1)[..., None]
        bgb = cv2.GaussianBlur(out, (0, 0), 6)
        out = layer[..., :3] + out * (1 - al[..., None])
        out = out * (1 - edge * 0.25) + bgb * edge * 0.25
    return np.clip(out * 255, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    it = frames(PLATE)
    fr0 = next(it)
    mask = np.zeros((H, W), np.uint8)
    x0, y0, x1, y1 = C["track"]
    mask[y0:y1, x0:x1] = 255
    if OUT.endswith(".jpg"):
        picks, sel, M = [0, 60, 120, 180, 230], [], None
        for i, fr in enumerate([fr0] + list(it)):
            M = track(fr0, fr, mask, M)                    # every frame, so the warp chains through the move
            if i in picks:
                sel.append(cv2.resize(comp(fr, M), (432, 768), interpolation=cv2.INTER_AREA))
        cv2.imwrite(OUT, cv2.cvtColor(np.hstack(sel), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    Ms, M = [], None
    for fr in [fr0] + list(it):
        M = track(fr0, fr, mask, M)
        Ms.append(M.tolist())
        p.stdin.write(comp(fr, M).tobytes())
    p.stdin.close()
    p.wait()
    json.dump(Ms, open(OUT.rsplit(".", 1)[0] + "_track.json", "w"))
    print("frames", len(Ms))
