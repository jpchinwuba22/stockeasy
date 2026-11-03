# Tonal-only enhancement of the real group photo (no pixels invented): neutral white balance from the white bottles,
# local contrast (CLAHE on lightness), gentle clarity/sharpening, slight vibrance, lifted shadows.
import cv2, numpy as np
a = cv2.imread('group_clean.png')
f = a.astype(np.float32)
g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
white = (g > np.percentile(g, 88)) & (f.max(2) - f.min(2) < 40)
wb = f[white].mean(0); f = f * (wb.mean() / wb)
f = np.clip(f * (235 / np.percentile(f[white].mean(1), 70)), 0, 255)
lab = cv2.cvtColor(f.astype(np.uint8), cv2.COLOR_BGR2LAB)
L = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8)).apply(lab[..., 0])
L = cv2.addWeighted(L, 0.55, lab[..., 0], 0.45, 0)
lab[..., 0] = L
f = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR).astype(np.float32)
f = (f + 0.55 * (f - cv2.GaussianBlur(f, (0, 0), 1.2)) + 0.15 * (f - cv2.GaussianBlur(f, (0, 0), 6))) * 1.03 + 4
hsv = cv2.cvtColor(np.clip(f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
hsv[..., 1] = np.clip(hsv[..., 1] * 1.10, 0, 255)
f = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
cv2.imwrite('group_enh.png', f)
cv2.imwrite('qa/enh_cmp.jpg', np.vstack([a[100:700, 0:1280], f[100:700, 0:1280]]))
