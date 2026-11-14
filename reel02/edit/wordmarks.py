"""Apply fix_wordmark2 to every wrong 'Beethoven' in the Reel 02 stills. in: images/<p>_filled.png (or _raw), out: images/<p>_final.png"""
import cv2, sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_wordmark2 import fix, fix_ar
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wordmarks.json')))
only = sys.argv[1:] or list(CFG)
for p in only:
    c = CFG[p]; src = os.path.join(IMG, c['src']); img = cv2.imread(src)
    for i, w in enumerate(c['words']):
        if 'text' in w:
            img = fix_ar(img, w['bbox'], w['text'], width=w.get('width'), thr=w.get('thr', 14), angle=w.get('angle', 0.0), cy_override=w.get('cy')); continue
        img = fix(img, w['bbox'], w['seeds'], thr=w.get('thr', 14), scale=w.get('scale', 1.0), dil=w.get('dil', 4), weight=w.get('weight', 1.7), erase_thr=w.get('erase_thr', 7), hfit=w.get('hfit', False),
                  debug=f"/tmp/claude-0/-home-user-canva21/5eb1c6a6-e413-5964-b40d-255f9884d5dc/scratchpad/mask_{p}_{i}.png")
    cv2.imwrite(os.path.join(IMG, f'{p}_final.png'), img); print('wrote', p)
