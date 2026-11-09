"""Approved-box library: lock the look AND the arrangement of the product in a box across every new ad.

The client approved the filled boxes of ad 1. Re-generating an arrangement (AI or fill_container) never looks
"the same"; transplanting ONE approved heap into every box squashes it when the camera angle differs
(ad 2: the close high-angle heap warped into small low-angle boxes looked flat). So keep SEVERAL approved
heaps shot from different angles and always transplant the one whose box opening has the closest shape.

  add    : register an approved box     python box_masters.py add  NAME filled.png empty.png "BLx,BLy BRx,BRy FRx,FRy FLx,FLy" [--lib DIR]
  place  : fill a new empty box         python box_masters.py place empty.png out.png "BL BR FR FL" [--master NAME] [--relight 0.5] [--edge 5] [--lib DIR]
  sheet  : contact sheet of the library python box_masters.py sheet out.jpg [--lib DIR]

Quad = the box OPENING (inner top rim), order back-left, back-right, front-right, front-left, in image px.
Default library: ../assets/box_masters (Beethoven approved heaps, 4 angles).
"""
import argparse, json, os
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('args', nargs='*')
ap.add_argument('--lib', default=os.path.join(HERE, '..', 'assets', 'box_masters'))
ap.add_argument('--master'); ap.add_argument('--relight', type=float, default=0.5); ap.add_argument('--edge', type=int, default=5)
ap.add_argument('--tuck', type=float, default=0.12, help='how far the heap reaches under the front/side walls')
ap.add_argument('--back', type=float, default=0.1, help='empty band left at the back of the new box (fraction of depth)')
A = ap.parse_args(); os.makedirs(A.lib, exist_ok=True); META = os.path.join(A.lib, 'masters.json')
meta = json.load(open(META)) if os.path.exists(META) else {}


def q_of(s): return np.array([[float(v) for v in p.split(',')] for p in s.replace(';', ' ').split()], np.float32)


def lining_median(img, quad):
    """median colour of the cream lining visible inside the opening (scene light reference)."""
    lab = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.int16)
    m = ((lab[..., 0] > 90) & (np.abs(lab[..., 1] - 128) < 18) & (lab[..., 2] > 126) & (lab[..., 2] < 185)).astype(np.uint8)
    hp = np.zeros(m.shape, np.uint8); cv2.fillPoly(hp, [quad.astype(np.int32)], 1)
    hp = cv2.dilate(hp, np.ones((25, 25), np.uint8)); px = img[(m & hp) > 0]
    return np.median(px, 0) if len(px) > 200 else np.array([190, 215, 235], np.float32)


def shape(q):
    """camera-angle descriptor of an opening: back/front width ratio, depth/front width, side leans."""
    BL, BR, FR, FL = q; wf = np.linalg.norm(FR - FL); wb = np.linalg.norm(BR - BL)
    dl = FL - BL; dr = FR - BR
    return np.array([wb / wf, (np.linalg.norm(dl) + np.linalg.norm(dr)) / 2 / wf,
                     np.arctan2(dl[0], dl[1]), np.arctan2(dr[0], dr[1]),
                     np.arctan2(FR[1] - FL[1], FR[0] - FL[0])], np.float32)


if A.cmd == 'add':
    name, fp, ep, qs = A.args; F = cv2.imread(fp).astype(np.float32); E = cv2.imread(ep).astype(np.float32); q = q_of(qs)
    so = np.zeros(F.shape[:2], np.uint8); cv2.fillPoly(so, [q.astype(np.int32)], 1)
    a = np.clip((np.abs(F - E).max(2) - 10) / 30, 0, 1) * so
    lin = lining_median(E, q); g = F.mean(2)                     # product = changed AND clearly darker than the lining
    a *= np.clip((lin.mean() * 0.78 - g) / 25, 0, 1)                 # (drops light-falloff/shadow changes on the walls)
    n_, lb_, st_, _ = cv2.connectedComponentsWithStats((a > 0.3).astype(np.uint8))
    a *= (lb_ == 1 + np.argmax(st_[1:, 4])) if n_ > 1 else 1        # keep the heap itself, no stray specks
    a = cv2.GaussianBlur(a.astype(np.float32), (3, 3), 0)
    # back band the heap leaves empty (approved: nothing climbs the back wall) -> store the heap's own footprint
    BL, BR, FR, FL = q; t = []
    for u in np.linspace(0.2, 0.8, 7):
        b = BL + (BR - BL) * u; f = FL + (FR - FL) * u
        col = [a[int(y), int(x)] for x, y in (b + (f - b) * v for v in np.linspace(0, 1, 60))]
        t.append(next((v for v, c in zip(np.linspace(0, 1, 60), col) if c > 0.5), 0.0))
    bt = float(np.median(t)); fq = q.copy(); fq[0] = BL + (FL - BL) * bt; fq[1] = BR + (FR - BR) * bt
    a = cv2.GaussianBlur(cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)), (3, 3), 0)
    x0, y0 = np.maximum(q.min(0).astype(int) - 20, 0); x1, y1 = q.max(0).astype(int) + 20
    rgba = np.dstack([F[y0:y1, x0:x1], a[y0:y1, x0:x1] * 255]).clip(0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(A.lib, name + '.png'), rgba)
    meta[name] = {'quad': (q - [x0, y0]).round(1).tolist(), 'heap_quad': (fq - [x0, y0]).round(1).tolist(), 'back_gap': round(bt, 3),
                  'lining': lin.round(1).tolist(), 'shape': shape(q).round(4).tolist()}
    json.dump(meta, open(META, 'w'), indent=1); print('added', name, rgba.shape)

