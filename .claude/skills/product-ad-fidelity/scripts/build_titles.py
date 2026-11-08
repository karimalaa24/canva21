"""Burn word-by-word Arabic captions + pop-up badges onto a CLEAN (caption-free) edit, keeping its audio.

usage: python build_titles.py titles.json clean.mp4 audio_source.mp4 out.mp4

Why from scratch: lifting the old burned-in captions out of a previous render (difference against the
source clips) leaked old-scene pixels (ghost box edges / 'mirror' reflections) and made the dark band
flicker. Re-typing captions on the clean edit has none of those problems.

titles.json (see ../references/titles_example.json for the full Beethoven ad):
{
 "size": [1080,1920], "fps": 30,
 "font_ar": "<skill>/assets/almarai-arabic-800-normal.woff", "font_lat": "<skill>/assets/almarai-latin-800-normal.woff",
 "size1": 80, "size2": 84, "max_width": 950,
 "color1": [[250,247,240],[232,226,214]], "color2": [[246,222,168],[206,160,92]],   # top->bottom gradients (RGB)
 "layouts": {"top":[335,447], "bot":[1490,1608], "one":[335,null]},             # line1/line2 centre y
 "groups": [ {"start":0.45,"end":1.85,"layout":"top",
              "l1":[["هذي",0.45],["مو",0.52],["قطعة",0.60]], "l2":[["عود",1.0],["عادية...",1.4]]}, ...],
 "badges": [ {"image":"gift_badge.png","t":19.62,"group":8,"x":"center","y":1668},
             {"image":"logo_tabby.png","t":24.6,"group":10,"x":184,"y":378} ]
}
end >= 90 means "hold to the end". Words fade in (0.22 s, 16 px rise) at their final RTL positions;
each group fades out over the last 0.18 s. Badges pop with ease-out-back from 25-30 % scale.
Punctuation (! . …) is drawn with the latin font (the arabic subset has no such glyphs).
"""
import json, subprocess, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

C = json.load(open(sys.argv[1])); SRC, AUDIO, OUT = sys.argv[2], sys.argv[3], sys.argv[4]
W, H = C.get('size', [1080, 1920]); FPS = C.get('fps', 30)
FA = lambda s: ImageFont.truetype(C['font_ar'], s, layout_engine=ImageFont.Layout.RAQM)
FL = lambda s: ImageFont.truetype(C['font_lat'], s, layout_engine=ImageFont.Layout.RAQM)
F1, F2 = FA(C.get('size1', 80)), FA(C.get('size2', 84)); MAXW = C.get('max_width', 950)
COL1 = C.get('color1', [[250, 247, 240], [232, 226, 214]]); COL2 = C.get('color2', [[246, 222, 168], [206, 160, 92]])
PUN = '!.…'
split_p = lambda w: (w.rstrip(PUN), w[len(w.rstrip(PUN)):])


def wlen(word, font):
    core, p = split_p(word)
    return font.getlength(core, direction='rtl') + (FL(font.size).getlength(p) + font.size * 0.04 if p else 0)


def word_img(word, font, ct, cb):
    core, p = split_p(word); fl = FL(font.size)
    l, t, r, b = font.getbbox(core, direction='rtl', anchor='ls'); pad = 24
    pw = (fl.getlength(p) + font.size * 0.04) if p else 0
    w, h = int(r - l + pw) + 2 * pad, b - t + 2 * pad
    mask = Image.new('L', (w, h), 0); dd = ImageDraw.Draw(mask)
    dd.text((pad - l + pw, pad - t), core, font=font, fill=255, direction='rtl', anchor='ls')
    if p: dd.text((pad, pad - t), p, font=fl, fill=255, anchor='ls')
    g = np.linspace(0, 1, h)[:, None, None]; col = (np.array(ct) * (1 - g) + np.array(cb) * g) * np.ones((h, w, 1))
    img = Image.fromarray(np.dstack([col, np.array(mask)]).astype(np.uint8), 'RGBA')
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); sh.putalpha(mask.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.6)))
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0)); base.alpha_composite(sh, (0, 3)); base.alpha_composite(img)
    return np.array(base), (-(l - pw) + pad, -t + pad)


