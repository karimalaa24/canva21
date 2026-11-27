"""Source reel S1 (sorting table): erase the AI-drawn chips on the black velvet and lay REAL Kinam cut-outs instead:
a loose heap on the left (several layers) + a neat row of selected pieces on the right. Warm lamp from the upper left,
3/4 view (vertical squash), contact + soft shadows, Kinam colour target. Free, local.
usage: sorting_pieces.py in.png out.png seed"""
import cv2, numpy as np, json, glob, sys
K = '/home/user/canva21/kinam/'; T = json.load(open(K + 'pieces/target_kinam.json'))
P = sorted(glob.glob(K + 'pieces/pieces_white_bg_*.png'))
im = cv2.imread(sys.argv[1]); H, W = im.shape[:2]; rng = np.random.default_rng(int(sys.argv[3]))
lab0 = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
# 1) erase AI chips (warm, brighter than velvet) inside the heap + row areas
box = np.zeros((H, W), np.uint8); cv2.rectangle(box, (70, 1280), (810, 1790), 1, -1); cv2.rectangle(box, (890, 1230), (1390, 1530), 1, -1)
chip = ((lab0[..., 0] > 42) & (lab0[..., 2] > 132)).astype(np.uint8) * box
chip = cv2.dilate(cv2.morphologyEx(chip, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)), np.ones((11, 11), np.uint8))
sm = cv2.inpaint(cv2.resize(im, None, fx=0.25, fy=0.25), cv2.resize(chip * 255, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_NEAREST), 6, cv2.INPAINT_TELEA)
sm = cv2.GaussianBlur(cv2.resize(sm, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32), (0, 0), 4)
velvet = (im.astype(np.float32) - cv2.GaussianBlur(im.astype(np.float32), (0, 0), 3))[chip == 0]
grain = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.9)[..., None] * velvet.std() * 0.8
out = np.where(chip[..., None] > 0, sm + grain, im.astype(np.float32))
SQ = 0.72
def piece(i, cx, cy, L, ang, flip=False, depth=1.0):
    global out
    p = cv2.imread(P[i], -1)
    if flip: p = p[:, ::-1].copy()
    h, w = p.shape[:2]; s = L / max(h, w); p = cv2.resize(p, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA); h, w = p.shape[:2]
    D = int(np.hypot(h, w)) + 40; c = np.zeros((D, D, 4), np.uint8); c[(D - h) // 2:(D - h) // 2 + h, (D - w) // 2:(D - w) // 2 + w] = p
    c = cv2.warpAffine(c, cv2.getRotationMatrix2D((D / 2, D / 2), ang, 1), (D, D), flags=cv2.INTER_CUBIC)
    c = cv2.resize(c, (D, int(D * SQ)), interpolation=cv2.INTER_AREA); h, w = c.shape[:2]
    a = cv2.GaussianBlur(cv2.erode(c[..., 3].astype(np.float32) / 255, np.ones((3, 3), np.uint8)), (0, 0), 0.6)
    lab = cv2.cvtColor(c[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32); sel = a > 0.9
    if sel.sum() < 20: return
    bright = lab[..., 0] > np.percentile(lab[..., 0][sel], 97); a[bright & (a < 0.98)] *= 0.3
    Lp = lab[..., 0]; Lp = (Lp - Lp[sel].mean()) / (Lp[sel].std() + 1e-3) * 26 + 92 * depth
    yy, xx = np.mgrid[0:h, 0:w]; Lp = Lp * (1.12 - 0.24 * (0.5 * yy / h + 0.5 * xx / w))       # lamp from the upper left
    edge = np.clip(a - np.roll(a, -4, 0), 0, 1); Lp *= 1 - 0.5 * cv2.GaussianBlur(edge, (0, 0), 1.1)
    top = np.clip(a - np.roll(a, 3, 0), 0, 1); Lp += 8 * cv2.GaussianBlur(top, (0, 0), 0.8)
    lab[..., 0] = np.clip(Lp, 0, 255); Lm = lab[..., 0][sel].mean()
    for ch, key, warm in ((1, 'a_of_L', 3.0), (2, 'b_of_L', 10.0)):
        own = lab[..., ch]; lab[..., ch] = (own - own[sel].mean()) * 1.3 + T[key][0] * Lm + T[key][1] + warm
    rgb = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    rgb = rgb + 0.3 * (rgb - cv2.GaussianBlur(rgb, (0, 0), 1.2))
    X, Y = int(cx - w / 2), int(cy - h / 2)
    if X < 0 or Y < 0 or X + w > W or Y + h > H: return
    reg = out[Y:Y + h, X:X + w]
    soft = cv2.warpAffine(cv2.GaussianBlur(a, (0, 0), 10), np.float32([[1, 0, 10], [0, 1, 12]]), (w, h))
    cont = cv2.warpAffine(cv2.GaussianBlur(a, (0, 0), 2.5), np.float32([[1, 0, 2], [0, 1, 3]]), (w, h))
    reg *= (1 - 0.6 * soft[..., None]) * (1 - 0.6 * cont[..., None] * (1 - a[..., None]))
    reg[:] = rgb * a[..., None] + reg * (1 - a[..., None])
# 2) heap: mound, back to front, lower layers darker
CX, CY, RX, RY = 445, 1525, 330, 205
items = []
for layer in range(4):
    for k in range([70, 55, 38, 22][layer]):
        t, r = rng.uniform(0, 2 * np.pi), np.sqrt(rng.uniform(0, 1)) * (1.0 - 0.18 * layer)
        items.append((layer, CY + r * RY * np.sin(t), CX + r * RX * np.cos(t)))
items.sort(key=lambda v: (v[0], v[1]))
for layer, y, x in items:
    piece(int(rng.integers(len(P))), x, y - 6 * layer, rng.uniform(130, 190), rng.uniform(-180, 180), bool(rng.random() < 0.5), 0.78 + 0.08 * layer)
# 3) the selected row (right): 5 whole pieces, neat spacing
for i, (x, y, a) in enumerate([(960, 1300, 6), (1130, 1310, -10), (1295, 1295, 12), (1030, 1450, -4), (1215, 1455, 9)]):
    piece([3, 5, 6, 0, 8][i], x, y, 165, a, i % 2 == 1, 1.08)
cv2.imwrite(sys.argv[2], np.clip(out, 0, 255).astype(np.uint8)); print('erased px', int(chip.sum()))
