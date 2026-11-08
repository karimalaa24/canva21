"""Shared helpers: load real product cut-outs, grade them into a scene, place them with shadows,
and apply the approved target colour. Used by scatter_on_surface.py and fill_container.py.

Colour pipeline (the one the client approved):
  1. normalise each cut-out by the reference photo's paper white  -> albedo
  2. multiply by the scene light colour (sampled from a white/cream area of the plate) * WARM tint
  3. after compositing, re-map every product pixel in LAB to the target-colour model
     (L mean/std + a(L), b(L) regressions measured on wood-only crops of the real product)
"""
import glob, json, os
import cv2
import numpy as np


# ---------- pieces ----------------------------------------------------------------------------
def load_pieces(piece_dir, dark_thr=92, warm_thr=125):
    """Load RGBA cut-outs from extract_pieces.py. Returns list of (name, bgr float32, alpha float32),
    each rotated so its long axis is horizontal and with light fringes removed."""
    pool = []
    for f in sorted(glob.glob(os.path.join(piece_dir, '*.png'))):
        t = cv2.imread(f, cv2.IMREAD_UNCHANGED).astype(np.float32)
        rgb, a = t[..., :3], t[..., 3] / 255.
        gray = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        B, R = rgb[..., 0], rgb[..., 2]
        # product = dark pixels, or warm (R>B) mid pixels; bluish-grey = cast shadow of the photo -> drop
        wood = ((gray < dark_thr) | (((R - B) > 2) & (gray < warm_thr))).astype(np.uint8) & (a > 0.5).astype(np.uint8)
        wood = cv2.morphologyEx(wood, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        wood = cv2.morphologyEx(wood, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        n, lab, st, _ = cv2.connectedComponentsWithStats(wood)
        if n < 2:
            continue
        wood = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
        cn, _ = cv2.findContours(wood, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        wood = np.zeros_like(wood); cv2.drawContours(wood, cn, -1, 1, -1)
        wood = cv2.erode(wood, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        a = cv2.GaussianBlur(wood.astype(np.float32), (3, 3), 0)
        # colour decontamination: pull light edge pixels toward neighbouring wood colour
        fill = rgb.copy()
        for _ in range(6):
            er = cv2.erode(fill, np.ones((3, 3), np.uint8))
            fill = np.where((cv2.cvtColor(np.clip(fill, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY) > 110)[..., None], er, fill)
        # rotate long axis horizontal
        c2 = max(cv2.findContours((a > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
        (_, _), (rw, rh), ra = cv2.minAreaRect(c2); ra = ra if rw >= rh else ra + 90
        h0, w0 = a.shape; D0 = int(np.hypot(h0, w0)) + 4
        M0 = cv2.getRotationMatrix2D((w0 / 2, h0 / 2), ra, 1); M0[0, 2] += (D0 - w0) / 2; M0[1, 2] += (D0 - h0) / 2
        fill = cv2.warpAffine(fill, M0, (D0, D0)); a = cv2.warpAffine(a, M0, (D0, D0))
        ys, xs = np.where(a > 0.05)
        fill = fill[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        lg = cv2.cvtColor(np.clip(fill, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        a = a * np.clip((150 - lg) / 25, 0, 1)
        pool.append((os.path.basename(f)[:-4], fill, a))
    if not pool:
        raise SystemExit('no usable pieces in ' + piece_dir)
    return pool


def paper_white(ref_photo):
    r = cv2.imread(ref_photo).astype(np.float32)
    g = cv2.cvtColor(r.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    return np.median(r[g > 200], axis=0)


def scene_light(plate, poly=None):
    """Median colour of bright neutral pixels (cloth / cream lining) = colour of the scene light."""
    m = np.ones(plate.shape[:2], bool)
    if poly is not None:
        mm = np.zeros(plate.shape[:2], np.uint8); cv2.fillPoly(mm, [np.array(poly, np.int32)], 1); m = mm > 0
    g = cv2.cvtColor(plate.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    sel = m & (g > 150)
    return np.median(plate[sel], axis=0) if sel.sum() > 100 else np.array([176., 194., 224.])


def xform(rgb, a, length, ang, flip, elong=1.0, squash=1.0):
    """Scale piece so its long side == length (then stretch by elong), rotate, optional vertical squash
    for floor perspective."""
    if flip:
        rgb = rgb[:, ::-1]; a = a[:, ::-1]
    h, w = a.shape; s = length / w
    nw, nh = max(2, int(w * s * elong)), max(2, int(h * s))
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
    rgb = cv2.resize(rgb, (nw, nh), interpolation=interp); a = cv2.resize(a, (nw, nh), interpolation=interp)
    D = int(np.hypot(nh, nw)) + 4
    M = cv2.getRotationMatrix2D((nw / 2, nh / 2), ang, 1); M[0, 2] += (D - nw) / 2; M[1, 2] += (D - nh) / 2
    rgb = cv2.warpAffine(rgb, M, (D, D)); a = cv2.warpAffine(a, M, (D, D))
    if squash != 1.0:
        rgb = cv2.resize(rgb, (D, max(2, int(D * squash))), interpolation=cv2.INTER_AREA)
        a = cv2.resize(a, (D, max(2, int(D * squash))), interpolation=cv2.INTER_AREA)
    return rgb, a


class Canvas:
    """Accumulates pieces on a plate with soft cast shadow + contact shadow + thin separation line."""

    def __init__(self, plate):
        self.plate = plate.astype(np.float32); self.img = self.plate.copy()
        self.H, self.W = plate.shape[:2]; self.wood = np.zeros((self.H, self.W), np.float32)

    def place(self, rgb, a, cx, cy, shadow=(-8, 11), sop=0.6, sblur=10, contact=0.55, csig=2.0, line=0.35):
        H, W = self.H, self.W
        h, w = a.shape; x0 = int(cx - w / 2); y0 = int(cy - h / 2)
        xs, ys = max(0, x0), max(0, y0); xe, ye = min(W, x0 + w), min(H, y0 + h)
        if xe <= xs or ye <= ys:
            return None
        sa = a[ys - y0:ye - y0, xs - x0:xe - x0]; srgb = rgb[ys - y0:ye - y0, xs - x0:xe - x0]
        sh = np.zeros((H, W), np.float32); sh[ys:ye, xs:xe] = sa
        soft = np.roll(np.roll(cv2.GaussianBlur(sh, (0, 0), sblur), shadow[1], 0), shadow[0], 1)
        tight = cv2.GaussianBlur(sh, (0, 0), csig)
        rim = np.clip(cv2.dilate(sh, np.ones((3, 3), np.uint8)) - sh, 0, 1) * line   # separates overlapping pieces
        tight = np.maximum(tight, rim)
        self.img *= (1 - np.clip(sop * soft + contact * tight * (1 - sh), 0, 0.85))[..., None]
        self.img[ys:ye, xs:xe] = self.img[ys:ye, xs:xe] * (1 - sa[..., None]) + srgb * sa[..., None]
        self.wood[ys:ye, xs:xe] = np.maximum(self.wood[ys:ye, xs:xe], sa)
        m = np.zeros((H, W), bool); m[ys:ye, xs:xe] = sa > 0.5
        return m

    def light_falloff(self, ref_mask, gamma=0.6, lo=0.6, hi=1.3, sigma=90):
        lum = cv2.GaussianBlur(cv2.cvtColor(self.plate.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), sigma)
        lm = np.clip((lum / np.median(lum[ref_mask])) ** gamma, lo, hi)
        k = cv2.GaussianBlur((self.wood > 0.5).astype(np.float32), (3, 3), 0)[..., None]
        self.img = self.img * (1 - k) + self.img * lm[..., None] * k


# ---------- target colour --------------------------------------------------------------------
def load_target(path):
    t = json.load(open(path))
    return np.array(t['L']), np.array(t['a_of_L']), np.array(t['b_of_L'])


def apply_target_colour(img, wood_alpha, target, region=None, LM=-4.0, CK=0.25, DA=0.0, DB=0.0):
    """Re-map product pixels: L standardised to the target mean/std (+LM), a/b from the target's
    brightness->chroma regression, keeping a fraction CK of each pixel's own chroma variation."""
    RL, RA, RB = target
    lab = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    wm = wood_alpha > 0.5
    if region is not None:
        wm &= region
    mu, sd = lab[..., 0][wm].mean(), lab[..., 0][wm].std()
    Ln = (lab[..., 0] - mu) * (RL[1] / sd) + RL[0] + LM
    an = DA + np.polyval(RA, Ln) + (lab[..., 1] - lab[..., 1][wm].mean()) * CK
    bn = DB + np.polyval(RB, Ln) + (lab[..., 2] - lab[..., 2][wm].mean()) * CK
    nb = cv2.cvtColor(np.clip(np.dstack([Ln, an, bn]), 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    kw = cv2.GaussianBlur(wood_alpha, (3, 3), 0)[..., None]
    return img * (1 - kw) + nb * kw
