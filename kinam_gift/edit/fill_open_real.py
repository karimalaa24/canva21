"""Replace the dark tiger oud in the real open boxes (client video frame, 2x) with the approved Kinam heap (kinam_ref master).
Old wood is first erased to a cream floor, then the master heap is warped into each interior quad and clipped to it (never over a rim);
skin (fingers over the rim) stays on top. Free, local. usage: fill_open_real.py in2x.png out.png"""
import cv2, numpy as np, sys
M = cv2.imread('/home/user/canva21/.claude/skills/product-ad-fidelity/assets/box_masters/kinam_ref.png', -1).astype(np.float32)
src = np.float32([[75, 43], [404, 43], [404, 191], [75, 191]])
im = cv2.imread(sys.argv[1]); out = im.astype(np.float32); H, W = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int); f = im.astype(int)
skin = ((f[..., 2] > f[..., 1] + 18) & (f[..., 2] > 110) & (hsv[..., 1] > 50)).astype(np.uint8)
skin = cv2.dilate(cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)), np.ones((5, 5), np.uint8))
BOXES = [  # interior polygon (visible floor area between back wall and front rim), heap quad (TL TR BR BL; bottom goes under the front rim)
    ([(140, 1206), (510, 1206), (514, 1452), (106, 1452)], [[(95, 1222), (545, 1222), (545, 1426), (95, 1426)], [(80, 1292), (560, 1292), (560, 1510), (80, 1510)]]),
    ([(610, 1170), (1005, 1177), (1000, 1392), (598, 1382)], [[(565, 1190), (1040, 1196), (1040, 1400), (565, 1394)], [(555, 1258), (1050, 1264), (1050, 1482), (555, 1476)]]),
]
for poly, quads in BOXES:
    pm = np.zeros((H, W), np.uint8); cv2.fillPoly(pm, [np.array(poly, np.int32)], 1); pm &= (1 - skin)
    # cream floor (sampled from the back wall just above), darker toward the front = shadow under the heap
    x0, x1 = min(p[0] for p in poly), max(p[0] for p in poly); yb = min(p[1] for p in poly)
    cream = np.percentile(out[yb - 60:yb - 10, x0 + 30:x1 - 30].reshape(-1, 3), 75, axis=0)   # lit part of the cream back wall
    ys = np.arange(H)[:, None]; shade = np.clip(1.0 - 0.25 * (ys - yb) / 200, 0.75, 1.0)[..., None]   # floor: just under the back wall's shadow, lighter toward the front
    row = cv2.GaussianBlur(out[yb - 14:yb - 4].mean(0, keepdims=True), (0, 0), sigmaX=6, sigmaY=0.1)[0]   # back-wall colour per column
    gr = (row[:, 1] > row[:, 2] + 8); row[gr] = np.median(row[~gr], 0)                                       # green wall columns -> wall colour
    floor = row[None] * shade * np.ones((H, 1, 1))
    A = cv2.GaussianBlur(pm.astype(np.float32), (0, 0), 2.5)[..., None]; A[:yb - 4] *= 0   # keep the real back-wall line
    out = out * (1 - A) + floor * A
    for quad in quads:      # back layer first, then a lower front layer over it (dense fill, real-size pieces)
        T = cv2.getPerspectiveTransform(src, np.float32(quad)); wm = cv2.warpPerspective(M, T, (W, H), flags=cv2.INTER_CUBIC)
        a = (wm[..., 3] / 255) * pm; a = cv2.GaussianBlur(a, (0, 0), 0.8)[..., None]
        sh = cv2.GaussianBlur(a[..., 0], (0, 0), 8)[..., None]; out *= 1 - 0.5 * np.clip(np.roll(sh, 10, 0) - a, 0, 1) * pm[..., None]
        wood = cv2.GaussianBlur(wm[..., :3], (0, 0), 0.9)
        g = wood.mean(2, keepdims=True); wood = (g + (wood - g) * 0.85) * 0.80 + 12
        d = cv2.distanceTransform(pm, cv2.DIST_L2, 5); edge = np.clip(1 - d / 22, 0, 1)[..., None]
        wood = wood * (1 - 0.45 * edge)
        out = out * (1 - a) + wood * a
cv2.imwrite(sys.argv[2], np.clip(out, 0, 255).astype(np.uint8))
