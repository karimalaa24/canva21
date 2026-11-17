"""Reel 03: *_final.png = filled stills + wordmark fixes (BeetHoven, bag Arabic). Free, local."""
import cv2, numpy as np, sys, shutil
sys.path.insert(0, '/home/user/canva21/reel01/edit'); from fix_wordmark import src_word, ar_word, fix
sys.path.insert(0, '/home/user/canva21/reel03/edit'); from fin_helpers import erase_rect, bag_rebuild, erase_keep_above
IMG = '/home/user/canva21/reel03/images/'
FS = ar_word('فخامة سمو')
def word_from(path, x0, y0, x1, y1):   # clean BeetHoven alpha cut from an approved lid of THIS reel (gold on cream)
    im = cv2.imread(path); R = im[y0:y1, x0:x1].astype(np.float32)
    bg = cv2.medianBlur(im[y0 - 40:y1 + 40, x0 - 40:x1 + 40], 41)[40:-40, 40:-40].astype(np.float32)
    d = (bg - R).mean(2); a = np.clip((d - 6) / (np.percentile(d, 99.5) - 6), 0, 1)
    ys, xs = np.where(a > 0.15); return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
BH = word_from(IMG + 'p02_close_raw.png', 478, 1403, 662, 1468)
# P02 open lid: already a correct, sharp BeetHoven (no change)
shutil.copy(IMG + 'p02_close_filled.png', IMG + 'p02_close_final.png')
# P03: open lid already BeetHoven
shutil.copy(IMG + 'p03_high3_filled.png', IMG + 'p03_high3_final.png')
# P04: open lid + two closed lids "Beethoven"
im = cv2.imread(IMG + 'p04_low3_filled.png')
PADR = {(302, 1757, 440, 1797): 4, (876, 1886, 1000, 1910): 4, (1136, 1773, 1218, 1791): 12}
PADT = {(302, 1757, 440, 1797): 1, (876, 1886, 1000, 1910): 3, (1136, 1773, 1218, 1791): 1}
for box, w, ang, cy in [((302, 1757, 440, 1797), 132, 0, 1778), ((876, 1886, 1000, 1910), 112, 3, 1899), ((1136, 1773, 1218, 1791), 78, 3, 1782)]:
    _, g = fix(im.copy(), box, BH, width=w)
    x0, y0, x1, y1 = box; im = erase_rect(im, x0 - 5, y0 - 2, x1 + PADR[box], y1 + 2, thr=10, dil=3)
    im, _ = fix(im, box, BH, width=w, angle=ang, gold=g, thr=200, cy=cy)
cv2.imwrite(IMG + 'p04_low3_final.png', im)
shutil.copy(IMG + 'p05_flatlay_raw.png', IMG + 'p05_flatlay_final.png')
# P06 bag: garbled Arabic -> فخامة سمو
im = cv2.imread(IMG + 'p06_bag_raw.png')
_, g = fix(im.copy(), (622, 1692, 712, 1718), FS, width=86)
im = bag_rebuild(im, 606, 736, 1686, 1726); im, _ = fix(im, (622, 1692, 712, 1718), FS, width=86, gold=g, thr=200, cy=1705)
cv2.imwrite(IMG + 'p06_bag_final.png', im)
shutil.copy(IMG + 'p07_offer_filled.png', IMG + 'p07_offer_final.png')
# P08 bag: wrong wordmark + large Arabic -> BeetHoven + small فخامة سمو
im = cv2.imread(IMG + 'p08_close_hero_filled.png')
_, g = fix(im.copy(), (1000, 1785, 1100, 1817), BH, width=104)
im = bag_rebuild(im, 985, 1135, 1780, 1882)
im, _ = fix(im, (1000, 1785, 1100, 1817), BH, width=104, gold=g, thr=200, cy=1800)
im, _ = fix(im, (1012, 1822, 1088, 1840), FS, width=64, gold=g, thr=200, cy=1831)
cv2.imwrite(IMG + 'p08_close_hero_final.png', im)
shutil.copy(IMG + 'p01_hook_raw.png', IMG + 'p01_hook_final.png'); shutil.copy(IMG + 'plate_raw.png', IMG + 'plate_final.png')
print('finals written')
