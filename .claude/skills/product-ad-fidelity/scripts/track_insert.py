"""Put a STATIC object into an already-animated clip, glued to a plane (table, lid, wall), no new generation.
Used for: the wooden burner / incense sticks on the marble, the gift card inside the box lid.

Two ways to get the object layer:
  A) still mode: a still with the same framing as the clip's first frame, that already shows the object
     (e.g. a Magnific edit "add the burner" on the clip's start image). --poly = object outline in that still.
  B) quad mode: cut a flat object (card, label) from any image by its 4 corners --src-quad and place it at
     --dst-quad in the clip frame --ref (in pixels of that frame).

usage:
  python track_insert.py clip.mp4 out.mp4 --still with_prop.png --poly "x,y x,y ..." [--track "x,y ..."] [--ref 0]
  python track_insert.py clip.mp4 out.mp4 --src ref.png --src-quad "TLx,TLy TRx,TRy BRx,BRy BLx,BLy" \
        --dst-quad "..." --track "x,y ..." [--ref 21] [--shadow=-9,6] [--glow 23.1,25.1 --t0 21.3]
--track: polygon of the plane to follow (default: a ring around the object). For a card in a lid, give the lid
lining polygon. The plane is tracked with LK optical flow from frame --ref, homographies smoothed over 7 frames.
Check the result on first / middle / last frame; drift is measured against the plane (aim < 4 px).
"""
import argparse, subprocess
import cv2
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument('clip'); ap.add_argument('out')
ap.add_argument('--still'); ap.add_argument('--poly')
ap.add_argument('--src'); ap.add_argument('--src-quad'); ap.add_argument('--dst-quad')
ap.add_argument('--track'); ap.add_argument('--ref', type=int, default=0); ap.add_argument('--feather', type=float, default=6)
ap.add_argument('--shadow', default=''); ap.add_argument('--glow', default=''); ap.add_argument('--t0', type=float, default=0.0)
A = ap.parse_args()
P = lambda s: np.float32([[float(v) for v in p.split(',')] for p in s.split()])

cap = cv2.VideoCapture(A.clip); fps = cap.get(5) or 30; fr = []
while True:
    ok, im = cap.read()
    if not ok: break
    fr.append(im)
h, w = fr[0].shape[:2]; R = fr[A.ref]; gR = cv2.cvtColor(R, cv2.COLOR_BGR2GRAY)

if A.still:   # A) still -> reference frame by ORB homography on the whole image
    K = cv2.resize(cv2.imread(A.still), (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
    poly = P(A.poly); orb = cv2.ORB_create(8000)
    ka, da = orb.detectAndCompute(cv2.cvtColor(K.astype(np.uint8), cv2.COLOR_BGR2GRAY), None); kb, db = orb.detectAndCompute(gR, None)
    m = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db), key=lambda x: x.distance)[:2500]
    H0, inl = cv2.findHomography(np.float32([ka[x.queryIdx].pt for x in m]), np.float32([kb[x.trainIdx].pt for x in m]), cv2.RANSAC, 2.5)
    print('still -> frame inliers', int(inl.sum()))
    layer = cv2.warpPerspective(K, H0, (w, h), flags=cv2.INTER_LANCZOS4)
    alpha = np.zeros((h, w), np.float32); cv2.fillPoly(alpha, [cv2.perspectiveTransform(poly[None], H0)[0].astype(np.int32)], 1.0)
    alpha = cv2.GaussianBlur(alpha, (0, 0), A.feather); obj = cv2.perspectiveTransform(poly[None], H0)[0]
else:         # B) flat object by quads
    S = cv2.imread(A.src).astype(np.float32); sq, dq = P(A.src_quad), P(A.dst_quad)
    cw = int(max(np.linalg.norm(sq[1] - sq[0]), np.linalg.norm(sq[2] - sq[3]))); ch = int(max(np.linalg.norm(sq[3] - sq[0]), np.linalg.norm(sq[2] - sq[1])))
    flat = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]])
    card = cv2.warpPerspective(S, cv2.getPerspectiveTransform(sq, flat), (cw, ch), flags=cv2.INTER_CUBIC)
    M = cv2.getPerspectiveTransform(flat, dq)
    layer = cv2.warpPerspective(card, M, (w, h), flags=cv2.INTER_CUBIC)
    alpha = cv2.GaussianBlur(cv2.warpPerspective(np.ones((ch, cw), np.float32), M, (w, h)), (0, 0), 0.8); obj = dq

trk = np.zeros((h, w), np.uint8)
if A.track: cv2.fillPoly(trk, [P(A.track).astype(np.int32)], 255)
else:
    o = np.zeros((h, w), np.uint8); cv2.fillPoly(o, [obj.astype(np.int32)], 255)
    trk = cv2.dilate(o, np.ones((241, 241), np.uint8)); trk[o > 0] = 0
pts = cv2.goodFeaturesToTrack(gR, 1200, 0.003, 5, mask=trk)
G = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]
Hs = [None] * len(fr)
for k in range(len(fr)):   # direct flow ref -> k (no drift accumulation)
    q, st, _ = cv2.calcOpticalFlowPyrLK(gR, G[k], pts, None, winSize=(31, 31), maxLevel=5); ok = st.ravel() == 1
    Hs[k] = cv2.findHomography(pts[ok], q[ok], cv2.RANSAC, 1.5)[0] if k != A.ref else np.eye(3)
C = np.array([cv2.perspectiveTransform(obj[None], Hh)[0] for Hh in Hs])
Cs = np.array([C[max(0, i - 3):i + 4].mean(0) for i in range(len(C))])
sh = [float(v) for v in A.shadow.split(',')] if A.shadow else None
gl = [float(v) for v in A.glow.split(',')] if A.glow else None
ss = lambda x: (lambda y: y * y * (3 - 2 * y))(min(max(x, 0), 1))
vw = cv2.VideoWriter(A.out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
for k, f in enumerate(fr):
    Hk = cv2.findHomography(obj, Cs[k])[0] if len(obj) > 4 else cv2.getPerspectiveTransform(obj[:4].astype(np.float32), Cs[k][:4].astype(np.float32))
    lay = cv2.warpPerspective(layer, Hk, (w, h), flags=cv2.INTER_LANCZOS4); a = cv2.warpPerspective(alpha, Hk, (w, h))
    o = f.astype(np.float32)
    if sh: o *= (1 - cv2.GaussianBlur(np.roll(np.roll(a, int(sh[0]), 1), int(sh[1]), 0), (0, 0), 9) * 0.45 * (1 - a))[..., None]
    o = o * (1 - a[..., None]) + lay * a[..., None]
    if gl:
        t = A.t0 + k / fps; g = ss((t - gl[0]) / 0.5) * (1 - ss((t - (gl[1] - 0.5)) / 0.5))
        if g > 0:
            halo = np.clip(cv2.GaussianBlur(a, (0, 0), 18) * 1.6 + cv2.GaussianBlur(a, (0, 0), 45) * 0.9, 0, 1) * (1 - a)
            o += (halo * g * 0.55)[..., None] * np.array([70, 170, 255], np.float32)
    vw.write(np.clip(o, 0, 255).astype(np.uint8))
vw.release(); print('frames', len(fr))
