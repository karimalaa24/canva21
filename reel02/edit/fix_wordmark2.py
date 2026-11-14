"""Reel 02: replace a wrong script wordmark ("Beethoven") with the approved "BeetHoven", free and local.

Source word = the correct BeetHoven engraved on the P03 lid lining (reel02/images/v1/p03_raw.png (first P03 take)), alpha from
difference to the local median background. Target word = connected gold components that touch the given seed
points (so the B monogram above and the Arabic below are never touched). The old word is inpainted, then the
source word is scaled to the old word's length along its principal axis, rotated to its angle and composited in
the old word's own gold (sampled), with the source's engraving shading.

usage (module): fix(img_bgr, bbox, seeds, thr=14, scale=1.0) -> img_bgr
"""
import cv2, numpy as np, os
HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = None


def src_word():
    global _SRC
    if _SRC is None:
        s = cv2.imread(os.path.join(HERE, '..', 'images', 'v1', 'p03_raw.png'))
        x0, y0, x1, y1 = 868, 1334, 1078, 1390
        P = 40
        R = s[y0:y1, x0:x1].astype(np.float32)
        bg = cv2.medianBlur(s[y0 - P:y1 + P, x0 - P:x1 + P], 41)[P:-P, P:-P].astype(np.float32)
        d = (bg - R).mean(2)
        a = np.clip((d - 6) / (np.percentile(d, 99.5) - 6), 0, 1)
        ys, xs = np.where(a > 0.15)
        _SRC = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return _SRC


def axis(mask):
    ys, xs = np.nonzero(mask)
    pts = np.stack([xs, ys], 1).astype(np.float64)
    c = pts.mean(0)
    u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
    v = vt[0] if vt[0][0] >= 0 else -vt[0]
    t = (pts - c) @ v
    return c, v, t.min(), t.max()


