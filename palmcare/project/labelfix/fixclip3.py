"""Label replacement v3: optional camera lock + drift-free label + clean relight.
- LOCK ranges: the bottle is registered to a keyframe (ECC affine on a bottle-only box) and every frame is warped back
  onto the keyframe, so a product standing on a counter is perfectly still in frame (the AI camera creep is removed);
  a small uniform zoom hides the borders.
- Labels: placed once on the keyframe (anchored on the brown name banner) and moved with the bottle's exact
  per-frame motion (ECC directly to the keyframe, so errors never accumulate).
- Relight: the clip's light is measured on the white bottle surface only (the old AI print is ignored), so the old
  banner can no longer shadow through the new label.
Usage: fixclip3.py IN.mp4 OUT.mp4 SPEC
SPEC defines ITEMS = [(label, roi_key, occlude, t_from, t_to, t_key[, min_fill])]
and optionally LOCK = [(t_from, t_to, t_key, (x0, y0, x1, y1))]"""
import runpy
import subprocess
import sys

import cv2
import numpy as np
from scipy import ndimage

sys.path.insert(0, "labelfix")
import labelpatch as lp  # noqa: E402
from fixclip2 import LABELS, W, H, FPS, read_frames, key_matrix, compose, render, bottle_mask, register, gray  # noqa: E402

LABELS = dict(LABELS)
LABELS.update({
    "citrus": ("straight/out/citrus.png", (0.02, 1.0, 0.02, 3.08)),
    "molecular": ("straight/out/molecular.png", (0.01, 1.33, 0.03, 3.17)),
})
ORANGE = {"citrus", "molecular"}
_brown = lp.brown_mask


def orange_mask(arr):
    h, s, v = lp.hsv(arr)
    return (h > 14) & (h < 40) & (s > 0.55) & (v > 0.30)


def use_mask(name):
    """Orange label bands (Video 2) vs brown ones (Video 1)."""
    lp.brown_mask = orange_mask if name in ORANGE else _brown


def track(frames, ik, i0, i1, mask):
    """Warps (key -> frame) for i0..i1-1, walking out from the keyframe."""
    kg = gray(frames[ik])
    warps = {ik: np.array([[1, 0, 0], [0, 1, 0]], np.float32)}
    ccs = {ik: 1.0}
    for rng in (range(ik + 1, i1), range(ik - 1, i0 - 1, -1)):
        prev = warps[ik]
        for i in rng:
            w, cc = register(kg, mask, gray(frames[i]), prev)
            if w is None or cc < 0.55:
                w = prev
            warps[i], ccs[i] = w, cc
            prev = w
    return warps, ccs


def smooth(warps, idx):
    P = np.array([warps[i].ravel() for i in idx])
    Ps = P.copy()
    for k in range(1, len(idx) - 1):
        Ps[k] = (P[k - 1] + 2 * P[k] + P[k + 1]) / 4
    return {i: Ps[k].reshape(2, 3) for k, i in enumerate(idx)}


def lock(frames, t_from, t_to, t_key, box):
    n = len(frames)
    i0, i1, ik = int(round(t_from * FPS)), min(n, int(round(t_to * FPS))), min(n - 1, int(round(t_key * FPS)))
    m = np.zeros((H, W), np.uint8)
    m[box[1]:box[3], box[0]:box[2]] = 255
    warps, ccs = track(frames, ik, i0, i1, m)
    idx = list(range(i0, i1))
    warps = smooth(warps, idx)
    # smallest centred zoom Z so that every output pixel maps inside its source frame
    c = np.array([W / 2, H / 2])
    corners = np.array([[0, 0], [W, 0], [0, H], [W, H]], np.float64)

    def ok(Z):
        k = c + (corners - c) / Z
        for i in idx:
            p = (warps[i][:, :2] @ k.T).T + warps[i][:, 2]
            if p[:, 0].min() < 0 or p[:, 1].min() < 0 or p[:, 0].max() > W or p[:, 1].max() > H:
                return False
        return True
    Z = 1.0
    while not ok(Z):
        Z += 0.002
    Zinv = np.array([[1 / Z, 0, c[0] - c[0] / Z], [0, 1 / Z, c[1] - c[1] / Z]])
    out = list(frames)
    for i in idx:
        M = compose(warps[i], Zinv)          # output -> key -> frame i
        out[i] = cv2.warpAffine(frames[i], M.astype(np.float32), (W, H), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                                borderMode=cv2.BORDER_REPLICATE)
    print(f"lock {t_from}-{t_to}: zoom {Z:.3f}, cc min {min(ccs.values()):.3f}")
    return out


