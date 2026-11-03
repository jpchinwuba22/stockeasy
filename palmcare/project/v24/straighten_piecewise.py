# Level every line of the real jar label. The phone photo curls the label's lower right upward (rule and
# "Tone Refining" climb ~47 px, FACE MOISTURISER ~9 px, logo ~3 px). For each column, target rows of each line map to
# that line's measured source row (piecewise-linear between lines), so every baseline lands on one straight row.
# Real pixels only.
import cv2, numpy as np
D = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
j = cv2.imread(D + 'v24/jar_cut_orig.png', -1).astype(np.float32)
h, w = j.shape[:2]
x = np.arange(w, dtype=np.float32)
rule = np.interp(x, [227, 350, 460, 535, 591, 640], [579, 573, 562, 550, 532, 517])
bright = np.interp(x, [229, 350, 460, 491, 540, 591, 640], [600, 598, 594, 584, 572, 553, 538])
face = np.minimum(571 - 9 * np.clip((x - 330) / 150, 0, None) ** 2, rule - 8)
logo = 507 - 3 * np.clip((x - 330) / 161, 0, None) ** 2
T = np.array([430, 507, 571, 579, 600, 625, 700], np.float32)                  # target (level) rows
my = np.zeros((h, w), np.float32)
ys = np.arange(h, dtype=np.float32)
for c in range(w):
    S = np.array([430, logo[c], face[c], rule[c], bright[c], 625, 700], np.float32)
    my[:, c] = np.interp(ys, T, S)
mx = np.tile(x, (h, 1)).astype(np.float32)
out = cv2.remap(np.ascontiguousarray(j), mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)   # outline levelled too
cv2.imwrite(D + 'v24/jar_straight.png', np.clip(out, 0, 255).astype(np.uint8))
