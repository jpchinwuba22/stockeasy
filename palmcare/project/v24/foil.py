# Even out the gold-foil shine on the real logo, "VITAMIN C" and palm leaf (phone-photo glare made some letters pale).
# Glyph shapes come from the photo (gold coverage = saturation + darkness vs the label paper); only the foil colour is
# made uniform, using the gold of the photo's own darker letters.
import cv2, numpy as np
j = cv2.imread('jar_straight.png', -1).astype(np.float32)
rgb = j[..., :3]
paper = cv2.GaussianBlur(cv2.dilate(rgb, np.ones((17, 17), np.uint8)), (0, 0), 6)
hsv = cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
php = cv2.cvtColor(np.clip(paper, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
dark = np.clip((paper.mean(2) - rgb.mean(2)) / 110, 0, 1)
sat = np.clip((hsv[..., 1] - php[..., 1] - 8) / 70, 0, 1)
a = np.maximum(dark, sat)
R = np.zeros(a.shape, np.float32); R[455:548, 222:515] = 1; R[455:615, 85:205] = 1   # logo, VITAMIN C, leaf
R = cv2.GaussianBlur(R, (0, 0), 3)
core = (a > 0.6) & (R > 0.5)
gold = np.median(rgb[core & (dark > 0.45)], 0)                                    # the photo's own deeper gold
print('gold BGR', gold.round(1), 'pixels', int(core.sum()))
a = np.clip(a * 1.25, 0, 1)
shade = (paper / np.maximum(paper.mean(2, keepdims=True), 1))                       # keep the jar's lighting
flat = paper * (1 - a[..., None]) + gold[None, None, :] * shade * (paper.mean(2, keepdims=True) / 235) * a[..., None]
out = rgb * (1 - R[..., None]) + flat * R[..., None]
j[..., :3] = out
cv2.imwrite('jar_straight.png', np.clip(j, 0, 255).astype(np.uint8))
