"""Reel 02 builder (deterministic, frame-indexed). Helpers (captions, pills, gift badge, logos, review cards, lift)
copied from reel01/edit/build_reel.py (read-only source).
usage: python reel02/edit/build_reel.py out.mp4 [--clean] [--audio file.wav] [--clips]
Timeline = measured on the NEW VO (reel02/audio/voice_over.mp3, 48.01 s, 19 phrases) + 0.8 s pause for the customer photo
card (reel02/audio/vo_pauses.json) + ending hold. Every scene cut sits in the middle of a real pause."""
import cv2, numpy as np, subprocess, sys, os, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = '/home/user/canva21/reel02/'
FONT = '/home/user/canva21/oud-fix5/fonts/Almarai-ExtraBold.ttf'
LOGOS = '/home/user/canva21/.claude/skills/product-ad-fidelity/assets/'
PZ = json.load(open(R + 'audio/vo_pauses.json'))['pauses_added']
def M(t): return t + sum(d for p, d in PZ if p < t - 1e-6)            # original-VO time -> paced time
W, H, FPS = 1080, 1920, 30
END = round(M(47.66) + 1.30, 2)
args = sys.argv[1:]; OUT = args[0]; CLEAN = '--clean' in args; USE_CLIPS = '--clips' in args
AUDIO = args[args.index('--audio') + 1] if '--audio' in args else R + 'audio/vo_paced.wav'
def FA(s): return ImageFont.truetype(FONT, s, layout_engine=ImageFont.Layout.RAQM)
def ss(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def eo(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_back(t):
    c1 = 1.70158; c3 = c1 + 1; t = min(max(t, 0), 1); return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def paste(canvas, rgba, x, y, alpha=1.0, scale=1.0):
    if alpha <= 0.003: return
    im = rgba
    if abs(scale - 1) > 1e-3:
        h, w = im.shape[:2]; nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        im = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LINEAR); x = int(round(x + (w - nw) / 2)); y = int(round(y + (h - nh) / 2))
    h, w = im.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = im[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32); a = s[..., 3:] / 255. * alpha
    canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a


def lift(f, strength=1.0):   # ad-5 product light lift, weighted to the lower frame
    x = f.astype(np.float32) / 255; L = 0.299 * x[..., 2] + 0.587 * x[..., 1] + 0.114 * x[..., 0] + 1e-4
    gain = np.clip(np.power(L, 0.80) / L, 1, 1.5); m = np.clip((np.arange(H) / H - 0.30) / 0.30, 0, 1); m = m * m * (3 - 2 * m)
    gain = 1 + (gain - 1) * m[:, None] * strength; y = x * gain[..., None]; g = y.mean(2, keepdims=True); y = g + (y - g) * 1.05
    return np.clip(y * 255, 0, 255).astype(np.uint8)
def cover(im):
    h, w = im.shape[:2]; s = max(W / w, H / h); im = cv2.resize(im, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LANCZOS4)
    y0 = (im.shape[0] - H) // 2; x0 = (im.shape[1] - W) // 2; return im[y0:y0 + H, x0:x0 + W]

def card(path, width):
    x = cv2.imread(path); h, w = x.shape[:2]; sc = width / w
    x = cv2.resize(x, (width, int(round(h * sc))), interpolation=cv2.INTER_LANCZOS4)
    x = cv2.cvtColor(x, cv2.COLOR_BGR2RGB).astype(np.float32); bl = cv2.GaussianBlur(x, (0, 0), 1.0); x = np.clip(x + 0.35 * (x - bl), 0, 255)
    hh, ww = x.shape[:2]; P = 30; out = np.zeros((hh + 2 * P, ww + 2 * P, 4), np.float32)
    sh = np.zeros(out.shape[:2], np.float32); sh[P + 8:P + hh + 8, P:P + ww] = 1; out[..., 3] = cv2.GaussianBlur(sh, (0, 0), 12) * 0.45 * 255
    out[P:P + hh, P:P + ww, :3] = x; out[P:P + hh, P:P + ww, 3] = 255
    return out.astype(np.uint8), P, hh

WT, WB, GT, GB = (250, 247, 240), (232, 226, 214), (246, 222, 168), (206, 160, 92)
F1, F2 = FA(74), FA(78)
def grad_text(word, font, ct, cb):
    l, t, r, b = font.getbbox(word, direction='rtl', anchor='ls'); pad = 24; w, h = int(r - l) + 2 * pad, b - t + 2 * pad
    mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).text((pad - l, pad - t), word, font=font, fill=255, direction='rtl', anchor='ls')
    g = np.linspace(0, 1, h)[:, None, None]; col = (np.array(ct) * (1 - g) + np.array(cb) * g) * np.ones((h, w, 1))
    img = Image.fromarray(np.dstack([col, np.array(mask)]).astype(np.uint8), 'RGBA')
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); sh.putalpha(mask.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.65)))
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0)); base.alpha_composite(sh, (0, 3)); base.alpha_composite(img); return np.array(base), (-l + pad, -t + pad)
def line_img(text, font, ct, cb, maxw=940):
    while font.getlength(text, direction='rtl') > maxw: font = FA(font.size - 2)
    return grad_text(text, font, ct, cb)
