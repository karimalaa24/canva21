"""Kinam rough cut: each Kling clip from its first frame at real speed (24 fps -> 30 by frame picking), cut to scene_timing.json, VO under it. No captions yet."""
import cv2, numpy as np, json, subprocess, sys
K = '/home/user/canva21/kinam/'; W, H, FPS = 1080, 1920, 30
T = json.load(open(K + 'vo/scene_timing.json'))['scenes']; out = sys.argv[1]
def cover(im):
    h, w = im.shape[:2]; s = max(W / w, H / h); im = cv2.resize(im, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y0 = (im.shape[0] - H) // 2; x0 = (im.shape[1] - W) // 2; return im[y0:y0 + H, x0:x0 + W]
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', K + 'vo/vo_kinam_paced.wav',
                        '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-af', 'apad', '-t', str(T[-1]['end']), out], stdin=subprocess.PIPE)
N = int(round(T[-1]['end'] * FPS))
for i, sc in enumerate(T):
    c = cv2.VideoCapture(K + 'clips/raw/S%02d.mp4' % (i + 1)); fr = []
    while True:
        ok, im = c.read()
        if not ok: break
        fr.append(cover(im))
    a, b = int(round(sc['start'] * FPS)), int(round(sc['end'] * FPS)) if i < len(T) - 1 else N
    for n in range(a, b):
        k = min(int((n - a) / FPS * 24), len(fr) - 1); enc.stdin.write(fr[k].tobytes())
enc.stdin.close(); enc.wait(); print('frames', N)
