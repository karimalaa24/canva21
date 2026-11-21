"""Tone/pitch of fix takes vs the original phrases. usage: compare_tone.py fixA.wav [fixB.wav ...]"""
import numpy as np, wave, sys
SR = 48000
def load(f):
    w = wave.open(f); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
def cut(x, s, e, pad=0.04): return x[max(0, int((s - pad) * SR)):int((e + pad) * SR)].copy()
def segs(x):
    h = int(SR * 0.01); n = len(x) // h; db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9); sp = db > -42; out = []; i = 0
    while i < n:
        if sp[i]:
            j = i
            while j < n and sp[j:j + 12].any(): j += 1
            out.append((i / 100, j / 100)); i = j
        else: i += 1
    return out
def ltas(x, n=4096):
    fr = [x[i:i + n] * np.hanning(n) for i in range(0, len(x) - n, n // 2) if np.sqrt(np.mean(x[i:i + n] ** 2)) > 0.02]
    return 10 * np.log10(np.mean([np.abs(np.fft.rfft(f)) ** 2 for f in fr], 0) + 1e-12)
def f0(x):
    v = []; n = 2048
    for i in range(0, len(x) - n, n // 2):
        s = x[i:i + n]
        if np.sqrt(np.mean(s ** 2)) < 0.03: continue
        ac = np.correlate(s, s, 'full')[n - 1:]; lo, hi = int(SR / 350), int(SR / 70); v.append(SR / (lo + np.argmax(ac[lo:hi])))
    return np.median(v)
A, B = load('take4.wav'), load('take2.wav'); ref = np.concatenate([cut(B, 4.90, 6.84), cut(B, 17.67, 20.19), cut(A, 22.90, 25.12), cut(A, 2.61, 4.10)])
f = np.fft.rfftfreq(4096, 1 / SR); R = ltas(ref); bands = [(80, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 14000)]
print('F0 originals %.0f Hz' % f0(ref))
for nm in sys.argv[1:]:
    x = load(nm); s = segs(x); xx = cut(x, s[0][0], s[-1][1]); N = ltas(xx); base = (N - R)[(f > 200) & (f < 4000)].mean()
    dev = [(N - R)[(f >= lo) & (f < hi)].mean() - base for lo, hi in bands]
    print(nm, 'segments', ' '.join('%.2f-%.2f' % a for a in s))
    print('  tone:', ' '.join('%d-%d:%+.1f' % (lo, hi, d) for (lo, hi), d in zip(bands, dev)), '| mean abs %.1f dB | F0 %.0f Hz' % (np.mean(np.abs(dev)), f0(xx)))