WHITE, GOLD = (WT, WB), (GT, GB)

def pill(text, fs=60):
    f = FA(fs); tw = f.getlength(text, direction='rtl'); bw, bh = int(tw + 100), int(fs * 1.7); S = 3
    img = Image.new('RGBA', (bw * S, bh * S), (0, 0, 0, 0)); g = np.linspace(0, 1, bh * S)[:, None, None]; col = np.array(GT) * (1 - g) + np.array(GB) * g
    m = Image.new('L', (bw * S, bh * S), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bw * S - 1, bh * S - 1), radius=bh * S // 2, fill=255)
    img.alpha_composite(Image.fromarray(np.dstack([col * np.ones((1, bw * S, 1)), np.array(m)]).astype(np.uint8), 'RGBA'))
    d = ImageDraw.Draw(img); f3 = FA(fs * S); l, tp, r, b = f3.getbbox(text, direction='rtl')
    d.text(((bw * S - (r - l)) / 2 - l, (bh * S - (b - tp)) / 2 - tp), text, font=f3, fill=(58, 30, 14, 255), direction='rtl')
    img = img.resize((bw, bh), Image.LANCZOS); out = Image.new('RGBA', (bw + 60, bh + 60), (0, 0, 0, 0)); sh = Image.new('L', (bw + 60, bh + 60), 0)
    ImageDraw.Draw(sh).rounded_rectangle((30, 38, 30 + bw, 38 + bh), radius=bh // 2, fill=150); sh = sh.filter(ImageFilter.GaussianBlur(12))
    shimg = Image.new('RGBA', (bw + 60, bh + 60), (0, 0, 0, 255)); shimg.putalpha(sh); out.alpha_composite(shimg); out.alpha_composite(img, (30, 30)); return np.array(out)
P1, P2, CTA = pill('٣ أَوْقِيَّات'), pill('+ ٣ هدية'), pill('اطلب الآن', 64)

def gift_badge(bw=560, bh=190):   # secret gift: burgundy card, gold gift icon + "هدية سرّية" (contents stay undisclosed)
    S = 3; img = Image.new('RGBA', (bw * S, bh * S), (0, 0, 0, 0))
    g = np.linspace(0, 1, bh * S)[:, None, None]; col = np.array([128, 26, 42]) * (1 - g) + np.array([66, 10, 20]) * g
    m = Image.new('L', (bw * S, bh * S), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bw * S - 1, bh * S - 1), radius=30 * S, fill=255)
    img.alpha_composite(Image.fromarray(np.dstack([col * np.ones((1, bw * S, 1)), np.array(m)]).astype(np.uint8), 'RGBA'))
    d = ImageDraw.Draw(img); d.rounded_rectangle((4 * S, 4 * S, bw * S - 5 * S, bh * S - 5 * S), radius=27 * S, outline=(226, 188, 118, 255), width=3 * S)
    gold, gold2, rib = (232, 196, 126, 255), (196, 150, 78, 255), (128, 26, 42, 255)
    gx, gy, gw = (bw - 150) * S, 42 * S, 104 * S                       # gift icon on the right (RTL reading starts there)
    d.rounded_rectangle((gx, gy + 34 * S, gx + gw, gy + gw + 6 * S), radius=7 * S, fill=gold2)
    d.rounded_rectangle((gx - 7 * S, gy + 18 * S, gx + gw + 7 * S, gy + 42 * S), radius=7 * S, fill=gold)
    d.rectangle((gx + gw / 2 - 9 * S, gy + 18 * S, gx + gw / 2 + 9 * S, gy + gw + 6 * S), fill=rib)
    d.ellipse((gx + gw / 2 - 40 * S, gy - 8 * S, gx + gw / 2 - 2 * S, gy + 22 * S), outline=gold, width=9 * S)
    d.ellipse((gx + gw / 2 + 2 * S, gy - 8 * S, gx + gw / 2 + 40 * S, gy + 22 * S), outline=gold, width=9 * S)
    d.ellipse((gx + gw / 2 - 10 * S, gy + 3 * S, gx + gw / 2 + 10 * S, gy + 23 * S), fill=gold)
    d.line(((bw - 182) * S, 32 * S, (bw - 182) * S, (bh - 32) * S), fill=(226, 188, 118, 150), width=2 * S)
    f3 = FA(70 * S); txt = 'هدية سرّية'; l, tp, r, b = f3.getbbox(txt, direction='rtl'); area = (bw - 190) * S
    tw = Image.new('L', (bw * S, bh * S), 0); ImageDraw.Draw(tw).text(((area - (r - l)) / 2 - l + 8 * S, (bh * S - (b - tp)) / 2 - tp), txt, font=f3, fill=255, direction='rtl')
    gg = np.linspace(0, 1, bh * S)[:, None, None]; tc = np.array(GT) * (1 - gg) + np.array(GB) * gg
    img.alpha_composite(Image.fromarray(np.dstack([tc * np.ones((1, bw * S, 1)), np.array(tw)]).astype(np.uint8), 'RGBA'))
    img = img.resize((bw, bh), Image.LANCZOS); out = Image.new('RGBA', (bw + 60, bh + 60), (0, 0, 0, 0)); sh = Image.new('L', (bw + 60, bh + 60), 0)
    ImageDraw.Draw(sh).rounded_rectangle((30, 40, 30 + bw, 40 + bh), radius=30, fill=160); sh = sh.filter(ImageFilter.GaussianBlur(14))
    shimg = Image.new('RGBA', (bw + 60, bh + 60), (0, 0, 0, 255)); shimg.putalpha(sh); out.alpha_composite(shimg); out.alpha_composite(img, (30, 30)); return np.array(out)
