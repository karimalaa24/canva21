"""Kinam final builder (frame-indexed, real Kling frames 24->30 by frame picking, product light lift).
usage: build_kinam.py out.mp4 --audio mix.wav [--clean]
Timeline = vo/scene_timing.json (cuts at the middle of the VO gaps) ; captions = two-line white + gold, line 2 appears on its word.
Graphics (S8): discount badge on «خصم» (client: no tabby/tamara), pop SFX times written to edit/pop_times.json (used by make_mixes_kinam.py)."""
import cv2, numpy as np, subprocess, sys, json, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
K = '/home/user/canva21/kinam/'; FONT = '/home/user/canva21/oud-fix5/fonts/Almarai-ExtraBold.ttf'; LOGOS = '/home/user/canva21/.claude/skills/product-ad-fidelity/assets/'
W, H, FPS = 1080, 1920, 30
args = sys.argv[1:]; OUT = args[0]; CLEAN = '--clean' in args; AUDIO = args[args.index('--audio') + 1]
SC = json.load(open(K + 'vo2/scene_timing.json'))['scenes']; VM = json.load(open(K + 'vo2/vo_kinam2_map.json'))
PH = {p['i']: p for p in VM['phrases']}
END = round(PH[15]['end'] + 1.35, 2); SC[-1]['end'] = END       # hold the final frame with the offer graphics
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
for sc in SC:
    c = cv2.VideoCapture(K + 'clips/raw/%s.mp4' % sc['clip']); fr = []
    while True:
        ok, im = c.read()
        if not ok: break
        fr.append(lift(cover(im)))
    off = sc.get('src_from', 0)
    if off == 'tail': off = max(0, len(fr) - int(np.ceil((sc['end'] - sc['start']) * 24)) - 1)
    CL[sc['scene']] = (fr, off)
def base_frame(t):
    sc = [s for s in SC if s['start'] <= t + 1e-6 < s['end'] + 1e-6][0]; fr, off = CL[sc['scene']]
    return fr[min(off + int((t - sc['start']) * 24), len(fr) - 1)]

# ---------------- word onset of caption line 2: VO energy dip nearest to the proportional estimate ----------------
w = wave.open(K + 'vo2/vo_kinam2_paced.wav'); SR = w.getframerate(); vx = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
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
TOP, HIGH, LOW = (335, 447), (215, 327), (1545, 1657)
# phrase -> (white line, gold line, zone)
CAPS = {1: ('يا ليتك تقدر تشم', 'هاللقطة…', HIGH), 2: ('هذا كينام', 'بيتهوفن', LOW), 3: ('قرّب وشوف', 'عروق هالكسرة', TOP),
        4: ('مع حرارة الجمر', 'يبان فخامة دهن العود', HIGH), 5: ('ويزيد فوحانه', 'شوي شوي', TOP), 6: ('طابع عطري', 'ولمسة بخورية دافية', TOP),
        7: ('ويبقى له أثر طيب', 'في المجلس', TOP), 8: ('عود كينام طبيعي', 'تربل سوبر', TOP), 9: ('من أفخم اختيارات', 'بيتهوفن', TOP),
        10: ('تلقاه بالوزن', 'اللي تبيه', TOP), 11: ('ومع الضمان الذهبي', 'من بيتهوفن', TOP), 12: (None, 'إذا ما ناسبك العود', TOP),
        13: ('تقدر ترجعه', 'ونرد لك كامل المبلغ', TOP), 14: ('وعليه خصم قوي', 'الحين', TOP), 15: (None, 'لا يفوتك', TOP)}
