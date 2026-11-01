# Original jam-band style score for the 45 s Sag Harbor v4 cut (no existing songs, melodies or samples).
# 128 bpm (one bar = 1.875 s, 24 bars), E mixolydian, I - bVII - IV - I. Karplus-Strong guitar, drawbar organ,
# walking bass, shuffle drums. Wobble and sweep follow the trip. Calm hold on the key cinema shot, then peaks on
# the cinema sign (16.8 s), the windmill pinwheel (28.6 s) and the whale spout (39.5 s). Ends on the opening lick.
import sys, wave
import numpy as np

out_path = sys.argv[1] if len(sys.argv) > 1 else 'score.wav'
SR, T, BPM = 48000, 45.0, 128
BEAT = 60 / BPM
BAR = 4 * BEAT
N = int(SR * T)
t = np.arange(N) / SR
rng = np.random.default_rng(11)
L = np.zeros(N); Rt = np.zeros(N)
# shot times (match SHOTS in scene_sh.html)
KEY_CALM, KEY_TRIP, KEY_END = 15.0, 16.8, 19.0
WINDMILL, PINWHEEL, HARBOR = 27.0, 28.6, 31.5
WHALE, SPOUT, RAIN = 36.0, 39.5, 42.0

def env(a, b): return np.clip((t - a) / (b - a), 0, 1)
def add(sig, start, gain=1.0, pan=0.0):
    i0 = int(start * SR)
    if i0 >= N or i0 < 0: return
    sig = sig[:N - i0]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i0:i0 + len(sig)] += sig * gain * l * 1.41
    Rt[i0:i0 + len(sig)] += sig * gain * r * 1.41

def hz(note):
    names = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    n = names[note[0]]; rest = note[1:]
    if rest[0] in '#b': n += 1 if rest[0] == '#' else -1; rest = rest[1:]
    return 440 * 2 ** ((n + 12 * (int(rest) + 1) - 69) / 12)

def pluck(f, dur, bright=0.5, decay=0.996):
    P = max(2, int(round(SR / f))); n = int(dur * SR)
    buf = np.convolve(rng.uniform(-1, 1, P), [bright, 1 - bright], 'same')
    y = np.zeros(n + P); y[:P] = buf
    for i in range(P, n + P, P):
        prev = y[i - P:i]
        nxt = 0.5 * (prev + np.roll(prev, 1)) * decay
        y[i:i + P] = nxt[:len(y[i:i + P])]
    y = y[P:]
    a = np.minimum(1, np.arange(n) / 60); r = np.minimum(1, (n - np.arange(n)) / (0.04 * SR))
    return (np.tanh(2.2 * y) * 0.6 + y * 0.4) * a * r

