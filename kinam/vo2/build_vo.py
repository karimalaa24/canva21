"""Kinam VO: best phrase from two Lahajati takes (A = _4, B = _2), loudness-matched, paced (gaps 0.32 s, 0.40 s at key cuts), speech x1.03.
Writes vo_kinam2_paced.wav + vo_kinam2_map.json (phrase -> out start/end). Phrases 4, 6, 8 hold the 3 words to re-voice (can be swapped via REPL dict)."""
import json, subprocess, numpy as np, wave, os, sys
SR = 48000
TEMPO = 1.0   # take 3 is already ~8% faster than takes 2/4, so no x1.03 (it would sound rushed)
def load(f):
    w = wave.open(f); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
C = load('take_g4.wav')
P = [("يا ليتك تقدر تشم هاللقطة", 'C', 0.04, 2.07),
     ("هذا كينام بيتهوفن", 'C', 2.63, 4.10),
     ("قرب وشوف عروق هالكسرة", 'C', 4.68, 6.50),
     ("مع حرارة الجمر يبان فخامة دهن العود", 'C', 6.97, 10.41),
     ("ويزيد فوحانه شوي شوي", 'C', 10.77, 13.06),
     ("طابع عطري ولمسة بخورية دافية", 'C', 13.76, 16.81),
     ("ويبقى له أثر طيب في المجلس", 'C', 17.20, 19.62),
     ("عود كينام طبيعي تربل سوبر", 'C', 20.14, 23.03),
     ("من أفخم اختيارات بيتهوفن", 'C', 23.39, 25.61),
     ("تلقاه بالوزن اللي تبيه", 'C', 26.17, 27.77),
     ("ومع الضمان الذهبي من بيتهوفن", 'C', 28.29, 30.53),
     ("إذا ما ناسبك العود", 'C', 30.96, 32.37),
     ("تقدر ترجعه ونرد لك كامل المبلغ", 'C', 32.75, 35.58),
     ("وعليه خصم قوي الحين", 'C', 36.10, 37.89),
     ("لا يفوتك", 'C', 38.34, 39.14)]
REPL = json.load(open('replacements.json')) if os.path.exists('replacements.json') else {}   # {"4": "file.wav", ...} re-voiced phrases
GAP = {1: 0.40, 2: 0.32, 3: 0.32, 4: 0.32, 5: 0.40, 6: 0.32, 7: 0.40, 8: 0.32, 9: 0.40, 10: 0.40, 11: 0.25, 12: 0.32, 13: 0.40, 14: 0.32}
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
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', '_raw_concat.wav', '-af', 'atempo=%.4f' % TEMPO, '-ar', '48000', 'vo_kinam2_paced.wav'], check=True)
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', 'vo_kinam2_paced.wav', '-b:a', '192k', 'vo_kinam2_paced.mp3'], check=True)
os.remove('_raw_concat.wav')
dur = len(y) / SR / TEMPO
json.dump({'phrases': MAP, 'duration': round(dur, 3), 'tempo': TEMPO}, open('vo_kinam2_map.json', 'w'), ensure_ascii=False, indent=1)
for m in MAP: print('%2d %s %6.2f-%6.2f  %s' % (m['i'], m['take'], m['start'], m['end'], m['text']))
print('duration %.2f s' % dur)
