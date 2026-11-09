"""Voice tools: find the pauses, add breathing room between sentences, or cut a phrase out.

  python pace_voice.py gaps   ad.mp4                       -> list of silences (start, end) to choose from
  python pace_voice.py insert ad.mp4 out.m4a "5.45:0.35 7.76:0.35 ..."   -> adds room tone at those times
  python pace_voice.py cut    ad.mp4 out.m4a 11.40 13.333                -> removes a phrase (40 ms fades)

`insert` also writes out.m4a.json = [[time, extra], ...]: pass it as "time_map" to karaoke_captions.py and use
it to stretch each scene (new_frames = old_frames + 30*sum(extra inside the scene)); stretch picture with
ffmpeg "setpts=PTS*r,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1" (keep r <= 1.2).
Only insert inside real silences (< -42 dB), at sentence ends: 0.3-0.4 s; a breath inside a sentence 0.2 s.
"""
import json, subprocess, sys
import numpy as np

cmd, src = sys.argv[1], sys.argv[2]; SR = 48000
a = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                                 capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)
if cmd == 'gaps':
    m = a.mean(1); hop = SR // 100; r = np.sqrt(np.convolve(m * m, np.ones(2 * hop) / (2 * hop), 'same'))[::hop]
    sil = 20 * np.log10(r + 1e-6) < -42; i = 0
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]: j += 1
            if j - i >= 6: print(f'{i / 100:.2f} - {j / 100:.2f}  ({(j - i) / 100:.2f} s)')
            i = j
        else: i += 1
    sys.exit()
out = sys.argv[3]
if cmd == 'insert':
    INS = sorted([tuple(map(float, p.split(':'))) for p in sys.argv[4].split()]); rng = np.random.RandomState(0); parts = []; prev = 0
    for t, d in INS:
        i = int(t * SR); parts.append(a[prev:i]); seg = a[max(0, i - SR // 20):i + SR // 20]
        parts.append((rng.randn(int(d * SR), 2) * min(float(np.sqrt((seg ** 2).mean())), 0.0005)).astype(np.float32)); prev = i
    parts.append(a[prev:]); b = np.concatenate(parts); json.dump([list(x) for x in INS], open(out + '.json', 'w'))
elif cmd == 'cut':
    t0, t1 = float(sys.argv[4]), float(sys.argv[5]); i0, i1 = int(t0 * SR), int(t1 * SR); f = SR // 25
    x, y = a[:i0].copy(), a[i1:].copy(); x[-f:] *= np.linspace(1, 0, f)[:, None]; y[:f] *= np.linspace(0, 1, f)[:, None]
    b = np.concatenate([x, y])
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'aac', '-b:a', '192k', out],
               input=b.astype(np.float32).tobytes(), check=True)
print('wrote', out, round(len(b) / SR, 3), 's')
