"""D9 box: a low, flat layer of medium REAL Kinam cut-outs (same colour treatment as the scale-pan pieces, g10_pieces.py),
rows back->front, overlapping until the floor is covered, clipped by the box opening (tucked behind every wall). Free.
usage: box_pieces.py empty.png out.png seed"""
import cv2, numpy as np, json, sys, random
K = '/home/user/canva21/kinam/'; T = json.load(open(K + 'pieces/target_kinam.json'))
ai = cv2.imread(K + 'images/s07_scale_ai_pan.png'); Lai = cv2.cvtColor(ai, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32)
ell = np.zeros(Lai.shape, np.uint8); cv2.ellipse(ell, (1050, 1945), (300, 125), 0, 0, 360, 1, -1)
w0 = Lai[(ell > 0) & (ai.astype(np.float32).mean(2) < 110)]; Lmu, Lsd = w0.mean(), w0.std()
IDS = ['01', '03', '04', '05', '06', '07', '08', '09', '10']
im = cv2.imread(sys.argv[1]); out = im.astype(np.float32); H, W = im.shape[:2]; seed = int(sys.argv[3])
rng = np.random.default_rng(seed); random.seed(seed)
CLIP = np.array([[548, 1886], [803, 1886], [817, 1904], [860, 1974], [600, 1998], [553, 1910]], np.int32)
FLOOR = np.array([[553, 1912], [813, 1906], [860, 1974], [600, 1998]], np.int32)
clip = np.zeros((H, W), np.float32); cv2.fillPoly(clip, [CLIP], 1)
floor = np.zeros((H, W), np.float32); cv2.fillPoly(floor, [FLOOR], 1)
SQ = 0.55
acc = np.zeros((H, W, 3), np.float32) + np.array([18, 28, 40.]); cov = np.zeros((H, W), np.float32)
def piece(name, length, ang, cx, cy, flip):
    p = cv2.imread(K + 'pieces/pieces_white_bg_%s.png' % name, -1)
    if flip: p = p[:, ::-1]
    h, w = p.shape[:2]; s = length / max(h, w); p = cv2.resize(p, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    h, w = p.shape[:2]; D = int(np.hypot(h, w)) + 40; c = np.zeros((D, D, 4), np.uint8); c[(D - h) // 2:(D - h) // 2 + h, (D - w) // 2:(D - w) // 2 + w] = p
    c = cv2.warpAffine(c, cv2.getRotationMatrix2D((D / 2, D / 2), ang, 1), (D, D), flags=cv2.INTER_CUBIC)
    c = cv2.resize(c, (D, int(D * SQ)), interpolation=cv2.INTER_AREA); h, w = c.shape[:2]
    a = cv2.GaussianBlur(cv2.erode(c[..., 3].astype(np.float32) / 255, np.ones((3, 3), np.uint8)), (0, 0), 0.5)
    lab = cv2.cvtColor(c[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32); sel = a > 0.9
    Lp = (lab[..., 0] - lab[..., 0][sel].mean()) / (lab[..., 0][sel].std() + 1e-3) * Lsd * 0.9 + Lmu * rng.uniform(0.9, 1.08)
    yy, xx = np.mgrid[0:h, 0:w]; Lp = Lp * (1.10 - 0.2 * (0.6 * yy / h + 0.4 * xx / w))
    edge = np.clip(a - np.roll(a, -4, 0), 0, 1); Lp = Lp * (1 - 0.5 * cv2.GaussianBlur(edge, (0, 0), 1.0))
    top = np.clip(a - np.roll(a, 3, 0), 0, 1); Lp = Lp + 7 * cv2.GaussianBlur(top, (0, 0), 0.8)
    lab[..., 0] = np.clip(Lp, 0, 255); Lm = lab[..., 0][sel].mean()
    for ch, key, warm in ((1, 'a_of_L', 2.0), (2, 'b_of_L', 6.0)):
        own = lab[..., ch]; lab[..., ch] = (own - own[sel].mean()) * 1.3 + T[key][0] * Lm + T[key][1] + warm
    rgb = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    X0, Y0 = int(cx - w / 2), int(cy - h / 2); reg = acc[Y0:Y0 + h, X0:X0 + w]
    cont = cv2.warpAffine(cv2.GaussianBlur(a, (0, 0), 2.5), np.float32([[1, 0, 2], [0, 1, 4]]), (w, h))
    reg *= (1 - 0.6 * cont[..., None] * (1 - a[..., None]))
    reg[:] = rgb * a[..., None] + reg * (1 - a[..., None]); cov[Y0:Y0 + h, X0:X0 + w] = np.maximum(cov[Y0:Y0 + h, X0:X0 + w], a)
import os
LEN = [float(v) for v in os.environ.get('LEN', '88,112').split(',')]; FL = [float(v) for v in os.environ.get('FLEN', '80,100').split(',')]
rows = [float(v) for v in os.environ.get('ROWS', '1918,1936,1954,1972,1990').split(',')]; NPR = [int(v) for v in os.environ.get('NPR', '4,4,5,5,5').split(',')]
for li, ry in enumerate(rows):
    xl = 553 + (ry - 1912) * 0.55; xr = 813 + (ry - 1906) * 0.69
    n = NPR[li]
    for j in range(n):
        cx = xl + (j + rng.uniform(0.2, 0.8)) * (xr - xl) / n; cy = ry + rng.uniform(-5, 5)
        piece(random.choice(IDS), rng.uniform(*LEN), rng.uniform(-35, 35), cx, cy, rng.random() < 0.5)
# gap filler pass: drop extra pieces where the floor still shows
for _ in range(25):
    hole = (floor > 0) & (cov < 0.5); ys, xs = np.where(hole)
    if len(ys) < 150: break
    k = rng.integers(len(ys)); piece(random.choice(IDS), rng.uniform(*FL), rng.uniform(-35, 35), xs[k], ys[k] + 4, rng.random() < 0.5)
d = cv2.distanceTransform((clip > 0).astype(np.uint8), cv2.DIST_L2, 5); acc *= (0.72 + 0.28 * np.clip(d / 22, 0, 1))[..., None]   # wall shade
keep = np.maximum(floor, cov) * clip; A = cv2.GaussianBlur(keep, (0, 0), 0.7)[..., None]
out = out * (1 - A) + acc * A
print('floor covered', round(float(((cov > 0.5) & (floor > 0)).sum() / floor.sum()), 3))
cv2.imwrite(sys.argv[2], np.clip(out, 0, 255).astype(np.uint8))
