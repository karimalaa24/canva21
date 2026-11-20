"""Fill bright cream 'holes' inside the placed heap (kinam_ref keeps a cream floor gap that reads as a white chip): inpaint them from the wood around. usage: fill_holes.py empty.png filled.png out.png [minL]"""
import cv2, numpy as np, sys
from scipy.ndimage import binary_fill_holes
e = cv2.imread(sys.argv[1]).astype(np.float32); f = cv2.imread(sys.argv[2]); minL = float(sys.argv[4]) if len(sys.argv) > 4 else 150
wood = (np.abs(f.astype(np.float32) - e).mean(2) > 18).astype(np.uint8)
wood = cv2.morphologyEx(wood, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, l, st, _ = cv2.connectedComponentsWithStats(wood); big = max(range(1, n), key=lambda i: st[i, 4]); wood = (l == big)
inside = binary_fill_holes(cv2.morphologyEx(wood.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)))
hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); L = f.astype(np.float32).mean(2)
hole = inside & (L > minL) & (hsv[..., 1] < 90)
hole = binary_fill_holes(hole) & inside
# keep only holes fully surrounded by wood (not touching the open floor outside the heap)
n, l, st, _ = cv2.connectedComponentsWithStats(hole.astype(np.uint8)); out = np.zeros_like(hole)
outer = cv2.dilate((~inside).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
for i in range(1, n):
    c = l == i
    if not (c & outer).any() and st[i, 4] > 30: out |= c
m = cv2.dilate(out.astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
# clone real wood texture from the nearest offset whose source is all wood (looks like another piece), slightly shaded
r = f.astype(np.float32).copy(); ys, xs = np.where(m > 0); H, W = m.shape; best = None
for d in range(60, 400, 10):
    for dx, dy in [(-d, 0), (d, 0), (-d, -d // 3), (d, -d // 3), (0, -d // 2)]:
        y2, x2 = ys + dy, xs + dx
        if y2.min() < 0 or x2.min() < 0 or y2.max() >= H or x2.max() >= W: continue
        if wood[y2, x2].mean() > 0.97 and not (m[y2, x2] > 0).any(): best = (dx, dy); break
    if best: break
print('clone offset', best)
if best: r[ys, xs] = f[ys + best[1], xs + best[0]].astype(np.float32) * 0.85
else: r = cv2.inpaint(f, m, 9, cv2.INPAINT_TELEA).astype(np.float32) * 0.5
A = cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), 1.5)[..., None]
cv2.imwrite(sys.argv[3], np.clip(r * A + f * (1 - A), 0, 255).astype(np.uint8)); print('holes px', int(out.sum()))
