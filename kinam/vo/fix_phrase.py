"""Cut a re-voiced phrase from a Lahajati fix file and match it to the main VO (smooth EQ to the neighbouring phrases' long-term spectrum).
usage: fix_phrase.py fix.wav start end out.wav      (level is matched later by build_vo.py)"""
import numpy as np, wave, sys
SR = 48000
def load(f):
    w = wave.open(f); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
def cut(x, s, e, pad=0.04): return x[max(0, int((s - pad) * SR)):int((e + pad) * SR)].copy()
def ltas(x, n=4096):
    fr = [x[i:i + n] * np.hanning(n) for i in range(0, len(x) - n, n // 2) if np.sqrt(np.mean(x[i:i + n] ** 2)) > 0.02]
    return 10 * np.log10(np.mean([np.abs(np.fft.rfft(f)) ** 2 for f in fr], 0) + 1e-12)
A, B = load('take4.wav'), load('take2.wav')
ref = np.concatenate([cut(B, 4.90, 6.84), cut(B, 17.67, 20.19), cut(A, 22.90, 25.12), cut(A, 2.61, 4.10)])
src, s, e, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
x = cut(load(src), s, e); f = np.fft.rfftfreq(4096, 1 / SR)
d = ltas(ref) - ltas(x); d -= d[(f > 200) & (f < 4000)].mean()
cf = 63 * 2 ** (np.arange(0, 24) / 3); cf = cf[cf < 16000]       # 1/3-octave smoothing (keeps the low-mid correction)
bd = np.array([d[(f >= c / 2 ** (1 / 6)) & (f < c * 2 ** (1 / 6))].mean() for c in cf])
d = np.clip(np.interp(np.log(np.maximum(f, 1)), np.log(cf), bd), -8, 8); d[f < 60] = 0
X = np.fft.rfft(x); g = 10 ** (np.interp(np.fft.rfftfreq(len(x), 1 / SR), f, d) / 20); y = np.fft.irfft(X * g, len(x)).astype(np.float32)
w = wave.open(out, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
print(out, 'len %.2f s, max EQ %.1f dB' % (len(y) / SR, np.abs(d[(f > 80) & (f < 12000)]).max()))
