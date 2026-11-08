"""Make one AI-generated region (e.g. a piece held in fingers that Magnific drew) match the
product pieces already in the image, by histogram-matching its L channel to theirs and rebuilding
a/b from the target model. Mean-matching alone was NOT enough (client still saw a different piece);
histogram matching + target chroma was.

usage: python match_piece_color.py image.png region_mask.png ref_mask.png target.json out.png
  region_mask = white where the piece to fix is;  ref_mask = white on the approved pieces (e.g. inside the box)
Prefer, when possible, replacing the AI piece with a real cut-out run through fill_container.py
('held' option) and only keeping the AI fingers on top: that guarantees identical colour/pattern.
"""
import sys
import cv2
import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from common import load_target

img, rm, fm, tg, out = sys.argv[1:6]
im = cv2.imread(img); lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
R = cv2.imread(rm, 0) > 127; F = cv2.imread(fm, 0) > 127
RL, RA, RB = load_target(tg)
ref = np.sort(lab[..., 0][F]); src = np.sort(lab[..., 0][R])
q = np.searchsorted(src, lab[..., 0]) / max(len(src) - 1, 1)
Ln = ref[np.clip((q * (len(ref) - 1)).astype(int), 0, len(ref) - 1)]
offa = lab[..., 1][F].mean() - np.polyval(RA, lab[..., 0][F]).mean(); offb = lab[..., 2][F].mean() - np.polyval(RB, lab[..., 0][F]).mean()
an = np.polyval(RA, Ln) + (lab[..., 1] - lab[..., 1][R].mean()) * 0.25 + offa
bn = np.polyval(RB, Ln) + (lab[..., 2] - lab[..., 2][R].mean()) * 0.25 + offb
nb = cv2.cvtColor(np.clip(np.dstack([Ln, an, bn]), 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
A = cv2.GaussianBlur(R.astype(np.float32), (5, 5), 0)[..., None]
cv2.imwrite(out, np.clip(im * (1 - A) + nb * A, 0, 255).astype(np.uint8))
o2 = cv2.cvtColor(cv2.imread(out), cv2.COLOR_BGR2LAB).astype(float)
print('region LAB', o2[R].mean(0).round(1), 'ref LAB', o2[F].mean(0).round(1))
