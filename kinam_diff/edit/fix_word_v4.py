"""Night v4 lid: remove the garbled AI word by inpainting only its gold pixels (keeps leather grain), then draw the approved
BeetHoven script (from fix_word.py) in the lid gold. usage: fix_word_v4.py in out x0 y0 x1 y1 width"""
import cv2, numpy as np, sys, importlib.util
x0, y0, x1, y1, W = [int(v) for v in sys.argv[3:8]]
im = cv2.imread(sys.argv[1]); f = im.astype(np.float32)
R = f[y0:y1, x0:x1]; warm = R[..., 2] - R[..., 0]
g = (warm > np.percentile(warm, 45) + 25).astype(np.uint8)
m = np.zeros(im.shape[:2], np.uint8); m[y0:y1, x0:x1] = cv2.dilate(g, np.ones((5, 5), np.uint8))
out = cv2.inpaint(im, m * 255, 4, cv2.INPAINT_TELEA).astype(np.float32)
# lid gold from the Arabic line just below
A2 = f[y1 + 4:y1 + 40, x0 - 40:x1 + 40]; w2 = A2[..., 2] - A2[..., 0]; gold = np.median(A2[w2 > np.percentile(w2, 93)], 0)
src = open('/home/user/canva21/kinam/edit/fix_word.py').read().split('import os')[0]; ns = {}; exec(src, ns); BH = ns['BH']
a = cv2.resize(BH, (W, int(W * BH.shape[0] / BH.shape[1])), interpolation=cv2.INTER_AREA); h, w = a.shape
A = np.zeros(im.shape[:2], np.float32); cx, cy = (x0 + x1) // 2, (y0 + y1) // 2; A[cy - h // 2:cy - h // 2 + h, cx - w // 2:cx - w // 2 + w] = a
A = np.clip(cv2.GaussianBlur(A, (0, 0), 0.5) * 1.5, 0, 1)[..., None]
cv2.imwrite(sys.argv[2], np.clip(out * (1 - A) + gold * A, 0, 255).astype(np.uint8)); print('gold', gold.round())
