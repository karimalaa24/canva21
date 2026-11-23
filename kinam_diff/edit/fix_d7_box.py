"""D7/D8 night clip: replace Kling's box (inherited from the warped-perspective still) with the rigid frontal box of
d07_night_v4_final.png on every frame. Smoke/burner/room stay the original Kling frames. Free, local.
usage: fix_d7_box.py clips/D7_night.mp4 clips/D7_night_fixed.mp4"""
import cv2, numpy as np, sys, subprocess
H = np.load('/home/user/canva21/kinam_diff/edit/H7_still_to_clip.npy')
new = cv2.imread('/home/user/canva21/kinam_diff/images/d07_night_v4_final.png'); old = cv2.imread('/home/user/canva21/kinam_diff/images/d07_night_v2_final.png')
cap = cv2.VideoCapture(sys.argv[1]); W, Hh = int(cap.get(3)), int(cap.get(4)); fps = cap.get(5)
P = cv2.warpPerspective(new, H, (W, Hh)).astype(np.float32); O = cv2.warpPerspective(old, H, (W, Hh)).astype(np.float32)
m = np.zeros(old.shape[:2], np.float32); cv2.fillPoly(m, [np.array([[402, 1772], [1024, 1772], [1024, 2470], [402, 2470]], np.int32)], 1)
m = cv2.warpPerspective(m, H, (W, Hh)); M = cv2.GaussianBlur(cv2.erode(m, np.ones((9, 9), np.uint8)), (0, 0), 5)
rm = cv2.GaussianBlur(m, (0, 0), 3); M[:, int(1018 * H[0, 0]):] = np.minimum(M[:, int(1018 * H[0, 0]):], rm[:, int(1018 * H[0, 0]):])
ring = (cv2.dilate(m, np.ones((41, 41), np.uint8)) > 0) & (m == 0); ring[:, int(1000 * H[0, 0]):] = False
bgmask = np.ones((Hh // 2, W // 2), np.uint8) * 255; bgmask[int(1150 / 2):int(1800 / 2), :] = 0; bgmask[:, int(W * 0.55 / 2):] = 0   # ECC: left room/table only
g0 = None; frames = []
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{Hh}', '-r', str(fps), '-i', '-',
                      '-c:v', 'libx264', '-crf', '12', '-preset', 'slow', '-pix_fmt', 'yuv420p', sys.argv[2]], stdin=subprocess.PIPE)
i = 0
while True:
    r, f = cap.read()
    if not r: break
    g = cv2.cvtColor(cv2.resize(f, (W // 2, Hh // 2)), cv2.COLOR_BGR2GRAY).astype(np.float32)
    if g0 is None: g0 = g; A = np.eye(2, 3, dtype=np.float32)
    else:
        try: _, A = cv2.findTransformECC(g0, g, A.copy(), cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 1e-5), bgmask, 5)
        except cv2.error: pass
    A2 = A.copy(); A2[:, 2] *= 2
    Pf = cv2.warpAffine(P, A2, (W, Hh), borderMode=cv2.BORDER_REPLICATE); Mf = cv2.warpAffine(M, A2, (W, Hh))[..., None]
    Of = cv2.warpAffine(O, A2, (W, Hh), borderMode=cv2.BORDER_REPLICATE); rf = cv2.warpAffine(ring.astype(np.uint8), A2, (W, Hh)) > 0
    gain = (f[rf].astype(np.float32).mean(0) + 1) / (Of[rf].mean(0) + 1)
    out = f.astype(np.float32) * (1 - Mf) + Pf * gain * Mf
    p.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
    if i % 30 == 0: print(i, A.round(4).tolist(), gain.round(3)); sys.stdout.flush()
    i += 1
p.stdin.close(); p.wait(); print('frames', i)
