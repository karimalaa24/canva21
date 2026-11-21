"""Kinam VO: best phrase from two Lahajati takes (A = _4, B = _2), loudness-matched, paced (gaps 0.32 s, 0.40 s at key cuts), speech x1.03.
Writes vo_kinam_paced.wav + vo_kinam_map.json (phrase -> out start/end). Phrases 4, 6, 8 hold the 3 words to re-voice (can be swapped via REPL dict)."""
import json, subprocess, numpy as np, wave, os, sys
SR = 48000
def load(f):
    w = wave.open(f); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
A, B = load('take4.wav'), load('take2.wav')
# (phrase text, take, start, end)  — bounds from the -42 dB envelope, 10 ms grid
P = [("يا ليتك تقدر تشم هاللقطة", 'B', 0.03, 2.20),
     ("هذا كينام بيتهوفن", 'A', 2.61, 4.10),
     ("قرب وشوف عروق هالكسرة", 'B', 4.90, 6.84),
     ("مع حرارة الجمر يبان فخامة دهن العود", 'B', 7.42, 10.89),
     ("ويزيد فوحانه شوي شوي", 'A', 10.72, 12.86),
     ("طابع عطري ولمسة بخورية دافية", 'B', 14.17, 17.20),
     ("ويبقى له أثر طيب في المجلس", 'B', 17.67, 20.19),
     ("عود كينام طبيعي تربل سوبر", 'A', 19.84, 22.55),
     ("من أفخم اختيارات بيتهوفن", 'A', 22.90, 25.12),
     ("تلقاه بالوزن اللي تبيه", 'A', 25.71, 27.30),
     ("وعليه خصم قوي الحين", 'A', 27.66, 29.54),
     ("لا يفوتك", 'A', 29.92, 30.81)]
REPL = json.load(open('replacements.json')) if os.path.exists('replacements.json') else {}   # {"4": "file.wav", ...} re-voiced phrases
GAP = {1: 0.40, 2: 0.32, 3: 0.32, 4: 0.32, 5: 0.40, 6: 0.32, 7: 0.40, 8: 0.32, 9: 0.40, 10: 0.32, 11: 0.32}   # gap AFTER phrase i (1-based)
PAD = 0.04; FADE = int(0.012 * SR)
def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2)) + 1e-9)
segs = []
for i, (txt, tk, s, e) in enumerate(P, 1):
    if str(i) in REPL: x = load(REPL[str(i)])
    else: src = A if tk == 'A' else B; x = src[int((s - PAD) * SR) if s > PAD else 0:int((e + PAD) * SR)].copy()
    x[:FADE] *= np.linspace(0, 1, FADE); x[-FADE:] *= np.linspace(1, 0, FADE); segs.append(x)
ref = np.median([rms_db(x) for x in segs])
segs = [x * 10 ** ((ref - rms_db(x)) / 20) for x in segs]
out = [np.zeros(int(0.10 * SR), np.float32)]; t = 0.10; MAP = []
for i, x in enumerate(segs, 1):
    MAP.append({'i': i, 'text': P[i - 1][0], 'take': 'R' if str(i) in REPL else P[i - 1][1], 'start': round(t / 1.03, 3), 'end': round((t + len(x) / SR) / 1.03, 3)})
    out.append(x); t += len(x) / SR
    if i in GAP: out.append(np.zeros(int(GAP[i] * 1.03 * SR), np.float32)); t += GAP[i] * 1.03
out.append(np.zeros(int(0.30 * SR), np.float32)); y = np.concatenate(out)
y = y / max(1e-6, np.abs(y).max()) * 0.89
wave_out = wave.open('_raw_concat.wav', 'wb'); wave_out.setnchannels(1); wave_out.setsampwidth(2); wave_out.setframerate(SR)
wave_out.writeframes((y * 32767).astype(np.int16).tobytes()); wave_out.close()
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', '_raw_concat.wav', '-af', 'atempo=1.03', '-ar', '48000', 'vo_kinam_paced.wav'], check=True)
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', 'vo_kinam_paced.wav', '-b:a', '192k', 'vo_kinam_paced.mp3'], check=True)
os.remove('_raw_concat.wav')
dur = len(y) / SR / 1.03
json.dump({'phrases': MAP, 'duration': round(dur, 3), 'tempo': 1.03}, open('vo_kinam_map.json', 'w'), ensure_ascii=False, indent=1)
for m in MAP: print('%2d %s %6.2f-%6.2f  %s' % (m['i'], m['take'], m['start'], m['end'], m['text']))
print('duration %.2f s' % dur)