def fix(img, bbox, seeds, thr=14, scale=1.0, dil=3, debug=None, weight=1.7, erase_thr=None, hfit=False):
    x0, y0, x1, y1 = bbox
    P = 40
    pad = cv2.copyMakeBorder(img, P, P, P, P, cv2.BORDER_REFLECT)
    bg = cv2.medianBlur(pad[y0:y1 + 2 * P, x0:x1 + 2 * P], 31)[P:-P, P:-P].astype(np.float32)
    R = img[y0:y1, x0:x1].astype(np.float32)
    d = np.abs(R - bg).mean(2)
    m = (d > thr).astype(np.uint8)
    n, lab = cv2.connectedComponents(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8)))
    keep = set()
    for sx, sy in seeds:
        lx, ly = sx - x0, sy - y0
        win = lab[max(0, ly - 5):ly + 6, max(0, lx - 5):lx + 6]
        ids, cnt = np.unique(win[win > 0], return_counts=True)
        if len(ids):
            keep.add(int(ids[np.argmax(cnt)]))
    word = np.isin(lab, list(keep)).astype(np.uint8)
    if word.sum() < 20:
        raise SystemExit(f'no word found at {bbox}')
    # small stray parts of the old word (swashes, dots) whose centre lies inside the word's oriented box
    ys, xs = np.nonzero(word)
    box = cv2.boxPoints(cv2.minAreaRect(np.stack([xs, ys], 1).astype(np.float32)))
    wa = word.sum()
    for i in range(1, n):
        if i in keep: continue
        cm = lab == i; ar = cm.sum()
        if ar > 0.5 * wa: continue
        yy, xx = np.nonzero(cm)
        if cv2.pointPolygonTest(box, (float(xx.mean()), float(yy.mean())), False) >= 0:
            word[cm] = 1
    # gold = median of the strongest old-word pixels
    gold = np.median(R[(word > 0) & (d > np.percentile(d[word > 0], 50))], 0)
    # erase
    mask = np.zeros(img.shape[:2], np.uint8)
    wm = word.copy()
    if erase_thr is not None:  # grow the erase mask into faint word edges
        faint = (d > erase_thr).astype(np.uint8)
        wm = cv2.bitwise_and(faint, cv2.dilate(word, np.ones((7, 7), np.uint8)))| word
    mask[y0:y1, x0:x1] = cv2.dilate(wm * 255, np.ones((2 * dil + 1, 2 * dil + 1), np.uint8))
    # fill = local median background (letters are thin, so the median is leather/lining) + real fine texture
    # copied from a nearby letter-free offset of the same surface
    out = img.astype(np.float32).copy()
    # background = normalized convolution over NON-gold pixels only (no letter colour bleeds into the fill)
    goldm = np.zeros(img.shape[:2], np.float32); goldm[y0:y1, x0:x1] = (d > max(thr, 18))
    w = 1.0 - cv2.dilate(goldm, np.ones((7, 7), np.uint8)); w[mask > 0] = 0
    full_bg = cv2.GaussianBlur(out * w[..., None], (0, 0), 8) / (cv2.GaussianBlur(w, (0, 0), 8)[..., None] + 1e-4)
    tex = out - cv2.GaussianBlur(out, (0, 0), 2.0)
    # texture: noise with the local leather/lining fine-texture statistics (no copied patches -> no ghost letters)
    ring = cv2.dilate(mask, np.ones((15, 15), np.uint8)) & ~cv2.dilate(mask, np.ones((5, 5), np.uint8))
    rs = (ring > 0) & (w > 0)
    sd = 1.4826 * np.median(np.abs(tex[rs] - np.median(tex[rs], 0)), 0) if rs.sum() > 50 else np.array([2., 2., 2.])
    rng = np.random.RandomState(1)
    noise = cv2.GaussianBlur(rng.randn(*img.shape[:2]).astype(np.float32), (0, 0), 0.7)
    noise = noise / (noise.std() + 1e-6)
    sh = noise[..., None] * sd[None, None, :]
    mk = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 1.2)[..., None]
    out = out * (1 - mk) + (full_bg + sh * 0.9) * mk
    # geometry of the old word
    c, v, t0, t1 = axis(word)
    c = c + np.array([x0, y0]) + v * (t0 + t1) / 2
    L = (t1 - t0) * scale
    ang = np.degrees(np.arctan2(v[1], v[0]))
    a = src_word()
    sc, sv, s0, s1 = axis(a > 0.3)
    k = L / (s1 - s0)
    sang = np.degrees(np.arctan2(sv[1], sv[0]))
    # anisotropic fit: source length -> old length along the axis, source height -> old height across it
    ys2, xs2 = np.nonzero(word); P2 = np.stack([xs2, ys2], 1) + np.array([x0, y0]) - c
    u = np.array([-v[1], v[0]]); h_old = np.percentile(P2 @ u, 97) - np.percentile(P2 @ u, 3)
    sy, sx = np.nonzero(a > 0.3); S2 = np.stack([sx, sy], 1) - (sc + sv * (s0 + s1) / 2)
    su = np.array([-sv[1], sv[0]]); h_src = np.percentile(S2 @ su, 97) - np.percentile(S2 @ su, 3)
    ky = (h_old / h_src) * scale if hfit else k
    scen = sc + sv * (s0 + s1) / 2
    def rot(t):
        t = np.radians(t); return np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    Lm = rot(ang) @ np.diag([k, ky]) @ rot(-sang)
    M = np.zeros((2, 3)); M[:, :2] = Lm; M[:, 2] = c - Lm @ scen
    A = cv2.warpAffine(a, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_AREA if k < 1 else cv2.INTER_LINEAR)
    A = np.clip(A * weight, 0, 1) ** 0.85
    def thick(mk):
        dt = cv2.distanceTransform(mk.astype(np.uint8), cv2.DIST_L2, 3)
        ridge = (dt >= cv2.dilate(dt, np.ones((3, 3), np.uint8)) - 1e-3) & (dt > 0.5)
        return 2 * np.median(dt[ridge]) if ridge.any() else 1.0
    w_old = thick(word > 0); w_new = thick(A > 0.5)
    grow = min(0.6, (w_old - w_new) / 2)
    if grow > 0.3:
        r = int(np.ceil(grow)); Ad = cv2.dilate(A, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
        A = A + (Ad - A) * min(1.0, grow / r)
    # engraving shade from the source alpha gradient
    shade = 1.0 + 0.08 * cv2.Sobel(cv2.GaussianBlur(A, (0, 0), 0.8), cv2.CV_32F, 0, 1, ksize=3)
    g = np.array(gold, np.float32)[None, None, :] * np.clip(shade, 0.8, 1.2)[..., None]
    out = out * (1 - A[..., None]) + g * A[..., None]
    if debug is not None:
        cv2.imwrite(debug, (word * 255))
    return np.clip(out, 0, 255).astype(np.uint8)


def ar_alpha(text, ttf=os.path.join(HERE, '..', '..', 'oud-fix5', 'fonts', 'Almarai-ExtraBold.ttf')):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(ttf, 200, layout_engine=ImageFont.Layout.RAQM)
    im = Image.new('L', (2400, 600), 0)
    ImageDraw.Draw(im).text((100, 100), text, font=f, fill=255, direction='rtl')
    a = np.array(im).astype(np.float32) / 255
    ys, xs = np.where(a > 0.05)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def fix_ar(img, bbox, text, width=None, thr=14, dil=2, angle=0.0, weight=1.0, cy_override=None):
    """Erase every gold stroke inside bbox and render `text` (full Almarai TTF) centred there, same gold."""
    x0, y0, x1, y1 = bbox
    P = 40
    pad = cv2.copyMakeBorder(img, P, P, P, P, cv2.BORDER_REFLECT)
    bg = cv2.medianBlur(pad[y0:y1 + 2 * P, x0:x1 + 2 * P], 31)[P:-P, P:-P].astype(np.float32)
    R = img[y0:y1, x0:x1].astype(np.float32)
    d = np.abs(R - bg).mean(2)
    word = (d > thr).astype(np.uint8)
    gold = np.median(R[(word > 0) & (d > np.percentile(d[word > 0], 50))], 0)
    ys, xs = np.nonzero(word)
    cx, cy = x0 + (xs.min() + xs.max()) / 2, y0 + (ys.min() + ys.max()) / 2
    W = width or (xs.max() - xs.min())
    if cy_override is not None: cy = cy_override
    mask = np.zeros(img.shape[:2], np.uint8)
    mask[y0:y1, x0:x1] = cv2.dilate(word * 255, np.ones((2 * dil + 1, 2 * dil + 1), np.uint8))
    out = img.astype(np.float32)
    w = np.ones(img.shape[:2], np.float32); w[mask > 0] = 0
    w[y0:y1, x0:x1] *= 1 - cv2.dilate(word.astype(np.float32), np.ones((7, 7), np.uint8))
    full_bg = cv2.GaussianBlur(out * w[..., None], (0, 0), 6) / (cv2.GaussianBlur(w, (0, 0), 6)[..., None] + 1e-4)
    tex = out - cv2.GaussianBlur(out, (0, 0), 2.0)
    ring = cv2.dilate(mask, np.ones((15, 15), np.uint8)) & ~cv2.dilate(mask, np.ones((5, 5), np.uint8))
    rs = (ring > 0) & (w > 0)
    sd = 1.4826 * np.median(np.abs(tex[rs] - np.median(tex[rs], 0)), 0) if rs.sum() > 50 else np.array([2., 2., 2.])
    noise = cv2.GaussianBlur(np.random.RandomState(2).randn(*img.shape[:2]).astype(np.float32), (0, 0), 0.7)
    noise /= noise.std() + 1e-6
    mk = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 1.0)[..., None]
    out = out * (1 - mk) + (full_bg + noise[..., None] * sd) * mk
    a = ar_alpha(text)
    k = W / a.shape[1]
    M = cv2.getRotationMatrix2D((a.shape[1] / 2, a.shape[0] / 2), angle, k)
    M[0, 2] += cx - a.shape[1] / 2
    M[1, 2] += cy - a.shape[0] / 2
    A = np.clip(cv2.warpAffine(a, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_AREA) * weight, 0, 1)
    out = out * (1 - A[..., None]) + np.array(gold, np.float32) * A[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)
