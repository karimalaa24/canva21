"""Reel 02: fill an EMPTY open box with WHOLE real oud pieces only (client 14 Nov: "no cut heap — keep the look
and distribution, but real whole pieces"). No heap master is used: every piece is one of the real cut-outs in
.claude/skills/product-ad-fidelity/assets/box_masters/pieces, laid flat on the box floor in a rectified (top-down)
floor plane, then warped into the photo with the floor's perspective. LOW fill: one layer covering the floor wall to
wall + a light second layer; cream lining stays visible at the back. A piece may only disappear behind the FRONT
wall (and, with --hide_side, behind the side wall whose outer face the camera sees) — never a visible cut.

usage: python whole_fill.py empty.png out.png "<rim quad BL BR FR FL>" [--hide_side l|r] [--seed N] [--len 0.24]
"""
import argparse, json, os, random, sys
import cv2, numpy as np
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.claude', 'skills', 'product-ad-fidelity')
sys.path.insert(0, os.path.join(SK, 'scripts'))
from common import load_pieces, xform, Canvas, load_target, apply_target_colour

ap = argparse.ArgumentParser()
ap.add_argument('empty'); ap.add_argument('out'); ap.add_argument('quad')
ap.add_argument('--hide_side', default='', choices=['', 'l', 'r'])
ap.add_argument('--seed', type=int, default=1)
ap.add_argument('--len', type=float, default=0.3, help='piece length / local floor width')
ap.add_argument('--squash', type=float, default=0, help='vertical squash (0 = from the view)')
ap.add_argument('--kf', type=float, default=0.06); ap.add_argument('--kb', type=float, default=0.035)
ap.add_argument('--cov', type=float, default=0.05, help='stop layer 1 when this fraction of the floor is uncovered')
ap.add_argument('--l2', type=float, default=0.25, help='second layer pieces as a fraction of layer 1')
ap.add_argument('--depth', type=float, default=0.85, help='floor depth / width (real box)')
A = ap.parse_args()
rng = random.Random(A.seed)
LIB = os.path.join(SK, 'assets', 'box_masters')

D = cv2.imread(A.empty).astype(np.float32); H, W = D.shape[:2]
Q = np.float32([[float(v) for v in p.split(',')] for p in A.quad.split()])           # rim BL BR FR FL
L = np.linalg.norm(Q[2] - Q[3]); LQ = Q.copy(); LQ[:, 1] += np.array([A.kb, A.kb, A.kf, A.kf]) * L   # lowered floor quad

# Pieces are placed in IMAGE space (like the approved ad-1 fill): size follows the local floor width (perspective),
# a mild vertical squash keeps their faces readable (real pieces lie tilted on each other, not flat).
Hd = cv2.getPerspectiveTransform(LQ, np.float32([[0, 0], [1, 0], [1, 1], [0, 1]]))
yy, xx = np.mgrid[0:H, 0:W]
UV = cv2.perspectiveTransform(np.c_[xx.ravel(), yy.ravel()].astype(np.float32)[None], Hd)[0].reshape(H, W, 2)
U, V = UV[..., 0], UV[..., 1]
cm = np.zeros((H, W), np.uint8); cv2.fillPoly(cm, [Q.astype(np.int32)], 1)
Uq = cv2.perspectiveTransform(np.c_[xx.ravel(), yy.ravel()].astype(np.float32)[None],
                              cv2.getPerspectiveTransform(Q, np.float32([[0, 0], [1, 0], [1, 1], [0, 1]])))[0].reshape(H, W, 2)
