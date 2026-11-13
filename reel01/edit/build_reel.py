"""Reel 01 builder (deterministic, frame-indexed => seek-safe).
usage: python build_reel.py out.mp4 [--clean] [--audio voice.wav] [--clips]   (default: preview from stills)
Timeline = measured on the real VO (reel01/audio/voice_over.mp3, 45.6 s, 19 phrases) + ending hold to 47.0 s.
Scene sources: approved stills with LOCAL_STILL_MOTION (preview) or Kling clips in reel01/clips/<scene>.mp4 (--clips).
Review crops are the genuine WhatsApp PNGs (never redrawn); R01B packaging message revealed by a rectangular mask."""
import cv2, numpy as np, subprocess, sys, os, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = '/home/user/canva21/reel01/'
FONT = '/home/user/canva21/oud-fix5/fonts/Almarai-ExtraBold.ttf'
LOGOS = '/home/user/canva21/.claude/skills/product-ad-fidelity/assets/'
import json as _json
PZ = _json.load(open('/home/user/canva21/reel01/audio/vo_pauses.json'))['pauses_added']   # [(pos_in_original_vo, seconds)]
def M(t):    # original-VO time -> paced time (pauses inserted at the gap midpoints)
    return t + sum(d for p, d in PZ if p < t - 1e-6)
def CUT(t):  # a cut at a gap midpoint lands in the middle of the lengthened pause
    return M(t) + sum(d / 2 for p, d in PZ if abs(p - t) < 0.06)
def EXT(t):  # a caption that ends just before a pause stays on through it
    return M(t) + sum(d for p, d in PZ if t - 1e-6 <= p < t + 0.12)
W, H, FPS = 1080, 1920, 30
END = round(M(45.65) + 1.40, 2)      # last word + natural ending hold
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

# ---------------- scenes (cut points = middle of the measured VO pauses) ----------------
SC = [  # id, start, end, source still, motion(u 0..1) -> (scale, cx, cy, dx, dy)
 ('S01', 0.00, 2.03, 'plate', None),
 ('S02', 2.03, 6.03, 's02_close', lambda u: (1.04 + 0.06 * u, 540, 1150, -40 + 80 * u, 0)),       # lateral slide
 ('S03', 6.03, 10.65, 'plate', None),
 ('S04', 10.65, 16.83, 'plate', None),
 ('S05', 16.83, 19.00, 'plate', None),
 ('S06', 19.00, 21.84, 's06_high3', lambda u: (1.14 - 0.12 * eo(u), 560, 960, 0, 0)),            # pull-back (final: local)
 ('S07', 21.84, 28.26, 's07_low3', lambda u: (1.08 + 0.03 * u, 540, 1300, 50 - 100 * u, 0)),     # lateral
 ('S08', 28.26, 33.39, 's08_flatlay', lambda u: (1.10 + 0.04 * u, 540, 900, 0, 60 - 120 * u)),   # overhead slide (final: local)
 ('S09', 33.39, 36.27, 's09_bagstill', lambda u: (1.02 + 0.09 * ss(u), 470, 1150, 0, 0)),   # client: Kling take rejected (bag turned) -> approved still, straight push-in, smoke removed
 ('S10', 36.27, 41.05, 's10_offer', lambda u: (1.02 + 0.04 * u, 540, 1250, 0, 0)),
 ('S11', 41.05, END, 's11_close_hero', lambda u: (1.02 + 0.05 * eo(min(u * 1.25, 1)), 560, 1300, 0, 0)),
]
SC = [(sid, CUT(a), (END if b >= 46 else CUT(b)), src, mv) for sid, a, b, src, mv in SC]
LOCAL_FINAL = {'S06', 'S08', 'S09'}   # stay as local still motion in the final

def lift(f, strength=1.0):   # ad-5 product light lift, weighted to the lower frame
    x = f.astype(np.float32) / 255; L = 0.299 * x[..., 2] + 0.587 * x[..., 1] + 0.114 * x[..., 0] + 1e-4
    gain = np.clip(np.power(L, 0.80) / L, 1, 1.5); m = np.clip((np.arange(H) / H - 0.30) / 0.30, 0, 1); m = m * m * (3 - 2 * m)
    gain = 1 + (gain - 1) * m[:, None] * strength; y = x * gain[..., None]; g = y.mean(2, keepdims=True); y = g + (y - g) * 1.05
    return np.clip(y * 255, 0, 255).astype(np.uint8)
