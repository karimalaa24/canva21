import cv2, numpy as np
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

def erase_keep_above(img, x0, y0, x1, y1, thr=10, dil=3, look=160):
    """Erase the old word in the rect, but keep every gold stroke connected to artwork ABOVE the rect (the B monogram's swash)."""
    P = 40; pad = cv2.copyMakeBorder(img, P, P, P, P, cv2.BORDER_REFLECT)
    Y0 = max(0, y0 - look)
    bg = cv2.medianBlur(pad[Y0:y1 + 2 * P, x0:x1 + 2 * P], 41)[P:-P, P:-P].astype(np.float32)
    d = np.abs(img[Y0:y1, x0:x1].astype(np.float32) - bg).mean(2); m = (d > thr).astype(np.uint8)
    n, lab = cv2.connectedComponents(cv2.dilate(m, np.ones((3, 3), np.uint8)))
    keep_ids = set(np.unique(lab[:max(1, y0 - Y0 - 2)])) - {0}
    keep = np.isin(lab, list(keep_ids)).astype(np.uint8)
    word = m.copy(); word[:y0 - Y0] = 0; word[keep > 0] = 0
    mask = np.zeros(img.shape[:2], np.uint8); mask[Y0:y1, x0:x1] = cv2.dilate(word * 255, np.ones((dil, dil), np.uint8))
    mask[Y0:y1, x0:x1][cv2.dilate(keep, np.ones((3, 3), np.uint8)) > 0] = 0
    return cv2.inpaint(img, mask, 7, cv2.INPAINT_TELEA)