front_band = (Uq[..., 1] > 0.8) & (Uq[..., 0] > 0.03) & (Uq[..., 0] < 0.97)
wall = cv2.erode(cm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * 4 + 1,) * 2)).astype(bool)   # thin lining strip (sides/back)
wall |= front_band & (cm > 0)                                                                       # front: wood right up to the rim
fl = np.zeros((H, W), np.uint8); cv2.fillPoly(fl, [LQ.astype(np.int32)], 1)
back_ok = V > 0.06                                    # cream stays visible at the back
allow = wall & back_ok
allow |= (V > 0.85) & (U > -0.02) & (U < 1.02) & back_ok   # may slide behind the front wall
if A.hide_side == 'l': allow |= (U < 0.1) & back_ok & (V > 0) & (V < 1.3)
if A.hide_side == 'r': allow |= (U > 0.9) & back_ok & (V > 0) & (V < 1.3)
floor = (fl > 0) & wall & back_ok
s_v = (np.linalg.norm((LQ[3] + LQ[2]) / 2 - (LQ[0] + LQ[1]) / 2)) / (np.linalg.norm(LQ[2] - LQ[3]) * A.depth)
SQ = float(np.clip(0.45 + s_v, 0.55, 0.9)) if A.squash <= 0 else A.squash
wfront, wback = np.linalg.norm(LQ[2] - LQ[3]), np.linalg.norm(LQ[1] - LQ[0])
local_w = lambda y: wback + (wfront - wback) * float(np.clip(V[int(y), int(np.clip(xx[0].mean(), 0, W - 1))], 0, 1))
print(f'view squash {SQ:.2f} (floor depth ratio {s_v:.2f})')

def lining_median(img, quad):
    lab = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.int16)
    m = ((lab[..., 0] > 90) & (np.abs(lab[..., 1] - 128) < 18) & (lab[..., 2] > 126) & (lab[..., 2] < 185)).astype(np.uint8)
    hp = np.zeros(m.shape, np.uint8); cv2.fillPoly(hp, [quad.astype(np.int32)], 1)
    hp = cv2.dilate(hp, np.ones((25, 25), np.uint8)); px = img[(m & hp) > 0]
    return np.median(px, 0) if len(px) > 200 else np.array([190, 215, 235], np.float32)

kit = json.load(open(os.path.join(LIB, 'kit.json'))); light = lining_median(D, Q)
grade = lambda c, g: np.clip(c / np.array(kit['paper_white'], np.float32) * light * g * np.array([0.86, 0.97, 1.08]), 0, 255)
pool = load_pieces(os.path.join(LIB, 'pieces'))
cv = Canvas(D)

def fits(aa, cx, cy):
    h_, w_ = aa.shape; ys, xs = np.where(aa > 0.2); ys = ys + int(cy - h_ / 2); xs = xs + int(cx - w_ / 2)
    if ys.min() < 0 or xs.min() < 0 or ys.max() >= H or xs.max() >= W: return False
    return bool(allow[ys, xs].all())

