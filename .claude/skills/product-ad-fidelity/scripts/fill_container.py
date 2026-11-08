"""Fill an EMPTY open box/tray-in-box with real product pieces: full, layered, natural gaps, nothing
cut at the box edges, nothing climbing the back wall.

usage: python fill_container.py config.json [seed]

config.json:
{
 "plate": "empty_box.png", "pieces": "pieces/", "ref_photo": "ref.jpg", "target": "target.json", "out": "box_out.png",
 "rim":   [[xBL? no -> back-left],[back-right],[front-right],[front-left]],   # opening corners, image px, order: BL,BR,FR,FL
 "floor": [[back-left],[back-right],[front-right],[front-left]],            # inner floor corners
 "poly": optional full opening polygon when a corner is off-frame,
 "backt": 0.6,          # 0 = pieces may reach the back rim, 1 = only on the floor. 0.6-0.7 stopped 'climbing the back wall'
 "leftwide": false,     # keep the left edge at the rim while pulling the back in
 "frac": 0.33,          # piece length as a fraction of the box FRONT edge (client: ~1/3 of box width, like the reel)
 "elong": 1.12, "squash": 0.85,
 "cov": 0.05,           # stop layer-1 when uncovered area < 5% (lower = fuller)
 "l2": 0.30, "l3": 0.10,# extra layers as fraction of layer-1 count (wood on top of wood)
 "leftfill": 0,         # extra pieces in the left 40% if that side looks empty
 "LM": -4, "CK": 0.25,
 "held": {"x":..,"y":..,"len":..,"ang":..,"piece":"<name>","handpoly":[[x,y],...]}   # optional pinched piece
}
"""
import json, os, random, sys
import cv2
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import load_pieces, paper_white, scene_light, xform, Canvas, load_target, apply_target_colour

cfg = json.load(open(sys.argv[1])); seed = int(sys.argv[2]) if len(sys.argv) > 2 else 4; rng = random.Random(seed)
plate = cv2.imread(cfg['plate']).astype(np.float32); H, W = plate.shape[:2]
pool = load_pieces(cfg['pieces']); names = [p[0] for p in pool]
rim = np.array(cfg['rim'], np.float32); flo = np.array(cfg['floor'], np.float32)
open_ = np.zeros((H, W), np.uint8); cv2.fillPoly(open_, [np.array(cfg.get('poly', rim.tolist()), np.int32)], 1)
WHITE = paper_white(cfg['ref_photo']); LIGHT = scene_light(plate, flo.tolist())
WARM = np.array(cfg.get('warm', [0.86, 0.97, 1.08]), np.float32)
grade = lambda rgb, g=1.0: np.clip(rgb / WHITE * LIGHT * cfg.get('expo', 1.0) * g * WARM, 0, 255)
LEN = np.linalg.norm(rim[2] - rim[3]) * cfg.get('frac', 0.33); EL = cfg.get('elong', 1.12); SQ = cfg.get('squash', 0.85)
BT = cfg.get('backt', 0.0); reg = rim.copy()
for i in (0, 1):
    reg[i, 1] = rim[i, 1] * (1 - BT) + flo[i, 1] * BT; reg[i, 0] = rim[i, 0] * (1 - BT * 0.3) + flo[i, 0] * BT * 0.3
if cfg.get('leftwide'): reg[0, 0] = rim[0, 0]
area = np.zeros((H, W), np.uint8); cv2.fillPoly(area, [reg.astype(np.int32)], 1); area &= open_
fitm = cv2.erode(area, np.ones((9, 9), np.uint8)).astype(bool)          # every piece must lie fully inside
inner = cv2.erode(area, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(LEN * 0.45) | 1,) * 2)).astype(bool)
sc = LEN / 195.0; SHD = (int(-8 * sc), int(11 * sc)); SB = 10 * sc
cv = Canvas(plate); last = -1


def fits(aa, cx, cy):
    h, w = aa.shape; ys, xs = np.where(aa > 0.25); ys = ys + int(cy - h / 2); xs = xs + int(cx - w / 2)
    if ys.min() < 0 or xs.min() < 0 or ys.max() >= H or xs.max() >= W: return False
    return fitm[ys, xs].all()


