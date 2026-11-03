"""Fit a bottle's left/right body edges on one frame from rough guesses (x_top, y_top, x_bot, y_bot)."""
import cv2, numpy as np
def frame(path, t):
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * 24))); return cv2.resize(cap.read()[1], (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
def fit(img, rough, win=45, n=60):
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.2)
    gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3))
    xt, yt, xb, yb = rough; pts = []
    for y in np.linspace(yt, yb, n).astype(int):
        xc = xt + (xb - xt) * (y - yt) / (yb - yt)
        a, c = int(max(0, xc - win)), int(min(img.shape[1] - 1, xc + win))
        row = gx[y, a:c]
        if row.max() > 8: pts.append((y, a + np.argmax(row)))
    P = np.array(pts, float)
    for _ in range(3):
        k, m = np.polyfit(P[:, 0], P[:, 1], 1); r = np.abs(P[:, 1] - (k * P[:, 0] + m)); P = P[r <= max(1.5, np.percentile(r, 70))]
    k, m = np.polyfit(P[:, 0], P[:, 1], 1)
    return k, m, float(np.median(np.abs(P[:, 1] - (k * P[:, 0] + m)))), len(P)
