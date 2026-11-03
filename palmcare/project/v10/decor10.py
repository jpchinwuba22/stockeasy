"""Clean a Flow set plate of the AI-invented decor bottles/jars on the blurred background shelves, so the only products
on screen are the real PalmCare ones composited later. The decor boxes are drawn on frame 0, follow the background's
camera drift (ECC affine on the shelf area), and are filled by inpainting at quarter resolution (the background is
soft focus, so this is seamless and stable). Fast foreground elements crossing them (milk ribbons, bubbles, citrus) are
protected and kept. Usage: decor10.py PLATE.mp4 CONFIG OUT(.mp4|.jpg)"""
import subprocess
import sys

import cv2
import numpy as np

W, H, FPS = 1080, 1920, 24
PLATE, CFG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CONFIGS = {
    "P1": dict(boxes=[(395, 0, 525, 205), (25, 330, 235, 575), (315, 395, 625, 585)], track=(0, 0, 1080, 700), citrus=False),
    "P2": dict(boxes=[(105, 175, 355, 455), (265, 555, 425, 805)], track=(0, 0, 1080, 760), citrus=True),
}
C = CONFIGS[CFG]


def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}:flags=lanczos", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            return
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)


def track(g0, g, m, M):
    try:
        _, M = cv2.findTransformECC(g0, g, M, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 1e-5), m, 3)
    except cv2.error:
        pass
    return M


def clean(fr, M):
    q = 4
    small = cv2.resize(fr, (W // q, H // q), interpolation=cv2.INTER_AREA)
    m0 = np.zeros((H, W), np.uint8)
    for x0, y0, x1, y1 in C["boxes"]:
        m0[y0:y1, x0:x1] = 255
    Mf = M.copy()
    m = cv2.warpAffine(m0, Mf, (W, H), flags=cv2.INTER_NEAREST)
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV).astype(int)
    keep = hsv[..., 2] > 238                                                           # milk ribbons / bubbles in front
    if C["citrus"]:
        keep |= (hsv[..., 1] > 110) & (hsv[..., 2] > 150)                                # flying citrus in front
    keep = cv2.dilate(keep.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    ms = cv2.resize(m, (W // q, H // q), interpolation=cv2.INTER_NEAREST)
    fill = cv2.inpaint(small, ms, 9, cv2.INPAINT_TELEA)
    fill = cv2.GaussianBlur(fill, (0, 0), 2.0)
    big = cv2.resize(fill, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    a = cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), 14)
    a = np.clip(a * 1.6, 0, 1) * (1 - cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 3))
    return (fr * (1 - a[..., None]) + big * a[..., None]).astype(np.uint8)


if __name__ == "__main__":
    it = frames(PLATE)
    fr0 = next(it)
    q = 4
    g0 = cv2.GaussianBlur(cv2.cvtColor(cv2.resize(fr0, (W // q, H // q)), cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1)
    tm = np.zeros((H // q, W // q), np.uint8)
    x0, y0, x1, y1 = C["track"]
    tm[y0 // q:y1 // q, x0 // q:x1 // q] = 255
    M = np.eye(2, 3, dtype=np.float32)
    jpg = OUT.endswith(".jpg")
    if not jpg:
        wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                               "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", OUT],
                              stdin=subprocess.PIPE)
    sel = []
    for i, fr in enumerate([fr0] + list(it)):
        g = cv2.GaussianBlur(cv2.cvtColor(cv2.resize(fr, (W // q, H // q)), cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1)
        Ms = M.copy(); Ms[:, 2] /= q
        Ms = track(g0, g, tm, Ms) if i else Ms
        M = Ms.copy(); M[:, 2] *= q
        out = clean(fr, M)
        if jpg:
            if i in (0, 80, 160, 230):
                sel.append(np.vstack([fr[0:900], out[0:900]]))
        else:
            wr.stdin.write(out.tobytes())
    if jpg:
        cv2.imwrite(OUT, cv2.resize(np.hstack(sel), None, fx=0.45, fy=0.45), [cv2.IMWRITE_JPEG_QUALITY, 88])
    else:
        wr.stdin.close()
        wr.wait()