def piece(k, x, y, g):
    _, rgb, a_ = pool[k]
    vloc = float(np.clip(V[int(y), int(x)], 0, 1)); lw = wback + (wfront - wback) * vloc
    ang = rng.uniform(-35, 35) if rng.random() < 0.6 else rng.uniform(35, 145)     # mostly lying across the box, like the approved heaps
    rr, aa = xform(grade(rgb, g), a_, A.len * lw * rng.uniform(0.85, 1.1), ang, rng.random() < 0.5, 1.12, SQ)
    lum = cv2.cvtColor(np.clip(rr, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    aa = aa * np.clip((150 - lum) / 30, 0, 1)                      # no pale fringe specks
    n_, lb_, st_, _ = cv2.connectedComponentsWithStats((aa > 0.3).astype(np.uint8))
    if n_ > 2: aa = aa * cv2.dilate((lb_ == 1 + np.argmax(st_[1:, 4])).astype(np.uint8), np.ones((3, 3), np.uint8))   # one whole piece, no crumbs
    return rr, aa

placed = []; unc = floor.copy(); tot = floor.sum(); fails = 0; last = -1
while unc.sum() > A.cov * tot and fails < 400:
    dt = cv2.distanceTransform(unc.astype(np.uint8), cv2.DIST_L2, 5); y, x = np.unravel_index(np.argmax(dt), dt.shape)
    ok = False
    for _ in range(80):
        k = (last + rng.randrange(1, len(pool))) % len(pool)
        rr, aa = piece(k, x, y, rng.uniform(0.94, 1.05))
        cx = x + rng.uniform(-0.25, 0.25) * aa.shape[1]; cy = y + rng.uniform(-0.25, 0.25) * aa.shape[0]
        if fits(aa, cx, cy):
            mm = cv.place(rr, aa, cx, cy, shadow=(-6, 9), sblur=8)
            placed.append(k); last = k; ok = True
            if mm is not None: unc &= ~mm
            break
    if not ok:
        cv2.circle(unc.view(np.uint8), (int(x), int(y)), 6, 0, -1); fails += 1
n1 = len(placed); n2 = 0; want = int(round(A.l2 * n1)); ys_, xs_ = np.where(floor)
for _ in range(want * 40):
    if n2 >= want: break
    i = rng.randrange(len(ys_)); x, y = xs_[i], ys_[i]
    if V[y, x] < 0.25 or V[y, x] > 0.9 or U[y, x] < 0.12 or U[y, x] > 0.88: continue
    rr, aa = piece(rng.randrange(len(pool)), x, y, rng.uniform(1.0, 1.1))
    if fits(aa, x, y):
        cv.place(rr, aa, x, y, shadow=(-6, 9), sblur=8); n2 += 1
print(f'whole pieces: layer1 {n1}, layer2 {n2}, uncovered floor {unc.sum() / tot:.3f}')
# colour model of the approved boxes; wood only inside the real rim (front wall / clasp hide the rest)
img = apply_target_colour(cv.img, cv.wood, load_target(os.path.join(LIB, 'target.json')), region=cv.wood > 0.5)
ch = cv2.GaussianBlur((np.abs(img - D).max(2) > 2).astype(np.float32), (0, 0), 0.8)
cmk = cv2.erode(cm, np.ones((5, 5), np.uint8)) | (front_band & (cm > 0)).astype(np.uint8)
al = (np.clip(ch, 0, 1) * cv2.GaussianBlur(cmk.astype(np.float32), (0, 0), 1.0))[..., None]
out = D * (1 - al) + img * al
Uc = cv2.perspectiveTransform(np.c_[xx.ravel(), yy.ravel()].astype(np.float32)[None],
                              cv2.getPerspectiveTransform(Q, np.float32([[0, 0], [1, 0], [1, 1], [0, 1]])))[0].reshape(H, W, 2)
hid = (Uc[..., 1] >= 0.85) | ((Uc[..., 0] < 0.5) if A.hide_side == 'l' else False) | ((Uc[..., 0] > 0.5) if A.hide_side == 'r' else False)
print('visible cut px: %d' % int(((cv.wood > 0.35) & (cmk == 0) & ~hid).sum()))
# finish (approved ad-4): light sharpen + warm lift on the wood, every leather px back from the empty plate
m_ = (np.abs(out - D).max(2) > 6).astype(np.float32)
lab_ = cv2.cvtColor(D.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.int16)
g_ = cv2.morphologyEx(((lab_[..., 1] < 124) & (lab_[..., 0] > 30)).astype(np.float32), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
m_ = (cv2.GaussianBlur(m_, (0, 0), 2) * (1 - g_))[..., None]
sh_ = (out + (out - cv2.GaussianBlur(out, (0, 0), 1.6)) * 0.9) * np.array([0.97, 1.0, 1.06]) * 1.06
out = out * (1 - m_) + sh_ * m_
ga_ = cv2.GaussianBlur(g_, (0, 0), 0.7)[..., None]; out = out * (1 - ga_) + D * ga_
cv2.imwrite(A.out, np.clip(out, 0, 255).astype(np.uint8)); print('wrote', A.out)
