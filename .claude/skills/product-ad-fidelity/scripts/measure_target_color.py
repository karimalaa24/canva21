"""Build the target-colour model from crops that contain ONLY product (no fingers, no background).

usage: python measure_target_color.py OUT.json crop1.jpg[:x0,y0,x1,y1] [crop2 ...] [--warm 1 --da 0 --db 0]

The model = L mean/std + linear regressions a(L), b(L) in OpenCV LAB (0-255).
Lesson from the oud project: measuring on a big crop that includes skin pulls the colour purple/red;
always crop tightly inside the product. The client-approved oud model was roughly
  L=(53.3, 26.5), a(L)=0.06*L+128+1.8, b(L)=0.14*L+128+2.2  (dark brown, muted beige streaks).
--da/--db shift chroma afterwards (e.g. +1.5/+4 to warm wood that reads cool next to gold brass).
"""
import argparse, json
import cv2
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('crops', nargs='+')
ap.add_argument('--da', type=float, default=0); ap.add_argument('--db', type=float, default=0)
args = ap.parse_args()
P = []
for c in args.crops:
    path, _, box = c.partition(':'); im = cv2.imread(path)
    if box:
        x0, y0, x1, y1 = map(int, box.split(',')); im = im[y0:y1, x0:x1]
    P.append(cv2.cvtColor(im, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32))
L = np.vstack(P)
ra = np.polyfit(L[:, 0], L[:, 1], 1); rb = np.polyfit(L[:, 0], L[:, 2], 1)
ra[1] += args.da; rb[1] += args.db
out = {'L': [float(L[:, 0].mean()), float(L[:, 0].std())], 'a_of_L': ra.tolist(), 'b_of_L': rb.tolist()}
json.dump(out, open(args.out, 'w'), indent=1); print(out)
