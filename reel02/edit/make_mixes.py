"""Reel 02 audio: paced VO + pops (+ approved Reel 01 heritage music, read-only) -> -14 LUFS / -1.5 dBTP, two-pass loudnorm.
usage: python reel02/edit/make_mixes.py END   (writes reel02/audio/mix_music.wav, mix_no_music.wav)"""
import numpy as np, subprocess, json, os, sys
A = '/home/user/canva21/reel02/audio/'; R1 = '/home/user/canva21/reel01/audio/'
sr = 48000; END = float(sys.argv[1]); N = int(END * sr)
def rd(f):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '2', '-ar', '48000', '-f', 'f32le', '-'], capture_output=True); return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()
v = rd(A + 'vo_paced.wav'); v = np.concatenate([v, np.zeros((max(0, N - len(v)), 2), np.float32)])[:N]
pop = rd(R1 + 'pop_sfx.wav'); pop[-int(0.03 * sr):] *= np.linspace(1, 0, int(0.03 * sr))[:, None]
pops = np.zeros_like(v)
for k, t in json.load(open(A + 'pop_times.json')).items():
    g = 0.55 if k in ('R2A', 'PHOTO', 'R2B4', 'reveal') else 0.85; i = int((t - 0.035) * sr); pops[i:i + len(pop)] += pop[:max(0, N - i)] * g
vp = v + pops
# steadiest window of the approved heritage track (continuity test: share of 0.5 s windows >10 dB under the median)
mu = rd(R1 + 'music_heritage_v3.mp3'); best = None
for off in np.arange(0, (len(mu) - N) / sr, 0.5):
    seg = mu[int(off * sr):int(off * sr) + N].mean(1); w = int(0.5 * sr)
    db = 20 * np.log10(np.sqrt((seg[:len(seg) // w * w].reshape(-1, w) ** 2).mean(1)) + 1e-9)
    q = float((db < np.median(db) - 10).mean())
    if best is None or q < best[0]: best = (q, off)
q, OFF = best; print(f'music window {OFF:.1f}-{OFF + END:.1f} s, quiet-window share {q:.3f}')
m = mu[int(OFF * sr):int(OFF * sr) + N]
GAP_DB, UNDER_DB = -20, -28; hop = int(0.02 * sr); n = N // hop
e = np.array([np.sqrt((v[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)])
act = np.convolve((20 * np.log10(e + 1e-9) > -38).astype(float), np.ones(13), 'same') > 0
g = np.zeros(n); cur = 0
for i in range(n):
    tg = 1.0 if act[i] else 0.0; cur += (0.33 if tg > cur else 0.044) * (tg - cur); g[i] = cur
duck = np.repeat(10 ** ((GAP_DB + (UNDER_DB - GAP_DB) * g) / 20), hop); duck = np.concatenate([duck, np.full(N - len(duck), duck[-1])])
tt = np.arange(N) / sr; env = duck * np.clip(tt / 0.8, 0, 1) * np.clip((END - tt) / 2.0, 0, 1)
json.dump({'music': R1 + 'music_heritage_v3.mp3', 'window_s': [OFF, OFF + END], 'quiet_share': q, 'gap_db': GAP_DB, 'under_db': UNDER_DB}, open(A + 'music_window.json', 'w'), indent=1)
for name, mix in [('mix_music', vp + m * env[:, None]), ('mix_no_music', vp)]:
    raw = A + name + '_raw.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', '-', '-c:a', 'pcm_s16le', raw], input=mix.astype(np.float32).tobytes(), check=True)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', raw, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    f = f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', f, '-ar', '48000', A + name + '.wav'], check=True); os.remove(raw); print(name, 'ok')
