# Unwrap the real jar label the way the photo bent it. A printed ring on a round jar seen from above appears as an
# ellipse arc: y(x) = y_front - b * (1 - sqrt(1 - ((x - xc) / a)^2)). Moving each column down by that amount (pure
# column shifts, smooth, same for a whole line) lays every line flat with no stretching, bending or rescaling of the
# letters. a = jar radius on the photo, xc = jar axis; b per row measured from the letter positions: logo and VITAMIN C
# are nearly flat on the photo, FACE MOISTURISER and everything below bow by b ~ 128 px. Real pixels only.
import cv2, numpy as np
D = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
j = cv2.imread(D + 'v24/jar_cut_orig.png', -1).astype(np.float32)
h, w = j.shape[:2]
XC, AX = 335.0, 328.0
x = np.arange(w, dtype=np.float32); y = np.arange(h, dtype=np.float32)
u = np.clip((x - XC) / AX, -0.97, 0.97)
f = 1 - np.sqrt(1 - u ** 2)                                   # 0 at the jar axis, grows to the edges
f = f * np.clip((x - 200) / 22, 0, 1)                          # palm-leaf column (flat on the photo) stays untouched
f = f * np.clip((652 - x) / 40, 0, 1)                          # past the last letter, ease off so the body shading stays smooth
b = np.interp(y, [0, 440, 515, 544, 552, h], [0, 12, 22, 25, 128, 128]).astype(np.float32)
mx, my = np.meshgrid(x, y)
my = (my - b[:, None] * f[None, :]).astype(np.float32)
out = cv2.remap(np.ascontiguousarray(j), mx.astype(np.float32), my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
# rows above FACE MOISTURISER sample only the logo / VITAMIN C zone: right of the logo, the curled tips of the lower
# lines (rule tail, "Refining") would otherwise be picked up twice, so that zone samples clean label paper there
paper = cv2.GaussianBlur(cv2.dilate(j[..., :3], np.ones((15, 15), np.uint8)), (0, 0), 6)
up = j.copy()
g8 = j[..., :3].astype(np.uint8)
ink = ((1 - np.clip(j[..., :3] / np.maximum(paper, 1), 0, 1).mean(2)) > 0.08).astype(np.uint8)
im = np.zeros(ink.shape, np.uint8); im[500:562, 500:] = ink[500:562, 500:]
im = cv2.dilate(im, np.ones((5, 5), np.uint8))
up[..., :3] = cv2.inpaint(g8, im, 6, cv2.INPAINT_TELEA).astype(np.float32)
out_up = cv2.remap(np.ascontiguousarray(up), mx.astype(np.float32), my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
wsel = np.clip((y - 544) / 6, 0, 1)[:, None, None]
out = out_up * (1 - wsel) + out * wsel
out[..., 3] = np.maximum(j[..., 3], out[..., 3])                # real outline, plus room for the levelled lines
cv2.imwrite(D + 'v24/jar_straight.png', np.clip(out, 0, 255).astype(np.uint8))
