"""Reel 02: put the approved still's product pixels back into a Kling clip whose camera moves but whose products must
stay identical (Kling re-drew lid lettering and oud). Generalises reel01/edit/fix_bag_track.py to several objects:
each object = polygon in STILL px, tracked separately (ORB matches inside the dilated polygon, still -> frame homography,
corners smoothed over +-3 frames), pasted with a feathered polygon mask and a low-frequency light match.
Optional per-object colour mask ("bag": reddish-dark pixels only) keeps background out of loose shapes.
usage: python track_products.py still.png clip.mp4 out.mp4 objects.json
objects.json: [{"name": "boxA", "poly": [[x,y],...], "mask": "poly"|"bag"}, ...]"""
import cv2, numpy as np, sys, json, subprocess
st_p, clip, out, cfg = sys.argv[1:5]; OBJ = json.load(open(cfg))
cap = cv2.VideoCapture(clip); fps = cap.get(5); fr = []
while True:
    ok, im = cap.read()
    if not ok: break
    fr.append(im)
h, w = fr[0].shape[:2]; S0 = cv2.imread(st_p); sx, sy = w / S0.shape[1], h / S0.shape[0]
S = cv2.resize(S0, (w, h), interpolation=cv2.INTER_AREA); gS = cv2.cvtColor(S, cv2.COLOR_BGR2GRAY)
orb = cv2.ORB_create(5000); bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
gF = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]
layers = []
ALL = np.zeros((h, w), np.uint8)
for o in OBJ: cv2.fillPoly(ALL, [(np.float32(o['poly']) * [sx, sy]).astype(np.int32)], 255)
for o in OBJ:
    poly = np.float32(o['poly']) * [sx, sy]
    pm = np.zeros((h, w), np.uint8); cv2.fillPoly(pm, [poly.astype(np.int32)], 255)
    a = (pm > 0).astype(np.float32)
    if o.get('mask') == 'bag':
        r = S.astype(np.float32); a *= ((r[..., 2] > r[..., 1] + 12) & (r.mean(2) < 150)).astype(np.float32)
        a = cv2.erode(a, np.ones((3, 3), np.uint8))
    else:
        a = cv2.erode(a, np.ones((5, 5), np.uint8))
    a = cv2.GaussianBlur(a, (0, 0), 2.5)
    roi = cv2.dilate(ALL if o.get('roi') == 'all' else pm, np.ones((41, 41), np.uint8)); kS, dS = orb.detectAndCompute(gS, roi)
    x0, y0, bw, bh = cv2.boundingRect(poly.astype(np.int32)); C = np.float32([[x0, y0], [x0 + bw, y0], [x0 + bw, y0 + bh], [x0, y0 + bh]])
    P = []; Hprev = np.eye(3)
    for g in gF:
        # search where the object was last seen
        rf = cv2.warpPerspective(roi, Hprev, (w, h)); rf = cv2.dilate(rf, np.ones((81, 81), np.uint8))
        kF, dF = orb.detectAndCompute(g, rf)
        Hm = None
        if dF is not None and len(kF) > 20:
            m = sorted(bf.match(dS, dF), key=lambda x: x.distance)[:800]
            if len(m) > 20:
                Hm, inl = cv2.findHomography(np.float32([kS[x.queryIdx].pt for x in m]), np.float32([kF[x.trainIdx].pt for x in m]), cv2.RANSAC, 2.0)
        if Hm is None: Hm = Hprev
        Hprev = Hm; P.append(cv2.perspectiveTransform(C[None], Hm)[0])
    P = np.array(P); Ps = np.array([P[max(0, i - 3):i + 4].mean(0) for i in range(len(P))])
    print(o['name'], 'corner jitter px (median):', round(float(np.median(np.abs(P - Ps))), 3), 'kp', len(kS))
    layers.append((C, Ps, a))
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-',
                        '-c:v', 'libx264', '-crf', '12', '-preset', 'slow', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
for k, f in enumerate(fr):
    o = f.astype(np.float32)
    for C, Ps, a in layers:
        Hk = cv2.getPerspectiveTransform(C, Ps[k].astype(np.float32))
        lay = cv2.warpPerspective(S, Hk, (w, h), flags=cv2.INTER_LANCZOS4).astype(np.float32); ak = cv2.warpPerspective(a, Hk, (w, h))[..., None]
        lo_f = cv2.GaussianBlur(o, (0, 0), 25); lo_l = cv2.GaussianBlur(lay, (0, 0), 25)
        lay = lay * np.clip(lo_f / np.maximum(lo_l, 1), 0.8, 1.25)
        o = o * (1 - ak) + lay * ak
    enc.stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('frames', len(fr))
