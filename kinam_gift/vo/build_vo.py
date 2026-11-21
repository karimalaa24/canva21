"""Kinam GIFT reel VO: single Lahajati take (_4) (A = _4, B = _2), loudness-matched, paced (gaps 0.32 s, 0.40 s at key cuts), speech x1.03.
Writes vo_gift_paced.wav + vo_gift_map.json (phrase -> out start/end). Phrases 4, 6, 8 hold the 3 words to re-voice (can be swapped via REPL dict)."""
import json, subprocess, numpy as np, wave, os, sys
SR = 48000
TEMPO = 1.0   # take 3 is already ~8% faster than takes 2/4, so no x1.03 (it would sound rushed)
def load(f):
    w = wave.open(f); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
C = load('take_gift4.wav')
P = [("تدور على هدية فخمة لواحد يحب العود؟", 'C', 0.04, 2.57),
     ("اختر له كينام بيتهوفن", 'C', 3.17, 4.80),
     ("عود طبيعي تربل سوبر", 'C', 5.31, 6.89),
     ("يجيك بعلبة فخمة جاهزة للإهداء", 'C', 7.27, 9.50),
     ("يوم يفتحها", 'C', 10.05, 10.88),
     ("يشوف عروق الخشب وتفاصيل الكسر", 'C', 11.15, 13.64),
     ("وعلى الجمر تفوح ريحته شوي شوي", 'C', 14.17, 17.04),
     ("بطابع عطري ولمسة بخورية دافية", 'C', 17.42, 20.29),
     ("ومع الضمان الذهبي من بيتهوفن", 'C', 20.78, 22.79),
     ("إذا ما ناسبك العود", 'C', 23.12, 24.40),
     ("تقدر ترجعه ونرد لك كامل المبلغ", 'C', 24.75, 27.38),
     ("اختر الوزن اللي تبيه", 'C', 27.98, 29.27),
     ("وادفع عن طريق تابي أو تمارا", 'C', 29.63, 31.75),
     ("وعليه خصم قوي الحين", 'C', 32.13, 33.78),
     ("اطلبه من بيتهوفن لا يفوتك", 'C', 34.30, 36.64)]
REPL = json.load(open('replacements.json')) if os.path.exists('replacements.json') else {}   # {"4": "file.wav", ...} re-voiced phrases
GAP = {1: 0.40, 2: 0.32, 3: 0.32, 4: 0.40, 5: 0.25, 6: 0.32, 7: 0.32, 8: 0.40, 9: 0.32, 10: 0.25, 11: 0.40, 12: 0.32, 13: 0.40, 14: 0.32}   # gap AFTER phrase i
PAD = 0.04; FADE = int(0.012 * SR)
def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2)) + 1e-9)
segs = []
for i, (txt, tk, s, e) in enumerate(P, 1):
    if str(i) in REPL: x = load(REPL[str(i)])
    else: src = C; x = src[int((s - PAD) * SR) if s > PAD else 0:int((e + PAD) * SR)].copy()
    x[:FADE] *= np.linspace(0, 1, FADE); x[-FADE:] *= np.linspace(1, 0, FADE); segs.append(x)
ref = np.median([rms_db(x) for x in segs])
segs = [x * 10 ** ((ref - rms_db(x)) / 20) for x in segs]
out = [np.zeros(int(0.10 * SR), np.float32)]; t = 0.10; MAP = []
for i, x in enumerate(segs, 1):
    MAP.append({'i': i, 'text': P[i - 1][0], 'take': 'R' if str(i) in REPL else P[i - 1][1], 'start': round(t / TEMPO, 3), 'end': round((t + len(x) / SR) / TEMPO, 3)})
    out.append(x); t += len(x) / SR
    if i in GAP: out.append(np.zeros(int(GAP[i] * TEMPO * SR), np.float32)); t += GAP[i] * TEMPO
out.append(np.zeros(int(0.30 * SR), np.float32)); y = np.concatenate(out)
y = y / max(1e-6, np.abs(y).max()) * 0.89
wave_out = wave.open('_raw_concat.wav', 'wb'); wave_out.setnchannels(1); wave_out.setsampwidth(2); wave_out.setframerate(SR)
wave_out.writeframes((y * 32767).astype(np.int16).tobytes()); wave_out.close()
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', '_raw_concat.wav', '-af', 'atempo=%.4f' % TEMPO, '-ar', '48000', 'vo_gift_paced.wav'], check=True)
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', 'vo_gift_paced.wav', '-b:a', '192k', 'vo_gift_paced.mp3'], check=True)
os.remove('_raw_concat.wav')
dur = len(y) / SR / TEMPO
json.dump({'phrases': MAP, 'duration': round(dur, 3), 'tempo': TEMPO}, open('vo_gift_map.json', 'w'), ensure_ascii=False, indent=1)
for m in MAP: print('%2d %s %6.2f-%6.2f  %s' % (m['i'], m['take'], m['start'], m['end'], m['text']))
print('duration %.2f s' % dur)
