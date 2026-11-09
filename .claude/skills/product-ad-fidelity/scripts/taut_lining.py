"""Make a wrinkled satin floor look like a fitted, taut lining: replace the floor by a smooth fitted shading
(quadratic in x,y per channel), keep the walls, add a soft crease shadow along the back/right walls."""
import cv2, numpy as np, sys, json
src, out, poly = sys.argv[1], sys.argv[2], np.array(json.loads(sys.argv[3]), np.int32)
im = cv2.imread(src).astype(np.float32); H, W = im.shape[:2]
fm = np.zeros((H, W), np.uint8); cv2.fillPoly(fm, [poly], 1)
lab = cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.int16)
opn = ((lab[..., 1] >= 124) & (lab[..., 0] > 60)).astype(np.uint8)          # cream only, never the green rim
opn = cv2.morphologyEx(opn, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
opn &= cv2.dilate(fm, np.ones((61, 61), np.uint8))
cn_, _ = cv2.findContours(opn, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); opf = np.zeros_like(opn)
cv2.fillConvexPoly(opf, cv2.convexHull(max(cn_, key=cv2.contourArea)), 1)   # straight along the rim: fold shadows / specks filled
fm &= cv2.erode(opf, np.ones((5, 5), np.uint8)); keep = opf
inner = cv2.erode(fm, np.ones((15, 15), np.uint8)) > 0
ys, xs = np.where(inner); sel = np.random.RandomState(0).choice(len(xs), min(40000, len(xs)), replace=False)
x = xs[sel] / W; y = ys[sel] / H
Amat = np.c_[np.ones_like(x), x, y, x * x, x * y, y * y]
X, Y = np.meshgrid(np.arange(W) / W, np.arange(H) / H)
B = np.dstack([np.ones_like(X), X, Y, X * X, X * Y, Y * Y]).astype(np.float32)
fit = np.zeros_like(im)
for c in range(3):
    v = im[ys[sel], xs[sel], c]
    co = np.linalg.lstsq(Amat, v, rcond=None)[0]
    for _ in range(3):   # robust: wrinkles' bright folds and dark troughs are outliers
        r = v - Amat @ co; k = np.abs(r) < 1.5 * np.std(r) + 1
        co = np.linalg.lstsq(Amat[k], v[k], rcond=None)[0]
    fit[..., c] = B @ co.astype(np.float32)
# fine satin grain (very subtle) so it does not look painted
g = cv2.GaussianBlur(np.random.RandomState(1).randn(H, W).astype(np.float32), (0, 0), 1.2) * 1.6
fit += g[..., None]
# soft crease shadow along the floor's back and right edges (where the floor meets the inner walls)
P = poly.astype(np.float32); edge = np.zeros((H, W), np.uint8)
cv2.line(edge, tuple(map(int, P[0])), tuple(map(int, P[1])), 1, 3); cv2.line(edge, tuple(map(int, P[1])), tuple(map(int, P[2])), 1, 3)
sh = cv2.GaussianBlur(edge.astype(np.float32), (0, 0), 9); sh = sh / (sh.max() + 1e-6)
fit *= (1 - 0.10 * sh)[..., None]
a = (cv2.GaussianBlur(fm.astype(np.float32), (0, 0), 1.5) * keep)[..., None]   # never touches the rim
res = im * (1 - a) + fit * a
cv2.imwrite(out, np.clip(res, 0, 255).astype(np.uint8))