def try_place(x, y, gain, lift, tries=14, jit=0.2):
    global last
    for _ in range(tries):
        k = (last + rng.randrange(1, len(pool))) % len(pool); _, rgb, a = pool[k]
        rr, aa = xform(grade(rgb, gain * rng.uniform(0.95, 1.05)), a, LEN * rng.uniform(0.85, 1.05), rng.uniform(0, 360), rng.random() < 0.5, EL, SQ)
        cx = x + rng.uniform(-LEN * jit, LEN * jit); cy = y + rng.uniform(-LEN * jit, LEN * jit)
        if fits(aa, cx, cy):
            last = k; return cv.place(rr, aa, cx, cy, shadow=(int(SHD[0] * lift), int(SHD[1] * lift)), sblur=SB * lift)
    return None


unc = open_.astype(bool) & fitm; tot = unc.sum(); n = fails = 0
while unc.sum() > tot * cfg.get('cov', 0.07) and n < 300 and fails < 200:
    dt = cv2.distanceTransform(unc.astype(np.uint8), cv2.DIST_L2, 5); y, x = np.unravel_index(np.argmax(dt), dt.shape)
    m = try_place(x, y, 0.95, 1.0)
    if m is None:
        cv2.circle(unc.view(np.uint8), (int(x), int(y)), max(6, int(LEN * 0.12)), 0, -1); fails += 1
    else:
        unc &= ~m; n += 1
LF = cfg.get('leftfill', 0)
if LF:
    xl = np.percentile(np.where(area > 0)[1], 40)
    for _ in range(LF * 6):
        if LF <= 0: break
        cand = np.argwhere((area > 0) & (cv.wood < 0.5) & (np.arange(W)[None, :] < xl))
        if len(cand) == 0: break
        y, x = cand[rng.randrange(len(cand))]
        if try_place(x, y, 0.97, 1.1, tries=20, jit=0.1) is not None: LF -= 1
ys, xs = np.where(inner)
for frac, gain, lift in ((cfg.get('l2', 0.30), 1.02, 1.4), (cfg.get('l3', 0.10), 1.07, 1.8)):
    for _ in range(int(n * frac)):
        i = rng.randrange(len(xs)); try_place(xs[i], ys[i], gain, lift, jit=0.05)
# gaps enclosed by wood read as shadow, open edges stay as the box floor
enc = cv2.morphologyEx((cv.wood > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(LEN * 0.35) | 1,) * 2)).astype(bool)
g = cv2.GaussianBlur((enc & (cv.wood < 0.5) & (open_ > 0)).astype(np.float32), (0, 0), 3); cv.img *= (1 - 0.6 * g)[..., None]
clip = cv2.GaussianBlur(open_.astype(np.float32), (3, 3), 0); handm = None
if 'held' in cfg:
    hc = cfg['held']; _, rgb, a = pool[names.index(hc['piece'])] if hc.get('piece') in names else pool[0]
    rr, aa = xform(grade(rgb, 1.0), a, hc['len'], hc['ang'], hc.get('flip', False), EL, 1.0)
    rr = np.clip(rr * 1.8 - cv2.GaussianBlur(rr, (0, 0), 2.0) * 0.8, 0, 255)   # match sharpness of the plate
    cv.place(rr, aa, hc['x'], hc['y'], shadow=(int(-14 * sc), int(22 * sc)), sop=0.25, sblur=16 * sc, contact=0.0)
    h_, w_ = aa.shape; Y, X = np.mgrid[0:h_, 0:w_]; Y += int(hc['y'] - h_ / 2); X += int(hc['x'] - w_ / 2)
    ok = (Y >= 0) & (Y < H) & (X >= 0) & (X < W); hm = np.zeros((H, W), np.float32); hm[Y[ok], X[ok]] = aa[ok]
    clip = np.maximum(clip, cv2.GaussianBlur(np.clip(hm * 3, 0, 1), (3, 3), 0))
    sk = np.zeros((H, W), np.uint8); cv2.fillPoly(sk, [np.array(hc['handpoly'], np.int32)], 1)
    handm = cv2.GaussianBlur(sk.astype(np.float32), (5, 5), 0)
cv.light_falloff(open_ > 0)
img = apply_target_colour(cv.img, cv.wood, load_target(cfg['target']), region=clip > 0.5, LM=cfg.get('LM', -4), CK=cfg.get('CK', 0.25))
out = plate * (1 - clip[..., None]) + img * clip[..., None]
if handm is not None: out = out * (1 - handm[..., None]) + plate * handm[..., None]
cv2.imwrite(cfg['out'], np.clip(out, 0, 255).astype(np.uint8)); print('pieces', n)
