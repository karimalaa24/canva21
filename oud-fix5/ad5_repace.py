"""Ad 5 at the approved ad pace (same principle as reel 01): long inter-phrase gaps trimmed to ~0.32 s (0.40 s before the
offer and before the closing), speech x1.03 (pitch kept), light compression + presence, -14 LUFS.
Writes audio/timemap.json (used by base5.py / titles5.py through env TMAP) + voice / mixes."""
import numpy as np, subprocess, json, os
V5 = '/tmp/claude-0/-home-user-canva21/d92bd60e-9f87-52c3-ac35-11b21dbe0949/scratchpad/v5/'
A = '/home/user/canva21/oud-fix5/audio/'; sr = 48000; TEMPO = 1.03
# measured gaps in voice6.wav (old ad-5 timeline): (gap start, gap end, target)
GAPS = [(8.24, 9.02, 0.40), (14.31, 14.61, 0.30), (15.22, 15.68, 0.32), (16.69, 17.12, 0.32), (18.18, 18.50, 0.32),
        (19.44, 19.88, 0.32), (22.17, 22.84, 0.32), (23.86, 24.21, 0.32), (26.50, 27.17, 0.40), (28.37, 28.74, 0.32)]
P = [[round((a + b) / 2, 3), round(min(0.0, tg - (b - a)), 3)] for a, b, tg in GAPS]
def M(t):
    s = t
    for p, d in P:
        r = -d; a, b = p - r / 2, p + r / 2
        if t >= b: s -= r
        elif t > a: s -= (t - a)
    return s / TEMPO
END = round(M(29.94) + 1.35, 2)
json.dump({'tempo': TEMPO, 'pauses_added': P, 'end': END}, open(A + 'timemap.json', 'w'), indent=1)
def rd(f, ch=2):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', str(ch), '-ar', '48000', '-f', 'f32le', '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, ch).copy()
x = rd(V5 + 'voice6.wav'); out = []; last = 0
for p, d in P:
    r = -d; s = int((p - r / 2) * sr); e = int((p + r / 2) * sr); out.append(x[last:s]); last = e
out.append(x[last:]); np.concatenate(out).astype(np.float32).tofile(A + 't.f32')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', A + 't.f32', '-af',
                f'atempo={TEMPO},highpass=f=70,equalizer=f=3200:t=q:w=1.2:g=2,acompressor=threshold=-20dB:ratio=2.5:attack=6:release=100:makeup=1.5',
                '-ar', '48000', '-c:a', 'pcm_s16le', A + 'voice_paced.wav'], check=True); os.remove(A + 't.f32')
N = int(END * sr); v = rd(A + 'voice_paced.wav'); v = np.concatenate([v, np.zeros((max(0, N - len(v)), 2), np.float32)])[:N]
pop = rd('/home/user/canva21/reel01/audio/pop_sfx.wav'); pop[-int(0.03 * sr):] *= np.linspace(1, 0, int(0.03 * sr))[:, None]
for t in [M(25.85), M(26.15)]:            # tabby / tamara pops (review-pile pops are already in the voice track)
    i = int((t - 0.035) * sr); v[i:i + len(pop)] += pop * 0.85
m = rd(V5 + 'music.mp3'); m = np.concatenate([m, np.zeros((max(0, N - len(m)), 2), np.float32)])[:N]
hop = int(0.02 * sr); n = N // hop
e = np.array([np.sqrt((v[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)])
act = np.convolve((20 * np.log10(e + 1e-9) > -38).astype(float), np.ones(13), 'same') > 0
g = np.zeros(n); cur = 0
for i in range(n):
    tg = 1.0 if act[i] else 0.0; cur += (0.33 if tg > cur else 0.044) * (tg - cur); g[i] = cur
duck = np.repeat(10 ** ((-22 - 8 * g) / 20), hop); duck = np.concatenate([duck, np.full(N - len(duck), duck[-1])])
tt = np.arange(N) / sr; env = duck * np.clip(tt / 0.6, 0, 1) * np.clip((END - tt) / 1.6, 0, 1)
for name, mix in [('mix_music', v + m * env[:, None]), ('mix_no_music', v)]:
    mix.astype(np.float32).tofile(A + name + '.f32')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', A + name + '.f32', '-c:a', 'pcm_s16le', A + name + '_raw.wav'], check=True)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', A + name + '_raw.wav', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    f = f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', A + name + '_raw.wav', '-af', f, '-ar', '48000', A + name + '.wav'], check=True)
    os.remove(A + name + '.f32'); os.remove(A + name + '_raw.wav')
print('removed', round(-sum(d for _, d in P), 2), 's, tempo', TEMPO, '-> END', END)
