"""Diff reel D3: lay the 9 REAL Kinam cut-outs (kinam/pieces, top view) on the empty velvet cloth, real proportions, warm lantern
light from the upper left, contact + soft shadows, colour toward the Kinam target. Free, local."""
import cv2, numpy as np, json, glob, random
K = '/home/user/canva21/kinam/'; T = json.load(open(K + 'pieces/target_kinam.json'))
out = cv2.imread('/home/user/canva21/kinam_diff/images/d03_cloth_empty.png').astype(np.float32); H, W = out.shape[:2]
P = sorted(glob.glob(K + 'pieces/pieces_white_bg_*.png'))
# (piece index, centre x, centre y, length px, angle)  -- loose, hand-placed look, more space at the top for captions
LAY = [(0, 560, 760, 430, -18), (1, 1040, 820, 400, 22), (2, 760, 1180, 300, 8), (3, 470, 1500, 420, -30), (4, 1060, 1420, 380, 35),
       (5, 700, 1880, 400, -8), (6, 1120, 1960, 300, 60), (7, 480, 2240, 300, 15), (8, 980, 2350, 400, -24)]
def piece(i, cx, cy, L, ang):
    global out
    p = cv2.imread(P[i], -1); hs = cv2.cvtColor(p[..., :3], cv2.COLOR_BGR2HSV).astype(int)
    a0 = (p[..., 3] > 128).astype(np.uint8); rim = (a0 > 0) & (cv2.erode(a0, np.ones((17, 17), np.uint8)) == 0)
    white = ((hs[..., 2] > 150) & (hs[..., 1] < 70)) | (rim & (hs[..., 1] < 60))   # halo + pale cut side faces on the outline
    al = p[..., 3].copy(); al[cv2.dilate(white.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0] = 0
    from scipy.ndimage import binary_fill_holes
    keep = cv2.morphologyEx((al > 128).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, l, st, _ = cv2.connectedComponentsWithStats(keep); keep = (l == max(range(1, n), key=lambda k: st[k, 4])).astype(np.uint8)
    p[..., 3] = (cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 0.8) * 255).astype(np.uint8)
    h, w = p.shape[:2]; s = L / max(h, w)
    p = cv2.resize(p, (int(w * s), int(h * s)), interpolation=cv2.INTER_CUBIC); h, w = p.shape[:2]
    D = int(np.hypot(h, w)) + 40; c = np.zeros((D, D, 4), np.uint8); c[(D - h) // 2:(D - h) // 2 + h, (D - w) // 2:(D - w) // 2 + w] = p
    c = cv2.warpAffine(c, cv2.getRotationMatrix2D((D / 2, D / 2), ang, 1), (D, D), flags=cv2.INTER_CUBIC)
    a = cv2.GaussianBlur(cv2.erode(c[..., 3].astype(np.float32) / 255, np.ones((3, 3), np.uint8)), (0, 0), 0.7)
    lab = cv2.cvtColor(c[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32); sel = a > 0.9
    bright = lab[..., 0] > np.percentile(lab[..., 0][sel], 97); a[bright & (a < 0.98)] *= 0.3
    Lp = lab[..., 0]; Lp = np.minimum(Lp, np.percentile(Lp[sel], 96)); Lp = (Lp - Lp[sel].mean()) / (Lp[sel].std() + 1e-3) * 28 + 70
    yy, xx = np.mgrid[0:D, 0:D]; Lp = Lp * (1.12 - 0.22 * (0.5 * yy / D + 0.5 * xx / D))
    edge = np.clip(a - np.roll(a, -4, 0), 0, 1); Lp *= 1 - 0.45 * cv2.GaussianBlur(edge, (0, 0), 1.2)
    lab[..., 0] = np.clip(Lp, 0, 255); Lm = lab[..., 0][sel].mean()
    for ch, key in ((1, 'a_of_L'), (2, 'b_of_L')):
        own = lab[..., ch]; lab[..., ch] = (own - own[sel].mean()) * 1.25 + T[key][0] * Lm + T[key][1] + 3
    rgb = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    rgb = rgb + 0.35 * (rgb - cv2.GaussianBlur(rgb, (0, 0), 1.2))
    X, Y = int(cx - D / 2), int(cy - D / 2); reg = out[Y:Y + D, X:X + D]
    soft = cv2.warpAffine(cv2.GaussianBlur(a, (0, 0), 14), np.float32([[1, 0, 14], [0, 1, 18]]), (D, D))
    cont = cv2.warpAffine(cv2.GaussianBlur(a, (0, 0), 3), np.float32([[1, 0, 3], [0, 1, 4]]), (D, D))
    reg *= (1 - 0.55 * soft[..., None]) * (1 - 0.5 * cont[..., None] * (1 - a[..., None]))
    reg[:] = rgb * a[..., None] + reg * (1 - a[..., None])
for args in LAY: piece(*args)
cv2.imwrite('/home/user/canva21/kinam_diff/images/d03_pieces_final.png', np.clip(out, 0, 255).astype(np.uint8))
