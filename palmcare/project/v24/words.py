import cv2, numpy as np
j = cv2.imread('jar_cut_orig.png', -1)
rgb = j[..., :3].astype(np.float32); A = j[..., 3]
paper = cv2.GaussianBlur(cv2.dilate(rgb, np.ones((15, 15), np.uint8)), (0, 0), 6)
r = np.clip(rgb / np.maximum(paper, 1), 0, 1)
inkv = 1 - r.mean(2)
y0, y1, x0, x1 = 548, 642, 215, 640
m = ((inkv > 0.14) & (A > 200)).astype(np.uint8)
m[:y0] = 0; m[y1:] = 0; m[:, :x0] = 0; m[:, x1:] = 0
n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
comps = [(i, st[i], cen[i]) for i in range(1, n) if st[i][4] >= 6]
print('components', len(comps))
for i, s, c in sorted(comps, key=lambda t: (t[2][1] // 12, t[2][0]))[:200]:
    print(i, 'x', s[0], 'y', s[1], 'w', s[2], 'h', s[3], 'a', s[4], 'c', np.round(c, 1))
np.save('cc.npy', {'lab': lab, 'st': st, 'cen': cen}, allow_pickle=True)
