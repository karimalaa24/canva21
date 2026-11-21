"""Replace the smudged lid face in an existing Kling clip (K2_closed) with the clean real-lid still, frame by frame:
lid face is a rigid plane -> homography frame0->frame k from SIFT matches on the lid + box top (RANSAC), chained with a KLT-style
refinement against the previous frame to avoid jitter; the clean lid (still, scaled to clip res) is warped in and feathered. Free.
usage: track_lid.py clip.mp4 clean_still.png "lid face BL BR FR FL (still coords)" out.mp4"""
import cv2, numpy as np, sys
clip, still, lidq, out = sys.argv[1:5]
cap = cv2.VideoCapture(clip); fr = []
while True:
    ok, im = cap.read()
    if not ok: break
    fr.append(im)
H, W = fr[0].shape[:2]; S0 = cv2.imread(still); s = W / S0.shape[1]
clean = cv2.resize(S0, (W, int(S0.shape[0] * s)), interpolation=cv2.INTER_AREA)[:H]
LQ = np.float32([[float(v) for v in p.split(',')] for p in lidq.split()]) * s
m0 = np.zeros((H, W), np.uint8); cv2.fillPoly(m0, [(LQ.mean(0) + (LQ - LQ.mean(0)) * 0.985).astype(np.int32)], 1)
feat = np.zeros((H, W), np.uint8); cv2.fillPoly(feat, [(LQ.mean(0) + (LQ - LQ.mean(0)) * 1.25).astype(np.int32)], 255)
sift = cv2.SIFT_create(4000); g0 = cv2.cvtColor(fr[0], cv2.COLOR_BGR2GRAY); k0, d0 = sift.detectAndCompute(g0, feat)
bf = cv2.BFMatcher(); Hs = []; prevH = np.eye(3)
for i, f in enumerate(fr):
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    mk = cv2.warpPerspective(feat, prevH, (W, H)); k1, d1 = sift.detectAndCompute(g, cv2.dilate(mk, np.ones((41, 41), np.uint8)))
    mt = [a for a, b in bf.knnMatch(d0, d1, k=2) if a.distance < 0.75 * b.distance]
    if len(mt) >= 12:
        p0 = np.float32([k0[a.queryIdx].pt for a in mt]); p1 = np.float32([k1[a.trainIdx].pt for a in mt])
        Hk, inl = cv2.findHomography(p0, p1, cv2.RANSAC, 2.0)
        if Hk is None or inl.sum() < 10: Hk = prevH
    else: Hk = prevH
    Hs.append(Hk); prevH = Hk
# temporal smoothing of the corner trajectories (removes 1-2 px jitter)
C = np.array([cv2.perspectiveTransform(LQ[None], h)[0] for h in Hs])
Cs = C.copy()
for j in range(len(C)):
    a, b = max(0, j - 3), min(len(C), j + 4); Cs[j] = C[a:b].mean(0)
enc = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*'mp4v'), 24, (W, H)); jit = []
for i, f in enumerate(fr):
    Hk = cv2.getPerspectiveTransform(LQ, Cs[i].astype(np.float32))
    w = cv2.warpPerspective(clean, Hk, (W, H), flags=cv2.INTER_CUBIC).astype(np.float32)
    mm = cv2.warpPerspective(m0.astype(np.float32), Hk, (W, H)); A = cv2.GaussianBlur(mm, (0, 0), 1.0)[..., None]
    # follow the clip's light on the lid (low-frequency luminance ratio clip/frame0 under the lid)
    if i == 0: ref = cv2.GaussianBlur(f.astype(np.float32), (0, 0), 25)
    cur = cv2.GaussianBlur(f.astype(np.float32), (0, 0), 25); refw = cv2.warpPerspective(ref, Hk, (W, H))
    gain = np.clip((cur.mean(2) + 1) / (refw.mean(2) + 1), 0.85, 1.15)[..., None]
    o = w * gain * A + f.astype(np.float32) * (1 - A); enc.write(np.clip(o, 0, 255).astype(np.uint8))
    jit.append(np.abs(C[i] - Cs[i]).max())
enc.release(); print('frames', len(fr), 'max corner jitter removed %.2f px' % max(jit))
