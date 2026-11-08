"""Make pop-up badge PNGs.

1) Lift a logo that is printed/embossed on a light surface (e.g. gold 'B Beethoven' on the cream lid
   lining) into an alpha mask:
     python make_badges.py logo  plate.png x0,y0,x1,y1  logo_alpha.png
2) Build a gift badge (burgundy card, gold border, gift icon, logo):
     python make_badges.py gift  logo_alpha.png  gift_badge.png  [--w 470 --h 165 --top 128,26,42 --bot 66,10,20]
3) Lift an existing rounded badge (tabby / tamara) from a frame of the original ad:
     python make_badges.py lift  frame.png x0,y0,x1,y1  logo_tabby.png  [--r 24]
"""
import argparse
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ap = argparse.ArgumentParser(); ap.add_argument('mode'); ap.add_argument('a'); ap.add_argument('b'); ap.add_argument('c', nargs='?')
ap.add_argument('--w', type=int, default=470); ap.add_argument('--h', type=int, default=165)
ap.add_argument('--top', default='128,26,42'); ap.add_argument('--bot', default='66,10,20'); ap.add_argument('--r', type=int, default=24)
A = ap.parse_args()

if A.mode == 'logo':
    x0, y0, x1, y1 = map(int, A.b.split(',')); p = cv2.imread(A.a)[y0:y1, x0:x1]
    lab = cv2.cvtColor(p, cv2.COLOR_BGR2LAB).astype(np.float32)
    bgL, bgB = np.percentile(lab[..., 0], 60), np.percentile(lab[..., 2], 40)       # surface = majority
    a = np.clip(np.maximum((bgL - lab[..., 0]) / 40, (lab[..., 2] - bgB) / 24), 0, 1)  # darker or more yellow = print
    a = cv2.GaussianBlur(a, (3, 3), 0); m = (a > 0.35).astype(np.uint8)
    n, l, st, _ = cv2.connectedComponentsWithStats(m); keep = np.zeros_like(m)
    for k in range(1, n):
        if st[k, 4] > 40: keep[l == k] = 1
    a = a * cv2.dilate(keep, np.ones((5, 5), np.uint8)); ys, xs = np.where(a > 0.3)
    a = a[max(0, ys.min() - 6):ys.max() + 7, max(0, xs.min() - 6):xs.max() + 7]
    cv2.imwrite(A.c, (a * 255).astype(np.uint8)); print('logo', a.shape)

elif A.mode == 'gift':
    bw, bh, S = A.w, A.h, 3; top = np.array(list(map(int, A.top.split(',')))); bot = np.array(list(map(int, A.bot.split(','))))
    g = np.linspace(0, 1, bh * S)[:, None]
    col = (top[None, None, :] * (1 - g[:, :, None]) + bot[None, None, :] * g[:, :, None]) * np.ones((1, bw * S, 1))
    m = Image.new('L', (bw * S, bh * S), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bw * S - 1, bh * S - 1), radius=26 * S, fill=255)
    img = Image.fromarray(np.dstack([col, np.array(m)]).astype(np.uint8), 'RGBA'); d = ImageDraw.Draw(img)
    d.rounded_rectangle((3 * S, 3 * S, bw * S - 4 * S, bh * S - 4 * S), radius=23 * S, outline=(226, 188, 118, 255), width=3 * S)
    gx, gy, gw = 44 * S, 34 * S, 96 * S; gold, gold2 = (232, 196, 126, 255), (196, 150, 78, 255)
    d.rounded_rectangle((gx, gy + 30 * S, gx + gw, gy + gw), radius=6 * S, fill=gold2)
    d.rounded_rectangle((gx - 6 * S, gy + 16 * S, gx + gw + 6 * S, gy + 38 * S), radius=6 * S, fill=gold)
    d.rectangle((gx + gw / 2 - 8 * S, gy + 16 * S, gx + gw / 2 + 8 * S, gy + gw), fill=tuple(top) + (255,))
    d.ellipse((gx + gw / 2 - 36 * S, gy - 6 * S, gx + gw / 2 - 2 * S, gy + 20 * S), outline=gold, width=8 * S)
    d.ellipse((gx + gw / 2 + 2 * S, gy - 6 * S, gx + gw / 2 + 36 * S, gy + 20 * S), outline=gold, width=8 * S)
    d.ellipse((gx + gw / 2 - 9 * S, gy + 4 * S, gx + gw / 2 + 9 * S, gy + 22 * S), fill=gold)
    d.line((168 * S, 28 * S, 168 * S, bh * S - 28 * S), fill=(226, 188, 118, 150), width=2 * S)
    la = cv2.imread(A.a, 0).astype(np.float32) / 255; la = cv2.dilate(np.clip((la - 0.12) / 0.5, 0, 1), np.ones((3, 3), np.uint8))
    th = int(bh * 0.84 * S); tw = int(la.shape[1] * th / la.shape[0]); la = cv2.resize(la, (tw, th), interpolation=cv2.INTER_AREA)
    gg = np.linspace(0, 1, th)[:, None, None]; lc = np.array([246, 222, 168]) * (1 - gg) + np.array([212, 168, 98]) * gg
    img.alpha_composite(Image.fromarray(np.dstack([lc * np.ones((th, tw, 1)), la * 255]).astype(np.uint8), 'RGBA'),
                        (int(168 * S + (bw * S - 168 * S - tw) / 2), int((bh * S - th) / 2)))
    img = img.resize((bw, bh), Image.LANCZOS)
    out = Image.new('RGBA', (bw + 60, bh + 60), (0, 0, 0, 0)); sh = Image.new('L', (bw + 60, bh + 60), 0)
    ImageDraw.Draw(sh).rounded_rectangle((30, 36, 30 + bw, 36 + bh), radius=26, fill=150)
    shi = Image.new('RGBA', (bw + 60, bh + 60), (0, 0, 0, 255)); shi.putalpha(sh.filter(ImageFilter.GaussianBlur(12)))
    out.alpha_composite(shi); out.alpha_composite(img, (30, 30)); out.save(A.b); print('badge', out.size)

elif A.mode == 'lift':
    x0, y0, x1, y1 = map(int, A.b.split(',')); im = cv2.imread(A.a); crop = im[y0:y1, x0:x1].copy(); h, w = crop.shape[:2]; r = A.r
    m = np.zeros((h, w), np.uint8); cv2.rectangle(m, (r, 0), (w - 1 - r, h - 1), 255, -1); cv2.rectangle(m, (0, r), (w - 1, h - 1 - r), 255, -1)
    for cx, cy in ((r, r), (w - 1 - r, r), (r, h - 1 - r), (w - 1 - r, h - 1 - r)): cv2.circle(m, (cx, cy), r, 255, -1)
    m = cv2.GaussianBlur(cv2.erode(m, np.ones((5, 5), np.uint8)), (3, 3), 0)
    cv2.imwrite(A.c, np.dstack([crop, m])); print('lifted', w, h)
