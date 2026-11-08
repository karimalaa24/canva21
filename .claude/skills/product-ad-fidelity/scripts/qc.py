"""Quality checks before showing anything to the client.

  python qc.py sheet  video.mp4 out.jpg [n=8] [y0 y1]   # n evenly spaced frames (optionally cropped rows) side by side
  python qc.py flicker video.mp4                       # 2nd-derivative of mean brightness per band (top/mid/low)
  python qc.py compare a.png b.png out.jpg x0,y0,x1,y1  # same crop of two images side by side (before/after, ref/result)

Flicker numbers: mean ~0.05-0.15 is a steady shot. Spikes > 1 in a band = flicker/artefact there
(e.g. caption band rebuilt per frame). Text fading in legitimately raises the caption band a little.
"""
import subprocess, sys
import cv2
import numpy as np

mode = sys.argv[1]
if mode == 'sheet':
    v, out = sys.argv[2], sys.argv[3]; n = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', v]))
    ims = []
    for t in np.linspace(0.05, d - 0.1, n):
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', str(t), '-i', v, '-frames:v', '1', '_q.png'], check=True)
        im = cv2.imread('_q.png')
        if len(sys.argv) > 6: im = im[int(sys.argv[5]):int(sys.argv[6])]
        im = cv2.resize(im, (300, int(300 * im.shape[0] / im.shape[1]))); cv2.putText(im, f'{t:.1f}', (4, 18), 0, 0.55, (0, 255, 255), 2); ims.append(im)
    cv2.imwrite(out, np.hstack(ims))
elif mode == 'flicker':
    v = sys.argv[2]
    p = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-i', v, '-vf', 'scale=270:480', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
    fr = []
    while True:
        b = p.stdout.read(270 * 480)
        if len(b) < 270 * 480: break
        fr.append(np.frombuffer(b, np.uint8).reshape(480, 270).astype(np.float32))
    for nm, (a, b) in (('top', (0, 160)), ('mid', (160, 325)), ('low', (325, 480))):
        m = np.array([f[a:b].mean() for f in fr]); hf = np.abs(m[2:] - 2 * m[1:-1] + m[:-2])
        cuts = np.where(hf > 15)[0]; ok = np.delete(hf, np.concatenate([cuts + d for d in (-1, 0, 1)]).clip(0, len(hf) - 1)) if len(cuts) else hf
        print(f'{nm}: mean {ok.mean():.2f}  max {ok.max():.2f}  (scene cuts ignored at frames {list(cuts + 1)})')
elif mode == 'compare':
    a, b = cv2.imread(sys.argv[2]), cv2.imread(sys.argv[3]); x0, y0, x1, y1 = map(int, sys.argv[5].split(','))
    b = cv2.resize(b, (a.shape[1], a.shape[0])); h = 600
    f = lambda i: cv2.resize(i[y0:y1, x0:x1], (int((x1 - x0) * h / (y1 - y0)), h))
    cv2.imwrite(sys.argv[4], np.hstack([f(a), np.full((h, 12, 3), 255, np.uint8), f(b)]))
