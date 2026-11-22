"""Kinam GIFT reel builder (from kinam/edit/build_kinam.py) (frame-indexed, real Kling frames 24->30 by frame picking, product light lift).
usage: build_kinam.py out.mp4 --audio mix.wav [--clean]
Timeline = vo/scene_timing.json (cuts at the middle of the VO gaps) ; captions = two-line white + gold, line 2 appears on its word.
Graphics (S8): discount badge on «خصم» (client: no tabby/tamara), pop SFX times written to edit/pop_times.json (used by make_mixes_kinam.py)."""
import cv2, numpy as np, subprocess, sys, json, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
K = '/home/user/canva21/kinam_diff/'; FONT = '/home/user/canva21/oud-fix5/fonts/Almarai-ExtraBold.ttf'; LOGOS = '/home/user/canva21/.claude/skills/product-ad-fidelity/assets/'
W, H, FPS = 1080, 1920, 30
args = sys.argv[1:]; OUT = args[0]; CLEAN = '--clean' in args; AUDIO = args[args.index('--audio') + 1]
SC = json.load(open(K + 'vo/scene_timing.json'))['scenes']; VM = json.load(open(K + 'vo/vo_diff_map.json'))
PH = {p['i']: p for p in VM['phrases']}
END = round(PH[19]['end'] + 1.35, 2); SC[-1]['end'] = END       # hold the final frame with the offer graphics
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
def lift(f, strength=1.0):
    x = f.astype(np.float32) / 255; L = 0.299 * x[..., 2] + 0.587 * x[..., 1] + 0.114 * x[..., 0] + 1e-4
    gain = np.clip(np.power(L, 0.80) / L, 1, 1.5); m = np.clip((np.arange(H) / H - 0.30) / 0.30, 0, 1); m = m * m * (3 - 2 * m)
    gain = 1 + (gain - 1) * m[:, None] * strength; y = x * gain[..., None]; g = y.mean(2, keepdims=True); y = g + (y - g) * 1.05
    return np.clip(y * 255, 0, 255).astype(np.uint8)
