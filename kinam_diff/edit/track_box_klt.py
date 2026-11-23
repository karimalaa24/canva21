"""D6: carry the real-lid-art still into the moving Kling clip. The plain AI lid has no texture for SIFT, so track the WHOLE
rigid box (lid edges, clasp, front face) frame-to-frame with KLT, homography per step (RANSAC), chained, smoothed, then warp the
clean lid face in with the clip's local light. Free. usage: track_box_klt.py clip still "lid BL BR FR FL" "box poly" out.mp4 [nframes]"""
import cv2, numpy as np, sys
clip, still, lidq, boxp, out = sys.argv[1:6]; NF = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 9
cap = cv2.VideoCapture(clip); fr = []
while len(fr) < NF:
    ok, im = cap.read()
    if not ok: break
    fr.append(im)
H, W = fr[0].shape[:2]; S0 = cv2.imread(still); s = W / S0.shape[1]
clean = cv2.resize(S0, (W, int(S0.shape[0] * s)), interpolation=cv2.INTER_AREA)[:H].astype(np.float32)
LQ = np.float32([[float(v) for v in p.split(',')] for p in lidq.split()]) * s
BP = np.float32([[float(v) for v in p.split(',')] for p in boxp.split()]) * s
m0 = np.zeros((H, W), np.float32); cv2.fillPoly(m0, [LQ.astype(np.int32)], 1)
Hc = np.eye(3); Hs = [Hc.copy()]; prev = cv2.cvtColor(fr[0], cv2.COLOR_BGR2GRAY)

for i in range(1, len(fr)):
    g = cv2.cvtColor(fr[i], cv2.COLOR_BGR2GRAY)
    bm = np.zeros((H, W), np.uint8); cv2.fillPoly(bm, [cv2.perspectiveTransform(BP[None], Hc)[0].astype(np.int32)], 255)
    p0 = cv2.goodFeaturesToTrack(prev, 600, 0.005, 5, mask=bm)
    if p0 is None or len(p0) < 12: Hs.append(Hc.copy()); prev = g; continue
    p1, st, _ = cv2.calcOpticalFlowPyrLK(prev, g, p0, None, winSize=(31, 31), maxLevel=4)
    pb, _, _ = cv2.calcOpticalFlowPyrLK(g, prev, p1, None, winSize=(31, 31), maxLevel=4)
    ok = (st[:, 0] == 1) & (np.linalg.norm(pb - p0, axis=2)[:, 0] < 1.0)
    Hstep, inl = cv2.findHomography(p0[ok], p1[ok], cv2.RANSAC, 1.5) if ok.sum() >= 12 else (None, None)
    if Hstep is None: Hstep = np.eye(3)
    Hc = Hstep @ Hc
    # lid-plane refinement frame-to-frame: ECC homography on the lid face + its outline (subpixel, one plane only)
    LM = np.zeros((H, W), np.uint8); cv2.fillPoly(LM, [cv2.perspectiveTransform(LQ[None], Hs[-1])[0].astype(np.int32)], 255); LM = cv2.dilate(LM, np.ones((9, 9), np.uint8))
    try:
        St = (Hstep / Hstep[2, 2]).astype(np.float32)
        _, St = cv2.findTransformECC(cv2.GaussianBlur(prev, (0, 0), 1.2).astype(np.float32), cv2.GaussianBlur(g, (0, 0), 1.2).astype(np.float32), St, cv2.MOTION_HOMOGRAPHY, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-6), LM, 5)
        Hc = St.astype(np.float64) @ Hs[-1]
    except cv2.error: print('ecc fail', i)
    Hs.append(Hc.copy()); prev = g
    if i % 20 == 0: print(i, int(ok.sum()), int(inl.sum()) if inl is not None else 0); sys.stdout.flush()
C = np.array([cv2.perspectiveTransform(LQ[None], h)[0] for h in Hs]); Cs = C.copy()
for j in range(len(C)): a, b = max(0, j - 2), min(len(C), j + 3); Cs[j] = C[a:b].mean(0)
enc = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*'mp4v'), 24, (W, H))
ref = cv2.GaussianBlur(fr[0].astype(np.float32), (0, 0), 20)
for i, f in enumerate(fr):
    Hk = cv2.getPerspectiveTransform(LQ, Cs[i].astype(np.float32))
    w = cv2.warpPerspective(clean, Hk, (W, H), flags=cv2.INTER_CUBIC)
    A = cv2.GaussianBlur(cv2.warpPerspective(m0, Hk, (W, H)), (0, 0), 0.8)[..., None]
    cur = cv2.GaussianBlur(f.astype(np.float32), (0, 0), 20); refw = cv2.warpPerspective(ref, Hk, (W, H))
    gain = np.clip((cur + 1) / (refw + 1), 0.8, 1.25)
    o = w * gain * A + f.astype(np.float32) * (1 - A); enc.write(np.clip(o, 0, 255).astype(np.uint8))
enc.release(); print('frames', len(fr))
