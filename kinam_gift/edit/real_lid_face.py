"""Replace the whole closed-lid TOP FACE of an AI box with the client's REAL lid (video frame 6.45 s): real leather, real stitching,
real gold artwork in one piece (no erase/inpaint -> no smudge). Homography stitched-border -> stitched-border, masked to the target
lid face, colour matched (Lab mean/std) to the AI lid it replaces, softened to the target's sharpness. Free, local.
usage: real_lid_face.py in.png out.png "tgt stitched BL BR FR FL" "tgt lid face BL BR FR FL" """
import cv2, numpy as np, sys
V = cv2.imread('/home/user/canva21/kinam_gift/references/src_closed_6.45.png')
SRC = np.float32([(164, 387), (481, 454), (420, 662), (84, 576)])
im = cv2.imread(sys.argv[1]); H, W = im.shape[:2]
DST = np.float32([[float(v) for v in p.split(',')] for p in sys.argv[3].split()])
LID = np.float32([[float(v) for v in p.split(',')] for p in sys.argv[4].split()])
Vu = cv2.resize(V, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)                 # warp from a 3x upsample (smoother edges)
T = cv2.getPerspectiveTransform(SRC * 3, DST)
w = cv2.warpPerspective(Vu, T, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [(LID.mean(0) + (LID - LID.mean(0)) * 0.985).astype(np.int32)], 1)
# colour: match leather (non-gold) statistics of the AI lid
def lab(x): return cv2.cvtColor(np.clip(x, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
lt, lw = lab(im), lab(w); ft = im.astype(np.float32)
leath_t = (m > 0) & ((ft[..., 2] - ft[..., 0]) < 20); leath_w = (m > 0) & ((w[..., 2] - w[..., 0]) < 20)
for c in range(3):
    mt, st = lt[..., c][leath_t].mean(), lt[..., c][leath_t].std(); mw, sw = lw[..., c][leath_w].mean(), lw[..., c][leath_w].std()
    k = np.clip(st / (sw + 1e-3), 0.7, 1.3) if c == 0 else 1.0
    lw[..., c] = (lw[..., c] - mw) * k + mt
# keep the AI lid's own light falloff (low frequency of its L channel)
lowt = cv2.GaussianBlur(lt[..., 0], (0, 0), 40); loww = cv2.GaussianBlur(lw[..., 0], (0, 0), 40)
lw[..., 0] += (lowt - loww) * 0.8
out_w = cv2.cvtColor(np.clip(lw, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
# gold artwork + stitching: keep it warm gold (the leather colour match pulls it green) -> recolour with the scene's own gold
gw = np.clip(((w[..., 2] - w[..., 0]) - 35) / 50, 0, 1) * (m > 0)
gt_px = ft[(m > 0) & ((ft[..., 2] - ft[..., 0]) > 80)]
gold = np.percentile(gt_px, 70, axis=0) if len(gt_px) > 50 else np.array([90, 165, 220.])
Lg = lw[..., 0] / max(1, lw[..., 0][gw > 0.5].mean()) if (gw > 0.5).any() else 1
gcol = gold[None, None] * np.clip(Lg, 0.6, 1.3)[..., None]
out_w = out_w * (1 - gw[..., None]) + gcol * gw[..., None]
out_w = cv2.GaussianBlur(out_w, (0, 0), 0.6)
A = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2)[..., None]
cv2.imwrite(sys.argv[2], np.clip(out_w * A + ft * (1 - A), 0, 255).astype(np.uint8))
