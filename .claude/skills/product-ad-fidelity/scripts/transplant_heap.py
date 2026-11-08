"""Copy an APPROVED filled box (heap of pieces) into another empty box, pixel-for-pixel, warped to
the new box's perspective. Use this when the client says "make all boxes exactly like that one":
re-generating a new arrangement never reaches 99 % identity; transplanting does.

usage: python transplant_heap.py cfg.json
{
 "src_filled": "approved_filled.png", "src_empty": "approved_empty_plate.png",
 "src_quad": [[BLx,BLy],[BRx,BRy],[FRx,FRy],[FLx,FLy]],      # opening corners in the approved image
 "dst_empty": "new_empty_plate.png", "out": "new_filled.png",
 "dst_quad": optional; if absent it is fitted to the cream lining of dst_empty inside "dst_hint" polygon,
 "dst_hint": [[x,y],...],                                     # rough polygon around the new opening
 "relight": 0.5                                               # 0 = keep approved colours, 1 = full scene-light match
}
"""
import json, sys
import cv2
import numpy as np

c = json.load(open(sys.argv[1]))
F = cv2.imread(c['src_filled']).astype(np.float32); E = cv2.imread(c['src_empty']).astype(np.float32)
D = cv2.imread(c['dst_empty']).astype(np.float32); H, W = D.shape[:2]
sq = np.array(c['src_quad'], np.float32)


def lining(img, poly):
    lab = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.int16)
    m = ((lab[..., 0] > 90) & (np.abs(lab[..., 1] - 128) < 18) & (lab[..., 2] > 126) & (lab[..., 2] < 185) & (lab[..., 2] - lab[..., 1] > 2)).astype(np.uint8)
    hp = np.zeros(m.shape, np.uint8); cv2.fillPoly(hp, [np.array(poly, np.int32)], 1); m &= hp
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, lb, st, _ = cv2.connectedComponentsWithStats(m); m = (lb == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
    cn, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); m = np.zeros_like(m); cv2.drawContours(m, cn, -1, 1, -1)
    return m


def quad_of(mask):
    cn, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); hull = cv2.convexHull(max(cn, key=cv2.contourArea)).reshape(-1, 2).astype(np.float32)
    s = hull.sum(1); d = hull[:, 0] - hull[:, 1]
    bl = hull[np.argmin(s)]          # top-left in image = back-left
    fr = hull[np.argmax(s)]          # bottom-right = front-right
    br = hull[np.argmax(d)]          # top-right = back-right
    fl = hull[np.argmin(d)]          # bottom-left = front-left
    return np.array([bl, br, fr, fl], np.float32)


dlin = lining(D, c['dst_hint'])
dq = np.array(c['dst_quad'], np.float32) if 'dst_quad' in c else quad_of(dlin)
# heap layer of the approved image: everything that differs from its empty plate inside the opening
so = np.zeros(F.shape[:2], np.uint8); cv2.fillPoly(so, [sq.astype(np.int32)], 1)
diff = np.abs(F - E).max(2); a = np.clip((diff - 10) / 30, 0, 1) * so
a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); a = cv2.GaussianBlur(a, (3, 3), 0)
Hm = cv2.getPerspectiveTransform(sq, dq)
wF = cv2.warpPerspective(F, Hm, (W, H), flags=cv2.INTER_CUBIC); wa = cv2.warpPerspective(a, Hm, (W, H), flags=cv2.INTER_LINEAR)
# relight: approved heap was lit by the old scene; nudge toward the new lining colour
rl = c.get('relight', 0.5)
oldL = np.median(E[(lining(E, sq.tolist()) > 0)], axis=0); newL = np.median(D[dlin > 0], axis=0)
wF = wF * ((newL / oldL) ** rl)
qm = np.zeros((H, W), np.uint8); cv2.fillPoly(qm, [dq.astype(np.int32)], 1)
qm = cv2.erode(qm, np.ones((c.get('edge_px', 5),) * 2, np.uint8))
clip = cv2.GaussianBlur(qm.astype(np.float32), (3, 3), 0)   # never outside the new opening (front wall / clasp stay on top)
A = (wa * clip)[..., None]
out = D * (1 - A) + wF * A
cv2.imwrite(c['out'], np.clip(out, 0, 255).astype(np.uint8))
print('dst_quad', dq.round().tolist())
