"""Kinam mixes: paced VO + pop SFX on graphics (+ approved heritage music, -20 dB under silence / -28 dB under voice), -14 LUFS / -1.5 dBTP two-pass."""
import numpy as np, subprocess, json, os
K = '/home/user/canva21/kinam_majlis/'; A = K + 'audio/'; os.makedirs(A, exist_ok=True)
sr = 48000; VM = json.load(open(K + 'vo/vo_majlis_map.json')); END = round(VM['phrases'][-1]['end'] + 1.35, 2); N = int(END * sr)
def rd(f):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '2', '-ar', '48000', '-f', 'f32le', '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()
v = rd(K + 'vo/vo_majlis.wav'); v = np.concatenate([v, np.zeros((max(0, N - len(v)), 2), np.float32)])[:N]
pop = rd('/home/user/canva21/reel01/audio/pop_sfx.wav'); pop[-int(0.03 * sr):] *= np.linspace(1, 0, int(0.03 * sr))[:, None]
POPS = json.load(open(K + 'edit/pop_times.json')); pops = np.zeros_like(v)
for k, t in POPS.items():
    i = int((t - 0.035) * sr); seg = pop[:max(0, min(len(pop), N - i))]; pops[i:i + len(seg)] += seg * 0.85
vp = v + pops
m = rd('/home/user/canva21/reel01/audio/music_heritage_v3.mp3')[int(69.0 * sr):int(69.0 * sr) + N]
hop = int(0.02 * sr); n = N // hop
e = np.array([np.sqrt((v[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)])
act = np.convolve((20 * np.log10(e + 1e-9) > -38).astype(float), np.ones(13), 'same') > 0
g = np.zeros(n); cur = 0
for i in range(n):
    tg = 1.0 if act[i] else 0.0; cur += (0.33 if tg > cur else 0.044) * (tg - cur); g[i] = cur
duck = np.repeat(10 ** ((-20 - 8 * g) / 20), hop); duck = np.concatenate([duck, np.full(N - len(duck), duck[-1])])
tt = np.arange(N) / sr; env = duck * np.clip(tt / 0.8, 0, 1) * np.clip((END - tt) / 2.0, 0, 1)
for name, mix in [('mix_music', vp + m * env[:, None]), ('mix_no_music', vp)]:
    mix.astype(np.float32).tofile(A + name + '.f32')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', A + name + '.f32', '-c:a', 'pcm_s16le', A + name + '_raw.wav'], check=True)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', A + name + '_raw.wav', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    f = f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', A + name + '_raw.wav', '-af', f, '-ar', '48000', A + name + '.wav'], check=True)
    os.remove(A + name + '.f32'); os.remove(A + name + '_raw.wav'); print(name, 'ok')
