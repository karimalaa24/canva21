"""G3 v4: paste the REAL pieces (client hand photo) onto the AI re-staging (same arrangement): one similarity transform from ORB
matches on the wood, real-piece mask only, colour matched to the warm room light (Lab mean/std of the AI pieces). Free, local."""
import cv2, numpy as np
from scipy.ndimage import binary_fill_holes
S = '/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/'
R = cv2.imread('/home/user/canva21/kinam/references/hand_pieces_ref.jpg'); A = cv2.imread('g03v4_raw.png'); H, W = A.shape[:2]
def woodmask(im, roi):
    lab = cv2.cvtColor(cv2.GaussianBlur(im, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(int)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32); hp = g - cv2.GaussianBlur(g, (0, 0), 2); tex = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 5))
    m = ((lab[..., 1] < 146) & (lab[..., 2] > 140) & (tex > 2.0)).astype(np.uint8)
    r = np.zeros_like(m); r[roi[1]:roi[3], roi[0]:roi[2]] = 1; m &= r
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)); m = binary_fill_holes(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))).astype(np.uint8)
    n, l, st, _ = cv2.connectedComponentsWithStats(m); return np.isin(l, [i for i in range(1, n) if st[i, 4] > 5000]).astype(np.uint8)
mr = woodmask(R, (150, 300, 1000, 1100)); ma = woodmask(A, (600, 1000, 1300, 1700))
o = cv2.SIFT_create(6000)
k1, d1 = o.detectAndCompute(cv2.cvtColor(R, cv2.COLOR_BGR2GRAY), cv2.dilate(mr, np.ones((15, 15), np.uint8)) * 255)
k2, d2 = o.detectAndCompute(cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.dilate(ma, np.ones((15, 15), np.uint8)) * 255)
mt = [m for m, n in cv2.BFMatcher().knnMatch(d1, d2, k=2) if m.distance < 0.8 * n.distance]
p1 = np.float32([k1[m.queryIdx].pt for m in mt]); p2 = np.float32([k2[m.trainIdx].pt for m in mt])
M, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=6)
print('matches', len(mt), 'inliers', int(inl.sum()), 'scale %.3f' % np.hypot(M[0, 0], M[0, 1]))
Rw = cv2.warpAffine(R, M, (W, H), flags=cv2.INTER_LANCZOS4); mw = cv2.warpAffine(mr.astype(np.float32), M, (W, H))
# colour: match real pieces to the AI pieces' Lab statistics (same room light)
la = cv2.cvtColor(A, cv2.COLOR_BGR2LAB).astype(np.float32); lr = cv2.cvtColor(Rw, cv2.COLOR_BGR2LAB).astype(np.float32)
sa = ma > 0; sr = mw > 0.5
for c in range(3): lr[..., c] = (lr[..., c] - lr[..., c][sr].mean()) / (lr[..., c][sr].std() + 1e-3) * la[..., c][sa].std() + la[..., c][sa].mean()
Rc = cv2.cvtColor(np.clip(lr, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
# cover the AI pieces fully: union of both masks; outside the real pieces but inside the AI ones -> palm (inpaint)
gap = ((ma > 0) & (mw < 0.5)).astype(np.uint8)
base = cv2.inpaint(A, cv2.dilate(gap, np.ones((9, 9), np.uint8)) * 255, 9, cv2.INPAINT_TELEA).astype(np.float32)
sh = cv2.GaussianBlur(np.roll(np.roll(mw, 10, 0), 6, 1), (0, 0), 9)[..., None]; base *= 1 - 0.35 * np.clip(sh - mw[..., None], 0, 1)
a = cv2.GaussianBlur(cv2.erode(mw, np.ones((3, 3), np.uint8)), (0, 0), 1.0)[..., None]
out = Rc * a + base * (1 - a); cv2.imwrite('g03v4_real.png', np.clip(out, 0, 255).astype(np.uint8))
cv2.imwrite(S + 'g3r.jpg', np.hstack([A[950:1700, 550:1300], np.clip(out, 0, 255).astype(np.uint8)[950:1700, 550:1300]]))
