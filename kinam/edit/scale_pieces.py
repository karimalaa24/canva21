"""S07: replace the AI pieces on the scale pan with real cut-outs (kinam/pieces), flat on the pan (foreshortened), colour-matched, soft shadows. Free."""
import cv2, numpy as np
K = '/home/user/canva21/kinam/'; S = '/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/'
im = cv2.imread(K + 'images/s07_scale_final.png'); f = im.astype(np.float32); H, W = im.shape[:2]
x0, y0, x1, y1 = 800, 1810, 1300, 2080
L = f.mean(2); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
m = np.zeros((H, W), np.uint8); ell = np.zeros((H, W), np.uint8); cv2.ellipse(ell, (1050, 1945), (300, 125), 0, 0, 360, 1, -1)
sub = ((L < 118) & (ell > 0))[y0:y1, x0:x1]
m[y0:y1, x0:x1] = sub; m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, l, st, _ = cv2.connectedComponentsWithStats(m); keep = [i for i in range(1, n) if st[i, 4] > 2000]; m = np.isin(l, keep).astype(np.uint8)
m = cv2.dilate(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8)), np.ones((11, 11), np.uint8)) & ell
wood_ref = f[(m > 0) & (L < 125)]; mu, sd = wood_ref.mean(0), wood_ref.std(0)
small = cv2.inpaint(cv2.resize(im, None, fx=.5, fy=.5), cv2.resize(m * 255, None, fx=.5, fy=.5, interpolation=cv2.INTER_NEAREST), 12, cv2.INPAINT_TELEA)
fill = cv2.GaussianBlur(cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32), (0, 0), 5)
A = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)[..., None]; out = fill * A + f * (1 - A)
cv2.imwrite(S + 's07_pan_empty.png', np.clip(out, 0, 255).astype(np.uint8))
def piece(name, length, ang, cx, cy, flip=False, squash=0.62):
    global out
    p = cv2.imread(K + 'pieces/pieces_white_bg_%s.png' % name, -1).astype(np.float32)
    if flip: p = p[:, ::-1]
    h, w = p.shape[:2]; s = length / max(h, w); p = cv2.resize(p, (int(w * s), int(h * s)), interpolation=cv2.INTER_CUBIC)
    h, w = p.shape[:2]; D = int(np.hypot(h, w)) + 4; c = np.zeros((D, D, 4), np.float32); c[(D - h) // 2:(D - h) // 2 + h, (D - w) // 2:(D - w) // 2 + w] = p
    c = cv2.warpAffine(c, cv2.getRotationMatrix2D((D / 2, D / 2), ang, 1), (D, D), flags=cv2.INTER_CUBIC)
    c = cv2.resize(c, (D, int(D * squash)), interpolation=cv2.INTER_AREA); h, w = c.shape[:2]
    rgb, a = c[..., :3], np.clip(c[..., 3] / 255, 0, 1); a = cv2.GaussianBlur(cv2.erode(a, np.ones((3, 3), np.uint8)), (0, 0), 0.8)
    sel = a > 0.9; pm, ps = rgb[sel].mean(0), rgb[sel].std(0); rgb = (rgb - pm) / ps * sd * 0.8 + mu   # match the scene's wood
    X, Y = int(cx - w / 2), int(cy - h / 2)
    sh = cv2.GaussianBlur(a, (0, 0), 7); M = np.float32([[1, 0, 5], [0, 1, 9]]); sh = cv2.warpAffine(sh, M, (w, h))
    reg = out[Y:Y + h, X:X + w]; reg *= (1 - 0.55 * sh[..., None])
    reg[:] = rgb * a[..., None] + reg * (1 - a[..., None])
piece('05', 400, 25, 1110, 1915, squash=0.75)
piece('07', 270, -8, 960, 1960, squash=0.75)
piece('04', 220, -15, 1150, 1990, flip=True, squash=0.75)
r = np.clip(out, 0, 255).astype(np.uint8); cv2.imwrite(K + 'images/s07_scale_final2.png', r)
cv2.imwrite(S + 'pan2.jpg', np.hstack([im[1700:2300, 600:1500], r[1700:2300, 600:1500]]))
