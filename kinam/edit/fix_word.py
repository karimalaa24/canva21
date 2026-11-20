"""Replace the AI lid word ('Best Flavor') with the approved BeetHoven script. Free, local.
usage: fix_word.py in.png out.png x0 y0 x1 y1 blur dark angle   (gold sampled from the Arabic line under the word)"""
import cv2, numpy as np, sys
def word_from(path, x0, y0, x1, y1):
    im = cv2.imread(path); R = im[y0:y1, x0:x1].astype(np.float32)
    bg = cv2.medianBlur(im[y0 - 40:y1 + 40, x0 - 40:x1 + 40], 41)[40:-40, 40:-40].astype(np.float32)
    d = (bg - R).mean(2); a = np.clip((d - 6) / (np.percentile(d, 99.5) - 6), 0, 1)
    ys, xs = np.where(a > 0.15); return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
BH = word_from('/home/user/canva21/reel03/images/p02_close_raw.png', 478, 1403, 662, 1468)
import os
POLY = os.environ.get('POLY'); WW = os.environ.get('WW')
src, dst = sys.argv[1:3]; x0, y0, x1, y1 = [int(v) for v in sys.argv[3:7]]; blur, dark, ang = [float(v) for v in sys.argv[7:10]]
im = cv2.imread(src)
R = im[y1 + 8:y1 + 8 + (y1 - y0) * 2, x0 - 30:x1 + 50].astype(np.float32); L = R.mean(2)
lightbg = np.median(L) > 110
gold = np.array([float(v) for v in os.environ["GOLD"].split(",")]) * dark if os.environ.get("GOLD") else np.median(R[L < np.percentile(L, 4)] if lightbg else R[(L > np.percentile(L, 88)) & (L < np.percentile(L, 97))], 0) * dark
m = np.zeros(im.shape[:2], np.uint8); m[y0:y1, x0:x1] = 255
if POLY: m[:] = 0; cv2.fillPoly(m, [np.array([[int(v) for v in p.split(',')] for p in POLY.split()], np.int32)], 255)
rect = m.copy()
if not lightbg:   # gold neighbours (B, Arabic): mask every gold px around so the fill only sees leather
    P = 60; reg = im[y0 - P:y1 + P, x0 - P:x1 + P].astype(np.float32)
    g = ((reg[..., 2] - reg[..., 0]) > 0.6 * np.percentile(reg[..., 2] - reg[..., 0], 99)).astype(np.uint8)
    m[y0 - P:y1 + P, x0 - P:x1 + P] |= cv2.dilate(g, np.ones((7, 7), np.uint8)) * 255
out = cv2.inpaint(im, m, 15, cv2.INPAINT_TELEA).astype(np.float32)
if not lightbg:   # put back the untouched gold artwork outside the word rect
    keep = (rect == 0) & (m > 0); out[keep] = im[keep]
sm = cv2.GaussianBlur(out, (0, 0), 6); rA = cv2.GaussianBlur((rect > 0).astype(np.float32), (0, 0), 1.5)[..., None]; out = sm * rA + out * (1 - rA)
if not lightbg:   # match the patch to the leather around it (non-gold ring)
    ring = (cv2.dilate(rect, np.ones((41, 41), np.uint8)) > 0) & (m == 0)
    inr = rect > 0; out[inr] += (im[ring].astype(np.float32).mean(0) - out[inr].mean(0))
tex = im.astype(np.float32) - cv2.GaussianBlur(im.astype(np.float32), (0, 0), 2)   # leather/lining grain from just above-left
if lightbg: sh = np.roll(tex, (0, -(x1 - x0)), (0, 1)); out[y0:y1, x0:x1] += sh[y0:y1, x0:x1] * 0.8
else: out += np.random.default_rng(1).normal(0, 2.5, out.shape) * (rect[..., None] > 0)   # leather grain (no gold nearby to copy)
W = int(WW) if WW else int((x1 - x0) * 0.98); a = cv2.resize(BH, (W, int(W * BH.shape[0] / BH.shape[1])), interpolation=cv2.INTER_AREA)
h, w = a.shape; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0); M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
A = cv2.warpAffine(a, M, (im.shape[1], im.shape[0]))
A = cv2.dilate(A, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))); A = np.clip(cv2.GaussianBlur(A, (0, 0), blur) * float(os.environ.get("AG", 1.2)), 0, 1)
f = np.clip(out * (1 - A[..., None]) + gold * A[..., None], 0, 255).astype(np.uint8)
cv2.imwrite(dst, f); print('gold', gold.round(), 'light bg' if lightbg else 'dark bg')