def cover(im):
    h, w = im.shape[:2]; s = max(W / w, H / h); im = cv2.resize(im, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y0 = (im.shape[0] - H) // 2; x0 = (im.shape[1] - W) // 2; return im[y0:y0 + H, x0:x0 + W]
CL = {}
G3MASK = None
for sc in SC:
    p = sc['src'] if sc['src'].startswith('/') else K + sc['src']
    if sc['type'] == 'still':
        CL[sc['scene']] = ('still', lift(cover(cv2.imread(p))), sc['zoom'], sc.get('center', (540, 960))); continue
    if p in [v[3] for v in CL.values() if v[0] == 'clip']:
        fr = [v for v in CL.values() if v[0] == 'clip' and v[3] == p][0][1]
    else:
        c = cv2.VideoCapture(p); fr = []
        while True:
            ok, im = c.read()
            if not ok: break
            fr.append(lift(cover(im)))
    CL[sc['scene']] = ('clip', fr, sc['offset'], p)
XF = {}
for sc in SC:
    if sc.get('xfade'): XF[sc['scene']] = lift(cover(cv2.imread(K + sc['xfade']['still'])))
def warp_zoom(im, s, c=(540, 960)):
    cx, cy = c; M = np.float32([[s, 0, cx - s * cx + (540 - cx) * (s - 1) / s * 0 ], [0, s, cy - s * cy]]); return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
def base_frame(t):
    sc = [s for s in SC if s['start'] <= t + 1e-6 < s['end'] + 1e-6][0]; v = CL[sc['scene']]; u = (t - sc['start']) / (sc['end'] - sc['start'])
    if v[0] == 'still':
        z0, z1 = v[2]; return warp_zoom(v[1], z0 + (z1 - z0) * (u * u * (3 - 2 * u)), v[3])
    fr = v[1]; e = t - sc['start']
    if sc.get('segs'):     # cut on action: play the listed source windows back to back (hides a bad middle section)
        for a_, b_ in sc['segs']:
            ln = min(b_, len(fr) / 24) - a_
            if e < ln or (a_, b_) == tuple(sc['segs'][-1]): src_t = a_ + e; break
            e -= ln
    else: src_t = v[2] + e * sc.get('speed', 1.0)
    f = fr[min(int(src_t * 24), len(fr) - 1)]
    if sc.get('xfade'):   # night -> morning: soft dissolve into the aligned day still with a slow push
        x = sc['xfade']; k = min(max((e - x['at']) / x['dur'], 0), 1); k = k * k * (3 - 2 * k)
        if k > 0:
            day = warp_zoom(XF[sc['scene']], 1.0 + 0.03 * max(0, e - x['at']) / 3)
            f = np.clip(f.astype(np.float32) * (1 - k) + day.astype(np.float32) * k, 0, 255).astype(np.uint8)
    if sc.get('push'):   # free local camera move on top of a locked Kling clip
        z0, z1, cx, cy = sc['push']; uu = u * u * (3 - 2 * u); f = warp_zoom(f, z0 + (z1 - z0) * uu, (cx, cy))
    return f

# ---------------- word onset of caption line 2: VO energy dip nearest to the proportional estimate ----------------
w = wave.open(K + 'vo/vo_diff_paced.wav'); SR = w.getframerate(); vx = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
if w.getnchannels() == 2: vx = vx.reshape(-1, 2).mean(1)
hop = int(SR * 0.01); en = np.sqrt((vx[:len(vx) // hop * hop].reshape(-1, hop) ** 2).mean(1)); en = np.convolve(en, np.ones(5) / 5, 'same')
def onset(i, l1, full):
    p = PH[i]; est = p['start'] + (p['end'] - p['start']) * len(l1.replace(' ', '')) / len(full.replace(' ', ''))
    a, b = int((est - 0.30) * 100), int((est + 0.30) * 100); k = a + int(np.argmin(en[a:b])); return round(k / 100 + 0.03, 2)

# ---------------- captions ----------------
WT, WB, GT, GB = (250, 247, 240), (232, 226, 214), (246, 222, 168), (206, 160, 92)
WHITE, GOLD = (WT, WB), (GT, GB); F1, F2 = FA(74), FA(80)
def grad_text(word, font, ct, cb):
    l, t, r, b = font.getbbox(word, direction='rtl', anchor='ls'); pad = 24; w_, h_ = int(r - l) + 2 * pad, b - t + 2 * pad
    mask = Image.new('L', (w_, h_), 0); ImageDraw.Draw(mask).text((pad - l, pad - t), word, font=font, fill=255, direction='rtl', anchor='ls')
    g = np.linspace(0, 1, h_)[:, None, None]; col = (np.array(ct) * (1 - g) + np.array(cb) * g) * np.ones((h_, w_, 1))
    img = Image.fromarray(np.dstack([col, np.array(mask)]).astype(np.uint8), 'RGBA')
    sh = Image.new('RGBA', (w_, h_), (0, 0, 0, 0)); sh.putalpha(mask.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.70)))
    base = Image.new('RGBA', (w_, h_), (0, 0, 0, 0)); base.alpha_composite(sh, (0, 3)); base.alpha_composite(img); return np.array(base)
def line_img(text, font, ct, cb, maxw=940):
    while font.getlength(text, direction='rtl') > maxw: font = FA(font.size - 2)
    return grad_text(text, font, ct, cb)
TOP, HIGH, LOW, LOW2 = (335, 447), (215, 327), (1545, 1657), (1660, 1772)
MID = (560, 672)
CAPS = {1: ('وش يفرق كينام بيتهوفن', 'عن غيره؟', MID), 2: (None, 'قرّب وشوف الكسر', TOP), 3: ('تبان لك عروق الخشب', 'وتدرجات لونه', TOP),
        4: ('وكل كسرة', 'لها شكلها', TOP), 5: ('هذا عود كينام', 'طبيعي', TOP), 6: (None, 'تريبل سوبر', TOP), 7: ('من أفخم اختيارات', 'بيتهوفن', TOP),
        8: ('وعلى الجمر', 'يبان طابع الكينام', TOP), 9: ('مع الحرارة', 'يطلع عبق دهن العود', TOP), 10: ('ويزيد فوحانه', 'شوي شوي', TOP),
        11: ('ريحة عطرية', 'بلمسة بخورية دافية', TOP), 12: ('وأثرها بالمجلس', 'يدوم لين ثلاث أيام', TOP), 13: (None, 'ومع الضمان الذهبي', TOP),
        14: (None, 'إذا ما ناسبك العود', TOP), 15: ('تقدر ترجعه', 'ونرد لك كامل المبلغ', TOP), 16: ('اختر الوزن', 'اللي تبيه', TOP),
        17: ('وادفع عن طريق', 'تابي أو تمارا', TOP), 18: ('وعليه خصم جبار', 'الحين', TOP), 19: (None, 'لا يفوتك', TOP)}
CAPI = []
for i, (l1, l2, (y1, y2)) in CAPS.items():
    p = PH[i]; st = p['start']; nxt = PH[i + 1]['start'] - 0.06 if i < 19 else 99
    items = []
    if l1: items.append((st, line_img(l1, F1, *WHITE), y1)); t2 = onset(i, l1, l1 + ' ' + l2); items.append((t2, line_img(l2, F2, *GOLD), y2))
    else: items.append((st, line_img(l2, F2, *GOLD), y1 + 50))
    items = [(ton, im, int(W / 2 - im.shape[1] / 2), int(cy - im.shape[0] / 2)) for ton, im, cy in items]
    ys = [y1, y2] if l1 else [y1 + 50]; top, bot = min(ys) - 60, max(ys) + 60
    wmax = max(it[1].shape[1] for it in items) - 48; bw = min(1080, int(wmax + 300)); bh = bot - top + 150
    m = Image.new('L', (bw, bh), 0); ImageDraw.Draw(m).rounded_rectangle((100, 60, bw - 100, bh - 60), radius=60, fill=255)
    a = np.array(m.filter(ImageFilter.GaussianBlur(45))).astype(np.float32) * 0.50
    CAPI.append((st, nxt, items, (np.dstack([np.zeros((bh, bw, 3)), a]).astype(np.uint8), int(W / 2 - bw / 2), top - 75)))
def draw_captions(fr, t):
    for st, en_, items, (bd, bx, by) in CAPI:
        if not (st - 0.05 <= t <= en_): continue
        ga = ss((t - st) / 0.22) * (1 - ss((t - (en_ - 0.16)) / 0.16)) if en_ < 90 else ss((t - st) / 0.22)
        paste(fr, bd, bx, by, ga)
        for ton, im, x, y in items:
            a = ss((t - ton) / 0.22)
            if a > 0: paste(fr, im, x, int(y + (1 - a) * 14), a * ga)

# ---------------- offer graphics ----------------
def badge(txt, bw=600, bh=180, icon='%'):   # burgundy card, gold icon + script wording (no invented numbers)
    S = 3; img = Image.new('RGBA', (bw * S, bh * S), (0, 0, 0, 0))
    g = np.linspace(0, 1, bh * S)[:, None, None]; col = np.array([128, 26, 42]) * (1 - g) + np.array([66, 10, 20]) * g
    m = Image.new('L', (bw * S, bh * S), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bw * S - 1, bh * S - 1), radius=30 * S, fill=255)
    img.alpha_composite(Image.fromarray(np.dstack([col * np.ones((1, bw * S, 1)), np.array(m)]).astype(np.uint8), 'RGBA'))
    d = ImageDraw.Draw(img); d.rounded_rectangle((4 * S, 4 * S, bw * S - 5 * S, bh * S - 5 * S), radius=27 * S, outline=(226, 188, 118, 255), width=3 * S)
    gold = (232, 196, 126, 255); cx, cy, r = (bw - 95) * S, bh * S // 2, 52 * S
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=gold)
    if icon == '%':
        fp = FA(70 * S); l, tp, rr, b = fp.getbbox('%'); d.text((cx - (rr - l) / 2 - l, cy - (b - tp) / 2 - tp), '%', font=fp, fill=(110, 20, 34, 255))
    else:   # check mark (guarantee)
        d.line([(cx - 24 * S, cy + 2 * S), (cx - 6 * S, cy + 20 * S), (cx + 26 * S, cy - 18 * S)], fill=(110, 20, 34, 255), width=11 * S, joint='curve')
    d.line(((bw - 170) * S, 30 * S, (bw - 170) * S, (bh - 30) * S), fill=(226, 188, 118, 150), width=2 * S)
    area = (bw - 175) * S; fs = 70
    while FA(fs * S).getlength(txt, direction='rtl') > area - 60 * S: fs -= 2      # shrink to fit left of the divider
    f3 = FA(fs * S); l, tp, rr, b = f3.getbbox(txt, direction='rtl')
    tw = Image.new('L', (bw * S, bh * S), 0); ImageDraw.Draw(tw).text(((area - (rr - l)) / 2 - l + 6 * S, (bh * S - (b - tp)) / 2 - tp), txt, font=f3, fill=255, direction='rtl')
    gg = np.linspace(0, 1, bh * S)[:, None, None]; tc = np.array(GT) * (1 - gg) + np.array(GB) * gg
    img.alpha_composite(Image.fromarray(np.dstack([tc * np.ones((1, bw * S, 1)), np.array(tw)]).astype(np.uint8), 'RGBA'))
    img = img.resize((bw, bh), Image.LANCZOS); out = Image.new('RGBA', (bw + 60, bh + 60), (0, 0, 0, 0)); sh = Image.new('L', (bw + 60, bh + 60), 0)
    ImageDraw.Draw(sh).rounded_rectangle((30, 40, 30 + bw, 40 + bh), radius=30, fill=160); sh = sh.filter(ImageFilter.GaussianBlur(14))
    shimg = Image.new('RGBA', (bw + 60, bh + 60), (0, 0, 0, 255)); shimg.putalpha(sh); out.alpha_composite(shimg); out.alpha_composite(img, (30, 30)); return np.array(out)
