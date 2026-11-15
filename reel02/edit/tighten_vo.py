"""Reel 02 v2 pace (client 15 Nov: "faster rhythm, shorter silences between the important lines, like the last reviews reel").
Every long silence of the ORIGINAL VO (measured: pace_voice.py gaps, < -42 dB) is set to a target length by removing (or adding)
room tone in the MIDDLE of the silence only, with 20 ms crossfades. Speech is never cut, stretched or sped up.
Writes audio/vo_paced.wav and audio/vo_pauses.json {"pauses_added": [[gap_mid, delta_s], ...]} (delta < 0 = removed)."""
import numpy as np, subprocess, json
A = '/home/user/canva21/reel02/audio/'; SR = 48000
a = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', A + 'voice_over.mp3', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                                 capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)
# (gap start, gap end, target length) — original-VO seconds
G = [(2.01, 2.64, .30), (4.61, 5.56, .35), (8.12, 8.72, .30), (9.62, 10.37, .35), (12.28, 12.89, .30), (13.98, 15.08, .45),
     (16.33, 17.16, 1.30),                                     # customer photo card sits in this pause
     (17.93, 18.79, .25), (20.82, 21.60, .35), (22.28, 23.18, .40), (23.73, 24.53, .25), (25.23, 25.92, .30), (27.22, 28.20, .35),
     (29.95, 30.39, .30), (33.29, 33.71, .30), (34.70, 35.21, .30), (37.39, 38.21, .35), (39.31, 40.12, .35), (42.65, 43.71, .40),
     (45.25, 45.79, .30)]
X = int(0.02 * SR); out = []; prev = 0; edits = []; rng = np.random.RandomState(0)
for s, e, tgt in G:
    mid = (s + e) / 2; d = tgt - (e - s); i = int(mid * SR)
    if d < 0:
        r = int(-d * SR); i0, i1 = i - r // 2, i - r // 2 + r
        seg = a[prev:i0].copy(); tail = a[i1:i1 + X].copy(); fade = np.linspace(1, 0, X)[:, None]
        seg[-X:] = seg[-X:] * fade + tail * (1 - fade); out.append(seg); prev = i1 + X
    else:
        lvl = min(float(np.sqrt((a[i - SR // 20:i + SR // 20] ** 2).mean())), 0.0005)
        out.append(a[prev:i]); out.append((rng.randn(int(d * SR), 2) * lvl).astype(np.float32)); prev = i
    edits.append([round(mid, 3), round(d, 3)])
out.append(a[prev:]); b = np.concatenate(out)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_s16le', A + 'vo_paced.wav'], input=b.tobytes(), check=True)
json.dump({'pauses_added': edits, 'targets': G, 'silence_only': True, 'no_time_stretch': True, 'duration_s': round(len(b) / SR, 3),
           'note': 'v2 pace 15 Nov; v1 (+0.8 s photo pause only) was 48.81 s'}, open(A + 'vo_pauses.json', 'w'), indent=1)
print('paced VO', round(len(b) / SR, 2), 's; removed', round(-sum(d for _, d in edits), 2), 's net')
