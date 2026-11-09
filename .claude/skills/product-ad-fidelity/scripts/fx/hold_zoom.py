"""Camera move added locally on a LOCKED Kling clip (approved for the long scene): hold, then slow zoom-in.
usage: python hold_zoom.py locked.mp4 out.mp4 FRAMES [--hold 2.0 --zoom 1.22 --cx 470 --cy 1150 --speed 1.0226]
Generate the Kling clip with a "locked-off tripod" prompt (only smoke/flame move) — then every zoom is free.
"""
import argparse, glob, os, subprocess, tempfile
import cv2
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('frames', type=int)
ap.add_argument('--hold', type=float, default=2.0); ap.add_argument('--zoom', type=float, default=1.22)
ap.add_argument('--cx', type=float, default=540); ap.add_argument('--cy', type=float, default=1150); ap.add_argument('--speed', type=float, default=1.0)
A = ap.parse_args(); d = tempfile.mkdtemp()
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', A.src, '-vf', f'setpts=PTS*{A.speed},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,deflicker=size=9:mode=pm',
                '-frames:v', str(A.frames), f'{d}/%04d.png'], check=True)
F = sorted(glob.glob(f'{d}/*.png')); T = (len(F) - 1) / 30
for j, f in enumerate(F):
    t = j / 30; u = 0 if t <= A.hold else (t - A.hold) / (T - A.hold); e = u * u * (3 - 2 * u) * 0.5 + u * 0.5; s = 1 + (A.zoom - 1) * e
    M = np.float32([[s, 0, A.cx - s * A.cx], [0, s, A.cy - s * A.cy]])
    cv2.imwrite(f, cv2.warpAffine(cv2.imread(f), M, (1080, 1920), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT))
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-framerate', '30', '-i', f'{d}/%04d.png', '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', '-pix_fmt', 'yuv420p', A.out], check=True)
print('frames', len(F))