DISC = badge('خصم جبار الحين', bw=660)
GUAR = badge('الضمان الذهبي', bw=640, icon='check')
REFUND = badge('استرجاع كامل المبلغ', bw=700, icon='check')
def day_pill(n):
    t = 'اليوم ' + '١٢٣'[n - 1]
    return badge(t, bw=430, bh=150, icon='check')
DAYS = [day_pill(n) for n in (1, 2, 3)]
def load_rgba(p, size):
    x = cv2.cvtColor(cv2.imread(p, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA); a = x[..., 3].astype(np.float32)
    a = cv2.erode(a, np.ones((5, 5), np.uint8)); x[..., 3] = cv2.GaussianBlur(a, (3, 3), 0).astype(np.uint8); return cv2.resize(x, size, interpolation=cv2.INTER_AREA)
TABBY, TAMARA = load_rgba(LOGOS + 'logo_tabby.png', (320, 124)), load_rgba(LOGOS + 'logo_tamara.png', (320, 125))
def pop_in(fr, im, cx, cy, t0, t, t1=99, s0=0.35):
    if t < t0 or t > t1: return
    k = (t - t0) / 0.40; a = ss(k * 2.2) * (1 - ss((t - (t1 - 0.15)) / 0.15)) if t1 < 90 else ss(k * 2.2)
    h, w_ = im.shape[:2]; paste(fr, im, int(cx - w_ / 2), int(cy - h / 2), a, s0 + (1 - s0) * ease_back(k))
d0 = PH[12]['start'] + 0.35; dstep = (PH[12]['end'] - d0) / 3
POPS = {'day1': d0, 'day2': d0 + dstep, 'day3': d0 + 2 * dstep,
        'guarantee': PH[13]['start'] - 0.05, 'refund': onset(15, 'تقدر ترجعه ونرد', 'تقدر ترجعه ونرد لك كامل المبلغ') - 0.05,
        'tabby': onset(17, 'وادفع عن طريق', 'وادفع عن طريق تابي أو تمارا') - 0.03, 'tamara': onset(17, 'وادفع عن طريق تابي أو', 'وادفع عن طريق تابي أو تمارا') - 0.03,
        'discount': onset(18, 'وعليه', 'وعليه خصم جبار الحين') - 0.05}
POPS = {k: round(v, 2) for k, v in POPS.items()}
json.dump(POPS, open(K + 'edit/pop_times.json', 'w'), indent=1)
import os
if os.environ.get('DRY'): print(POPS); sys.exit()
def draw_graphics(fr, t):
    for n, k in enumerate(('day1', 'day2', 'day3')):
        t1 = POPS[('day2', 'day3', 'x')[n]] if n < 2 else PH[12]['end'] + 0.3
        pop_in(fr, DAYS[n], 540, 1600, POPS[k], t, t1 + 0.12, s0=0.6)
    pop_in(fr, GUAR, 540, 1560, POPS['guarantee'], t, PH[15]['end'] + 0.25, s0=0.25)
    pop_in(fr, REFUND, 540, 1745, POPS['refund'], t, PH[15]['end'] + 0.25, s0=0.25)
    pop_in(fr, TABBY, 735, 1655, POPS['tabby'], t, PH[17]['end'] + 0.25); pop_in(fr, TAMARA, 345, 1655, POPS['tamara'], t, PH[17]['end'] + 0.25)
    pop_in(fr, DISC, 540, 1650, POPS['discount'], t, s0=0.25)


if os.environ.get('SAMPLE'):
    ts = [float(v) for v in os.environ['SAMPLE'].split(',')]; tiles = []
    for t in ts:
        fr = cv2.cvtColor(base_frame(t), cv2.COLOR_BGR2RGB).astype(np.float32); draw_captions(fr, t); draw_graphics(fr, t)
        im = cv2.cvtColor(np.clip(fr, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR); im = cv2.resize(im, (270, 480)); cv2.putText(im, '%.1f' % t, (6, 472), 0, 0.6, (0, 255, 255), 2); tiles.append(im)
    while len(tiles) % 8: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(OUT, np.vstack([np.hstack(tiles[i:i + 8]) for i in range(0, len(tiles), 8)])); sys.exit()
# ---------------- render ----------------
N = int(round(END * FPS)); N0 = int(float(os.environ.get('T0', 0)) * FPS); N = int(float(os.environ['T1']) * FPS) if os.environ.get('T1') else N
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-ss', str(N0 / FPS), '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-af', f'apad=whole_dur={END}', '-t', str((N - N0) / FPS), '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for n in range(N0, N):
    t = n / FPS; fr = cv2.cvtColor(base_frame(t), cv2.COLOR_BGR2RGB).astype(np.float32)
    if not CLEAN: draw_captions(fr, t); draw_graphics(fr, t)
    enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('frames', N, 'END', END, 'pops', POPS)
