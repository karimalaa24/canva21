"""G5 v2: fill the two REAL open boxes (client frame 28.2 s, 2x) with a dense bed of REAL top-view Kinam pieces (kinam/pieces,
photographed from above = same view as this shot). Each box gets its own random layout (no duplicated heap), pieces sized to the
real box (~3-5 cm in a ~10 cm box), several overlapping layers until the whole visible floor is covered up to the back wall,
contact shadows, Kinam colour target. Pieces are clipped by the box walls (= tucked under the rim, never a visible cut edge
inside the box). Free, local. usage: fill_open_pieces.py in2x.png out.png"""
import cv2, numpy as np, json, glob, random, sys
K = '/home/user/canva21/kinam/'
T = json.load(open(K + 'pieces/target_kinam.json'))
PCS = [cv2.imread(p, -1) for p in sorted(glob.glob(K + 'pieces/pieces_white_bg_*.png'))]
im = cv2.imread(sys.argv[1]); out = im.astype(np.float32); H, W = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int); f = im.astype(int)
skin = ((f[..., 2] > f[..., 1] + 18) & (f[..., 2] > 110) & (hsv[..., 1] > 50)).astype(np.uint8)
skin = cv2.dilate(cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)), np.ones((5, 5), np.uint8))
# visible interior (floor + lower back wall) of each box, 2x coords: wood fills all of it
BOXES = [([(132, 1200), (512, 1200), (516, 1452), (104, 1452)], 11, 1120), ([(606, 1166), (1004, 1172), (1001, 1392), (597, 1384)], 23, 1090)]   # poly, seed, top of the visible back wall
def piece_img(p, length, ang, flip, squash):
    if flip: p = p[:, ::-1]
    h, w = p.shape[:2]; s = length / max(h, w); p = cv2.resize(p, (max(2, int(w * s)), max(2, int(h * s))), interpolation=cv2.INTER_AREA)
    h, w = p.shape[:2]; D = int(np.hypot(h, w)) + 6; c = np.zeros((D, D, 4), np.uint8); c[(D - h) // 2:(D - h) // 2 + h, (D - w) // 2:(D - w) // 2 + w] = p
    c = cv2.warpAffine(c, cv2.getRotationMatrix2D((D / 2, D / 2), ang, 1), (D, D), flags=cv2.INTER_CUBIC)
    c = cv2.resize(c, (D, max(2, int(D * squash))), interpolation=cv2.INTER_AREA)
    a = cv2.GaussianBlur(cv2.erode(c[..., 3].astype(np.float32) / 255, np.ones((4, 4), np.uint8)), (0, 0), 0.6)
    lab = cv2.cvtColor(c[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32); sel = a > 0.9
    if sel.sum() < 10: return None
    bright = (lab[..., 0] > np.percentile(lab[..., 0][sel], 97)); a[bright & (a < 0.98)] *= 0.3   # white-background fringe
    L = lab[..., 0]; L = (L - L[sel].mean()) / (L[sel].std() + 1e-3) * 30 + random.uniform(64, 84)
    yy = np.mgrid[0:c.shape[0], 0:c.shape[1]][0]; L = L * (1.06 - 0.12 * yy / c.shape[0])
    edge = np.clip(a - np.roll(a, -3, 0), 0, 1); L = L * (1 - 0.45 * cv2.GaussianBlur(edge, (0, 0), 1))
    lab[..., 0] = np.clip(L, 0, 255); Lm = lab[..., 0][sel].mean()
    for ch, key in ((1, 'a_of_L'), (2, 'b_of_L')):
        own = lab[..., ch]; lab[..., ch] = (own - own[sel].mean()) * 1.2 + T[key][0] * Lm + T[key][1] + 2
    rgb = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    return rgb, a
for poly, seed, wall_top in BOXES:
    random.seed(seed); rng = np.random.default_rng(seed)
    pm = np.zeros((H, W), np.uint8); cv2.fillPoly(pm, [np.array(poly, np.int32)], 1); pm &= (1 - skin)
    x0, x1 = min(p[0] for p in poly), max(p[0] for p in poly); y0, y1 = min(p[1] for p in poly), max(p[1] for p in poly); bw = x1 - x0
    clip = np.zeros((H, W), np.uint8); P = np.array(poly, np.int32).copy(); P[0, 1] = P[1, 1] = wall_top; cv2.fillPoly(clip, [P], 1); clip &= (1 - skin)
    cream = np.percentile(out[y0 - 70:y0 - 15, x0 + 30:x1 - 30].reshape(-1, 3), 70, axis=0)
    base = np.zeros((H, W, 3), np.float32) + np.array([30, 44, 60.])                                       # erased old oud -> cream (covered by pieces)
    acc = base.copy(); cov = np.zeros((H, W), np.float32)
    rows = np.linspace(y0 + 18, y1 + 30, 7)                                                     # back to front so front pieces overlap back ones
    for layer in range(3):
        for ry in rows:
            nx = 5
            for j in range(nx):
                cx = x0 + (j + rng.uniform(0.1, 0.9)) * bw / nx; cy = ry + rng.uniform(-18, 18)
                if layer >= 1 and cov[int(min(cy, H - 1)), int(min(cx, W - 1))] > 0.9 and rng.random() < 0.6: continue
                r = piece_img(random.choice(PCS), bw * rng.uniform(0.36, 0.50), rng.uniform(-80, 80), rng.random() < 0.5, 0.70)
                if r is None: continue
                rgb, a = r; h, w = a.shape; X, Y = int(cx - w / 2), int(cy - h / 2)
                xa, ya, xb, yb = max(0, X), max(0, Y), min(W, X + w), min(H, Y + h)
                if xb <= xa or yb <= ya: continue
                ap = a[ya - Y:yb - Y, xa - X:xb - X, None]; rp = rgb[ya - Y:yb - Y, xa - X:xb - X]
                sh = cv2.GaussianBlur(ap[..., 0], (0, 0), 5)[..., None]
                reg = acc[ya:yb, xa:xb]; reg *= 1 - 0.5 * np.clip(np.roll(sh, 5, 0) - ap, 0, 1)
                acc[ya:yb, xa:xb] = rp * ap + reg * (1 - ap); cov[ya:yb, xa:xb] = np.maximum(cov[ya:yb, xa:xb], ap[..., 0])
    acc = cv2.GaussianBlur(acc, (0, 0), 0.7)
    # wall shading: darker near the box walls / back (inside a box)
    d = cv2.distanceTransform(clip, cv2.DIST_L2, 5); acc *= (0.70 + 0.30 * np.clip(d / 35, 0, 1))[..., None]
    yy = np.arange(H)[:, None, None]; acc *= np.clip(0.85 + 0.15 * (yy - y0) / max(1, y1 - y0), 0.85, 1.0)
    keep = np.maximum(pm.astype(np.float32), cov * clip)              # old oud area always replaced; above it only where a piece is
    A = cv2.GaussianBlur(keep, (0, 0), 1.0)[..., None]
    out = out * (1 - A) + acc * A
    print('box', seed, 'floor covered %.3f' % ((cov > 0.5) & (pm > 0)).sum() / max(1, pm.sum()) if False else 'box', seed, 'covered', round(float(((cov > 0.5) & (pm > 0)).sum() / max(1, pm.sum())), 3))
cv2.imwrite(sys.argv[2], np.clip(out, 0, 255).astype(np.uint8))