def organ(freqs, dur, trem=5.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for h, g in [(0.5, 0.5), (1, 1.0), (2, 0.55), (3, 0.35), (4, 0.2), (6, 0.08)]:
            s += g * np.sin(2 * np.pi * f * h * tt + rng.uniform(0, 6))
    s *= (1 + 0.18 * np.sin(2 * np.pi * trem * tt)) / (len(freqs) * 2.7)
    return np.tanh(1.4 * s) * np.minimum(1, tt / 0.06) * np.minimum(1, (dur - tt) / 0.12)

def bass(f, dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.12 * np.sin(6 * np.pi * f * tt)
    return np.tanh(1.6 * s) * np.exp(-tt * 2.2) * np.minimum(1, tt / 0.005) * np.minimum(1, (dur - tt) / 0.03)

def kick():
    tt = np.arange(int(0.35 * SR)) / SR
    return np.sin(2 * np.pi * (52 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 11)
def snare():
    tt = np.arange(int(0.22 * SR)) / SR
    return 0.7 * rng.standard_normal(len(tt)) * np.exp(-tt * 22) + 0.4 * np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 30)
def hat(open_=False):
    tt = np.arange(int((0.18 if open_ else 0.05) * SR)) / SR
    n = rng.standard_normal(len(tt)); n = n - np.convolve(n, np.ones(6) / 6, 'same')
    return n * np.exp(-tt * (14 if open_ else 70))
def crash(d=2.2):
    tt = np.arange(int(d * SR)) / SR
    n = rng.standard_normal(len(tt)); n = n - np.convolve(n, np.ones(4) / 4, 'same')
    return n * np.exp(-tt * 1.8)

CH = {'E': ['E3', 'G#3', 'B3', 'D4'], 'D': ['D3', 'F#3', 'A3', 'C4'], 'A': ['A2', 'C#3', 'E3', 'G3']}
prog = ['E', 'D', 'A', 'E'] * 6
nbars = int(round(T / BAR))
calm = lambda s: KEY_CALM <= s < KEY_TRIP          # the key shot sits calm and real
intro = lambda s: s < 10                            # museum + church: sparse
trip = np.clip(0.1 * env(10, 12) + 0.25 * env(KEY_TRIP, 18) - 0.2 * env(18.8, 19.2) + 0.2 * env(WINDMILL, 30)
               + 0.15 * env(HARBOR, 34) + 0.25 * env(WHALE, SPOUT) - 0.6 * env(43, 44.8), 0, 1)
trip[(t >= KEY_CALM) & (t < KEY_TRIP)] = 0
def trip_at(s): return float(trip[min(N - 1, int(s * SR))])

# opening lick (original), also closes the loop
LICK = [('E4', 0, .5), ('G#4', .5, .25), ('B4', .75, .5), ('C#5', 1.25, .25), ('B4', 1.5, .5), ('A4', 2, .5), ('G#4', 2.5, .5), ('E4', 3, 1)]
def play_lick(start, gain=0.55):
    for n, b, d in LICK: add(pluck(hz(n), d * BEAT + 0.6, bright=0.55), start + b * BEAT, gain, -0.35)
play_lick(0.0)
play_lick(KEY_CALM + 0.1, 0.45)      # the lick again, gently, as the cinema comes up
play_lick(T - BAR)                    # loop back to the start

for b in range(nbars):
    s0 = b * BAR; ch = CH[prog[b]]
    if s0 >= T - BAR: break
    # comping stabs (skip in the calm hold)
    if not calm(s0) and s0 >= 2 * BAR:
        for beat in [1 + 2 / 3, 3 + 2 / 3]:
            for k, n in enumerate(ch[1:]):
                add(pluck(hz(n) * 2, 0.45, bright=0.35, decay=0.993), s0 + beat * BEAT + k * 0.012, 0.15, -0.45)
    # noodly lead: at the Wharf Shop and from the windmill on, higher over the harbor
    if (19 <= s0 < 27) or (s0 >= WINDMILL):
        scale = ['E4', 'F#4', 'G#4', 'A4', 'B4', 'C#5', 'D5', 'E5', 'F#5', 'G#5']
        steps, idx = (8, 3) if s0 < HARBOR else (12, 5)
        for k in range(steps):
            st = s0 + k * BAR / steps + (0.04 if k % 2 else 0)
            idx = int(np.clip(idx + rng.choice([-2, -1, 1, 1, 2]), 0, len(scale) - 1))
            add(pluck(hz(scale[idx]), 0.5, bright=0.6), st, 0.3 + 0.12 * trip_at(st), -0.2)
    # organ
    g = 0.08 + 0.1 * trip_at(s0) + (0.1 if calm(s0) else 0) + (0.05 if intro(s0) else 0)
    add(organ([hz(n) for n in ch], BAR), s0, g, 0.4)
    # walking bass (half-time feel in the intro and the calm hold)
    r = hz(ch[0]) / 2; nxt = hz(CH[prog[(b + 1) % len(prog)]][0]) / 2
    walk = [r, r * 2 ** (4 / 12), r * 2 ** (7 / 12), nxt * 2 ** (-1 / 12)]
    for k, f in enumerate(walk):
        if (intro(s0) or calm(s0)) and k % 2: continue
        add(bass(f, BEAT * (1.9 if (intro(s0) or calm(s0)) else 0.95)), s0 + k * BEAT, 0.4)
    # drums
    for beat in range(4):
        st = s0 + beat * BEAT
        if calm(st): continue
        if intro(st):
            add(hat(), st, 0.07, 0.5)
            if beat == 0: add(kick(), st, 0.45)
            continue
        if beat in (0, 2): add(kick(), st, 0.75)
        if beat in (1, 3): add(snare(), st, 0.35, 0.1)
        add(hat(), st, 0.12, 0.5); add(hat(), st + BEAT * 2 / 3, 0.09, 0.5)
        if st >= HARBOR and st < RAIN: add(hat(True), st + BEAT / 3, 0.06, 0.55)

# rolls into each peak, then the hits
for peak, length in [(KEY_TRIP, 0.6), (PINWHEEL, 1.2), (SPOUT, 1.5)]:
    for k in range(int(16 * length)):
        st = peak - length + k * length / (16 * length)
        add(snare(), st, 0.06 + 0.3 * k / (16 * length), 0.1)
    add(crash(), peak, 0.45, -0.2); add(kick(), peak, 1.0)
add(organ([hz(n) for n in ['E3', 'G#3', 'B3', 'D4', 'E4']], 2.2, trem=6.5), KEY_TRIP, 0.4, 0.2)
add(organ([hz(n) for n in ['D3', 'A3', 'D4', 'F#4', 'A4']], 2.8, trem=6.5), PINWHEEL, 0.42, -0.1)
add(organ([hz(n) for n in ['E2', 'B2', 'E3', 'G#3', 'B3', 'D4', 'E4', 'G#4']], 4.5, trem=6.8), SPOUT, 0.6, 0.0)

mix = np.stack([L, Rt])
def vdelay(x, d):
    idx = np.arange(N) - d * SR
    i0 = np.clip(np.floor(idx).astype(int), 0, N - 1); fr = idx - np.floor(idx)
    return x[i0] * (1 - fr) + x[np.clip(i0 + 1, 0, N - 1)] * fr
wob = 0.004 + 0.0025 * trip * (np.sin(2 * np.pi * 0.7 * t) + 0.4 * np.sin(2 * np.pi * 3.1 * t))
mix = np.stack([vdelay(ch, wob) for ch in mix])
sweep = 0.0008 + 0.0022 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t))
mix = np.stack([ch + 0.55 * trip * vdelay(ch, sweep + 0.0003 * k) * (-1) ** k for k, ch in enumerate(mix)])
mix *= np.minimum(1, t / 0.01) * np.minimum(1, (T - t) / 0.03)
mix /= np.max(np.abs(mix)) * 1.05
pcm = (mix.T * 32767).astype(np.int16)
w = wave.open(out_path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('wrote', out_path, f'{T}s stereo {SR} Hz, {nbars} bars at {BPM} bpm')
