"""Replace AI-rendered PalmCare labels with the real label, frame by frame.
The AI clips copy the label layout but garble the small print, so the real label (from the straightened product
photo) is mapped onto each bottle using its brown name banner as the anchor: the banner is found per frame, the
transform is smoothed over time, the real label is relit to the clip's shading (low-frequency gain), bright
highlights (water droplets, specular) from the clip are kept on top, and fingers over the label stay in front.
Frames are upscaled to 1080x1920 first so the replaced label is sharper than the source."""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from scipy.ndimage import map_coordinates

OW, OH = 1080, 1920
FEATHER = 9.0


def hsv(arr):
    a = arr.astype(np.float32) / 255
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn + 1e-6
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, d / (mx + 1e-6), 0)
    return h, s, mx


def brown_mask(arr):
    h, s, v = hsv(arr)
    return (h > 8) & (h < 42) & (s > 0.38) & (v > 0.22) & (v < 0.80)


def find_banner(arr, roi, aspect=None, close=3, min_fill=0.72, hclose=0):
    """Largest rectangular brown blob inside roi -> (x0, y0, x1, y1, angle_deg) in full-frame coords."""
    x0, y0, x1, y1 = [int(v) for v in roi]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(arr.shape[1], x1), min(arr.shape[0], y1)
    m = brown_mask(arr[y0:y1, x0:x1])
    m = ndimage.binary_opening(m, iterations=1)
    m = ndimage.binary_closing(m, iterations=close)
    if hclose:   # bridge a light vertical gap through the banner (glare)
        m = ndimage.binary_closing(m, structure=np.ones((1, hclose), bool))
    lab, n = ndimage.label(m)
    objs = [(i, sl) for i, sl in enumerate(ndimage.find_objects(lab), 1)
            if sl[1].stop - sl[1].start >= 12 and sl[0].stop - sl[0].start >= 10]
    cands = [((sl[0].start, sl[0].stop, sl[1].start, sl[1].stop), (i,)) for i, sl in objs]
    # a glare streak can split the banner in two: also try side-by-side pairs at the same height
    for a in range(len(objs)):
        for b in range(a + 1, len(objs)):
            (ia, sa), (ib, sb) = objs[a], objs[b]
            ov = min(sa[0].stop, sb[0].stop) - max(sa[0].start, sb[0].start)
            hmin = min(sa[0].stop - sa[0].start, sb[0].stop - sb[0].start)
            gap = max(sa[1].start, sb[1].start) - min(sa[1].stop, sb[1].stop)
            wsum = (sa[1].stop - sa[1].start) + (sb[1].stop - sb[1].start)
            if ov > 0.7 * hmin and gap < 0.12 * wsum:
                cands.append(((min(sa[0].start, sb[0].start), max(sa[0].stop, sb[0].stop),
                               min(sa[1].start, sb[1].start), max(sa[1].stop, sb[1].stop)), (ia, ib)))
    best, score = None, 0
    for (r0, r1, c0, c1), ids in cands:
        hh, ww = r1 - r0, c1 - c0
        if ww < 20 or hh < 10:
            continue
        comp = np.isin(lab[r0:r1, c0:c1], ids)
        fill = comp.sum() / (hh * ww)
        asp = ww / hh
        ok = fill > min_fill and 0.9 < asp < 4.5
        if aspect:
            ok = ok and abs(np.log(asp / aspect)) < 0.45
        if ok and fill * ww * hh > score:
            best, score = ((slice(r0, r1), slice(c0, c1)), comp), fill * ww * hh
    if best is None:
        return None
    sl, comp = best
    ys, xs = np.nonzero(comp)
    # tilt from the top edge of the banner
    cols = np.arange(comp.shape[1])
    tops = np.array([np.argmax(comp[:, c]) if comp[:, c].any() else np.nan for c in cols], np.float32)
    good = ~np.isnan(tops)
    lo, hi = int(len(cols) * 0.15), int(len(cols) * 0.85)
    sel = good.copy()
    sel[:lo] = False
    sel[hi:] = False
    ang = 0.0
    if sel.sum() > 8:
        ang = np.degrees(np.arctan(np.polyfit(cols[sel], tops[sel], 1)[0]))
    return (x0 + sl[1].start, y0 + sl[0].start, x0 + sl[1].stop, y0 + sl[0].stop, float(ang))


class Label:
    """Real label source from a straightened cutout: banner box + the front-label region to transplant."""

    def __init__(self, path, region):
        im = Image.open(path).convert("RGBA")
        self.rgba = np.asarray(im).astype(np.float32)
        b = find_banner(self.rgba[..., :3].astype(np.uint8) * (self.rgba[..., 3:] > 128), (0, 0, im.width, im.height))
        assert b, "no banner in cutout " + path
        self.banner = b[:4]
        bx0, by0, bx1, by1 = self.banner
        bw, bh = bx1 - bx0, by1 - by0
        # region given relative to the banner: (left, top, right, bottom) in banner widths/heights
        l, t, r, btm = region
        self.reg = (bx0 - l * bw, by0 - t * bh, bx1 + r * bw, by1 + btm * bh)


def similarity_from_banner(src_banner, dst, aniso=True):
    sx0, sy0, sx1, sy1 = src_banner
    dx0, dy0, dx1, dy1, ang = dst
    kx = (dx1 - dx0) / (sx1 - sx0)
    ky = (dy1 - dy0) / (sy1 - sy0)
    ky = (kx * ky) ** 0.5 if aniso else kx    # vertical: halfway (geometric) between width and height fits
    scx, scy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    dcx, dcy = (dx0 + dx1) / 2, (dy0 + dy1) / 2
    return kx, ky, np.radians(ang), scx, scy, dcx, dcy


