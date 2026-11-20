"""contact sheet: 6 frames per clip in one row. usage: sheet.py out.jpg clip1.mp4 [clip2.mp4 ...]"""
import cv2, numpy as np, sys
rows = []
for f in sys.argv[2:]:
    c = cv2.VideoCapture(f); n = int(c.get(cv2.CAP_PROP_FRAME_COUNT)); fr = []
    for k in np.linspace(0, n - 1, 6).astype(int):
        c.set(cv2.CAP_PROP_POS_FRAMES, k); ok, im = c.read()
        im = cv2.resize(im, (216, 384)); cv2.putText(im, '%s %d' % (f.split('/')[-1][:3], k), (6, 22), 0, 0.6, (255, 255, 255), 2); fr.append(im)
    rows.append(np.hstack(fr))
cv2.imwrite(sys.argv[1], np.vstack(rows))
