"""Source reel S2 (inspection): replace the AI-drawn chip held between thumb and index with a REAL Kinam cut-out
(kinam/pieces), its lower end tucked behind the thumb (original thumb pixels restored on top), lit like the scene
(warm lamp from the upper right), then crop away the foreign burner on the left. Free.
usage: held_piece.py in.png out.png piece_id length angle cx cy"""
import cv2, numpy as np, json, sys
K = '/home/user/canva21/kinam/'; T = json.load(open(K + 'pieces/target_kinam.json'))
im = cv2.imread(sys.argv[1]); H, W = im.shape[:2]; f = im.astype(np.float32)
pid, L, ang, cx, cy = sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])
lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
skin = ((lab[..., 1] > 136) & (lab[..., 0] > 95) & (hsv[..., 1] > 40) & (hsv[..., 1] < 170)).astype(np.uint8)
skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)); skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
# AI chip = everything in its box that is not skin
ai = np.zeros((H, W), np.uint8); cv2.fillPoly(ai, [np.array([[565, 1085], [735, 1075], [895, 1380], [875, 1485], [640, 1485], [565, 1250]], np.int32)], 1)
er = (ai * (1 - skin)).astype(np.uint8); er = cv2.dilate(er, np.ones((9, 9), np.uint8)) * (1 - skin)
ref = f[(lab[..., 0] < 200)]  # fallback
sm = cv2.inpaint(cv2.resize(im, None, fx=0.25, fy=0.25), cv2.resize(er * 255, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_NEAREST), 6, cv2.INPAINT_TELEA)
sm = cv2.GaussianBlur(cv2.resize(sm, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32), (0, 0), 6)
out = np.where(er[..., None] > 0, sm, f)
Ltarget = lab[..., 0][(ai > 0) & (skin == 0) & (lab[..., 0] > 40)].mean()
p = cv2.imread(K + 'pieces/pieces_white_bg_%s.png' % pid, -1)
h, w = p.shape[:2]; s = L / max(h, w); p = cv2.resize(p, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA); h, w = p.shape[:2]
D = int(np.hypot(h, w)) + 40; c = np.zeros((D, D, 4), np.uint8); c[(D - h) // 2:(D - h) // 2 + h, (D - w) // 2:(D - w) // 2 + w] = p
c = cv2.warpAffine(c, cv2.getRotationMatrix2D((D / 2, D / 2), ang, 1), (D, D), flags=cv2.INTER_CUBIC)
a = cv2.GaussianBlur(cv2.erode(c[..., 3].astype(np.float32) / 255, np.ones((3, 3), np.uint8)), (0, 0), 0.7)
pl = cv2.cvtColor(c[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32); sel = a > 0.9
bright = pl[..., 0] > np.percentile(pl[..., 0][sel], 97); a[bright & (a < 0.98)] *= 0.3
Lp = (pl[..., 0] - pl[..., 0][sel].mean()) / (pl[..., 0][sel].std() + 1e-3) * 24 + Ltarget * 0.86
yy, xx = np.mgrid[0:D, 0:D]; Lp = Lp * (0.92 + 0.18 * (0.6 * (1 - yy / D) + 0.4 * xx / D))      # lamp upper right
pl[..., 0] = np.clip(Lp, 0, 255); Lm = pl[..., 0][sel].mean()
for ch, key, warm in ((1, 'a_of_L', 3.0), (2, 'b_of_L', 10.0)):
    own = pl[..., ch]; pl[..., ch] = (own - own[sel].mean()) * 1.0 + T[key][0] * Lm + T[key][1] + warm * 0.4
rgb = cv2.cvtColor(np.clip(pl, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
rgb = rgb + 0.35 * (rgb - cv2.GaussianBlur(rgb, (0, 0), 1.2))
X, Y = int(cx - D / 2), int(cy - D / 2); reg = out[Y:Y + D, X:X + D]
reg[:] = rgb * a[..., None] + reg * (1 - a[..., None])
# fingers back on top (thumb / index that hold the piece) + soft contact shadow under the thumb
sk = cv2.GaussianBlur(skin.astype(np.float32), (0, 0), 1.0)[..., None]; hold = np.zeros((H, W), np.float32); hold[1430:1700, 600:1000] = 1
A = sk * hold[..., None]; out = out * (1 - A) + f * A
cv2.imwrite(sys.argv[2], np.clip(out, 0, 255).astype(np.uint8))