def render_patch(lbl, T, shape):
    """Warp the label region into frame space. Returns rgb (H,W,3) and alpha (H,W)."""
    kx, ky, a, scx, scy, dcx, dcy = T
    H, W = shape
    rx0, ry0, rx1, ry1 = lbl.reg
    # frame bbox of the warped region
    corners = np.array([[rx0, ry0], [rx1, ry0], [rx0, ry1], [rx1, ry1]]) - [scx, scy]
    ca, sa = np.cos(a), np.sin(a)
    px, py = corners[:, 0] * kx, corners[:, 1] * ky
    fx = dcx + (px * ca - py * sa)
    fy = dcy + (px * sa + py * ca)
    bx0, bx1 = int(max(0, fx.min() - 4)), int(min(W, fx.max() + 5))
    by0, by1 = int(max(0, fy.min() - 4)), int(min(H, fy.max() + 5))
    rgb = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W), np.float32)
    if bx1 <= bx0 or by1 <= by0:
        return rgb, al
    yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
    u, v = xx - dcx, yy - dcy
    sxs = scx + (u * ca + v * sa) / kx
    sys_ = scy + (-u * sa + v * ca) / ky
    inside = (sxs >= rx0) & (sxs <= rx1) & (sys_ >= ry0) & (sys_ <= ry1)
    for c in range(4):
        ch = map_coordinates(lbl.rgba[..., c], [sys_, sxs], order=3, mode="constant", cval=0)
        if c < 3:
            rgb[by0:by1, bx0:bx1, c] = ch
        else:
            al[by0:by1, bx0:bx1] = np.clip(ch / 255, 0, 1) * inside
    # feather the region edge (2.5 px in frame space)
    feather = ndimage.distance_transform_edt(al > 0.5)
    al = al * np.clip(feather / FEATHER, 0, 1)
    return rgb, al


def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def composite(frame, rgb, al, occlude_skin=True, keep_highlights=True):
    if al.max() <= 0:
        return frame
    f = frame.astype(np.float32)
    ys, xs = np.nonzero(al > 0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    w = x1 - x0
    sig = max(6.0, w / 7)
    F = f[y0:y1, x0:x1]
    P = rgb[y0:y1, x0:x1]
    A = al[y0:y1, x0:x1]
    # relight: per-channel low-frequency gain so the real label takes the clip's light and colour cast
    wts = ndimage.gaussian_filter(A, sig) + 1e-4
    out = P.copy()
    for c in range(3):
        fb = ndimage.gaussian_filter(F[..., c] * A, sig) / wts
        pb = ndimage.gaussian_filter(P[..., c] * A, sig) / wts
        out[..., c] = P[..., c] * np.clip(fb / (pb + 1.0), 0.4, 1.6)
    if keep_highlights:
        # only small bright specks (water droplets, speculars): white top-hat ignores the white around AI letters
        L = lum(F)
        th = L - ndimage.grey_opening(L, size=(5, 5))
        base = np.percentile(L[A > 0.5], 90) if (A > 0.5).any() else 240
        th = th * (L > base + 6)             # only specks brighter than the bottle white (not gaps between AI letters)
        hi = ndimage.gaussian_filter(np.clip(th - 10, 0, None), 0.7)[..., None]
        out = out + hi * 1.2
    m = A.copy()
    if occlude_skin:
        h, s, v = hsv(F.astype(np.uint8))
        # skin is clearly darker and more saturated than the (warm-lit) white bottle
        wv = np.percentile(v[A > 0.5], 75) if (A > 0.5).any() else 0.9
        skin = (h > 3) & (h < 40) & (s > 0.30) & (v > 0.12) & (v < wv * 0.82)
        diff = np.abs(ndimage.gaussian_filter(lum(F), 2) - ndimage.gaussian_filter(lum(out), 2)) > 28
        # fingers are big solid blobs; brown label text (also "skin-coloured") is thin, so open hard and drop small parts
        occ = ndimage.binary_opening(skin & diff, iterations=6)
        lab, n = ndimage.label(occ)
        if n:
            sizes = ndimage.sum(occ, lab, range(1, n + 1))
            occ = np.isin(lab, 1 + np.nonzero(sizes > 2500)[0])
        occ = ndimage.binary_dilation(occ, iterations=4)
        occf = ndimage.gaussian_filter(occ.astype(np.float32), 1.5)
        m = m * (1 - np.clip(occf * 1.3, 0, 1))
    res = f.copy()
    res[y0:y1, x0:x1] = F * (1 - m[..., None]) + out * m[..., None]
    return np.clip(res, 0, 255).astype(np.uint8)


def smooth_tracks(tracks, k=5):
    """Median then mean smoothing of per-frame banner boxes (None = missing -> interpolated)."""
    arr = np.array([t if t is not None else [np.nan] * 5 for t in tracks], np.float64)
    for c in range(5):
        col = arr[:, c]
        idx = np.arange(len(col))
        good = ~np.isnan(col)
        if good.sum() == 0:
            return None
        col[~good] = np.interp(idx[~good], idx[good], col[good])
        med = ndimage.median_filter(col, size=k, mode="nearest")
        arr[:, c] = ndimage.uniform_filter1d(med, size=k, mode="nearest")
    return arr