CAPI = []
for i, (l1, l2, (y1, y2)) in CAPS.items():
    p = PH[i]; st = p['start']; nxt = PH[i + 1]['start'] - 0.06 if i < 15 else 99
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
def badge(txt, bw=600, bh=180, icon='%'):   # burgundy card, gold icon + script wording
    S = 3; img = Image.new('RGBA', (bw * S, bh * S), (0, 0, 0, 0))
    g = np.linspace(0, 1, bh * S)[:, None, None]; col = np.array([128, 26, 42]) * (1 - g) + np.array([66, 10, 20]) * g
    m = Image.new('L', (bw * S, bh * S), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bw * S - 1, bh * S - 1), radius=30 * S, fill=255)
    img.alpha_composite(Image.fromarray(np.dstack([col * np.ones((1, bw * S, 1)), np.array(m)]).astype(np.uint8), 'RGBA'))
    d = ImageDraw.Draw(img); d.rounded_rectangle((4 * S, 4 * S, bw * S - 5 * S, bh * S - 5 * S), radius=27 * S, outline=(226, 188, 118, 255), width=3 * S)
    gold = (232, 196, 126, 255); cx, cy, r = (bw - 95) * S, bh * S // 2, 52 * S
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=gold)
    if icon == '%':
        fp = FA(70 * S); l, tp, rr, b = fp.getbbox('%'); d.text((cx - (rr - l) / 2 - l, cy - (b - tp) / 2 - tp), '%', font=fp, fill=(110, 20, 34, 255))
    else: d.line([(cx - 24 * S, cy + 2 * S), (cx - 6 * S, cy + 20 * S), (cx + 26 * S, cy - 18 * S)], fill=(110, 20, 34, 255), width=11 * S, joint='curve')
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
DISC = badge('خصم قوي الحين', bw=660)
GUAR = badge('الضمان الذهبي', bw=640, icon='check')
REFUND = badge('استرجاع كامل المبلغ', bw=700, icon='check')
def load_rgba(p, size):
    x = cv2.cvtColor(cv2.imread(p, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA); a = x[..., 3].astype(np.float32)
    a = cv2.erode(a, np.ones((5, 5), np.uint8)); x[..., 3] = cv2.GaussianBlur(a, (3, 3), 0).astype(np.uint8); return cv2.resize(x, size, interpolation=cv2.INTER_AREA)
TABBY, TAMARA = load_rgba(LOGOS + 'logo_tabby.png', (320, 124)), load_rgba(LOGOS + 'logo_tamara.png', (320, 125))
def pop_in(fr, im, cx, cy, t0, t, t1=99, s0=0.35):
    if t < t0 or t > t1: return
    k = (t - t0) / 0.40; a = ss(k * 2.2) * (1 - ss((t - (t1 - 0.15)) / 0.15)) if t1 < 90 else ss(k * 2.2)
    h, w_ = im.shape[:2]; paste(fr, im, int(cx - w_ / 2), int(cy - h / 2), a, s0 + (1 - s0) * ease_back(k))
t_disc = onset(14, 'وعليه', 'وعليه خصم قوي الحين') - 0.05
POPS = {'guarantee': round(onset(11, 'ومع', 'ومع الضمان الذهبي من بيتهوفن') - 0.05, 2), 'refund': round(PH[13]['start'] - 0.05, 2), 'discount': round(t_disc, 2)}   # no tabby / tamara in this ad
json.dump(POPS, open(K + 'edit/pop_times.json', 'w'), indent=1)
import os
if os.environ.get('DRY'): print(POPS); sys.exit()
def draw_graphics(fr, t):
    pop_in(fr, GUAR, 540, 700, POPS['guarantee'], t, PH[13]['end'] + 0.25, s0=0.25)
    pop_in(fr, REFUND, 540, 885, POPS['refund'], t, PH[13]['end'] + 0.25, s0=0.25)
    pop_in(fr, DISC, 540, 1440, POPS['discount'], t, s0=0.25)

if os.environ.get('SAMPLE'):
    ts = [float(v) for v in os.environ['SAMPLE'].split(',')]; tiles = []
    for t in ts:
        fr = cv2.cvtColor(base_frame(t), cv2.COLOR_BGR2RGB).astype(np.float32); draw_captions(fr, t); draw_graphics(fr, t)
        im = cv2.cvtColor(np.clip(fr, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR); im = cv2.resize(im, (270, 480)); cv2.putText(im, '%.1f' % t, (6, 472), 0, 0.6, (0, 255, 255), 2); tiles.append(im)
    while len(tiles) % 7: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(OUT, np.vstack([np.hstack(tiles[i:i + 7]) for i in range(0, len(tiles), 7)])); sys.exit()
# ---------------- render ----------------
N = int(round(END * FPS))
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-af', f'apad=whole_dur={END}', '-t', str(END), '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; fr = cv2.cvtColor(base_frame(t), cv2.COLOR_BGR2RGB).astype(np.float32)
    if not CLEAN: draw_captions(fr, t); draw_graphics(fr, t)
    enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('frames', N, 'END', END, 'pops', POPS)
