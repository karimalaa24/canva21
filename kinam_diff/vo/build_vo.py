"""Kinam VO: best phrase from two Lahajati takes (A = _4, B = _2), loudness-matched, paced (gaps 0.32 s, 0.40 s at key cuts), speech x1.03.
Writes vo_diff_paced.wav + vo_diff_map.json (phrase -> out start/end). Phrases 4, 6, 8 hold the 3 words to re-voice (can be swapped via REPL dict)."""
import json, subprocess, numpy as np, wave, os, sys
SR = 48000
TEMPO = 1.0   # take 3 is already ~8% faster than takes 2/4, so no x1.03 (it would sound rushed)
def load(f):
    w = wave.open(f); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
C = load('take2.wav')
P = [("وش يفرق كينام بيتهوفن عن غيره؟", 'C', 0.03, 2.45),
     ("قرّب وشوف الكسر", 'C', 3.05, 4.53),
     ("تبان لك عروق الخشب وتدرجات لونه", 'C', 5.05, 7.97),
     ("وكل كسرة لها شكلها", 'C', 8.41, 10.33),
     ("هذا عود كينام طبيعي", 'C', 10.96, 12.68),
     ("تريبل سوبر", 'C', 13.12, 13.93),
     ("من أفخم اختيارات بيتهوفن", 'C', 14.30, 16.41),
     ("وعلى الجمر يبان طابع الكينام", 'C', 16.94, 19.47),
     ("مع الحرارة يطلع عبق دهن العود", 'C', 19.95, 22.76),
     ("ويزيد فوحانه شوي شوي", 'C', 23.08, 25.24),
     ("ريحة عطرية بلمسة بخورية دافية", 'C', 25.77, 28.92),
     ("وأثرها بالمجلس ممكن يدوم لين ثلاث أيام", 'C', 29.33, 33.08),
     ("ومع الضمان الذهبي", 'C', 33.60, 34.98),
     ("إذا ما ناسبك العود", 'C', 35.29, 36.65),
     ("تقدر ترجعه ونرد لك كامل المبلغ", 'C', 36.98, 39.87),
     ("اختر الوزن اللي تبيه", 'C', 40.49, 41.84),
     ("وادفع عن طريق تابي أو تمارا", 'C', 42.25, 44.55),
     ("وعليه خصم جبار الحين", 'C', 44.96, 46.87),
     ("لا يفوتك", 'C', 47.22, 48.06)]
REPL = json.load(open('replacements.json')) if os.path.exists('replacements.json') else {}   # {"4": "file.wav", ...} re-voiced phrases
GAP = {1: 0.40, 2: 0.32, 3: 0.25, 4: 0.40, 5: 0.25, 6: 0.25, 7: 0.40, 8: 0.32, 9: 0.32, 10: 0.32, 11: 0.32, 12: 0.40, 13: 0.25, 14: 0.25, 15: 0.40, 16: 0.25, 17: 0.40, 18: 0.32}
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
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', '_raw_concat.wav', '-af', 'atempo=%.4f' % TEMPO, '-ar', '48000', 'vo_diff_paced.wav'], check=True)
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', 'vo_diff_paced.wav', '-b:a', '192k', 'vo_diff_paced.mp3'], check=True)
os.remove('_raw_concat.wav')
dur = len(y) / SR / TEMPO
json.dump({'phrases': MAP, 'duration': round(dur, 3), 'tempo': TEMPO}, open('vo_diff_map.json', 'w'), ensure_ascii=False, indent=1)
for m in MAP: print('%2d %s %6.2f-%6.2f  %s' % (m['i'], m['take'], m['start'], m['end'], m['text']))
print('duration %.2f s' % dur)
