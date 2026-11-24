"""Guarantee card: Arabic gold-foil text drawn flat (Almarai, RAQM shaping) and warped onto the blank card face by the
gold inner-border homography; gold sampled from the card's own foil border. Free. usage: card_text.py in out "TL TR BR BL" """
import cv2, numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
FONT = '/home/user/canva21/oud-fix5/fonts/Almarai-ExtraBold.ttf'
F = lambda s: ImageFont.truetype(FONT, s, layout_engine=ImageFont.Layout.RAQM)
im = cv2.imread(sys.argv[1]); H, W = im.shape[:2]
Q = np.float32([[float(v) for v in p.split(',')] for p in sys.argv[3].split()])
CW, CH = 640, 1180
def layer(lines):
    m = Image.new('L', (CW, CH), 0); d = ImageDraw.Draw(m)
    for txt, size, y in lines:
        f = F(size); w = d.textlength(txt, font=f, direction='rtl'); d.text(((CW - w) / 2, y), txt, font=f, fill=255, direction='rtl')
    return np.array(m).astype(np.float32) / 255
gold = layer([('الضمان', 150, 250), ('الذهبي', 150, 440)])
cream = layer([('استرجاع كامل المبلغ', 62, 760)])
div = np.zeros((CH, CW), np.float32); cv2.line(div, (170, 700), (470, 700), 1, 3); cv2.circle(div, (320, 700), 7, 1, -1)
M = cv2.getPerspectiveTransform(np.float32([[0, 0], [CW, 0], [CW, CH], [0, CH]]), Q)
wg = lambda a: cv2.GaussianBlur(cv2.warpPerspective(a, M, (W, H), flags=cv2.INTER_AREA), (0, 0), 0.6)
G, C = wg(np.maximum(gold, div)), wg(cream)
# foil colour from the card's own border (bright warm pixels inside the card bbox)
x0, y0, x1, y1 = int(Q[:, 0].min()) - 25, int(Q[:, 1].min()) - 25, int(Q[:, 0].max()) + 25, int(Q[:, 1].max()) + 25
R = im[y0:y1, x0:x1].reshape(-1, 3).astype(np.float32); warm = R[:, 2] - R[:, 0]; foil = R[warm > np.percentile(warm, 99)]
gA, gB = np.percentile(foil, 40, 0), np.percentile(foil, 95, 0)
yy = np.mgrid[0:H, 0:W][0].astype(np.float32); t = np.clip((yy - y0) / (y1 - y0), 0, 1)[..., None]
sheen = gB * (1 - t) * 0.6 + gA * (0.4 + 0.6 * t)            # foil catches the light at the top, deeper lower down
out = im.astype(np.float32)
out = out * (1 - G[..., None]) + sheen * G[..., None]
out = out * (1 - 0.92 * C[..., None]) + np.array([200, 222, 236.]) * 0.92 * C[..., None]
cv2.imwrite(sys.argv[2], np.clip(out, 0, 255).astype(np.uint8)); print('foil', gA.round(), gB.round())
