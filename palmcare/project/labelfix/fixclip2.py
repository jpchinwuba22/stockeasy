"""Label replacement that sticks to the bottle (no drift): the real label is placed once on a keyframe (anchored on
the brown name banner), then every frame is registered to that keyframe with ECC affine alignment of the bottle
region (directly to the keyframe, so errors never accumulate) and the label follows that exact motion.
Usage: fixclip2.py IN.mp4 OUT.mp4 SPEC   SPEC defines ITEMS = [(label, roi_key, occlude, t_from, t_to, t_key[, min_fill])]"""
import runpy
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, "labelfix")
import labelpatch as lp  # noqa: E402

LABELS = {
    "milky": ("straight/out/milky.png", (0.07, 1.04, 0.07, 3.07)),
    "cacao": ("straight/out/cacao.png", (0.07, 1.75, 0.07, 3.4)),
}
W, H, FPS = 1080, 1920, 24
SC = 0.5   # registration runs at half resolution


def read_frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}:flags=lanczos", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    frames = []
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        frames.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
    return frames


def key_matrix(lbl, T):
    """2x3 matrix mapping cutout pixel coords -> frame coords for the banner-based placement T."""
    kx, ky, a, scx, scy, dcx, dcy = T
    ca, sa = np.cos(a), np.sin(a)
    A = np.array([[kx * ca, -ky * sa], [kx * sa, ky * ca]])
    t = np.array([dcx, dcy]) - A @ np.array([scx, scy])
    return np.hstack([A, t[:, None]])


def compose(Wf, M):
    """Wf (key->frame) after M (cutout->key)."""
    A = np.vstack([Wf, [0, 0, 1]]) @ np.vstack([M, [0, 0, 1]])
    return A[:2]


def render(lbl, M):
    rx0, ry0, rx1, ry1 = [int(round(v)) for v in lbl.reg]
    src = lbl.rgba.copy()
    region = np.zeros(src.shape[:2], np.float32)
    region[max(0, ry0):ry1, max(0, rx0):rx1] = 1
    src[..., 3] *= region
    warped = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    rgb = warped[..., :3]
    al = np.clip(warped[..., 3] / 255, 0, 1)
    feather = cv2.distanceTransform((al > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    al = al * np.clip(feather / lp.FEATHER, 0, 1)
    return rgb, al


def bottle_mask(lbl, M, grow=0.12):
    """Registration mask in key-frame coords: the label region grown a little (bottle edges are good features)."""
    rx0, ry0, rx1, ry1 = lbl.reg
    w, h = rx1 - rx0, ry1 - ry0
    pts = np.array([[rx0 - grow * w, ry0 - 0.15 * h], [rx1 + grow * w, ry0 - 0.15 * h], [rx1 + grow * w, ry1 + 0.03 * h],
                    [rx0 - grow * w, ry1 + 0.03 * h]], np.float32)
    fp = (M[:, :2] @ pts.T).T + M[:, 2]
    m = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(m, fp.astype(np.int32), 255)
    return m


def register(key_gray, mask, frame_gray, init):
    """ECC affine: returns 2x3 warp mapping key coords -> frame coords (full resolution)."""
    k = cv2.resize(key_gray, None, fx=SC, fy=SC, interpolation=cv2.INTER_AREA)
    f = cv2.resize(frame_gray, None, fx=SC, fy=SC, interpolation=cv2.INTER_AREA)
    m = cv2.resize(mask, None, fx=SC, fy=SC, interpolation=cv2.INTER_NEAREST)
    w = init.copy().astype(np.float32)
    w[:, 2] *= SC
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
    try:
        cc, w = cv2.findTransformECC(k, f, w, cv2.MOTION_AFFINE, crit, m, 5)
    except cv2.error:
        return None, 0.0
    w[:, 2] /= SC
    return w, cc


def gray(f):
    return cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32)


def main(src, dst, spec):
    items = runpy.run_path(spec)["ITEMS"]
    frames = read_frames(src)
    n = len(frames)
    out = list(frames)
    for it in items:
        name, roi, occl, t_from, t_to, t_key = it[:6]
        min_fill = it[6] if len(it) > 6 else 0.72
        lbl = lp.Label(*LABELS[name])
        aspect = (lbl.banner[2] - lbl.banner[0]) / (lbl.banner[3] - lbl.banner[1])
        ik = min(n - 1, int(round(t_key * FPS)))
        b = lp.find_banner(frames[ik], roi, aspect=aspect * 0.9, close=6, min_fill=min_fill)
        if b is None:
            print(f"{name}: no banner on keyframe {ik}")
            continue
        M = key_matrix(lbl, lp.similarity_from_banner(lbl.banner, b))
        kg = gray(frames[ik])
        mask = bottle_mask(lbl, M)
        i0, i1 = int(round(t_from * FPS)), min(n, int(round(t_to * FPS)))
        warps = {ik: np.array([[1, 0, 0], [0, 1, 0]], np.float32)}
        ccs = {}
        # walk outwards from the keyframe so each frame starts from its neighbour's warp
        for rng in (range(ik + 1, i1), range(ik - 1, i0 - 1, -1)):
            prev = warps[ik]
            for i in rng:
                w, cc = register(kg, mask, gray(frames[i]), prev)
                if w is None or cc < 0.55:
                    w = prev
                warps[i], ccs[i] = w, cc
                prev = w
        low = [i for i, c in ccs.items() if c < 0.55]
        print(f"{name}: frames {i0}-{i1}, key {ik}, cc min {min(ccs.values()) if ccs else 1:.3f}, weak {len(low)}")
        # light temporal smoothing of the warp parameters (3 frames) to remove sub-pixel shimmer, no lag
        idx = list(range(i0, i1))
        P = np.array([warps[i].ravel() for i in idx])
        Ps = P.copy()
        for k in range(1, len(idx) - 1):
            Ps[k] = (P[k - 1] + 2 * P[k] + P[k + 1]) / 4
        for k, i in enumerate(idx):
            Mf = compose(Ps[k].reshape(2, 3), M)
            rgb, al = render(lbl, Mf)
            out[i] = lp.composite(out[i], rgb, al, occlude_skin=occl)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "12", "-preset", "slow",
                          "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
    for f in out:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main(*sys.argv[1:4])
