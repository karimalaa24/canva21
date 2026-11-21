"""Gift reel: REAL hands + box (client video frame) cut out and laid over the blurred Najdi majlis, warm-graded. Free, local.
usage: real_hands_comp.py src_frame.png bg.png out.png"""
import cv2, numpy as np, sys
from scipy.ndimage import binary_fill_holes
src, bgp, out = sys.argv[1:4]
im = cv2.imread(src); h, w = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int); f = im.astype(int)
green = (hsv[..., 0] > 40) & (hsv[..., 0] < 95) & (hsv[..., 1] > 50) & (hsv[..., 2] < 170)
skin = (f[..., 2] > f[..., 1] + 15) & (f[..., 2] > 95) & (hsv[..., 1] > 45) & (hsv[..., 1] < 200)
gold = (hsv[..., 0] > 12) & (hsv[..., 0] < 35) & (hsv[..., 1] > 90) & (hsv[..., 2] > 120)
poly = np.zeros((h, w), np.uint8)
cv2.fillPoly(poly, [np.array([(0, 338), (205, 338), (300, 378), (522, 392), (542, 428), (541, 560), (505, 615), (470, 690), (440, 776), (330, 792), (130, 785), (0, 798)], np.int32)], 1)
m = ((green | skin | gold) & (poly > 0)).astype(np.uint8)
gc = np.where(m > 0, cv2.GC_PR_FGD, cv2.GC_PR_BGD).astype(np.uint8); gc[poly == 0] = cv2.GC_BGD
gc[cv2.erode(m, np.ones((9, 9), np.uint8)) > 0] = cv2.GC_FGD
cv2.grabCut(im, gc, None, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_MASK)
mm = ((gc == 1) | (gc == 3)).astype(np.uint8)
n, l, st, _ = cv2.connectedComponentsWithStats(mm); mm = np.isin(l, [i for i in range(1, n) if st[i, 4] > 3000]).astype(np.uint8)
mm = binary_fill_holes(mm).astype(np.uint8)
mm = cv2.morphologyEx(mm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
W, H = 1080, 1920; s = W / w
fg = cv2.resize(im, (W, int(h * s)), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
fg = fg + 0.6 * (fg - cv2.GaussianBlur(fg, (0, 0), 1.6))                          # recover detail after the upscale
a = cv2.GaussianBlur(cv2.resize(mm.astype(np.float32), (W, int(h * s)), interpolation=cv2.INTER_LINEAR), (0, 0), 1.8)[..., None]
fg = fg * np.array([0.86, 0.95, 1.08]) * 0.97                                       # daylight -> warm lamp light
bg = cv2.imread(bgp); bh, bw = bg.shape[:2]
crop = bg[int(bh * 0.10):int(bh * 0.10) + int(bw * H / W), :]                     # walls, niches, cushions
bgb = cv2.GaussianBlur(cv2.resize(crop, (W, H)), (0, 0), 22).astype(np.float32)
o = bgb.copy(); y0 = (H - fg.shape[0]) // 2
sh = cv2.GaussianBlur(a[..., 0], (0, 0), 25)[..., None]                             # soft shadow of hands/box on the blurred room
o[y0:y0 + fg.shape[0]] *= (1 - 0.35 * np.roll(sh, 30, 0))
o[y0:y0 + fg.shape[0]] = fg * a + o[y0:y0 + fg.shape[0]] * (1 - a)
cv2.imwrite(out, np.clip(o, 0, 255).astype(np.uint8))
