"""S07: replace the AI pieces on the scale pan with real cut-outs (kinam/pieces). Free, local.
1) empty pan: polar fill (the dish shading is concentric: masked px take the value at the same elliptical radius from the nearest clean angles)
2) real pieces: Lab colour from target_kinam.json (a,b as a function of L), L matched to the scene's wood, top-left light, thickness rim, contact + soft shadow."""
import cv2, numpy as np, json
K = '/home/user/canva21/kinam/'; S = '/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/'
im = cv2.imread(K + 'images/s07_scale_final.png'); f = im.astype(np.float32); H, W = im.shape[:2]
CX, CY, RX, RY = 1050, 1945, 300, 125            # pan inner ellipse (bowl floor + inner wall)
ell = np.zeros((H, W), np.uint8); cv2.ellipse(ell, (CX, CY), (RX, RY), 0, 0, 360, 1, -1)
L = f.mean(2); m = ((L < 118) & (ell > 0)).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, l, st, _ = cv2.connectedComponentsWithStats(m); m = np.isin(l, [i for i in range(1, n) if st[i, 4] > 2000]).astype(np.uint8)
m = cv2.dilate(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)), np.ones((17, 17), np.uint8)) & ell
wood = f[(m > 0) & (L < 118)]; Lw = cv2.cvtColor(np.clip(wood, 0, 255).astype(np.uint8)[None], cv2.COLOR_BGR2LAB)[0, :, 0].astype(np.float32)
Lmu, Lsd = Lw.mean(), Lw.std()
# --- AI piece footprint (hand-drawn polygon); the real pieces are laid over it, leftovers inpainted after
OX, OY = 700, 1750
poly = np.array([(120,240),(160,205),(165,170),(230,145),(290,80),(340,82),(400,112),(500,110),(525,130),(510,160),(490,175),(575,265),(560,300),(510,310),(470,295),(380,280),(330,300),(240,300),(140,265)], np.int32) + [OX, OY]
aim = np.zeros((H, W), np.uint8); cv2.fillPoly(aim, [poly], 1)
aiw = aim & ((L < 120) | (cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[..., 1] < 125)).astype(np.uint8)
aiw = cv2.dilate(cv2.morphologyEx(aiw, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), np.ones((7, 7), np.uint8))
out = f.copy(); cover = np.zeros((H, W), np.float32)
# --- real pieces
T = json.load(open(K + 'pieces/target_kinam.json'))
def piece(name, length, ang, cx, cy, flip=False, squash=0.8, sh_k=0.6):
    global out, cover
    p = cv2.imread(K + 'pieces/pieces_white_bg_%s.png' % name, -1)
    if flip: p = p[:, ::-1]
    h, w = p.shape[:2]; s = length / max(h, w); p = cv2.resize(p, (int(w * s), int(h * s)), interpolation=cv2.INTER_CUBIC)
    h, w = p.shape[:2]; D = int(np.hypot(h, w)) + 30; c = np.zeros((D, D, 4), np.uint8); c[(D - h) // 2:(D - h) // 2 + h, (D - w) // 2:(D - w) // 2 + w] = p
    c = cv2.warpAffine(c, cv2.getRotationMatrix2D((D / 2, D / 2), ang, 1), (D, D), flags=cv2.INTER_CUBIC)
    c = cv2.resize(c, (D, int(D * squash)), interpolation=cv2.INTER_AREA); h, w = c.shape[:2]
    a = cv2.GaussianBlur(cv2.erode(c[..., 3].astype(np.float32) / 255, np.ones((3, 3), np.uint8)), (0, 0), 0.7)
    lab = cv2.cvtColor(c[..., :3], cv2.COLOR_BGR2LAB).astype(np.float32); sel = a > 0.9
    Lp = lab[..., 0]; Lp = (Lp - Lp[sel].mean()) / (Lp[sel].std() + 1e-3) * Lsd * 0.9 + Lmu
    yy, xx = np.mgrid[0:h, 0:w]; Lp = Lp * (1.08 - 0.16 * (0.5 * yy / h + 0.5 * xx / w))   # light from top-left
    # thickness: darker rim along the lower edge
    rim = np.clip(a - np.roll(a, -6, 0), 0, 1); Lp = Lp * (1 - 0.45 * cv2.GaussianBlur(rim, (0, 0), 1.5))
    lab[..., 0] = np.clip(Lp, 0, 255); Lm = lab[..., 0][sel].mean()
    for ch, key, warm in ((1, 'a_of_L', 2.0), (2, 'b_of_L', 6.0)):   # keep the piece's own resin streak variation, shift its mean to the Kinam target (+ warm room light)
        own = lab[..., ch]; lab[..., ch] = (own - own[sel].mean()) * 1.3 + T[key][0] * Lm + T[key][1] + warm
    rgb = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    rgb = rgb + 0.2 * (rgb - cv2.GaussianBlur(rgb, (0, 0), 1.2))      # restore grain after upscale
    X0, Y0 = int(cx - w / 2), int(cy - h / 2); reg = out[Y0:Y0 + h, X0:X0 + w]
    soft = cv2.warpAffine(cv2.GaussianBlur(a, (0, 0), 12), np.float32([[1, 0, 8], [0, 1, 14]]), (w, h))
    cont = cv2.warpAffine(cv2.GaussianBlur(a, (0, 0), 3), np.float32([[1, 0, 2], [0, 1, 5]]), (w, h))
    reg *= (1 - sh_k * 0.55 * soft[..., None]) * (1 - 0.5 * cont[..., None] * (1 - a[..., None]))
    reg[:] = rgb * a[..., None] + reg * (1 - a[..., None]); cv = cover[Y0:Y0 + h, X0:X0 + w]; cv[:] = np.maximum(cv, a)
import sys
CFG = json.loads(sys.argv[1])
small = cv2.inpaint(cv2.resize(im, None, fx=.5, fy=.5), cv2.resize(aiw * 255, None, fx=.5, fy=.5, interpolation=cv2.INTER_NEAREST), 10, cv2.INPAINT_TELEA)
fill = cv2.GaussianBlur(cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32), (0, 0), 3)
A = cv2.GaussianBlur(aiw.astype(np.float32), (0, 0), 2)[..., None]; out = fill * A + f * (1 - A)
cv2.imwrite(S + 's07_pan_empty.png', np.clip(out, 0, 255).astype(np.uint8))
for pc in CFG: piece(*pc[:5], flip=pc[5] if len(pc) > 5 else False, squash=0.85)
left = (aiw > 0) & (cover < 0.5); print('AI px still visible', int(left.sum()))
r = np.clip(out, 0, 255).astype(np.uint8); cv2.imwrite(K + 'images/s07_scale_real.png', r)
v = r.copy(); v[left] = (v[left] * 0.4 + np.array([255, 0, 255]) * 0.6).astype(np.uint8)
cv2.imwrite(S + 'pan2.jpg', np.hstack([im[1700:2300, 600:1500], v[1700:2300, 600:1500], r[1700:2300, 600:1500]]))
