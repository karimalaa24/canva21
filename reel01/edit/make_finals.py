"""Rebuild every *_final.png from *_filled.png (oud already placed with box_masters --quad_only):
wordmark -> BeetHoven, bag Arabic -> فخامة سمو, s11 bag large Arabic removed. Free, local, deterministic."""
import cv2, numpy as np, sys, shutil
sys.path.insert(0, '/home/user/canva21/reel01/edit'); from fix_wordmark import *
IMG = '/home/user/canva21/reel01/images/'
BH = src_word(); FS = ar_word('فخامة سمو')
def erase_rect(img, x0, y0, x1, y1, thr=14, dil=5):
    P = 40; pad = cv2.copyMakeBorder(img, P, P, P, P, cv2.BORDER_REFLECT)
    bg = cv2.medianBlur(pad[y0:y1 + 2 * P, x0:x1 + 2 * P], 41)[P:-P, P:-P].astype(np.float32)
    d = np.abs(img[y0:y1, x0:x1].astype(np.float32) - bg).mean(2)
    m = np.zeros(img.shape[:2], np.uint8); m[y0:y1, x0:x1] = cv2.dilate(((d > thr) * 255).astype(np.uint8), np.ones((dil, dil), np.uint8))
    return cv2.inpaint(img, m, 7, cv2.INPAINT_TELEA)
def bag_rebuild(im, x0, x1, y0, y1):   # smooth bag surface between clean rows above/below (removes large printed Arabic)
    f = im.astype(np.float32); bl = cv2.GaussianBlur(f, (0, 0), 3)
    def clean_row(r):
        L = r.mean(1); base = np.median(L); bad = L > base + 8; good = np.where(~bad)[0]
        for ch in range(3): r[bad, ch] = np.interp(np.where(bad)[0], good, r[good, ch])
        return cv2.GaussianBlur(r[None], (0, 0), 8)[0]
    top = clean_row(np.median(bl[y0 - 8:y0, x0:x1], 0).copy()); bot = clean_row(np.median(bl[y1:y1 + 8, x0:x1], 0).copy())
    t = np.linspace(0, 1, y1 - y0)[:, None, None]; fill = top[None] * (1 - t) + bot[None] * t
    fill = fill + cv2.GaussianBlur(np.random.default_rng(3).normal(0, 3.2, (y1 - y0, x1 - x0)).astype(np.float32), (0, 0), 0.7)[..., None]
    m = np.zeros(im.shape[:2], np.float32); m[y0:y1, x0:x1] = 1; m = cv2.GaussianBlur(m, (0, 0), 3)[y0:y1, x0:x1][..., None]
    reg = f[y0:y1, x0:x1]; isbag = ((reg[..., 2] > reg[..., 1] + 15) & (reg.mean(2) < 140)).astype(np.float32)
    isbag = cv2.GaussianBlur(cv2.dilate(isbag, np.ones((9, 9), np.uint8)), (0, 0), 2)[..., None]
    f[y0:y1, x0:x1] = reg * (1 - m * isbag) + fill * (m * isbag); return np.clip(f, 0, 255).astype(np.uint8)
# S02, S06: names already correct
shutil.copy(IMG + 's02_close_filled.png', IMG + 's02_close_final.png'); shutil.copy(IMG + 's06_high3_filled.png', IMG + 's06_high3_final.png')
shutil.copy(IMG + 's08_flatlay_raw.png', IMG + 's08_flatlay_final.png')
# S07
im = cv2.imread(IMG + 's07_low3_filled.png')
im, _ = fix(im, (300, 1755, 440, 1800), BH, width=128)
_, g7 = fix(im.copy(), (876, 1886, 960, 1910), BH, width=76, angle=3)
im = erase_rect(im, 870, 1882, 990, 1914); im, _ = fix(im, (876, 1886, 960, 1910), BH, width=76, angle=3, gold=g7)
cv2.imwrite(IMG + 's07_low3_final.png', im)
# S09 (closed boxes only)
im = cv2.imread(IMG + 's09_bag_raw.png'); im, _ = fix(im, (836, 1610, 960, 1648), FS, width=112); cv2.imwrite(IMG + 's09_bag_final.png', im)
# S10
im = cv2.imread(IMG + 's10_offer_filled.png')
im, _ = fix(im, (706, 1408, 856, 1444), BH, width=132)
_, gb = fix(im.copy(), (376, 1446, 520, 1486), BH, width=150, clip_x=519)
im2 = cv2.inpaint(im, cv2.dilate(((np.abs(im[..., :].astype(np.float32) - cv2.medianBlur(im, 41).astype(np.float32)).mean(2) > 8) * 255).astype(np.uint8) * 0, np.ones((3, 3), np.uint8)), 3, cv2.INPAINT_TELEA)
im2 = erase_rect(im, 366, 1425, 519, 1510, thr=8, dil=7); im[:, :519] = im2[:, :519]
im, _ = fix(im, (376, 1446, 520, 1486), BH, width=150, clip_x=519, gold=gb, thr=200)
im, _ = fix(im, (400, 1488, 500, 1506), FS, width=76, clip_x=519, gold=gb, thr=200, cy=1497)
cv2.imwrite(IMG + 's10_offer_final.png', im)
# S11
im = cv2.imread(IMG + 's11_close_hero_filled.png')
im, _ = fix(im, (820, 1663, 928, 1693), BH, width=96)
_, gb = fix(im.copy(), (1085, 1630, 1232, 1666), BH, width=140)
im = bag_rebuild(im, 1050, 1280, 1613, 1772)
im, _ = fix(im, (1085, 1630, 1232, 1666), BH, width=140, gold=gb, thr=200, cy=1646)
im, _ = fix(im, (1100, 1676, 1220, 1700), FS, width=86, gold=gb, thr=200, cy=1686)
im, _ = fix(im, (1398, 1849, 1514, 1872), BH, width=96, angle=-4)
cv2.imwrite(IMG + 's11_close_hero_final.png', im)
print('finals written')
