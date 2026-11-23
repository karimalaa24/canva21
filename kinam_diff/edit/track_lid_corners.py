"""D6: track the 3 visible lid corners (BR, FR, FL; BL hides behind the burner) with forward-backward KLT, solve an affine
lid->frame per frame, smooth, and warp the real-lid-art still in. Only pixels that are lid-coloured in the CURRENT frame are
painted (burner / smoke stay in front). Free. usage: track_lid_corners.py clip still "lid BL BR FR FL" out.mp4 nframes"""
import cv2, numpy as np, sys
clip, still, lidq, out = sys.argv[1:5]; NF = int(sys.argv[5])
cap = cv2.VideoCapture(clip); fr = []
while len(fr) < NF:
    ok, im = cap.read()
    if not ok: break
    fr.append(im)
H, W = fr[0].shape[:2]; S0 = cv2.imread(still); s = W / S0.shape[1]
clean = cv2.resize(S0, (W, int(S0.shape[0] * s)), interpolation=cv2.INTER_AREA)[:H].astype(np.float32)
LQ = np.float32([[float(v) for v in p.split(',')] for p in lidq.split()]) * s
P = [LQ[1:4].copy()]; prev = cv2.cvtColor(fr[0], cv2.COLOR_BGR2GRAY)
for i in range(1, len(fr)):
    g = cv2.cvtColor(fr[i], cv2.COLOR_BGR2GRAY)
    p0 = P[-1].reshape(-1, 1, 2)
    p1, st, _ = cv2.calcOpticalFlowPyrLK(prev, g, p0, None, winSize=(41, 41), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 50, 0.01))
    P.append(p1.reshape(-1, 2)); prev = g
P = np.array(P); np.save(out + '.pts.npy', P)
import os
if os.environ.get('PTS'): P = np.load(os.environ['PTS'])[:len(fr)]
Ps = P.copy()
for j in range(len(P)): a, b = max(0, j - 2), min(len(P), j + 3); Ps[j] = P[a:b].mean(0) if not os.environ.get('PTS') else P[j]
m0 = np.zeros((H, W), np.float32); cv2.fillPoly(m0, [LQ.astype(np.int32)], 1)
import subprocess
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '24', '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'slow', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
ref = cv2.GaussianBlur(fr[0].astype(np.float32), (0, 0), 15)
for i, f in enumerate(fr):
    A2 = cv2.getAffineTransform(LQ[1:4], Ps[i].astype(np.float32))
    w = cv2.warpAffine(clean, A2, (W, H), flags=cv2.INTER_CUBIC); mm = cv2.warpAffine(m0, A2, (W, H))
    lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.float32)
    lidpx = np.clip((lab[..., 0] - 55) / 15, 0, 1) * (lab[..., 2] < 150) * (lab[..., 0] < 170)   # not burner (dark/gold), not smoke (white)
    lidpx = cv2.GaussianBlur(cv2.erode(cv2.morphologyEx(lidpx.astype(np.float32), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)), np.ones((3, 3), np.uint8)), (0, 0), 1.0)
    A = (cv2.GaussianBlur(mm, (0, 0), 0.8) * lidpx)[..., None]
    cur = cv2.GaussianBlur(f.astype(np.float32), (0, 0), 15); refw = cv2.warpAffine(ref, A2, (W, H))
    gain = np.clip((cur + 1) / (refw + 1), 0.8, 1.25)
    o = w * gain * A + f.astype(np.float32) * (1 - A); enc.stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('frames', len(fr)); print(P[::12].round(1).tolist())
