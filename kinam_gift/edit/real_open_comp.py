"""Gift reel G5: REAL two open boxes in hands (client frame 28.2 s, 2x, Kinam fill) on the blurred Najdi majlis. Free, local.
usage: real_open_comp.py filled2x.png bg.png out.png"""
import cv2, numpy as np, sys
src, bgp, out = sys.argv[1:4]
im = cv2.imread(src); h, w = im.shape[:2]; k = w / 576.0
P = lambda pts: np.array([(x * k, y * k) for x, y in pts], np.int32)
box = np.zeros((h, w), np.uint8)
cv2.fillPoly(box, [P([(47, 410), (276, 415), (279, 700), (263, 776), (30, 768), (22, 600)]), P([(320, 406), (539, 414), (532, 690), (506, 760), (287, 721), (290, 560)])], 1)
hand = np.zeros((h, w), np.uint8)
cv2.fillPoly(hand, [P([(0, 462), (64, 462), (70, 658), (0, 668)]), P([(518, 538), (576, 512), (576, 708), (518, 708)])], 1)
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int); f = im.astype(int)
skin = (f[..., 2] > f[..., 1] + 15) & (f[..., 2] > 95) & (hsv[..., 1] > 40)
white = (hsv[..., 1] < 35) & (hsv[..., 2] > 150)                                   # thobe / wall
lining = np.zeros((h, w), np.uint8)
cv2.fillPoly(lining, [P([(66, 428), (262, 432), (264, 712), (62, 712)]), P([(336, 424), (530, 430), (522, 690), (306, 690)])], 1)
m = ((box > 0) & ~(white & (lining == 0))) | ((hand > 0) & skin)
m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
from scipy.ndimage import binary_fill_holes
m = binary_fill_holes(m).astype(np.uint8); m = cv2.erode(m, np.ones((3, 3), np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
W, H = 1080, 1920; s = W / w
fg = cv2.resize(im, (W, int(h * s)), interpolation=cv2.INTER_AREA).astype(np.float32)
a = cv2.GaussianBlur(cv2.resize(m.astype(np.float32), (W, int(h * s))), (0, 0), 1.6)[..., None]
fg = fg * np.array([0.86, 0.95, 1.08]) * 0.97
bg = cv2.imread(bgp); bh, bw = bg.shape[:2]; crop = bg[int(bh * 0.10):int(bh * 0.10) + int(bw * H / W), :]
o = cv2.GaussianBlur(cv2.resize(crop, (W, H)), (0, 0), 22).astype(np.float32); y0 = (H - fg.shape[0]) // 2
sh = cv2.GaussianBlur(a[..., 0], (0, 0), 25)[..., None]; o[y0:y0 + fg.shape[0]] *= (1 - 0.35 * np.roll(sh, 30, 0))
o[y0:y0 + fg.shape[0]] = fg * a + o[y0:y0 + fg.shape[0]] * (1 - a)
cv2.imwrite(out, np.clip(o, 0, 255).astype(np.uint8))
