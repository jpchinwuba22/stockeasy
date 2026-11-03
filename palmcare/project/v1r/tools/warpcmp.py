"""ECC warps of source frames to a keyframe with two masks: label region vs. lower bottle body + sides."""
import sys
import cv2
import numpy as np
sys.path.insert(0, "labelfix")
from fixclip2 import read_frames, register, gray
src, ik, i0, i1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
boxes = [[int(v) for v in b.split(",")] for b in sys.argv[5:]]
F = read_frames(src)
kg = gray(F[ik])
res = []
for b in boxes:
    m = np.zeros((1920, 1080), np.uint8)
    m[b[1]:b[3], b[0]:b[2]] = 255
    out = {}
    for rng in (range(ik, i1), range(ik - 1, i0 - 1, -1)):
        prev = np.array([[1, 0, 0], [0, 1, 0]], np.float32)
        for i in rng:
            w, cc = register(kg, m, gray(F[i]), prev)
            if w is None:
                w = prev
            out[i] = (w, cc)
            prev = w
    res.append(out)
cx, cy = 510, 1300
for i in range(i0, i1, 3):
    s = []
    for out in res:
        w, cc = out[i]
        p = w[:, :2] @ np.array([cx, cy]) + w[:, 2]
        s.append(f"({p[0]-cx:+6.1f},{p[1]-cy:+6.1f}) sc{np.sqrt(abs(np.linalg.det(w[:, :2]))):.3f} cc{cc:.2f}")
    print(i, "  ".join(s))
