"""Source reel VO: take _5 (client's pick, best in review), silences tightened (0.20 s inside a sentence, 0.34 s at sentence ends)
then atempo 1.09. Writes vo_source.wav + vo_source_map.json (phrase -> new start/end)."""
import numpy as np, wave, json, subprocess
SEG = [(0.00, 0.99, 'مو كل عود'), (1.16, 2.95, 'يستاهل يوصل مجلسك'), (3.52, 4.32, 'في بيتهوفن'), (4.67, 6.70, 'الكينام يمر على يد خبير'),
       (6.85, 8.00, 'قبل لا يوصلك'), (8.33, 10.26, 'نفرزه قطعة قطعة'), (10.54, 13.18, 'نشوف كثافته ولمعة دهنه'), (13.50, 14.62, 'وعروق خشبه'),
       (14.88, 16.39, 'ونجربه على الجمر'), (16.72, 18.60, 'واللي ما يطابق معيارنا'), (18.89, 20.12, 'ما يدخل العلبة'),
       (20.43, 23.09, 'وهذا اللي يخلي كينام بيتهوفن'), (23.29, 24.25, 'تريبل سوبر'), (24.60, 26.26, 'من أفخم اختياراتنا'),
       (26.55, 27.56, 'من المصدر'), (27.82, 28.86, 'لين مجلسك'), (29.16, 32.64, 'اطلبه الحين مع الضمان الذهبي من بيتهوفن'), (32.82, 35.56, 'وادفع عن طريق تابي أو تمارا')]
END_S = {2, 5, 9, 11, 14, 16, 17}
TEMPO = 1.09
w = wave.open('take5.wav'); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
pad = int(0.04 * sr); out = []; t = 0.0; mp = []
for i, (a, b, txt) in enumerate(SEG, 1):
    s = x[max(0, int(a * sr) - pad):int(b * sr) + pad].copy(); f = int(0.01 * sr); s[:f] *= np.linspace(0, 1, f); s[-f:] *= np.linspace(1, 0, f)
    st = t; out.append(s); t += len(s) / sr; mp.append([i, txt, st + 0.04, t - 0.04])
    if i < len(SEG): g = 0.34 if i in END_S else 0.20; out.append(np.zeros(int(g * sr), np.float32)); t += g
y = np.concatenate(out); y = np.concatenate([np.zeros(int(0.10 * sr), np.float32), y])
open('tmp.raw', 'wb').write(np.clip(y, -32768, 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(sr), '-ac', '1', '-i', 'tmp.raw', '-af', f'atempo={TEMPO}', 'vo_source.wav'], check=True)
import os; os.remove('tmp.raw')
json.dump({'phrases': [{'i': i, 'text': txt, 'start': round((a + 0.10) / TEMPO, 2), 'end': round((b + 0.10) / TEMPO, 2)} for i, txt, a, b in mp]},
          open('vo_source_map.json', 'w'), ensure_ascii=False, indent=1)
print('dur', round(len(y) / sr / TEMPO, 2))
