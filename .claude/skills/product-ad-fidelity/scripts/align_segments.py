"""Find, for each cut of an edited ad, which source clip (from the Magnific project) it came from and
at what offset/speed. Needed to (a) rebuild the ad on the same timing, (b) get caption-free versions
of untouched scenes.

usage: python align_segments.py ad.mp4 "t0,t1" clipA.mp4 [clipB.mp4 ...]
Prints, for 3 times inside [t0,t1], the best (diff, clip time). Compare the clip-time slope with the
ad-time slope: ~1.0 = normal speed; ~0.8 = 24fps clip played frame-by-frame at 30fps (stretch x1.25).
Scene cuts in an ad: ffmpeg -i ad.mp4 -vf "select='gt(scene,0.15)',showinfo" -f null - 2>&1 | grep pts_time
"""
import subprocess, sys
import cv2
import numpy as np

ad, span, clips = sys.argv[1], sys.argv[2], sys.argv[3:]
t0, t1 = map(float, span.split(','))


def grab(f, t, scale=True):
    vf = 'scale=1080:1920' if scale else 'null'
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', str(t), '-i', f, '-frames:v', '1', '-vf', vf, '_g.png'], check=True)
    return cv2.imread('_g.png').astype(np.float32)


for c in clips:
    d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', c]))
    res = []
    for ta in (t0 + 0.1, (t0 + t1) / 2, t1 - 0.1):
        o = grab(ad, ta, False); best = None
        for tc in np.arange(0, d - 0.04, 1 / 24):
            s = grab(c, tc); dd = np.abs(o[700:1900:4, ::4] - s[700:1900:4, ::4]).mean()   # lower 2/3: avoids top captions
            if best is None or dd < best[0]: best = (round(float(dd), 2), round(float(tc), 3))
        res.append((round(ta, 2), best))
    print(c, res)
