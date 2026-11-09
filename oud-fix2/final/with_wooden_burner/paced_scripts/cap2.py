"""Ad-2 captions in the original's style: Alexandria Black, white + thick black outline, current word yellow;
group pops in over 3 frames; tabby / tamara badges pop with overshoot. Times are ORIGINAL ad times, mapped
to the cut edit (11.40-13.333 s removed)."""
import cv2, numpy as np, subprocess, json, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC = sys.argv[1] if len(sys.argv) > 1 else 'ad2_clean_fx.mp4'; OUT = sys.argv[2] if len(sys.argv) > 2 else 'ad2_final.mp4'
W, H, FPS = 1080, 1920, 30
CUT0, CUT1 = 999.0, 999.0   # original voice: no cut
INS = [[5.45, 0.35], [7.76, 0.35], [9.16, 0.3], [11.4, 0.35], [13.32, 0.35], [15.26, 0.3], [16.95, 0.35], [18.44, 0.2], [19.92, 0.4], [21.19, 0.3], [23.31, 0.3], [24.68, 0.35], [27.02, 0.2]]
def nt(t): return t + sum(d for ti, d in INS if ti < t)   # paced voice: pauses inserted
FONT = ImageFont.truetype('alex900.woff', 81, layout_engine=ImageFont.Layout.RAQM)
YEL = (252, 227, 3); WHITE = (253, 253, 253)
# (text, word start times, group end, centre y)   -- measured on the original at 30 fps
G = [('ضيفك يتذكر', [0.03, 0.40], 0.80, 1428), ('ريحة مجلسك', [0.87, 1.13], 1.50, 1428),
     ('أكثر من كلامك', [1.57, 1.90, 2.07], 3.00, 1425), ('عود تايقر', [3.53, 3.70], 4.00, 1660),
     ('الفيتنامي درجة أولى', [4.07, 4.60, 4.97], 5.53, 1660), ('دخنة تتعرف', [5.77, 6.03], 6.37, 1343),
     ('من أول لحظة', [6.40, 6.57, 7.00], 7.80, 1343), ('ثلاث أوقيات', [8.03, 8.27], 9.27, 1662),
     ('ومعها ثلاث أوقيات', [9.37, 9.63, 10.00], 10.40, 1662), ('مجانا', [10.47], 11.57, 1668), ('ومبخرة خشبية هدية', [11.70, 12.07, 12.47], 13.37, 1667),
     ('كلها في بوكس', [13.63, 13.83, 14.00], 14.20, 1672), ('جلدي فاخر', [14.27, 14.67], 15.50, 1672),
     ('تكفيك موسم كامل', [15.57, 15.90, 16.23], 17.17, 1668), ('ولو أهديت نصها', [17.23, 17.37, 17.73], 18.53, 1665),
     ('ما تنقص هيبتها', [18.60, 18.83, 19.07], 20.00, 1668), ('وفوق كل هذا', [20.27, 20.50, 20.63], 21.43, 308),
     ('بتجيك هدية سرية', [21.50, 21.77, 22.03], 22.40, 308), ('وقت الطلب', [22.47, 22.73], 23.47, 308),
     ('والشحن مجاني', [23.53, 23.87], 24.70, 308), ('وتقدر تدفع بسهولة', [24.97, 25.30, 25.57], 25.97, 258),
     ('عن طريق تابي', [26.00, 26.13, 26.53], 27.10, 258), ('أو تمارا', [27.17, 27.33], 99, 258)]
BADGES = [('../titles/logo_tabby.png', 26.567, (552, 330, 949, 488)), ('../titles/logo_tamara.png', 27.37, (102, 330, 499, 488))]


def render(words, hi):
    """RGBA of the whole line (pad around), word `hi` yellow."""
    sp = FONT.getlength(' ', direction='rtl', language='ar') * 1.05
    ws = [FONT.getlength(w, direction='rtl', language='ar') for w in words]
    tot = sum(ws) + sp * (len(words) - 1); P = 40; cw, ch = int(tot) + 2 * P, 200
    fill = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(fill)
    msk = Image.new('L', (cw, ch), 0); dm = ImageDraw.Draw(msk)
    x = P + tot
    for k, (w, ww) in enumerate(zip(words, ws)):
        x -= ww; col = YEL if k == hi else WHITE
        dm.text((x, 30), w, font=FONT, fill=255, direction='rtl', language='ar', stroke_width=8)
        d.text((x, 30), w, font=FONT, fill=col + (255,), direction='rtl', language='ar', stroke_width=8, stroke_fill=(0, 0, 0, 255))
        x -= sp
    sh = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); a = msk.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(5))
    sh.putalpha(a.point(lambda v: int(v * 0.85))); out = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    out.alpha_composite(sh, (-3, 7)); out.alpha_composite(fill)
    return np.array(out).astype(np.float32)


cache = {}
def line(gi, hi):
    if (gi, hi) not in cache: cache[(gi, hi)] = render(G[gi][0].split(' '), hi)
    return cache[(gi, hi)]


def paste(img, rgba, cx, cy, s=1.0, alpha=1.0):
    if s != 1.0: rgba = cv2.resize(rgba, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
    h, w = rgba.shape[:2]; x0 = int(round(cx - w / 2)); y0 = int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    r = rgba[ya - y0:yb - y0, xa - x0:xb - x0]; a = r[..., 3:4] / 255 * alpha
    img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a) + r[..., 2::-1][..., :3] * a


badges = []
for p, t0, (x0, y0, x1, y1) in BADGES:
    b = cv2.imread(p, -1).astype(np.float32); b = cv2.resize(b, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    b = b[..., [2, 1, 0, 3]]   # to RGBA order used by paste()
    badges.append((b, nt(t0), ((x0 + x1) / 2, (y0 + y1) / 2)))

dec = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', SRC, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '15', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'copy', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
i = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    t = i / FPS; img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
    for gi, (txt, wt, te, cy) in enumerate(G):
        nxt = G[gi + 1][1][0] if gi + 1 < len(G) else 99
        t0 = nt(wt[0]); te = nt(te) + sum(d for ti, d in INS if te <= ti < nxt)   # caption stays up through the added pause
        if not (t0 <= t < te): continue
        k = (t - t0) * FPS                                   # frames since the group appeared
        hi = -1 if k < 2 else max(j for j, w in enumerate(wt) if nt(w) <= t - 2 / FPS or j == 0)
        al = min(1.0, 0.35 + 0.33 * k); s = min(1.0, 0.94 + 0.03 * k)
        paste(img, line(gi, hi), W / 2, cy + 8, s, al)
    for b, t0, (cx, cy) in badges:
        if t < t0: continue
        d = t - t0
        s = 0.93 + 0.13 * min(1, d / 0.067) if d < 0.067 else 1.06 - 0.06 * min(1, (d - 0.067) / 0.1)   # pop + overshoot (measured)
        u = d / 0.1
        paste(img, b, cx, cy, s, min(1.0, 0.6 + u))
    enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes()); i += 1
enc.stdin.close(); enc.wait(); print('frames', i)
