# Hero still: frame 180 of the Flow clip (her face, smile, hand), with Flow's tube REPLACED by the real tube photo
# (true proportions, matched light), her fingers kept in front. Output: still_tube.png (1080x1920).
import cv2, numpy as np
S = 1.5
f = cv2.resize(cv2.imread('tf/0180.png'), (1080, 1920), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
H, W = f.shape[:2]
poly = (np.float32([[84, 390], [378, 390], [326, 998], [142, 998]]) * S).astype(np.int32)
reg = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(reg, poly, 255)
reg = cv2.dilate(reg, np.ones((31, 31), np.uint8))
hsv = cv2.cvtColor(f.astype(np.uint8), cv2.COLOR_BGR2HSV)
skin = ((hsv[..., 1] > 80) & (hsv[..., 0] < 25) & (hsv[..., 2] > 40) & (hsv[..., 2] < 225)).astype(np.uint8)
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, lab, _, _ = cv2.connectedComponentsWithStats(skin)
keep = np.zeros(n, bool); keep[np.unique(lab[(reg == 0) & (skin > 0)])] = True; keep[0] = False
fingers = keep[lab].astype(np.uint8)
fingers = cv2.erode(fingers, np.ones((3, 3), np.uint8))           # no white tube fringe around the fingers
# the thumb (lighter, sunlit) needs a gentler skin test inside its own box
tb = np.zeros((H, W), np.uint8); tb[int(700 * S):int(910 * S), int(305 * S):int(390 * S)] = 1
th_ = ((hsv[..., 1] > 30) & (hsv[..., 0] < 25) & (hsv[..., 2] < 245)).astype(np.uint8) & tb
th_ = cv2.morphologyEx(th_, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n2, l2, st2, _ = cv2.connectedComponentsWithStats(th_)
if n2 > 1:
    th_ = (l2 == 1 + np.argmax(st2[1:, 4])).astype(np.uint8)
    cs, _ = cv2.findContours(th_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); th_[:] = 0; cv2.drawContours(th_, cs, -1, 1, -1)
fingers = np.maximum(fingers, th_)
# 1) remove Flow's tube (everything in the region that is not finger)
hole = ((reg > 0) & (fingers == 0)).astype(np.uint8) * 255
sm = cv2.resize(f.astype(np.uint8), (W // 3, H // 3), interpolation=cv2.INTER_AREA)
hs = cv2.resize(hole, (W // 3, H // 3), interpolation=cv2.INTER_NEAREST)
inp = cv2.resize(cv2.inpaint(sm, hs, 9, cv2.INPAINT_TELEA), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
inp = cv2.GaussianBlur(inp, (0, 0), 6)
base = np.where(hole[..., None] > 0, inp, f)
# 2) the real tube, true proportions, matched to the scene light
t = cv2.imread('assets/tube_cut.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
th = int(round((985 - 404) * S)); tw = int(round(t.shape[1] * th / t.shape[0]))
t = cv2.resize(t, (tw, th), interpolation=cv2.INTER_AREA)
rgb, al = t[..., :3], t[..., 3] / 255
old_white = np.median(f[(reg > 0) & (fingers == 0) & (hsv[..., 2] > 180)], 0)
new_white = np.median(rgb[(al > 0.9) & (rgb.mean(2) > 180)], 0)
rgb = np.clip(rgb * (old_white / new_white), 0, 255)
# soft sunlight from the left like the scene: gentle horizontal falloff
gx = np.linspace(1.04, 0.93, tw)[None, :, None]; rgb = np.clip(rgb * gx, 0, 255)
cx, top = int(232 * S), int(404 * S)
x0 = cx - tw // 2
out = base.copy()
sh = np.zeros((H, W), np.float32); sh[top:top + th, x0:x0 + tw] = al
sh = cv2.GaussianBlur(np.roll(np.roll(sh, 14, 0), 10, 1), (0, 0), 14) * 0.35
out = out * (1 - sh[..., None])
A = np.zeros((H, W), np.float32); A[top:top + th, x0:x0 + tw] = al
C = np.zeros_like(f); C[top:top + th, x0:x0 + tw] = rgb
out = out * (1 - A[..., None]) + C * A[..., None]
# 3) her fingers back in front of the tube
fm = cv2.GaussianBlur(fingers.astype(np.float32), (0, 0), 1.2)[..., None]
out = out * (1 - fm) + f * fm
cv2.imwrite('still_tube.png', np.clip(out, 0, 255).astype(np.uint8))
cv2.imwrite('qa/still_crop.jpg', np.clip(out, 0, 255).astype(np.uint8)[450:1620, 0:760])