def white_mask(rgb, A):
    """Plain bottle surface: bright, low-saturation pixels (no print, no skin)."""
    h, s, v = lp.hsv(np.clip(rgb, 0, 255).astype(np.uint8))
    L = lp.lum(rgb)
    ref = np.percentile(L[A > 0.5], 80) if (A > 0.5).any() else 230
    wm = (s < 0.22) & (L > ref - 22)
    return ndimage.binary_erosion(wm, iterations=2).astype(np.float32)


def composite(frame, rgb, al, occlude_skin=True, fg=None, vcap=0.82, smin=0.30, guard=True, shade=None):
    if al.max() <= 0:
        return frame
    f = frame.astype(np.float32)
    ys, xs = np.nonzero(al > 0)
    pad = 60
    y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + 1 + pad)
    x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + 1 + pad)
    F, P, A = f[y0:y1, x0:x1], rgb[y0:y1, x0:x1], al[y0:y1, x0:x1]
    sig = max(8.0, (xs.max() - xs.min()) / 6)
    # light on the bottle: normalised blur over white bottle pixels only, in clip and in label
    Ad = ndimage.binary_dilation(A > 0.02, iterations=pad // 2).astype(np.float32)
    wf = white_mask(F, A) * Ad
    wp = white_mask(P, A) * (A > 0.5)
    gw_f = ndimage.gaussian_filter(wf, sig) + 1e-4
    gw_p = ndimage.gaussian_filter(wp, sig) + 1e-4
    out = P.copy()
    for ch in range(3):
        fb = ndimage.gaussian_filter(F[..., ch] * wf, sig) / gw_f
        pb = ndimage.gaussian_filter(P[..., ch] * wp, sig) / gw_p
        out[..., ch] = P[..., ch] * np.clip(fb / (pb + 1.0), 0.45, 1.5)
    # keep small bright specks (droplets, speculars) from the clip
    L = lp.lum(F)
    th = L - ndimage.grey_opening(L, size=(5, 5))
    base = np.percentile(L[A > 0.5], 90) if (A > 0.5).any() else 240
    th = th * (L > base + 6)
    out = out + ndimage.gaussian_filter(np.clip(th - 10, 0, None), 0.7)[..., None] * 1.2
    m = A.copy()
    if occlude_skin:
        h, s, v = lp.hsv(F.astype(np.uint8))
        wv = np.percentile(v[A > 0.5], 75) if (A > 0.5).any() else 0.9
        skin = (h > 3) & (h < 40) & (s > smin) & (v > 0.12) & (v < wv * vcap)
        diff = np.abs(ndimage.gaussian_filter(L, 2) - ndimage.gaussian_filter(lp.lum(out), 2)) > 28
        # fingers reach in from outside the label: keep only skin blobs connected to skin outside the label region,
        # so the old AI banner (brown, but wholly inside the label) can never show through
        outside = A < 0.05
        cand = ndimage.binary_opening(skin & (diff | outside), iterations=3)
        lab, nn = ndimage.label(cand)
        occ = np.zeros_like(cand)
        if nn:
            sizes = ndimage.sum(cand, lab, range(1, nn + 1))
            outs = ndimage.sum(cand & outside, lab, range(1, nn + 1))
            keep = 1 + np.nonzero((sizes > 2500) & (outs > 400))[0]
            occ = np.isin(lab, keep) & ~outside
        # never let the clip replace the real brown banner/print itself
        if guard:
            realprint = ndimage.binary_dilation(lp.brown_mask(np.clip(P, 0, 255).astype(np.uint8)) & (A > 0.5), iterations=3)
            occ = occ & ~realprint
        occ = ndimage.binary_opening(occ, iterations=2)
        occ = ndimage.binary_dilation(occ, iterations=4)
        m = m * (1 - np.clip(ndimage.gaussian_filter(occ.astype(np.float32), 1.5) * 1.3, 0, 1))
    if fg is not None:      # foreground objects passing in front of the bottle (milk, rings, pearls) stay in front
        m = m * (1 - fg[y0:y1, x0:x1])
    if shade is not None:   # local shadows cast on the bottle (a hand passing close) darken the new label too
        out = out * shade[y0:y1, x0:x1, None]
    res = f.copy()
    res[y0:y1, x0:x1] = F * (1 - m[..., None]) + out * m[..., None]
    return np.clip(res, 0, 255).astype(np.uint8)


def _lapvar(img, m):
    g = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    lap = cv2.Laplacian(g, cv2.CV_32F, ksize=3)
    return float(lap[m].var()) if m.any() else 0.0


def fruit_mask(frame, al):
    """Citrus fruit passing in front of the bottle: bright saturated orange/yellow regions connected to the area
    outside the label (the bottle's own orange banner is darker and enclosed by white, so it never qualifies)."""
    h, s, v = lp.hsv(frame)
    m = (h > 12) & (h < 50) & (s > 0.45) & (v > 0.70)
    m = ndimage.binary_opening(m, iterations=2)
    lab, n = ndimage.label(m)
    if not n:
        return np.zeros(al.shape, np.float32)
    outside = al < 0.05
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    outs = ndimage.sum(m & outside, lab, range(1, n + 1))
    keep = 1 + np.nonzero((sizes > 3000) & (outs > 800))[0]
    m = ndimage.binary_fill_holes(np.isin(lab, keep))
    # grow into the rind / pith (paler, still warm and saturated, unlike the white bottle) within 30 px of the flesh
    rind = (h > 12) & (h < 62) & (s > 0.14) & (v > 0.55)
    near = ndimage.binary_dilation(m, iterations=30)
    grown = m.copy()
    for _ in range(30):
        grown = ndimage.binary_dilation(grown, iterations=1) & (rind | m) & near
    m = ndimage.binary_fill_holes(ndimage.binary_closing(grown, iterations=4))
    m = ndimage.binary_dilation(m, iterations=2)
    return np.clip(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.0) * 1.2, 0, 1)