GIFT = gift_badge()

def load_rgba(p, size):
    x = cv2.cvtColor(cv2.imread(p, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA); a = x[..., 3].astype(np.float32)
    a = cv2.erode(a, np.ones((5, 5), np.uint8)); x[..., 3] = cv2.GaussianBlur(a, (3, 3), 0).astype(np.uint8); return cv2.resize(x, size, interpolation=cv2.INTER_AREA)
TABBY, TAMARA = load_rgba(LOGOS + 'logo_tabby.png', (340, 132)), load_rgba(LOGOS + 'logo_tamara.png', (340, 133))
def pop_in(fr, im, cx, cy, t0, t, t1=99, s0=0.35):
    if t < t0 or t > t1: return
    k = (t - t0) / 0.40; a = ss(k * 2.2) * (1 - ss((t - (t1 - 0.15)) / 0.15)) if t1 < 90 else ss(k * 2.2)
    h, w = im.shape[:2]; paste(fr, im, int(cx - w / 2), int(cy - h / 2), a, s0 + (1 - s0) * ease_back(k))

def cover(im):
    h, w = im.shape[:2]; s = max(W / w, H / h); im = cv2.resize(im, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LANCZOS4)
    y0 = (im.shape[0] - H) // 2; x0 = (im.shape[1] - W) // 2; return im[y0:y0 + H, x0:x0 + W]
def warp(im, s, cx, cy, dx, dy):
    Mx = np.float32([[s, 0, cx - s * cx + dx], [0, s, cy - s * cy + dy]]); return cv2.warpAffine(im, Mx, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)

# ---------------- scenes: cuts at the middle of measured VO pauses (original-VO seconds, mapped with M) ----------------
LIFT = 0.5
SC = [  # id, start, end, still, kling clip or None, local motion u->(scale,cx,cy,dx,dy)
 ('S01', 0.00, 2.33, 'p01', None, lambda u: (1.00 + 0.06 * ss(u), 540, 1380, 0, 0)),             # presentation detail, restrained push
 ('S02', 2.33, 5.08, 'p02', 'S02', None),                                                            # mabkhara, live smoke (Kling)
 ('S03', 5.08, 10.00, 'p03', None, lambda u: (1.08 + 0.02 * u, 600, 1500, 45 - 90 * ss(u), 0)),   # Kling take REJECTED (box turned) -> local lateral slide
 ('S04', 10.00, 14.53, 'p04', None, lambda u: (1.00 + 0.07 * ss(u), 560, 1250, 0, 0)),             # confidence: slow push-in
 ('S05', 14.53, 'R2A_END', 'plate', None, None),                                                     # R2A on the plate
 ('S06', 'R2A_END', 22.73, 'plate', None, None),                                                     # photo card, then R2B4
 ('S07', 22.73, 25.58, 'p04', None, lambda u: (1.10 - 0.08 * eo(u), 560, 1250, 0, 0)),             # offer bridge: local pull-back
 ('S08', 25.58, 30.17, 'p05', 'S08', None),                                                          # quantity hero (Kling)
 ('S09', 30.17, 34.96, 'p06', None, lambda u: (1.08 + 0.02 * u, 540, 960, 0, 50 - 100 * u)),       # overhead slide
 ('S10', 34.96, 37.80, 'p07', None, lambda u: (1.00 + 0.07 * ss(u), 470, 1250, 0, 0)),             # bag: straight push, bag never turns
 ('S11', 37.80, 43.18, 'p08', 'S11', None),                                                          # full offer, smoke (Kling)
 ('S12', 43.18, 99, 'p09', 'S12', None),                                                             # closing, pull-back (Kling)
]
R2A_END = 16.55                               # R2A holds past its last word (16.33), then the photo card takes the 1.6 s pause
PHOTO_IN, R2B_IN = R2A_END, M(17.16) - 0.12   # photo card 1.25 s, R2B4 enters just before «ما شاء الله»
def tm(x): return R2A_END if x == 'R2A_END' else (END if x >= 90 else M(x))
SC = [(sid, tm(a), tm(b), st, cl, mv) for sid, a, b, st, cl, mv in SC]
STILL = {}
for _, _, _, st, _, _ in SC:
    if st != 'plate' and st not in STILL: STILL[st] = lift(cover(cv2.imread(R + 'images/' + st + '_final.png')), LIFT)
plate_src = cover(cv2.imread(R + 'images/plate_final.png'))
PLATE = (cv2.GaussianBlur(plate_src, (0, 0), 1.4).astype(np.float32) * 0.86).astype(np.uint8)   # cards read clearly, mabkhara stays visible
CLIPS = {}
if USE_CLIPS:
    for sid, a, b, st, cl, mv in SC:
        if cl and os.path.exists(R + f'clips/{cl}.mp4'):
            c = cv2.VideoCapture(R + f'clips/{cl}.mp4'); src_fps = c.get(cv2.CAP_PROP_FPS) or 24; fr = []
            while True:
                ok, im = c.read()
                if not ok: break
                fr.append(lift(cover(im), LIFT))
            CLIPS[sid] = (fr, src_fps)
CLIP_POST = {'S12': lambda k, n: (1.0 + 0.26 * k / n, 540, 972)}   # S12: counter-zoom hides the coffered ceiling + marble floor Kling invented at the end of the pull-back
def base_frame(t):
    sid, a, b, st, cl, mv = [s for s in SC if s[1] <= t + 1e-6 < s[2] + 1e-6][0]; u = (t - a) / max(1e-6, b - a)
    if st == 'plate':
        s = 1.02 + 0.04 * ((t - M(14.53)) / (M(22.73) - M(14.53))); return warp(PLATE, s, 540, 1000, 0, 0), sid
    if sid in CLIPS:   # real Kling frames; source fps -> 30 by frame picking (real time kept, no synthesis)
        fr, sf = CLIPS[sid]; k = min(int((t - a) * sf), len(fr) - 1)
        if sid in CLIP_POST: sc, cx, cy = CLIP_POST[sid](k, len(fr)); return warp(fr[k], sc, cx, cy, 0, 0), sid
        return fr[k], sid
    if mv is None: return STILL[st], sid           # preview without clips: still frame
    s, cx, cy, dx, dy = mv(u); return warp(STILL[st], s, cx, cy, dx, dy), sid

# ---------------- genuine review cards (never retyped) ----------------
RV = R + 'references/reviews/'
REV = {'R2A': card(RV + '01_repeat_request_whatsapp.png', 900), 'PHOTO': card(RV + '06_photo_and_scent_whatsapp.png', 640),
       'R2B4': card(RV + '05_praise_and_reorder_whatsapp.png', 900)}
R2B4_SPLIT = int(round(72 / 139 * REV['R2B4'][2]))   # «وابي اطلب» bubble starts below native row ~72
RS = [('R2A', M(14.53), R2A_END, None, 820), ('PHOTO', PHOTO_IN, R2B_IN, None, 640), ('R2B4', R2B_IN, M(22.73), M(21.60) - 0.06, 820)]
def draw_review(fr, t):
    for k, a, b, reveal, cy in RS:
        if not (a <= t < b): continue
        im, P, hh = REV[k]; q = (t - a) / 0.32; al = ss(q * 1.4); dy = (1 - eo(q)) * 26
        y = int(cy - im.shape[0] / 2 + dy); x = int(W / 2 - im.shape[1] / 2)
        if reveal is not None:     # clean rectangular reveal of the lower request; same scale/position
            r = ss((t - reveal) / 0.40); vis = int(P + R2B4_SPLIT + (hh - R2B4_SPLIT) * r)
            m = im.copy(); m[vis:, :, 3] = 0
            if r > 0: m[P + hh:P + hh + 30, :, 3] = (im[P + hh:P + hh + 30, :, 3] * r).astype(np.uint8)
            im = m
        paste(fr, im, x, y, al)

# ---------------- captions: the words actually spoken (client: «خذه»; «من عود التايقر…» not in the VO) ----------------
TOP1, TOP2 = 335, 447
CAP = [
 (0.05, 2.33, [('فخامة تبدا من التقديم…', 0.05, WHITE, TOP1)]),
 (2.64, 5.08, [('وتكمل مع أول تبخيرة.', 2.64, GOLD, 1580)]),          # P02 smoke rises through the top: caption below the burner
 (5.56, 10.00, [('تايقر فيتنامي درجة أولى من بيتهوفن،', 5.56, WHITE, TOP1), ('يليق بذوقك.', 8.72, GOLD, TOP2)]),
 (10.37, 14.53, [('واثقين إن طلبك الأول…', 10.37, WHITE, TOP1), ('ما بيكون الأخير.', 12.89, GOLD, TOP2)]),
 (23.18, 25.58, [('والحين،', 23.18, WHITE, TOP1), ('خذه بهالعرض:', 24.53, GOLD, TOP2)]),
 (25.92, 30.17, [('اطلب ثلاث أَوْقِيَّات', 25.92, WHITE, TOP1), ('وخذ ثلاث أَوْقِيَّات هدية.', 28.20, GOLD, TOP2)]),
 (30.39, 34.96, [('ومعها مبخرة خشبية،', 30.39, WHITE, 230), ('وأعواد موروكي،', 32.22, GOLD, 342), ('وهدية سرّية.', 33.71, GOLD, 454)]),
 (35.21, 37.80, [('كلّها تجيك في', 35.21, WHITE, TOP1), ('كيس بيتهوفن الفاخر،', 36.15, GOLD, TOP2)]),
 (38.21, 39.95, [('والشحن مجّانًا.', 38.21, GOLD, TOP1)]),
 (40.12, 43.18, [('والدفع متوفر', 40.12, WHITE, TOP1), ('عن طريق تابي أو تمارا.', 41.08, GOLD, TOP2)]),
 (43.71, 99, [('اطلب عرض التايقر الحين…', 43.71, WHITE, TOP1), ('واستقبل ضيوفك بطيب يشرّفك.', 45.79, GOLD, TOP2)]),
]
CAP = [(M(st), (99 if en > 90 else M(en)), [(tx, M(ton), col, cy) for tx, ton, col, cy in lines]) for st, en, lines in CAP]
CAPI = []
for st, en, lines in CAP:
    items = []
    for text, ton, col, cy in lines:
        font = F1 if col is WHITE else F2; im, (ox, oy) = line_img(text, font, *col)
        items.append((ton, im, int(W / 2 - im.shape[1] / 2), int(cy - im.shape[0] / 2)))
    ys = [cy for _, _, _, cy in lines]; top, bot = min(ys) - 60, max(ys) + 60
    wmax = max(i[1].shape[1] for i in items) - 48; bw = min(1080, int(wmax + 300)); bh = bot - top + 150
    m = Image.new('L', (bw, bh), 0); ImageDraw.Draw(m).rounded_rectangle((100, 60, bw - 100, bh - 60), radius=60, fill=255)
    a = np.array(m.filter(ImageFilter.GaussianBlur(45))).astype(np.float32) * 0.50
    CAPI.append((st, en, items, (np.dstack([np.zeros((bh, bw, 3)), a]).astype(np.uint8), int(W / 2 - bw / 2), top - 75)))
def draw_captions(fr, t):
    for st, en, items, (bd, bx, by) in CAPI:
        if not (st - 0.05 <= t <= en): continue
        ga = ss((t - st) / 0.22) * (1 - ss((t - (en - 0.16)) / 0.16)) if en < 90 else ss((t - st) / 0.22)
        paste(fr, bd, bx, by, ga)
        for ton, im, x, y in items:
            a = ss((t - ton) / 0.22)
            if a > 0: paste(fr, im, x, int(y + (1 - a) * 14), a * ga)

def draw_graphics(fr, t):
    a, b, g = M(26.35), M(30.17) - 0.02, M(28.55)
    if a <= t <= b:    # buy three -> receive three
        mv = ss((t - g) / 0.35); pop_in(fr, P1, 540 + 200 * mv, 640, a, t, b)
        pop_in(fr, P2, 330, 640, g, t, b)
    TB, TM = M(41.30), M(41.85)
    pop_in(fr, TABBY, 735, 640, TB, t, M(43.18) - 0.02); pop_in(fr, TAMARA, 345, 640, TM, t, M(43.18) - 0.02)
    pop_in(fr, CTA, 540, 620, M(43.95), t)
    pop_in(fr, GIFT, 540, 1720, M(33.75), t, M(34.96) - 0.02, s0=0.25)   # secret gift badge with the word, clear space under the gifts
POPS = {'R2A': M(14.53), 'PHOTO': PHOTO_IN, 'R2B4': R2B_IN, 'reveal': M(21.60) - 0.06, 'P1': M(26.35), 'P2': M(28.55),
        'gift': M(33.75), 'tabby': M(41.30), 'tamara': M(41.85), 'cta': M(43.95)}
if __name__ == '__main__' and '--pops' in args:
    json.dump({k: round(v, 3) for k, v in POPS.items()}, open(R + 'audio/pop_times.json', 'w'), indent=1); print(POPS, END); sys.exit()

if '--frames' in args:   # QA: dump single frames as PNG
    for tt in map(float, args[args.index('--frames') + 1].split(',')):
        base, sid = base_frame(tt); fr = cv2.cvtColor(base, cv2.COLOR_BGR2RGB).astype(np.float32); draw_review(fr, tt)
        if not CLEAN: draw_captions(fr, tt); draw_graphics(fr, tt)
        cv2.imwrite(OUT.replace('.png', f'_{tt:05.2f}.png'), cv2.cvtColor(np.clip(fr, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    sys.exit()

# ---------------- render ----------------
N = int(round(END * FPS))
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-af', f'apad=whole_dur={END}', '-t', str(END), '-r', str(FPS), '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; base, sid = base_frame(t)
    fr = cv2.cvtColor(base, cv2.COLOR_BGR2RGB).astype(np.float32)
    draw_review(fr, t)                 # evidence stays in the clean version too
    if not CLEAN: draw_captions(fr, t); draw_graphics(fr, t)
    enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('frames', N, 'END', END)