elif A.cmd == 'place':
    ep, op, qs = A.args; D = cv2.imread(ep).astype(np.float32); H, W = D.shape[:2]; dq = q_of(qs); ds = shape(dq)
    wts = np.array([1.0, 1.5, 0.8, 0.8, 0.6])
    ranked = sorted(meta, key=lambda k: float((np.abs(np.array(meta[k]['shape']) - ds) * wts).sum()))
    name = A.master or ranked[0]; m = meta[name]
    print('masters by angle match:', ', '.join(ranked), '-> using', name)
    src = cv2.imread(os.path.join(A.lib, name + '.png'), cv2.IMREAD_UNCHANGED).astype(np.float32)
    tq = dq.copy(); tq[0] = dq[0] + (dq[3] - dq[0]) * A.back; tq[1] = dq[1] + (dq[2] - dq[1]) * A.back
    # tuck the heap slightly under the front and side walls (clipped below), so no bare satin / cut-off
    # piece shows in the front corners (client: "something stuck on / sticking out" at the front-left corner)
    c = tq.mean(0); tq = c + (tq - c) * (1 + A.tuck)   # grow front + sides; back corners are reset below
    tq[0] = dq[0] + (dq[3] - dq[0]) * A.back + (dq[0] - dq[1]) * A.tuck / 2; tq[1] = dq[1] + (dq[2] - dq[1]) * A.back + (dq[1] - dq[0]) * A.tuck / 2
    Hm = cv2.getPerspectiveTransform(np.array(m.get('heap_quad', m['quad']), np.float32), tq)   # heap footprint -> new opening
    wF = cv2.warpPerspective(src[..., :3], Hm, (W, H), flags=cv2.INTER_CUBIC)
    wa = cv2.warpPerspective(src[..., 3] / 255, Hm, (W, H), flags=cv2.INTER_LINEAR)
    wF *= (lining_median(D, dq) / np.array(m['lining'], np.float32)) ** A.relight   # match the new scene light
    qm = np.zeros((H, W), np.uint8); cv2.fillPoly(qm, [dq.astype(np.int32)], 1)
    # the real opening = the light, non-green inside of the EMPTY plate. A hand-read quad that runs a few px over
    # a wall top made the wall look "bent inward" under the wood (client, ad 2 front-left corner) -> never cover green.
    lab = cv2.cvtColor(D.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.int16)
    opn = ((lab[..., 1] >= 124) & (lab[..., 0] > 60)).astype(np.uint8) & cv2.dilate(qm, np.ones((41, 41), np.uint8))
    opn = cv2.morphologyEx(opn, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n_, lb_, st_, _ = cv2.connectedComponentsWithStats(opn)
    if n_ > 1:
        opn = (lb_ == 1 + np.argmax(st_[1:, 4])).astype(np.uint8); cn_, _ = cv2.findContours(opn, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        opn = np.zeros_like(opn); cv2.fillConvexPoly(opn, cv2.convexHull(max(cn_, key=cv2.contourArea)), 1);   # straight along the walls
        qm = cv2.dilate(qm, np.ones((15, 15), np.uint8)) & opn
    qm = cv2.erode(qm, np.ones((A.edge, A.edge), np.uint8))
    al = (wa * cv2.GaussianBlur(qm.astype(np.float32), (3, 3), 0))[..., None]   # never outside the opening
    cv2.imwrite(op, np.clip(D * (1 - al) + wF * al, 0, 255).astype(np.uint8)); print('wrote', op)

elif A.cmd == 'sheet':
    tiles = []
    for k in meta:
        im = cv2.imread(os.path.join(A.lib, k + '.png'), cv2.IMREAD_UNCHANGED); a = im[..., 3:4] / 255
        im = (im[..., :3] * a + 40 * (1 - a)).astype(np.uint8); im = cv2.resize(im, (480, int(480 * im.shape[0] / im.shape[1])))
        im = cv2.copyMakeBorder(im, 0, max(0, 420 - im.shape[0]), 0, 0, cv2.BORDER_CONSTANT, value=(40, 40, 40))[:420]
        cv2.putText(im, k, (10, 30), 0, 0.9, (0, 255, 255), 2); tiles.append(im)
    cv2.imwrite(A.args[0], np.hstack(tiles)); print('sheet', len(tiles))
