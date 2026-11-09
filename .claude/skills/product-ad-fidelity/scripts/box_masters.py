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
ap.add_argument('--left', type=float, default=0.0, help='starting margin at the left wall (fraction of width); the fit only pulls in')
ap.add_argument('--right', type=float, default=0.0)
ap.add_argument('--mirror', action='store_true')
ap.add_argument('--ring', type=int, default=1, help='fill the band between heap and walls with whole pieces')
ap.add_argument('--piece', type=float, default=0.27, help='ring piece length / box front width (ad 1: ~1/3)')
ap.add_argument('--depth_ratio', type=float, default=0.85, help='box depth / width (real proportions)')
ap.add_argument('--seed', type=int, default=3)
ap.add_argument('--max_ring', type=int, default=24)
ap.add_argument('--max_overlap', type=float, default=0.55)
ap.add_argument('--wall_px', type=int, default=8, help='even lining strip kept between wood and the walls (px at plate size)')
ap.add_argument('--front', type=float, default=0.0)
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
    # 1) the real opening of the EMPTY plate. Not a hand-read quad and not "non-green + convex hull": the rim's top band
    #    carries a golden highlight, and wood over it made the rim look wider in front / "bent" (client, ad 2).
    qm = np.zeros((H, W), np.uint8); cv2.fillPoly(qm, [dq.astype(np.int32)], 1)
    lab = cv2.cvtColor(D.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.int16)
    opn = ((lab[..., 1] >= 124) & (lab[..., 0] > 60)).astype(np.uint8) & cv2.dilate(qm, np.ones((41, 41), np.uint8))
    opn = cv2.morphologyEx(opn, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))   # drops the thin rim highlight
    n_, lb_, st_, _ = cv2.connectedComponentsWithStats(opn)
    if n_ > 1:
        opn = (lb_ == 1 + np.argmax(st_[1:, 4])).astype(np.uint8)
        opn = cv2.morphologyEx(opn, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
        cn_, _ = cv2.findContours(opn, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); opn = np.zeros_like(opn); cv2.drawContours(opn, cn_, -1, 1, -1)
        opn = (cv2.GaussianBlur(opn.astype(np.float32), (0, 0), 4) > 0.5).astype(np.uint8)      # smooth, straight edges
        qm = cv2.dilate(qm, np.ones((15, 15), np.uint8)) & opn
    qm = cv2.erode(qm, np.ones((A.edge, A.edge), np.uint8))
    if A.wall_px > 0:   # thin even lining strip between wood and every wall: rim edges stay crisp, same as the empty box
        qm = cv2.erode(qm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * A.wall_px + 1,) * 2))
    # the master's outermost few px hold the dark contact-shadow seam of its old (ad-1) rim cut: trim them
    src[..., 3] = cv2.erode(src[..., 3], cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
    # 2) the approved heap's own tight footprint (its natural outline: whole pieces, nothing cut)
    hq = np.array(m.get('heap_quad', m['quad']), np.float32)
    if A.mirror:
        src = src[:, ::-1].copy(); hq[:, 0] = src.shape[1] - 1 - hq[:, 0]; hq = hq[[1, 0, 3, 2]]
    S_ = 600; un = cv2.warpPerspective(src[..., 3] / 255, cv2.getPerspectiveTransform(hq, np.float32([[0, 0], [S_, 0], [S_, S_], [0, S_]])), (S_, S_))
    ys_, xs_ = np.where(un > 0.5); u0, u1 = np.percentile(xs_, [0.2, 99.8]) / S_; v0, v1 = np.percentile(ys_, [0.2, 99.8]) / S_
    Ph = lambda u, v: (1 - v) * ((1 - u) * hq[0] + u * hq[1]) + v * ((1 - u) * hq[3] + u * hq[2])
    sq = np.array([Ph(u0, v0), Ph(u1, v0), Ph(u1, v1), Ph(u0, v1)], np.float32)
    # 3) fit that footprint INSIDE the opening: start at the walls, pull in only the side(s) where wood would cross
    #    a rim, until no piece is cut (client, ad 2: "nothing sticking out over the edges").
    P = lambda u, v: (1 - v) * ((1 - u) * dq[0] + u * dq[1]) + v * ((1 - u) * dq[3] + u * dq[2])
    Hd = cv2.getPerspectiveTransform(dq, np.float32([[0, 0], [1, 0], [1, 1], [0, 1]]))
    mg = {'l': A.left, 'r': A.right, 'f': A.front, 'b': A.back}
    for it in range(80):
        tq = np.array([P(mg['l'], mg['b']), P(1 - mg['r'], mg['b']), P(1 - mg['r'], 1 - mg['f']), P(mg['l'], 1 - mg['f'])], np.float32)
        Hm = cv2.getPerspectiveTransform(sq, tq)
        wa = cv2.warpPerspective(src[..., 3] / 255, Hm, (W, H), flags=cv2.INTER_LINEAR)
        out = (wa > 0.35) & (qm == 0); n_out = int(out.sum())
        if n_out <= max(30, 0.0005 * (wa > 0.35).sum()): break
        oy, ox = np.where(out); uv = cv2.perspectiveTransform(np.c_[ox, oy].astype(np.float32)[None], Hd)[0]
        uu, vv = uv[:, 0], uv[:, 1]; k = 0.006
        if (uu < 0.25).sum() > 10: mg['l'] += k
        if (uu > 0.75).sum() > 10: mg['r'] += k
        if (vv > 0.7).sum() > 10: mg['f'] += k
        if (vv < 0.3).sum() > 10: mg['b'] += k
    print('fit: margins l %.3f r %.3f front %.3f back %.3f, wood px over a rim: %d' % (mg['l'], mg['r'], mg['f'], mg['b'], n_out))
    wF = cv2.warpPerspective(src[..., :3], Hm, (W, H), flags=cv2.INTER_CUBIC)
    wF *= (lining_median(D, dq) / np.array(m['lining'], np.float32)) ** A.relight   # match the new scene light
    wa = np.clip((wa - 0.3) / 0.45, 0, 1)    # drop the faint dark seam the master kept along its old (ad-1) rim cut
    al = (wa * cv2.GaussianBlur(qm.astype(np.float32), (0, 0), 1.6))[..., None]   # safety clip (should cut ~nothing now)
    out = D * (1 - al) + wF * al
    # 4) ring fill: the band between the whole heap and the walls gets WHOLE real pieces (same cut-outs, same colour
    #    model as ad 1), laid over the heap's edge -> the box looks full, the heap edge looks natural, and no piece is
    #    ever cut by a rim: every ring piece must lie fully inside the opening.
    pdir = os.path.join(A.lib, 'pieces')
    if A.ring and os.path.isdir(pdir):
        import random, sys
        sys.path.insert(0, HERE); from common import load_pieces, xform, Canvas, load_target, apply_target_colour
        rng = random.Random(A.seed); pool = load_pieces(pdir); kit = json.load(open(os.path.join(A.lib, 'kit.json')))
        fitm = cv2.erode(qm, np.ones((5, 5), np.uint8)).astype(bool)
        light = lining_median(D, dq)
        grade = lambda c, g: np.clip(c / np.array(kit['paper_white'], np.float32) * light * g * np.array([0.86, 0.97, 1.08]), 0, 255)
        LEN = A.piece * np.linalg.norm(dq[2] - dq[3]); cv = Canvas(out); last = -1
        def fits(aa, cx, cy):
            h_, w_ = aa.shape; ys, xs = np.where(aa > 0.25); ys = ys + int(cy - h_ / 2); xs = xs + int(cx - w_ / 2)
            if ys.min() < 0 or xs.min() < 0 or ys.max() >= H or xs.max() >= W: return False
            return fitm[ys, xs].all()
        heap = wa > 0.3
        def overlap(aa, cx, cy):
            h_, w_ = aa.shape; ys, xs = np.where(aa > 0.25); ys = ys + int(cy - h_ / 2); xs = xs + int(cx - w_ / 2)
            return float(heap[ys, xs].mean())
        # back band stays empty (nothing climbs the back wall)
        bm_ = np.zeros((H, W), np.uint8); cv2.fillPoly(bm_, [np.array([P(0, 0), P(1, 0), P(1, mg['b'] + 0.03), P(0, mg['b'] + 0.03)], np.int32)], 1)
        ring = (qm > 0) & ~heap & (bm_ == 0)
        walls = [(dq[3] - dq[0], 0), (dq[2] - dq[1], 1), (dq[2] - dq[3], 2)]          # left, right, front wall directions
        unc = ring.copy(); fails = 0; n_ring = 0; tot = max(1, ring.sum())
        while unc.sum() > 0.08 * tot and fails < 300 and n_ring < A.max_ring:
            dt = cv2.distanceTransform(unc.astype(np.uint8), cv2.DIST_L2, 5); y, x = np.unravel_index(np.argmax(dt), dt.shape)
            uvp = cv2.perspectiveTransform(np.float32([[[x, y]]]), Hd)[0, 0]
            wi = int(np.argmin([uvp[0], 1 - uvp[0], 1 - uvp[1]])); vec = walls[wi][0]
            ang0 = -np.degrees(np.arctan2(vec[1], vec[0])); ok = False
            for _ in range(40):
                k = (last + rng.randrange(1, len(pool))) % len(pool); _, rgb, a_ = pool[k]
                rr, aa = xform(grade(rgb, rng.uniform(0.95, 1.04)), a_, LEN * rng.uniform(0.8, 1.0), (ang0 + rng.uniform(-22, 22) if rng.random() < 0.5 else ang0 + rng.choice([-1, 1]) * rng.uniform(35, 70)), rng.random() < 0.5, 1.12, 0.85)
                ctr = dq.mean(0); nv = (ctr - [x, y]) / (np.linalg.norm(ctr - [x, y]) + 1e-6)   # inward, over the heap edge
                sh_ = rng.uniform(0.0, 0.25) * LEN
                cx = x + nv[0] * sh_ + rng.uniform(-LEN * 0.08, LEN * 0.08); cy = y + nv[1] * sh_ + rng.uniform(-LEN * 0.08, LEN * 0.08)
                if fits(aa, cx, cy) and overlap(aa, cx, cy) <= A.max_overlap:   # mostly in the gap, only its end on the heap
                    mm = cv.place(rr, aa, cx, cy, shadow=(-6, 9), sblur=8); last = k; ok = True; n_ring += 1
                    if mm is not None: unc &= ~mm
                    break
            if not ok:
                cv2.circle(unc.view(np.uint8), (int(x), int(y)), max(4, int(LEN * 0.1)), 0, -1); fails += 1
        if n_ring:
            out = apply_target_colour(cv.img, cv.wood, load_target(os.path.join(A.lib, 'target.json')), region=cv.wood > 0.5)
            ch = cv2.GaussianBlur(qm.astype(np.float32), (0, 0), 1.6)[..., None]          # shadows never leave the opening
            out = (D * (1 - al) + wF * al) * (1 - ch) + out * ch
        print('ring pieces', n_ring)
    cv2.imwrite(op, np.clip(out, 0, 255).astype(np.uint8)); print('wrote', op)


elif A.cmd == 'sheet':
    tiles = []
    for k in meta:
        im = cv2.imread(os.path.join(A.lib, k + '.png'), cv2.IMREAD_UNCHANGED); a = im[..., 3:4] / 255
        im = (im[..., :3] * a + 40 * (1 - a)).astype(np.uint8); im = cv2.resize(im, (480, int(480 * im.shape[0] / im.shape[1])))
        im = cv2.copyMakeBorder(im, 0, max(0, 420 - im.shape[0]), 0, 0, cv2.BORDER_CONSTANT, value=(40, 40, 40))[:420]
        cv2.putText(im, k, (10, 30), 0, 0.9, (0, 255, 255), 2); tiles.append(im)
    cv2.imwrite(A.args[0], np.hstack(tiles)); print('sheet', len(tiles))
