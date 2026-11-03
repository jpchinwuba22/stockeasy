"""Straight, colour-true cut-outs of the real Vitamin C Face Moisturiser box (perspective-rectified from camera geometry)
and jar (GrabCut seeded from its cylinder outline)."""
import cv2
import numpy as np

# ---------- box: rectify the front face ----------
im = cv2.imread("photos/box_front.jpg")
H0, W0 = im.shape[:2]
f, cx, cy = 1514.0, W0 / 2, H0 / 2
TL, TR, BR, BL = (230, 555), (1184, 555), (1132, 1228), (293, 1243)
K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]])
Ki = np.linalg.inv(K)
def ray(p):
    return Ki @ np.array([p[0], p[1], 1.0])
l1 = np.cross([*TL, 1], [*BL, 1]); l2 = np.cross([*TR, 1], [*BR, 1])
vv = np.cross(l1, l2)                                    # vertical vanishing point
dv = Ki @ vv; dv /= np.linalg.norm(dv)
h1 = np.cross([*TL, 1], [*TR, 1]); h2 = np.cross([*BL, 1], [*BR, 1])
vh = np.cross(h1, h2)
dh = Ki @ vh if abs(vh[2]) > 1e-9 else np.array([vh[0], vh[1], 0.0])
dh /= np.linalg.norm(dh)
n = np.cross(dh, dv)
P = {k: ray(p) / (n @ ray(p)) for k, p in dict(TL=TL, TR=TR, BR=BR, BL=BL).items()}
wid = (np.linalg.norm(P["TR"] - P["TL"]) + np.linalg.norm(P["BR"] - P["BL"])) / 2
hei = (np.linalg.norm(P["BL"] - P["TL"]) + np.linalg.norm(P["BR"] - P["TR"])) / 2
print("box aspect w/h", round(wid / hei, 3))
OW = 1100; OH = int(round(OW * hei / wid))
M = cv2.getPerspectiveTransform(np.float32([TL, TR, BR, BL]), np.float32([[0, 0], [OW, 0], [OW, OH], [0, OH]]))
box = cv2.warpPerspective(im, M, (OW, OH), flags=cv2.INTER_LANCZOS4)
# white balance from the plain white top band of the front (above the logo)
ref = box[int(OH * 0.03):int(OH * 0.10), int(OW * 0.05):int(OW * 0.55)].reshape(-1, 3).astype(np.float32)
g = np.clip(ref.mean(0).max() / ref.mean(0), 1.0, 1.35) * np.clip(246 / ref.mean(0).max(), 1.0, 1.25)
print("box gains", g.round(3))
box = np.clip(box.astype(np.float32) * g, 0, 255).astype(np.uint8)
a = np.full((OH, OW), 255, np.uint8)
cv2.imwrite("box_straight.png", np.dstack([box, a]))

# ---------- jar: GrabCut from its cylinder outline ----------
im = cv2.imread("photos/jar_front.jpg")
H0, W0 = im.shape[:2]
shape = np.zeros((H0, W0), np.uint8)
cv2.ellipse(shape, (662, 738), (300, 72), 0, 0, 360, 255, -1)          # lid top
cv2.rectangle(shape, (363, 738), (962, 960), 255, -1)                   # lid sides
cv2.rectangle(shape, (327, 885), (997, 1080), 255, -1)                  # gold collar
cv2.rectangle(shape, (334, 1060), (990, 1097), 255, -1)                 # body
cv2.ellipse(shape, (662, 1097), (328, 207), 0, 0, 180, 255, -1)         # bottom curve, fitted to the measured bottom edge
mask = np.full((H0, W0), cv2.GC_BGD, np.uint8)
mask[cv2.dilate(shape, np.ones((61, 61), np.uint8)) > 0] = cv2.GC_PR_BGD
mask[shape > 0] = cv2.GC_PR_FGD
mask[cv2.erode(shape, np.ones((41, 41), np.uint8)) > 0] = cv2.GC_FGD
bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
cv2.grabCut(im, mask, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
n_, lab, st, _ = cv2.connectedComponentsWithStats(m)
m = np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
m = cv2.bitwise_and(m, cv2.dilate(shape, np.ones((9, 9), np.uint8)))   # never outside the jar's own outline
m = cv2.GaussianBlur(m, (0, 0), 1.2)
x, y, w, h = cv2.boundingRect((m > 128).astype(np.uint8))
jar = im[y:y + h, x:x + w].astype(np.float32)
ref = im[1150:1230, 380:520].reshape(-1, 3).astype(np.float32)                 # plain white body left of the logo
g = np.clip(ref.mean(0).max() / ref.mean(0), 0.85, 1.25)
g *= np.clip(226 / (ref.mean(0) * g).max(), 1.0, 1.15)
print("jar gains", g.round(3), "bbox", x, y, w, h)
jar = np.clip(jar * g, 0, 255).astype(np.uint8)
cv2.imwrite("jar_cut.png", np.dstack([jar, m[y:y + h, x:x + w]]))

# preview on dark and light backgrounds
def comp(p, bgc):
    c = cv2.imread(p, cv2.IMREAD_UNCHANGED).astype(np.float32)
    al = c[..., 3:] / 255
    return (c[..., :3] * al + np.array(bgc, np.float32) * (1 - al)).astype(np.uint8)
b, j = comp("box_straight.png", (40, 30, 30)), comp("jar_cut.png", (40, 30, 30))
j2 = comp("jar_cut.png", (230, 235, 240))
hh = 700
row = [cv2.resize(x_, (int(x_.shape[1] * hh / x_.shape[0]), hh)) for x_ in (b, j, j2)]
cv2.imwrite("chk_cut.jpg", np.hstack(row))
