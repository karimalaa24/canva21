"""Kinam S01 v2 (real open box behind hand): real pieces pasted back (done -> s01b_pieces.png), lid word -> BeetHoven on cream. Free, local."""
import cv2, numpy as np, sys
K = '/home/user/canva21/kinam/'; S = '/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/'
def word_from(path, x0, y0, x1, y1):
    im = cv2.imread(path); R = im[y0:y1, x0:x1].astype(np.float32)
    bg = cv2.medianBlur(im[y0 - 40:y1 + 40, x0 - 40:x1 + 40], 41)[40:-40, 40:-40].astype(np.float32)
    d = (bg - R).mean(2); a = np.clip((d - 6) / (np.percentile(d, 99.5) - 6), 0, 1)
    ys, xs = np.where(a > 0.15); return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
BH = word_from('/home/user/canva21/reel03/images/p02_close_raw.png', 478, 1403, 662, 1468)
im = cv2.imread(K + 'images/s01b_pieces.png')
x0, y0, x1, y1 = [int(v) for v in sys.argv[1:5]]; blur = float(sys.argv[5]); dark = float(sys.argv[6])
R = im[y1 + 8:y1 + 70, x0 - 40:x1 + 60].astype(np.float32); L = R.mean(2); gold = np.median(R[L < np.percentile(L, 4)], 0) * dark   # gold of the Arabic line below
m = np.zeros(im.shape[:2], np.uint8); m[y0:y1, x0:x1] = 255
out = cv2.inpaint(im, m, 15, cv2.INPAINT_TELEA).astype(np.float32)
sm = cv2.GaussianBlur(out[y0 - 6:y1 + 6, x0 - 6:x1 + 6], (0, 0), 6); out[y0:y1, x0:x1] = sm[6:-6, 6:-6]
out += np.random.default_rng(1).normal(0, 1.0, out.shape).astype(np.float32) * (m[..., None] > 0)
W = int((x1 - x0) * 0.98); a = cv2.resize(BH, (W, int(W * BH.shape[0] / BH.shape[1])), interpolation=cv2.INTER_AREA)
h, w = a.shape; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
A = np.zeros(im.shape[:2], np.float32); ys, xs = int(cy - h / 2), int(cx - w / 2); A[ys:ys + h, xs:xs + w] = a
A = cv2.dilate(A, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))); A = np.clip(cv2.GaussianBlur(A, (0, 0), blur) * 1.2, 0, 1)
f = out * (1 - A[..., None]) + gold * A[..., None]; f = np.clip(f, 0, 255).astype(np.uint8)
cv2.imwrite(K + 'images/s01_hand_final.png', f)
cv2.imwrite(S + 'lid_fix.jpg', np.vstack([im[y0 - 160:y1 + 160, x0 - 250:x1 + 250], f[y0 - 160:y1 + 160, x0 - 250:x1 + 250]]))
print('gold', gold, w, h)
