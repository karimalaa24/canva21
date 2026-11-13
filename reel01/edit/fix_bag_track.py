"""Paste the clean bag artwork from the approved still onto a Kling clip that re-invented text (S11).
Per-frame homography still->frame from ORB matches inside a region around the bag (no drift), feathered bag-only mask,
local brightness match. usage: fix_bag_track.py still.png clip.mp4 out.mp4 x0 y0 x1 y1  (rect in still px)"""
import cv2, numpy as np, sys, subprocess
st_p, clip, out = sys.argv[1:4]; x0, y0, x1, y1 = map(int, sys.argv[4:8])
cap = cv2.VideoCapture(clip); fps = cap.get(5); fr = []
while True:
    ok, im = cap.read()
    if not ok: break
    fr.append(im)
h, w = fr[0].shape[:2]; S = cv2.imread(st_p); sx, sy = w / S.shape[1], h / S.shape[0]; S = cv2.resize(S, (w, h), interpolation=cv2.INTER_AREA)
X0, Y0, X1, Y1 = int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy)
reg = S[Y0:Y1, X0:X1].astype(np.float32); isbag = ((reg[..., 2] > reg[..., 1] + 12) & (reg.mean(2) < 150)).astype(np.float32)
isbag = cv2.erode(isbag, np.ones((5, 5), np.uint8))
alpha = np.zeros((h, w), np.float32); alpha[Y0:Y1, X0:X1] = isbag; alpha = cv2.GaussianBlur(alpha, (0, 0), 3)
# feature region around the bag (bag + its neighbours, same depth band)
roi = np.zeros((h, w), np.uint8); cv2.rectangle(roi, (max(0, X0 - 260), max(0, Y0 - 260)), (min(w - 1, X1 + 160), min(h - 1, Y1 + 260)), 255, -1)
orb = cv2.ORB_create(6000); gS = cv2.cvtColor(S, cv2.COLOR_BGR2GRAY); kS, dS = orb.detectAndCompute(gS, roi)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True); Hs = []
for f in fr:
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); kF, dF = orb.detectAndCompute(g, cv2.dilate(roi, np.ones((121, 121), np.uint8)))
    m = sorted(bf.match(dS, dF), key=lambda x: x.distance)[:1500]
    Hm, inl = cv2.findHomography(np.float32([kS[x.queryIdx].pt for x in m]), np.float32([kF[x.trainIdx].pt for x in m]), cv2.RANSAC, 2.0)
    Hs.append(Hm)
C = np.float32([[X0, Y0], [X1, Y0], [X1, Y1], [X0, Y1]])
P = np.array([cv2.perspectiveTransform(C[None], Hm)[0] for Hm in Hs]); Ps = np.array([P[max(0, i - 3):i + 4].mean(0) for i in range(len(P))])
print('corner jitter px (raw vs smoothed, median):', float(np.median(np.abs(P - Ps))))
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'slow', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
for k, f in enumerate(fr):
    Hk = cv2.getPerspectiveTransform(C, Ps[k].astype(np.float32))
    lay = cv2.warpPerspective(S, Hk, (w, h), flags=cv2.INTER_LANCZOS4).astype(np.float32); a = cv2.warpPerspective(alpha, Hk, (w, h))[..., None]
    o = f.astype(np.float32)
    # match local light of this frame (clip grade drifts): low-freq ratio on the bag area
    lo_f = cv2.GaussianBlur(o, (0, 0), 25); lo_l = cv2.GaussianBlur(lay, (0, 0), 25)
    lay = lay * np.clip(lo_f / np.maximum(lo_l, 1), 0.7, 1.4)
    o = o * (1 - a) + lay * a
    enc.stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('frames', len(fr))
