"""S07 v2: empty scale pan (Magnific edit, display 4.20 g) + 3 real cut-outs laid flat, loosely, realistic size (~3.5 cm on a ~12 cm pan). Free, local.
usage: s07b_pieces.py '[[name,len,ang,cx,cy,flip],...]' [squash]"""
import cv2, numpy as np, json, sys
K = '/home/user/canva21/kinam/'; S = '/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/'
T = json.load(open(K + 'pieces/target_kinam.json'))
# wood tone of the scene = the AI pieces that sat on this pan before (same light)
ai = cv2.imread(K + 'images/s07_scale_ai_pan.png'); Lai = cv2.cvtColor(ai, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32)
ell = np.zeros(Lai.shape, np.uint8); cv2.ellipse(ell, (1050, 1945), (300, 125), 0, 0, 360, 1, -1)
w = Lai[(ell > 0) & (ai.astype(np.float32).mean(2) < 110)]; Lmu, Lsd = w.mean(), w.std()
out = cv2.imread(K + 'images/s07b_boxed.png').astype(np.float32)
SQ = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
def piece(name, length, ang, cx, cy, flip=False):
    global out
    p = cv2.imread(K + 'pieces/pieces_white_bg_%s.png' % name, -1)
    if flip: p = p[:, ::-1]
    h, w = p.shape[:2]; s = length / max(h, w); p = cv2.resize(p, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    h, w = p.shape[:2]; D = int(np.hypot(h, w)) + 40; c = np.zeros((D, D, 4), np.uint8); c[(D - h) // 2:(D - h) // 2 + h, (D - w) // 2:(D - w) // 2 + w] = p
    c = cv2.warpAffine(c, cv2.getRotationMatrix2D((D / 2, D / 2), ang, 1), (D, D), flags=cv2.INTER_CUBIC)
    c = cv2.resize(c, (D, int(D * SQ)), interpolation=cv2.INTER_AREA); h, w = c.shape[:2]
    a = cv2.GaussianBlur(cv2.erode(c[..., 3].astype(np.float32) / 255, np.ones((4, 4), np.uint8)), (0, 0), 0.6)
    lab = cv2.cvtColor(c[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32); sel = a > 0.9
    Lp = (lab[..., 0] - lab[..., 0][sel].mean()) / (lab[..., 0][sel].std() + 1e-3) * Lsd * 0.9 + Lmu
    yy, xx = np.mgrid[0:h, 0:w]; Lp = Lp * (1.10 - 0.2 * (0.6 * yy / h + 0.4 * xx / w))        # warm light from the upper left
    edge = np.clip(a - np.roll(a, -5, 0), 0, 1); Lp = Lp * (1 - 0.5 * cv2.GaussianBlur(edge, (0, 0), 1.2))   # thickness: dark lower edge
    top = np.clip(a - np.roll(a, 4, 0), 0, 1); Lp = Lp + 7 * cv2.GaussianBlur(top, (0, 0), 1.0)              # thin highlight on the upper edge
    lab[..., 0] = np.clip(Lp, 0, 255); Lm = lab[..., 0][sel].mean()
    for ch, key, warm in ((1, 'a_of_L', 2.0), (2, 'b_of_L', 6.0)):
        own = lab[..., ch]; lab[..., ch] = (own - own[sel].mean()) * 1.3 + T[key][0] * Lm + T[key][1] + warm
    rgb = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    X0, Y0 = int(cx - w / 2), int(cy - h / 2); reg = out[Y0:Y0 + h, X0:X0 + w]
    soft = cv2.warpAffine(cv2.GaussianBlur(a, (0, 0), 9), np.float32([[1, 0, 7], [0, 1, 9]]), (w, h))
    cont = cv2.warpAffine(cv2.GaussianBlur(a, (0, 0), 2.5), np.float32([[1, 0, 2], [0, 1, 4]]), (w, h))
    reg *= (1 - 0.45 * soft[..., None]) * (1 - 0.55 * cont[..., None] * (1 - a[..., None]))
    # warm gold bounce from the polished pan on the lower part of the piece
    bounce = np.clip((yy / h - 0.4) / 0.6, 0, 1)[..., None] * np.array([0.0, 6.0, 14.0])
    reg[:] = (rgb + bounce) * a[..., None] + reg * (1 - a[..., None])
for pc in json.loads(sys.argv[1]): piece(*pc)
r = np.clip(out, 0, 255).astype(np.uint8); cv2.imwrite(K + 'images/s07_scale_final.png', r)
cv2.imwrite(S + 'pan4.jpg', r[1760:2160, 700:1400])
