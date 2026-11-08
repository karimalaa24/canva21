"""Scatter real product pieces loosely on a flat surface (tray, cloth, table) of an EMPTY plate.

usage: python scatter_on_surface.py config.json [seed]

config.json:
{
 "plate": "empty_plate.png",          # scene with the old product removed (Magnific edit)
 "pieces": "pieces/",                 # from extract_pieces.py
 "ref_photo": "ref.jpg",              # one of the white-background product photos (paper-white reference)
 "target": "target.json",             # from measure_target_color.py
 "out": "tray_out.png",
 "light_poly": [[x,y],...],           # optional: a white/cream area to sample the scene light colour
 "scatter": {"cx":560,"cy":1480,"rx":330,"ry":330,"n":22,"spacing":0.62},
 "length": 195, "elong": 1.12,        # piece long side in px, then x1.12 (client asked for slightly longer)
 "keep_out": [{"x":880,"y":1200,"r":240}],          # e.g. around the hand-held piece
 "hand_polys": [[[x,y],...], ...],    # drawn by hand on a gridded zoom; hands are restored on top
 "hand_margin": 0.75,                 # min distance from hands, in piece lengths (stops pieces 'floating' on fingers)
 "fixed": [ {"x":1150,"y":1330,"ang":-12,"piece":"<name>","flip":false,"len":195,"shadow":1.0}, ... ],
 "warm": [0.86,0.97,1.08], "expo": 1.0, "LM": -4, "CK": 0.25, "DA": 1.5, "DB": 4
}
"fixed" = pieces at exact spots (pieces on the cloth, the piece pinched by the fingers: put its tip
under the fingertip, then the hand polygon restores the fingers over it).
"""
import json, random, sys
import cv2
import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from common import load_pieces, paper_white, scene_light, xform, Canvas, load_target, apply_target_colour

cfg = json.load(open(sys.argv[1])); seed = int(sys.argv[2]) if len(sys.argv) > 2 else 3; rng = random.Random(seed)
plate = cv2.imread(cfg['plate']).astype(np.float32); H, W = plate.shape[:2]
pool = load_pieces(cfg['pieces']); names = [p[0] for p in pool]
WHITE = paper_white(cfg['ref_photo']); LIGHT = scene_light(plate, cfg.get('light_poly'))
WARM = np.array(cfg.get('warm', [0.86, 0.97, 1.08]), np.float32); EXPO = cfg.get('expo', 1.0)
grade = lambda rgb, g=1.0: np.clip(rgb / WHITE * LIGHT * EXPO * g * WARM, 0, 255)
LEN = cfg.get('length', 195); EL = cfg.get('elong', 1.0)
hand = np.zeros((H, W), np.uint8)
for poly in cfg.get('hand_polys', []):
    cv2.fillPoly(hand, [np.array(poly, np.int32)], 1)
hand_dist = cv2.distanceTransform((1 - hand).astype(np.uint8), cv2.DIST_L2, 5)
cv = Canvas(plate)
sc = cfg['scatter']; pts = []; tries = 0
while len(pts) < sc['n'] and tries < 5000:
    tries += 1; t = rng.uniform(0, 2 * np.pi); r = np.sqrt(rng.uniform(0, 1))
    x = sc['cx'] + sc['rx'] * r * np.cos(t); y = sc['cy'] + sc['ry'] * r * np.sin(t)
    if not (0 <= int(y) < H and 0 <= int(x) < W): continue
    if hand_dist[int(y), int(x)] < LEN * cfg.get('hand_margin', 0.75): continue
    if any(np.hypot(x - k['x'], y - k['y']) < k['r'] for k in cfg.get('keep_out', [])): continue
    if all(np.hypot(x - p[0], y - p[1]) > LEN * sc.get('spacing', 0.62) for p in pts): pts.append((x, y))
rng.shuffle(pts); last = -1
for x, y in pts:
    k = (last + rng.randrange(1, len(pool))) % len(pool); last = k; _, rgb, a = pool[k]
    rr, aa = xform(grade(rgb, rng.uniform(0.92, 1.08)), a, LEN * rng.uniform(0.88, 1.08), rng.uniform(0, 360), rng.random() < 0.5, EL)
    cv.place(rr, aa, x, y)
for f in cfg.get('fixed', []):
    _, rgb, a = pool[names.index(f['piece'])] if f.get('piece') in names else pool[0]
    rr, aa = xform(grade(rgb, 1.0), a, f.get('len', LEN), f['ang'], f.get('flip', False), EL)
    s = f.get('shadow', 1.0)
    cv.place(rr, aa, f['x'], f['y'], shadow=(int(-8 * s), int(11 * s)), sop=0.45, sblur=8 * s, contact=0.4)
ref = np.zeros((H, W), bool); ref[int(sc['cy'] - sc['ry'] / 2):int(sc['cy'] + sc['ry'] / 2), int(sc['cx'] - sc['rx'] / 2):int(sc['cx'] + sc['rx'] / 2)] = True
cv.light_falloff(ref, lo=0.8, hi=1.0)
img = apply_target_colour(cv.img, cv.wood, load_target(cfg['target']), LM=cfg.get('LM', -4), CK=cfg.get('CK', 0.25), DA=cfg.get('DA', 0), DB=cfg.get('DB', 0))
hm = cv2.GaussianBlur(hand.astype(np.float32), (5, 5), 0)[..., None]
img = img * (1 - hm) + plate * hm
cv2.imwrite(cfg['out'], np.clip(img, 0, 255).astype(np.uint8)); print('placed', len(pts), '+', len(cfg.get('fixed', [])))
