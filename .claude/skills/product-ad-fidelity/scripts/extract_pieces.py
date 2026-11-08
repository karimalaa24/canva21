"""Cut individual product pieces out of real photos shot on a light background.

usage: python extract_pieces.py OUT_DIR photo1.jpg [photo2.jpg ...] [--minlen 140 --maxlen 380]

Touching pieces are separated by progressive erosion. Writes OUT_DIR/<photo>_<n>.png (RGBA) and
OUT_DIR/_sheet.jpg to eyeball. Reject bad cut-outs by deleting their PNG.
Best input: 15-20 pieces spaced apart on a white sheet, daylight, original files (not WhatsApp).
"""
import argparse, os
import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('photos', nargs='+')
ap.add_argument('--thr', type=int, default=150, help='gray level below which a pixel is product/shadow')
ap.add_argument('--minlen', type=float, default=140); ap.add_argument('--maxlen', type=float, default=380)
ap.add_argument('--minw', type=float, default=50); ap.add_argument('--maxw', type=float, default=180)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
saved = []
for p in args.photos:
    im = cv2.imread(p); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); H, W = g.shape
    m = (g < args.thr).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    found = []
    for er in (0, 9, 15):
        e = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (er * 2 + 1, er * 2 + 1))) if er else m
        n, lab = cv2.connectedComponents(e)
        for k in range(1, n):
            seed = (lab == k).astype(np.uint8) * 255
            comp = cv2.dilate(seed, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (er * 2 + 3, er * 2 + 3))) & m if er else seed
            cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            if not cnts: continue
            c = max(cnts, key=cv2.contourArea); a = cv2.contourArea(c); x, y, w, h = cv2.boundingRect(c)
            if a < 5000 or x <= 2 or y <= 2 or x + w >= W - 2 or y + h >= H - 2: continue
            sol = a / cv2.contourArea(cv2.convexHull(c)); (cx, cy), (rw, rh), _ = cv2.minAreaRect(c)
            L, S = max(rw, rh), min(rw, rh)
            if not (args.minlen < L < args.maxlen and args.minw < S < args.maxw and sol > 0.8): continue
            if any(abs(cx - f[0]) < 25 and abs(cy - f[1]) < 25 for f in found): continue
            found.append((cx, cy))
            mask = np.zeros((H, W), np.uint8); cv2.drawContours(mask, [c], -1, 255, -1)
            mask = cv2.GaussianBlur(cv2.erode(mask, np.ones((3, 3), np.uint8)), (3, 3), 0)
            rgba = np.dstack([im, mask])[max(0, y - 3):y + h + 3, max(0, x - 3):x + w + 3]
            name = os.path.join(args.out, f'{os.path.splitext(os.path.basename(p))[0]}_{len(found):02d}.png')
            cv2.imwrite(name, rgba); saved.append(name)
tiles = []
for n in saved:
    t = cv2.imread(n, cv2.IMREAD_UNCHANGED); al = t[..., 3:] / 255.
    c = (t[..., :3] * al + 128 * (1 - al)).astype(np.uint8); s = 220 / max(c.shape[:2])
    tiles.append(cv2.resize(c, (int(c.shape[1] * s), int(c.shape[0] * s))))
if tiles:
    sheet = np.full((230 * ((len(tiles) + 7) // 8), 8 * 230, 3), 255, np.uint8)
    for i, t in enumerate(tiles):
        r, cc = divmod(i, 8); sheet[r * 230:r * 230 + t.shape[0], cc * 230:cc * 230 + t.shape[1]] = t
    cv2.imwrite(os.path.join(args.out, '_sheet.jpg'), sheet)
print(len(saved), 'pieces saved')
