"""Paste the oud area of the (updated) approved still into a Kling clip made from the old still.
KLT: points on the box body (rim, walls, front; oud excluded) tracked frame-to-frame from frame 0 (= the still),
forward-backward checked; H_k = homography(frame0 pts -> frame k pts); smoothed corners; feathered inner mask; light match.
usage: track_oud.py new_still.png clip.mp4 out.mp4 "x,y x,y ..." (opening polygon in still px)"""
import cv2, numpy as np, sys, subprocess
st, clip, out, poly = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
cap = cv2.VideoCapture(clip); fps = cap.get(5); fr = []
while True:
    ok, im = cap.read()
    if not ok: break
    fr.append(im)
h, w = fr[0].shape[:2]; S = cv2.imread(st); sx, sy = w / S.shape[1], h / S.shape[0]; S = cv2.resize(S, (w, h), interpolation=cv2.INTER_AREA)
P = np.float32([[float(v) for v in p.split(',')] for p in poly.split()]) * [sx, sy]
mask = np.zeros((h, w), np.uint8); cv2.fillPoly(mask, [P.astype(np.int32)], 255)
x0, y0, bw, bh = cv2.boundingRect(P.astype(np.int32))
roi = np.zeros((h, w), np.uint8); cv2.rectangle(roi, (max(0, x0 - 40), max(0, y0 - 20)), (min(w - 1, x0 + bw + 40), min(h - 1, y0 + bh + 140)), 255, -1)
roi[cv2.dilate(mask, np.ones((15, 15), np.uint8)) > 0] = 0
G = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]
p0 = cv2.goodFeaturesToTrack(G[0], 600, 0.005, 6, mask=roi); base = p0.copy(); cur = p0.copy(); alive = np.ones(len(p0), bool)
C = np.float32([[x0, y0], [x0 + bw, y0], [x0 + bw, y0 + bh], [x0, y0 + bh]]); Cs = [C.copy()]
lk = dict(winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))
for k in range(1, len(fr)):
    nxt, s1, _ = cv2.calcOpticalFlowPyrLK(G[k - 1], G[k], cur, None, **lk)
    back, s2, _ = cv2.calcOpticalFlowPyrLK(G[k], G[k - 1], nxt, None, **lk)
    fb = np.linalg.norm((back - cur).reshape(-1, 2), axis=1)
    alive &= (s1.ravel() == 1) & (s2.ravel() == 1) & (fb < 1.0)
    cur = nxt
    Hk, inl = cv2.findHomography(base[alive], cur[alive], cv2.RANSAC, 2.0)
    Cs.append(cv2.perspectiveTransform(C[None], Hk)[0])
print('points alive at end:', int(alive.sum()), 'of', len(p0))
Cs = np.array(Cs); Sm = np.array([Cs[max(0, i - 2):i + 3].mean(0) for i in range(len(Cs))])
mask = cv2.erode(mask, np.ones((9, 9), np.uint8)); alpha = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 2.0)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'slow', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
ringm = cv2.dilate(mask, np.ones((61, 61), np.uint8)) - cv2.dilate(mask, np.ones((21, 21), np.uint8))
for k, f in enumerate(fr):
    Hk = cv2.getPerspectiveTransform(C, Sm[k].astype(np.float32))
    lay = cv2.warpPerspective(S, Hk, (w, h), flags=cv2.INTER_LANCZOS4).astype(np.float32); a = cv2.warpPerspective(alpha, Hk, (w, h))[..., None]
    o = f.astype(np.float32); ring = cv2.warpPerspective(ringm, Hk, (w, h)) > 0
    if ring.sum() > 100: lay *= np.clip(o[ring].mean(0) / np.maximum(lay[ring].mean(0), 1), 0.8, 1.25)
    o = o * (1 - a) + lay * a; enc.stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('frames', len(fr))