def cover(im):
    h, w = im.shape[:2]; s = max(W / w, H / h); im = cv2.resize(im, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LANCZOS4)
    y0 = (im.shape[0] - H) // 2; x0 = (im.shape[1] - W) // 2; return im[y0:y0 + H, x0:x0 + W]
STILL = {}
for _, _, _, src, _ in SC:
    if src != 'plate' and src not in STILL: STILL[src] = lift(cover(cv2.imread(R + 'images/' + src + '_final.png')))
room = cover(cv2.imread(R + 'references/room_master_new_majlis.jpg'))
plate_src = cover(cv2.imread(R + 'images/review_plate_mabkhara_centered.png'))   # same majlis + gold mabkhara on the table (client)
PLATE = (cv2.GaussianBlur(plate_src, (0, 0), 2.2).astype(np.float32) * 0.80).astype(np.uint8)
CLIPS = {}
if USE_CLIPS:
    for sid, a, b, src, mv in SC:
        p = R + f'clips/{sid}.mp4'
        if os.path.exists(p) and sid not in LOCAL_FINAL:
            c = cv2.VideoCapture(p); fr = []
            while True:
                ok, im = c.read()
                if not ok: break
                fr.append(lift(cover(im)))
            CLIPS[sid] = fr
def warp(im, s, cx, cy, dx, dy):
    M = np.float32([[s, 0, cx - s * cx + dx], [0, s, cy - s * cy + dy]]); return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
def base_frame(t):
    sid, a, b, src, mv = [s for s in SC if s[1] <= t + 1e-6 < s[2] + 1e-6][0]; u = (t - a) / (b - a)
    if src == 'plate': s = 1.02 + 0.03 * ((t - 0) / 19.0); return warp(PLATE, s, 540, 960, 0, 0), sid
    if sid in CLIPS:   # real Kling frames, 24 -> 30 by frame picking, no synthesis
        fr = CLIPS[sid]; k = min(int((t - a) * 24), len(fr) - 1); return fr[k], sid
    s, cx, cy, dx, dy = mv(u); return warp(STILL[src], s, cx, cy, dx, dy), sid

# ---------------- genuine review cards ----------------
def card(path, width):
    x = cv2.imread(path); h, w = x.shape[:2]; sc = width / w
    x = cv2.resize(x, (width, int(round(h * sc))), interpolation=cv2.INTER_LANCZOS4)
    x = cv2.cvtColor(x, cv2.COLOR_BGR2RGB).astype(np.float32); bl = cv2.GaussianBlur(x, (0, 0), 1.0); x = np.clip(x + 0.35 * (x - bl), 0, 255)
    hh, ww = x.shape[:2]; P = 30; out = np.zeros((hh + 2 * P, ww + 2 * P, 4), np.float32)
    sh = np.zeros(out.shape[:2], np.float32); sh[P + 8:P + hh + 8, P:P + ww] = 1; out[..., 3] = cv2.GaussianBlur(sh, (0, 0), 12) * 0.45 * 255
    out[P:P + hh, P:P + ww, :3] = x; out[P:P + hh, P:P + ww, 3] = 255
    return out.astype(np.uint8), P, hh
CW = 900
REV = {'R01A': card(R + 'reviews/01A_expectation_whatsapp.png', CW), 'R01B': card(R + 'reviews/01B_result_whatsapp.png', CW),
       'R02': card(R + 'reviews/02_quality_whatsapp.png', CW), 'R03': card(R + 'reviews/03_fragrance_whatsapp.png', CW)}
R01B_SPLIT = int(round(108 / 220 * REV['R01B'][2]))      # packaging message starts at native row ~108
RCY = 820                                                # vertical centre of the evidence card
RS = [('R01A', 0.00, 2.03, None), ('R01B', 6.03, 10.65, 8.84), ('R02', 10.65, 16.83, None), ('R03', 16.83, 19.00, None)]
RS = [(k, CUT(a), CUT(b), (M(rv) if rv else None)) for k, a, b, rv in RS]
def draw_review(fr, t):
    for k, a, b, reveal in RS:
        if not (a <= t < b): continue
        im, P, hh = REV[k]; q = (t - a) / 0.32; al = ss(q * 1.4) if a > 0 else 1.0; dy = (1 - eo(q)) * 26 if a > 0 else 0
        y = int(RCY - (im.shape[0]) / 2 + dy); x = int(W / 2 - im.shape[1] / 2)
        if reveal is not None:     # rectangular reveal of the lower (packaging) message, stable scale/position
            r = ss((t - reveal + 0.05) / 0.40); vis = int(P + R01B_SPLIT + (hh - R01B_SPLIT) * r)
            m = im.copy(); m[vis:, :, 3] = 0
            if r > 0: m[P + hh:P + hh + 30, :, 3] = (im[P + hh:P + hh + 30, :, 3] * r).astype(np.uint8)
            im = m
        paste(fr, im, x, y, al)