def layout(words, font, cy):
    sp = font.getlength(' '); ws = [wlen(w, font) for w, _ in words]; tot = sum(ws) + sp * (len(ws) - 1)
    if tot > MAXW: return layout(words, FA(int(font.size * MAXW / tot)), cy)
    x = W / 2 + tot / 2; asc, desc = font.getmetrics(); base = cy + (asc - desc) / 2 * 0.62; out = []
    for (w, t), wl in zip(words, ws):
        out.append((w, t, x - font.getlength(split_p(w)[0], direction='rtl'), base)); x -= wl + sp
    return out, tot, font


groups = []
for g in C['groups']:
    c1, c2 = C['layouts'][g['layout']]; items = []; widths = []
    for words, font, cy, (ct, cb) in ((g.get('l1', []), F1, c1, COL1), (g.get('l2', []), F2, c2, COL2)):
        if not words or cy is None: continue
        lo, tot, f = layout(words, font, cy); widths.append(tot)
        for w, t, xl, by in lo:
            im, (ox, oy) = word_img(w, f, ct, cb); items.append((t, im, int(round(xl - ox)), int(round(by - oy))))
    top = c1 - 55; bot = (c2 or c1) + 55; wmax = max(widths)
    bh = bot - top + 160; bw = min(W, int(wmax + 340))
    m = Image.new('L', (bw, bh), 0); ImageDraw.Draw(m).rounded_rectangle((100, 60, bw - 100, bh - 60), radius=60, fill=255)
    bd = np.dstack([np.zeros((bh, bw, 3)), np.array(m.filter(ImageFilter.GaussianBlur(45))) * 0.5]).astype(np.uint8)
    groups.append(dict(st=g['start'], en=g['end'], items=items, top=top, bd=(bd, int(W / 2 - bw / 2), top - 80)))
dv = np.zeros((5, 240, 4)); x = np.linspace(-1, 1, 240)
dv[..., :3] = C.get('divider_rgb', [232, 196, 130]); dv[..., 3] = np.clip(1 - x ** 2, 0, 1)[None, :] * np.array([.4, .9, 1, .9, .4])[:, None] * 255
DIV = dv.astype(np.uint8)
badges = []
for b in C.get('badges', []):
    im = cv2.cvtColor(cv2.imread(b['image'], cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
    if b.get('erode', 0): im[..., 3] = cv2.GaussianBlur(cv2.erode(im[..., 3], np.ones((b['erode'],) * 2, np.uint8)), (3, 3), 0)
    bx = int(W / 2 - im.shape[1] / 2) if b['x'] == 'center' else b['x']
    badges.append(dict(im=im, t=b['t'], g=b['group'], x=bx, y=b['y']))
ease = lambda t: 1 + 2.70158 * (min(max(t, 0), 1) - 1) ** 3 + 1.70158 * (min(max(t, 0), 1) - 1) ** 2
sstep = lambda t: (lambda u: u * u * (3 - 2 * u))(min(max(t, 0), 1))


def paste(fr, rgba, x, y, alpha=1.0, scale=1.0):
    if alpha <= 0.003: return
    im = rgba
    if abs(scale - 1) > 1e-3:
        h, w = im.shape[:2]; nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        im = cv2.resize(im, (nw, nh)); x = int(round(x + (w - nw) / 2)); y = int(round(y + (h - nh) / 2))
    h, w = im.shape[:2]; x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = im[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32); a = s[..., 3:] / 255. * alpha
    fr[y0:y1, x0:x1] = fr[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a


dec = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '15', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
n = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32); t = n / FPS
    for gi, g in enumerate(groups):
        if not (g['st'] - 0.05 <= t <= g['en']): continue
        ga = sstep((t - g['st']) / 0.25) * ((1 - sstep((t - (g['en'] - 0.18)) / 0.18)) if g['en'] < 90 else 1)
        bd, bx, by = g['bd']; paste(fr, bd, bx, by, ga)
        dw = max(2, int(240 * sstep((t - g['st']) / 0.35))); paste(fr, cv2.resize(DIV, (dw, 5)), int(W / 2 - dw / 2), g['top'] - 18, ga)
        for wt, im, x, y in g['items']:
            a = sstep((t - wt) / 0.22)
            if a > 0: paste(fr, im, x, int(y + (1 - a) * 16), a * ga)
        for b in badges:
            if b['g'] == gi and t >= b['t']:
                k = (t - b['t']) / 0.42; paste(fr, b['im'], b['x'], b['y'], sstep(k * 2.2) * ga, 0.25 + 0.75 * ease(k))
    enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes()); n += 1
enc.stdin.close(); enc.wait(); print('frames', n)