def blur_for(frame, rgb, al, excl=None):
    """Defocus to apply to the sharp label so it matches the clip (rack focus): the blur at which the label's
    detail energy equals the clip's detail energy inside the label area."""
    m = al > 0.9
    if excl is not None:
        m &= excl < 0.05
    band = orange_mask(np.clip(rgb, 0, 255).astype(np.uint8))      # compare on the text-rich name banner only
    band = ndimage.binary_dilation(band, iterations=6) & m
    if band.sum() > 2000:
        m = band
    if m.sum() < 500:
        return 0.0
    target = _lapvar(frame, m)
    best, err = 0.0, 1e18
    for sg in np.arange(0.0, 9.01, 0.5):
        r = rgb if sg == 0 else cv2.GaussianBlur(rgb.astype(np.float32), (0, 0), sg)
        e = abs(np.log((_lapvar(r, m) + 1) / (target + 1)))
        if e < err:
            best, err = sg, e
    return best


def bottle_silhouette(frame, b):
    """White bottle body around the banner on the keyframe: bright low-saturation region connected to the banner,
    holes (print) filled, slightly eroded so the label never reaches the bottle edge."""
    h, s, v = lp.hsv(frame)
    white = (s < 0.16) & (v > 0.62)
    x0, y0, x1, y1 = [int(t) for t in b[:4]]
    m = white.copy()
    m[y0:y1, x0:x1] = True                       # the banner itself belongs to the bottle
    m = ndimage.binary_opening(m, iterations=2)
    lab, n = ndimage.label(m)
    keep = lab[(y0 + y1) // 2, (x0 + x1) // 2]
    m = lab == keep
    # fill each row between its extremes inside the label height (print, banner, text) -> solid bottle front
    m = ndimage.binary_closing(m, structure=np.ones((25, 3)), iterations=2)
    m = ndimage.binary_fill_holes(m)
    return ndimage.binary_erosion(m, iterations=4)


def patch(frames, out, it):
    n = len(frames)
    name, roi, occl, t_from, t_to, t_key = it[:6]
    min_fill = it[6] if len(it) > 6 and not isinstance(it[6], dict) else 0.72
    opts = next((x for x in it[6:] if isinstance(x, dict)), {})
    use_mask(name)
    lbl = lp.Label(*LABELS[name])
    aspect = (lbl.banner[2] - lbl.banner[0]) / (lbl.banner[3] - lbl.banner[1])
    ik = min(n - 1, int(round(t_key * FPS)))
    b = lp.find_banner(frames[ik], roi, aspect=aspect * 0.9, close=6, min_fill=min_fill)
    if b is None:
        print(f"{name}: no banner on keyframe {ik}")
        return
    M = key_matrix(lbl, lp.similarity_from_banner(lbl.banner, b, aniso=not opts.get("iso")))
    sil = None
    if opts.get("fitw"):
        # size the real label from the AI bottle's measured width (the AI draws its banner too wide for its bottle)
        sil = bottle_silhouette(frames[ik], b)
        cy = int((b[1] + b[3]) / 2)
        row = np.nonzero(sil[cy])[0]
        bx0, bx1 = row.min(), row.max()
        rx0, ry0, rx1, ry1 = lbl.reg
        k = opts["fitw"] * (bx1 - bx0) / (rx1 - rx0)
        ang = np.radians(b[4])
        scx, scy = (lbl.banner[0] + lbl.banner[2]) / 2, (lbl.banner[1] + lbl.banner[3]) / 2
        # horizontal: centre of the sticker on the bottle centre; vertical: banner centre on the AI banner centre
        stx = (rx0 + rx1) / 2
        T = (k, k, ang, stx, scy, (bx0 + bx1) / 2, (b[1] + b[3]) / 2)
        M = key_matrix(lbl, T)
        print(f"{name}: fit to bottle width {bx1 - bx0}px, scale {k:.3f}")
    i0, i1 = int(round(t_from * FPS)), min(n, int(round(t_to * FPS)))
    idx = list(range(i0, i1))
    if opts.get("static"):          # bottle measured still in frame: one placement for every frame
        warps = {i: np.array([[1, 0, 0], [0, 1, 0]], np.float32) for i in idx}
        print(f"{name}: frames {i0}-{i1}, key {ik}, static")
    else:
        bm = bottle_mask(lbl, M)
        if opts.get("ring"):
            # rigid parts only: bottle outline band + shoulders/pump; the AI's own label print (which morphs) is excluded
            rx0, ry0, rx1, ry1 = lbl.reg
            w, h = rx1 - rx0, ry1 - ry0
            inner = np.array([[rx0 + 0.10 * w, ry0 + 0.04 * h], [rx1 - 0.10 * w, ry0 + 0.04 * h],
                              [rx1 - 0.10 * w, ry1 - 0.04 * h], [rx0 + 0.10 * w, ry1 - 0.04 * h]], np.float32)
            fp = (M[:, :2] @ inner.T).T + M[:, 2]
            cut = np.zeros_like(bm)
            cv2.fillConvexPoly(cut, fp.astype(np.int32), 255)
            top = np.array([[rx0, ry0 - 0.55 * h], [rx1, ry0 - 0.55 * h], [rx1, ry0], [rx0, ry0]], np.float32)
            tp = (M[:, :2] @ top.T).T + M[:, 2]
            cv2.fillConvexPoly(bm, tp.astype(np.int32), 255)
            bm[cut > 0] = 0
            if opts.get("ring_skin"):        # never track the hand holding it
                hh, ss, vv = lp.hsv(frames[ik])
                skin = (hh > 3) & (hh < 40) & (ss > 0.22) & (vv > 0.15) & (vv < 0.92)
                bm[ndimage.binary_dilation(skin, iterations=12)] = 0
        warps, ccs = track(frames, ik, i0, i1, bm)
        print(f"{name}: frames {i0}-{i1}, key {ik}, cc min {min(ccs.values()):.3f}")
        warps = smooth(warps, idx)
    plate = None
    if opts.get("fg"):              # static shots: the median frame is the clean bottle; what differs is in front of it
        pr = opts.get("plate")
        pidx = list(range(int(pr[0] * FPS), int(pr[1] * FPS))) if pr else idx[::2]
        plate = np.median(np.stack([frames[i] for i in pidx]), axis=0).astype(np.float32)
    for i in idx:
        rgb, al = render(lbl, compose(warps[i], M))
        if sil is not None:      # never paint outside the bottle (moves with the bottle via the same warp)
            w = cv2.warpAffine(sil.astype(np.float32), warps[i].astype(np.float32), (W, H), flags=cv2.INTER_LINEAR)
            al = al * np.clip(cv2.GaussianBlur(w, (0, 0), 1.5) * 1.15 - 0.075, 0, 1)
        fg = None
        shade = None
        if plate is not None:
            ys, xs = np.nonzero(al > 0.02)
            y0, y1 = max(0, ys.min() - 90), min(H, ys.max() + 90)
            x0, x1 = max(0, xs.min() - 90), min(W, xs.max() + 90)
            f = frames[i][y0:y1, x0:x1].astype(np.float32)
            pl = plate[y0:y1, x0:x1]
            # remove slow light changes (light sweeps) before comparing
            gain = (ndimage.gaussian_filter(f, (40, 40, 0)) + 4) / (ndimage.gaussian_filter(pl, (40, 40, 0)) + 4)
            d = ndimage.gaussian_filter(np.abs(f - pl * gain).sum(-1), 1.5)
            # in front of the bottle = clearly different AND brighter than what the clean bottle shows there
            # (milk, cream ribbons, golden rings and pearls are all lighter than the print they cover)
            lf, lpl = lp.lum(f), lp.lum(pl * gain)
            brighter = (lf > lpl + 22) if opts.get("fg_bright", True) else True
            fgm = ndimage.binary_opening((d > opts.get("fg_thr", 70)) & brighter, iterations=1)
            # only objects that pass in front of the bottle from outside the label (milk ribbons, rings, splashes);
            # differences wholly inside the label (AI letters flickering) are never let through
            outside = al[y0:y1, x0:x1] < 0.05
            lab, n = ndimage.label(ndimage.binary_dilation(fgm, iterations=2))
            if n:
                outs = ndimage.sum(outside, lab, range(1, n + 1))
                keep = 1 + np.nonzero(outs > opts.get("fg_outs", 150))[0]
                fgm = np.isin(lab, keep) & ndimage.binary_dilation(fgm, iterations=2)
            else:
                fgm[:] = False
            if opts.get("fg_skin2"):      # hybrid: strict difference (keeps print exact) + solid skin body of the hand
                hsv = cv2.cvtColor(np.clip(f, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
                hh, ss, vv = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
                lo, hi = opts.get("skin_s", (118, 200))
                skin = (hh >= 3) & (hh <= 16) & (ss >= lo) & (ss <= hi) & (vv >= opts.get("skin_vmin", 135))
                skin = ndimage.binary_opening(skin, iterations=2)
                lab2, n2 = ndimage.label(skin)
                if n2:
                    outs2 = ndimage.sum(al[y0:y1, x0:x1] < 0.05, lab2, range(1, n2 + 1))
                    skin = np.isin(lab2, 1 + np.nonzero(outs2 > opts.get("fg_outs", 3000))[0])
                    skin = ndimage.binary_fill_holes(ndimage.binary_closing(skin, iterations=3))
                    if opts.get("fg_only_hand"):   # raw clip shows ONLY on the hand: skin body + bright nail beside it
                        hsv_v, hsv_s = vv, ss
                        nail = (hsv_v >= 165) & (hsv_s <= 95) & ndimage.binary_dilation(skin, iterations=opts.get("nail_reach", 22))
                        nail = nail & fgm
                        fgm = ndimage.binary_dilation(skin | ndimage.binary_closing(nail, iterations=2), iterations=1)
                    else:
                        fgm = fgm | ndimage.binary_dilation(skin, iterations=1)
            if opts.get("fg_skin"):       # keep only skin / nail colours: never the old print around the finger
                hsv = cv2.cvtColor(np.clip(f, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
                hh, ss, vv = hsv[..., 0], hsv[..., 1], hsv[..., 2]
                skin = ((hh <= 18) | (hh >= 170)) & (ss >= 28) & (ss <= 175) & (vv >= opts.get("skin_vmin", 110))
                fgm = fgm & ndimage.binary_opening(skin, iterations=1)
            if opts.get("fg_fill"):       # solid hands: no label showing through a finger's interior
                closed = ndimage.binary_closing(fgm, iterations=opts.get("fg_close", 4))
                fgm = ndimage.binary_dilation(ndimage.binary_fill_holes(closed) if opts.get("fg_holes", True) else closed,
                                              iterations=opts.get("fg_dil", 3))
                if opts.get("fg_keep"):     # a pixel that still matches the clean plate is old print, not finger
                    fgm &= ndimage.binary_closing(d > opts["fg_keep"], iterations=1)
            fg = np.zeros((H, W), np.float32)
            fg[y0:y1, x0:x1] = np.clip(ndimage.gaussian_filter(fgm.astype(np.float32), 1.2) * 1.2, 0, 1)
            if opts.get("fg_shade"):
                ratio = (ndimage.gaussian_filter(lf, 10) + 6) / (ndimage.gaussian_filter(lpl, 10) + 6)   # soft shadows only, never letter detail
                sh = np.clip(ratio, 0.35, 1.0)
                sh = np.where(sh < 0.93, sh, 1.0)
                shade = np.ones((H, W), np.float32)
                shade[y0:y1, x0:x1] = ndimage.gaussian_filter(sh, 2)
        if opts.get("fruit"):
            fm = fruit_mask(frames[i], al)
            fg = fm if fg is None else np.maximum(fg, fm)
        if opts.get("blur_curve"):
            ks = opts["blur_curve"]
            sig = float(np.interp(i, [k for k, _ in ks], [v for _, v in ks]))
            if sig > 0.3:
                rgb = cv2.GaussianBlur(rgb.astype(np.float32), (0, 0), sig)
                al = cv2.GaussianBlur(al.astype(np.float32), (0, 0), sig * 0.6)
        elif opts.get("defocus"):
            sig = blur_for(frames[i], rgb, al, fg)
            if sig > 0.3:
                rgb = cv2.GaussianBlur(rgb.astype(np.float32), (0, 0), sig)
                al = cv2.GaussianBlur(al.astype(np.float32), (0, 0), sig * 0.6)
        out[i] = composite(out[i], rgb, al, occlude_skin=occl, fg=fg, vcap=opts.get("vcap", 0.82), smin=opts.get("smin", 0.30), guard=opts.get("guard", True), shade=shade)


def main(src, dst, spec):
    sp = runpy.run_path(spec)
    frames = read_frames(src)
    for lk in sp.get("LOCK", []):
        frames = lock(frames, *lk)
    out = list(frames)
    for it in sp["ITEMS"]:
        patch(frames, out, it)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "12", "-preset", "slow",
                          "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
    for f in out:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main(*sys.argv[1:4])
