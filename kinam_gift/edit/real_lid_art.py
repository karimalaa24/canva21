"""Put the REAL lid artwork (gold B, BeetHoven, فخامة سمو للطيب, stitched border) from the client's video frame onto an AI
closed box: erase the AI gold print, warp the real gold mask by the stitched-border homography, colour it with the scene's gold.
Free, local. usage: real_lid_art.py in.png out.png "tgt border BL BR FR FL"   (BL = back-left ... as seen in the target)"""
import cv2, numpy as np, sys, os
V = cv2.imread('/home/user/canva21/kinam_gift/references/src_closed_6.45.png')
SRC = np.float32([(164, 387), (481, 454), (420, 662), (84, 576)])          # video stitched border: back-left, back-right, front-right, front-left
im = cv2.imread(sys.argv[1]); H, W = im.shape[:2]
DST = np.float32([[float(v) for v in p.split(',')] for p in sys.argv[3].split()])
# real gold mask (artwork + stitching) inside a slightly grown border quad
hv = cv2.cvtColor(V, cv2.COLOR_BGR2HSV).astype(np.float32); fv = V.astype(np.float32)
c = SRC.mean(0); grow = c + (SRC - c) * 1.06
qm = np.zeros(V.shape[:2], np.uint8); cv2.fillPoly(qm, [grow.astype(np.int32)], 1)
gold = np.clip((fv[..., 2] - fv[..., 0] - 40) / 70, 0, 1) * np.clip((hv[..., 2] - 110) / 60, 0, 1)
stitch = np.clip((hv[..., 2] - 150) / 50, 0, 1) * (hv[..., 1] < 120)
a = (gold if os.environ.get('ART_ONLY') else np.maximum(gold, stitch * 0.9)) * qm
T = cv2.getPerspectiveTransform(SRC, DST)
A = cv2.warpPerspective(a.astype(np.float32), T, (W, H), flags=cv2.INTER_CUBIC); A = np.clip(A * 1.7, 0, 1)
# erase the AI print inside the target border (gold + pale stitches), leather texture kept by inpainting at low res + grain
tq = np.zeros((H, W), np.uint8); cv2.fillPoly(tq, [(DST.mean(0) + (DST - DST.mean(0)) * 1.08).astype(np.int32)], 1)
ht = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32); ft = im.astype(np.float32)
old = (((ft[..., 2] - ft[..., 0]) > 22) | ((ht[..., 2] > 140) & (ht[..., 1] < 120))) & (tq > 0)
om = cv2.dilate(old.astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
gcol = np.percentile(ft[old & ((ft[..., 2] - ft[..., 0]) > 80)], 80, axis=0) if (old & ((ft[..., 2] - ft[..., 0]) > 80)).sum() > 50 else np.array([60, 160, 220.])
inner = np.zeros((H, W), np.uint8); cv2.fillPoly(inner, [(DST.mean(0) + (DST - DST.mean(0)) * 0.93).astype(np.int32)], 1)
if os.environ.get('ART_ONLY'):   # keep the AI stitching + leather: only the gold artwork area (inside the stitching) is replaced
    old2 = ((ft[..., 2] - ft[..., 0]) > 22) & (inner > 0)
    om = cv2.dilate(old2.astype(np.uint8) * 255, np.ones((9, 9), np.uint8))
else: om = np.maximum(om, inner * 255)                                # wipe the whole field inside the stitching (AI emboss ghosts)
import os
if os.environ.get('LID'):                                             # never touch pixels outside the lid face (background, edges)
    LQ = np.float32([[float(v) for v in p.split(',')] for p in os.environ['LID'].split()]); lf = np.zeros((H, W), np.uint8)
    cv2.fillPoly(lf, [(LQ.mean(0) + (LQ - LQ.mean(0)) * 0.97).astype(np.int32)], 1); om = om * lf; A_lim = lf
else: A_lim = np.ones((H, W), np.uint8)
sm = cv2.inpaint(cv2.resize(im, None, fx=0.25, fy=0.25), cv2.resize(om, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_NEAREST), 5, cv2.INPAINT_TELEA)
sm = cv2.GaussianBlur(cv2.resize(sm, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32), (0, 0), 3)
clean = np.where(om[..., None] > 0, sm, ft)
hp = ft - cv2.GaussianBlur(ft, (0, 0), 1.5); okg = (tq > 0) & (om == 0)
if os.environ.get('ART_ONLY'):
    src_rows = np.roll(hp, 140, 0); clean = clean + src_rows * (om[..., None] > 0)   # leather grain from the lid below the artwork
lv = ft[(tq > 0) & (om == 0)]; sd = (ft - cv2.GaussianBlur(ft, (0, 0), 2))[(tq > 0) & (om == 0)].std(0)
noise = cv2.GaussianBlur(np.random.default_rng(5).normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.8)[..., None] * sd.mean() * 0.9
clean = clean + noise * (om[..., None] > 0) * (0 if os.environ.get('ART_ONLY') else 1)
# shading: gold catches light toward the back (top), slightly darker toward the front
ys = np.arange(H)[:, None, None]; y0, y1 = DST[:, 1].min(), DST[:, 1].max()
shade = 1.08 - 0.18 * np.clip((ys - y0) / max(1, y1 - y0), 0, 1)
A3 = (cv2.GaussianBlur(A, (0, 0), 0.6) * A_lim)[..., None]
out = clean * (1 - A3) + np.clip(gcol * shade, 0, 255) * A3
cv2.imwrite(sys.argv[2], np.clip(out, 0, 255).astype(np.uint8)); print('gold', gcol.round())
