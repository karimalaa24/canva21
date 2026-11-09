"""Karaoke-style Arabic captions (the ad-2 look): bold font, white text with a thick black outline and soft
shadow, the word being spoken turns yellow; each group pops in over ~3 frames; optional logo badges
(tabby / tamara ...) pop with a small overshoot.

usage: python karaoke_captions.py cfg.json in.mp4 out.mp4
cfg.json:
{
 "font": "SKILL_DIR/assets/alexandria-arabic-900-normal.woff", "size": 81, "stroke": 8,
 "white": [253,253,253], "yellow": [252,227,3],
 "groups": [ {"text": "ضيفك يتذكر", "words": [0.03, 0.40], "end": 0.80, "y": 1428}, ... ],   # one start time per word
 "time_map": [[t_insert, extra_seconds], ...],    # optional: pauses inserted by pace_voice.py (shift every time)
 "badges": [ {"image": "logo_tabby.png", "t": 26.57, "box": [552,330,949,488]}, ... ]
}
Measure word times and y on the original ad (yellow-pixel tracking per frame, see references/edit_recipes.md).
"""
import json, os, subprocess, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)
cfg = json.load(open(sys.argv[1])); SRC, OUT = sys.argv[2], sys.argv[3]
fix = lambda p: p.replace('SKILL_DIR', SKILL)
W, H, FPS = 1080, 1920, 30
FONT = ImageFont.truetype(fix(cfg.get('font', 'SKILL_DIR/assets/alexandria-arabic-900-normal.woff')), cfg.get('size', 81),
                          layout_engine=ImageFont.Layout.RAQM)
ST = cfg.get('stroke', 8); YEL = tuple(cfg.get('yellow', [252, 227, 3])); WHITE = tuple(cfg.get('white', [253, 253, 253]))
INS = cfg.get('time_map', [])
nt = lambda t: t + sum(d for ti, d in INS if ti < t)
G = cfg['groups']


def render(words, hi):
    sp = FONT.getlength(' ', direction='rtl', language='ar') * 1.05
    ws = [FONT.getlength(w, direction='rtl', language='ar') for w in words]
    tot = sum(ws) + sp * (len(words) - 1); P = 40; cw, ch = int(tot) + 2 * P, 200
    if tot > 980:   # auto-shrink a long line
        return render_with(words, hi, FONT.size * 980 / tot)
    fill = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(fill)
    msk = Image.new('L', (cw, ch), 0); dm = ImageDraw.Draw(msk); x = P + tot
    for k, (w, ww) in enumerate(zip(words, ws)):
        x -= ww; col = YEL if k == hi else WHITE
        dm.text((x, 30), w, font=FONT, fill=255, direction='rtl', language='ar', stroke_width=ST)
        d.text((x, 30), w, font=FONT, fill=col + (255,), direction='rtl', language='ar', stroke_width=ST, stroke_fill=(0, 0, 0, 255))
        x -= sp
    sh = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); a = msk.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(5))
    sh.putalpha(a.point(lambda v: int(v * 0.85))); out = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    out.alpha_composite(sh, (-3, 7)); out.alpha_composite(fill)
    return np.array(out).astype(np.float32)


def render_with(words, hi, size):
    global FONT
    keep = FONT; FONT = ImageFont.truetype(FONT.path, int(size), layout_engine=ImageFont.Layout.RAQM)
    try: return render(words, hi)
    finally: FONT = keep


cache = {}
def line(gi, hi):
    if (gi, hi) not in cache: cache[(gi, hi)] = render(G[gi]['text'].split(' '), hi)
    return cache[(gi, hi)]


def paste(img, rgba, cx, cy, s=1.0, alpha=1.0):
    if s != 1.0: rgba = cv2.resize(rgba, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
    h, w = rgba.shape[:2]; x0 = int(round(cx - w / 2)); y0 = int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    r = rgba[ya - y0:yb - y0, xa - x0:xb - x0]; a = r[..., 3:4] / 255 * alpha
    img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a) + r[..., 2::-1][..., :3] * a


badges = []
for b in cfg.get('badges', []):
    x0, y0, x1, y1 = b['box']; im = cv2.imread(fix(b['image']), -1).astype(np.float32)
    im = cv2.resize(im, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)[..., [2, 1, 0, 3]]
    badges.append((im, nt(b['t']), ((x0 + x1) / 2, (y0 + y1) / 2)))

dec = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', SRC, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-crf', '15', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'copy', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
i = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    t = i / FPS; img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
    for gi, g in enumerate(G):
        wt = g['words']; t0 = nt(wt[0]); nxt = G[gi + 1]['words'][0] if gi + 1 < len(G) else 99
        te = nt(g['end']) + sum(d for ti, d in INS if g['end'] <= ti < nxt)   # stays up through an inserted pause
        if not (t0 <= t < te): continue
        k = (t - t0) * FPS
        hi = -1 if k < 2 else max(j for j, w in enumerate(wt) if nt(w) <= t - 2 / FPS or j == 0)
        paste(img, line(gi, hi), W / 2, g['y'] + 8, min(1.0, 0.94 + 0.03 * k), min(1.0, 0.35 + 0.33 * k))
    for b, t0, (cx, cy) in badges:
        if t < t0: continue
        d = t - t0
        s = 0.93 + 0.13 * min(1, d / 0.067) if d < 0.067 else 1.06 - 0.06 * min(1, (d - 0.067) / 0.1)
        paste(img, b, cx, cy, s, min(1.0, 0.6 + d / 0.1))
    enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes()); i += 1
enc.stdin.close(); enc.wait(); print('frames', i)