# ---------------- captions (Section-3 words; quotes gold, narrator white) ----------------
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
# (start, end, [(text, t_on, colour, centre_y)])  -- client: no caption while a WhatsApp screenshot is being read (it is already on screen)
CAP = [
 (2.40, 5.95, [('هذا كلام عميل بعد تجربته', 2.40, WHITE, 335), ('للتايقر من بيتهوفن', 4.27, GOLD, 447)]),   # words as actually spoken in the VO
 (10.97, 13.45, [('ومن رسايل عملائنا بعد التجربة:', 10.97, WHITE, 1430)]),
 (19.05, 21.76, [('والحين،', 19.05, WHITE, 335), ('التايقر يجيك بهالعرض:', 20.13, GOLD, 447)]),
 (22.17, 26.02, [('اطلب ثلاث أَوْقِيَّات', 22.17, WHITE, 335), ('من عود التايقر الفيتنامي درجة أولى،', 23.45, GOLD, 447)]),
 (26.23, 28.18, [('وخذ ثلاث أَوْقِيَّات هدية.', 26.23, GOLD, 335)]),
 (28.56, 33.31, [('ومعها مبخرة خشبية،', 28.56, WHITE, 1395), ('وأعواد موروكي،', 30.59, GOLD, 1505), ('وهدية سرّية.', 32.08, GOLD, 1615)]),
 (33.70, 36.19, [('كلها تجيك في', 33.70, WHITE, 335), ('كيس بيتهوفن الفاخر،', 34.67, GOLD, 447)]),
 (36.56, 37.98, [('والشحن مجّانًا.', 36.56, GOLD, 335)]),
 (38.21, 40.97, [('والدفع متوفر', 38.21, WHITE, 335), ('عن طريق تابي أو تمارا.', 39.10, GOLD, 447)]),
 (41.38, 99, [('اطلب التايقر الحين…', 41.38, WHITE, 335), ('ومن أول تبخيرة بتعرف ليه يمدحونه.', 43.19, GOLD, 447)]),
]
CAP = [(M(st), (99 if en > 90 else EXT(en)), [(tx, M(ton), col, cy) for tx, ton, col, cy in lines]) for st, en, lines in CAP]
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

# ---------------- offer graphics (script wording only) ----------------
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
def load_rgba(p, size):
    x = cv2.cvtColor(cv2.imread(p, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA); a = x[..., 3].astype(np.float32)
    a = cv2.erode(a, np.ones((5, 5), np.uint8)); x[..., 3] = cv2.GaussianBlur(a, (3, 3), 0).astype(np.uint8); return cv2.resize(x, size, interpolation=cv2.INTER_AREA)
TABBY, TAMARA = load_rgba(LOGOS + 'logo_tabby.png', (340, 132)), load_rgba(LOGOS + 'logo_tamara.png', (340, 133))
def pop_in(fr, im, cx, cy, t0, t, t1=99, s0=0.35):
    if t < t0 or t > t1: return
    k = (t - t0) / 0.40; a = ss(k * 2.2) * (1 - ss((t - (t1 - 0.15)) / 0.15)) if t1 < 90 else ss(k * 2.2)
    h, w = im.shape[:2]; paste(fr, im, int(cx - w / 2), int(cy - h / 2), a, s0 + (1 - s0) * ease_back(k))
def draw_graphics(fr, t):
    a, b, g = M(22.5), EXT(28.18), M(27.45)
    if a <= t <= b:    # buy three -> receive three
        mv = ss((t - g) / 0.35); pop_in(fr, P1, 540 + 200 * mv, 620, a, t, b)
        pop_in(fr, P2, 330, 620, g, t, b)
    pop_in(fr, TABBY, 735, 590, M(39.50), t, EXT(40.97)); pop_in(fr, TAMARA, 345, 590, M(40.00), t, EXT(40.97))
    pop_in(fr, CTA, 540, 610, M(41.70), t)

# ---------------- render ----------------
N = int(round(END * FPS))
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-af', f'apad=whole_dur={END}', '-t', str(END), '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; base, sid = base_frame(t)
    fr = cv2.cvtColor(base, cv2.COLOR_BGR2RGB).astype(np.float32)
    draw_review(fr, t)                 # evidence layer stays in the clean version too
    if not CLEAN: draw_captions(fr, t); draw_graphics(fr, t)
    enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('frames', N)
