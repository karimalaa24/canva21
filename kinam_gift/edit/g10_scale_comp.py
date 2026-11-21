"""G10: put the gold scale (cut from the AI still where the box was too big) in front of the ACCEPTED small open box, then 3 real
Kinam pieces on its pan. Free, local."""
import cv2, numpy as np, json
K = '/home/user/canva21/kinam_gift/'; S = '/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/'
base = cv2.imread(K + 'images/g02_hero_final.png').astype(np.float32); H, W = base.shape[:2]
sc = cv2.imread(S + 'scale_rgba.png', -1).astype(np.float32); f = 0.9
sc = cv2.resize(sc, None, fx=f, fy=f, interpolation=cv2.INTER_AREA); h, w = sc.shape[:2]; X, Y = 925, 2005
a = sc[..., 3:] / 255
# contact + soft shadow on the table (light from the back-left)
sh = np.zeros((H, W), np.float32); sh[Y:Y + h, X:X + w] = a[..., 0]
sh = cv2.GaussianBlur(np.roll(np.roll(sh, 14, 0), 10, 1), (0, 0), 16)
base *= 1 - 0.45 * sh[..., None]
reg = base[Y:Y + h, X:X + w]; base[Y:Y + h, X:X + w] = sc[..., :3] * a + reg * (1 - a)
cv2.imwrite(K + 'images/g10_scale_boxed.png', np.clip(base, 0, 255).astype(np.uint8))
print('pan centre', X + int(265 * f), Y + int(100 * f))
