"""Remove small light specks inside the oud fill: (a) lining visible through tiny ENCLOSED holes between whole pieces,
(b) tiny pale crumbs at piece edges. Only small connected components are touched (the cream at the back and the wood
grain stay as they are); each speck is filled from the surrounding wood (inpaint), not darkened.
usage: python fix_specks.py empty_raw.png filled.png out.png"""
import cv2, numpy as np, sys
from scipy.ndimage import binary_fill_holes
raw, fil, out = sys.argv[1:4]; FAC = float(sys.argv[4]) if len(sys.argv) > 4 else 0.82
R = cv2.imread(raw); F = cv2.imread(fil)
wood = (np.abs(F.astype(int) - R.astype(int)).max(2) > 10)
wood = cv2.morphologyEx(wood.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
holes = binary_fill_holes(wood) & ~wood
L = cv2.cvtColor(F, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32)
ring = (cv2.dilate(wood.astype(np.uint8), np.ones((41, 41), np.uint8)) > 0) & ~wood & (L > 120)
linL = float(np.median(L[ring])) if ring.sum() > 100 else 200.0
pale = wood & (L > FAC * linL)
cand = (holes | pale).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(cand, connectivity=8)
speck = np.zeros_like(cand)
for i in range(1, n):
    if st[i, 4] <= 350: speck[lab == i] = 1
speck = cv2.dilate(speck, np.ones((3, 3), np.uint8))
O = cv2.inpaint(F, speck * 255, 4, cv2.INPAINT_TELEA)
cv2.imwrite(out, O); print(out, 'specks', int((st[1:, 4] <= 350).sum()) if n > 1 else 0, 'px', int(speck.sum()), 'lining L', round(linL))
