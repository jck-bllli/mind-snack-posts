# Original jam-band style score for the 30 s Sag Harbor scene (no existing songs, melodies or samples).
# 120 bpm, E mixolydian, I - bVII - IV - I. Plucked Karplus-Strong guitar, drawbar organ, walking bass, shuffle drums.
# Phaser-ish sweep and tape wobble grow with the trip; build at the Wharf Shop stop (10.5-13.5 s), lift on the
# Long Wharf swoop (13.5-20.5 s), big organ chord when the whale spouts (22.5 s), ends on the opening lick to loop.
import sys, wave
import numpy as np

out_path = sys.argv[1] if len(sys.argv) > 1 else 'score.wav'
SR, T, BPM = 48000, 30.0, 120
BEAT = 60 / BPM
N = int(SR * T)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
L = np.zeros(N); Rt = np.zeros(N)

def env(a, b): return np.clip((t - a) / (b - a), 0, 1)
def add(sig, start, gain=1.0, pan=0.0):
    i0 = int(start * SR)
    if i0 >= N: return
    sig = sig[:N - i0]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i0:i0 + len(sig)] += sig * gain * l * 1.41
    Rt[i0:i0 + len(sig)] += sig * gain * r * 1.41

def hz(note):  # 'E4', 'G#3', 'Bb2'
    names = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    n = names[note[0]]; rest = note[1:]
    if rest[0] in '#b': n += 1 if rest[0] == '#' else -1; rest = rest[1:]
    return 440 * 2 ** ((n + 12 * (int(rest) + 1) - 69) / 12)

def pluck(f, dur, bright=0.5, decay=0.996):
    """Karplus-Strong string, block-vectorised."""
    P = max(2, int(round(SR / f))); n = int(dur * SR)
    buf = rng.uniform(-1, 1, P)
    buf = np.convolve(buf, [bright, 1 - bright], 'same')
    y = np.zeros(n + P); y[:P] = buf
    for i in range(P, n + P, P):
        prev = y[i - P:i]
        nxt = 0.5 * (prev + np.roll(prev, 1)) * decay
        y[i:i + P] = nxt[:len(y[i:i + P])]
    y = y[P:]
    a = np.minimum(1, np.arange(n) / 60)                       # tiny attack, no click
    r = np.minimum(1, (n - np.arange(n)) / (0.04 * SR))        # release
    twang = np.tanh(2.2 * y) * 0.6 + y * 0.4                   # a bit of bite
    return twang * a * r

def organ(freqs, dur, trem=5.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for h, g in [(0.5, 0.5), (1, 1.0), (2, 0.55), (3, 0.35), (4, 0.2), (6, 0.08)]:
            s += g * np.sin(2 * np.pi * f * h * tt + rng.uniform(0, 6))
    s *= (1 + 0.18 * np.sin(2 * np.pi * trem * tt)) / (len(freqs) * 2.7)
    a = np.minimum(1, tt / 0.06); r = np.minimum(1, (dur - tt) / 0.12)
    return np.tanh(1.4 * s) * a * r

def bass(f, dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.12 * np.sin(6 * np.pi * f * tt)
    return np.tanh(1.6 * s) * np.exp(-tt * 2.2) * np.minimum(1, tt / 0.005) * np.minimum(1, (dur - tt) / 0.03)

def kick():
    tt = np.arange(int(0.35 * SR)) / SR
    return np.sin(2 * np.pi * (52 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 11)
def snare():
    tt = np.arange(int(0.22 * SR)) / SR
    return (0.7 * rng.standard_normal(len(tt)) * np.exp(-tt * 22) + 0.4 * np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 30))
def hat(open_=False):
    tt = np.arange(int((0.18 if open_ else 0.05) * SR)) / SR
    n = rng.standard_normal(len(tt)); n = n - np.convolve(n, np.ones(6) / 6, 'same')
    return n * np.exp(-tt * (14 if open_ else 70))
def crash():
    tt = np.arange(int(2.2 * SR)) / SR
    n = rng.standard_normal(len(tt)); n = n - np.convolve(n, np.ones(4) / 4, 'same')
    return n * np.exp(-tt * 1.8)

# --- harmony: one chord per bar (2 s) ---
CH = {'E': ['E3', 'G#3', 'B3', 'D4'], 'D': ['D3', 'F#3', 'A3', 'C4'], 'A': ['A2', 'C#3', 'E3', 'G3']}
prog = ['E', 'D', 'A', 'E'] * 4
bar = 4 * BEAT
nbars = int(T / bar)

# trip amount over time (drives wobble, sweep, density)
trip = 0.15 * env(4.5, 8) + 0.25 * env(10.5, 13.5) + 0.35 * env(13.5, 20.5) + 0.25 * env(20, 23) - 0.5 * env(27, 29.5)
trip = np.clip(trip, 0, 1)
def trip_at(s): return float(trip[min(N - 1, int(s * SR))])

# --- opening lick (original): E mixolydian figure, also closes the loop ---
LICK = [('E4', 0, .5), ('G#4', .5, .25), ('B4', .75, .5), ('C#5', 1.25, .25), ('B4', 1.5, .5), ('A4', 2, .5), ('G#4', 2.5, .5), ('E4', 3, 1)]
def play_lick(start, gain=0.55, octave=1.0):
    for n, b, d in LICK:
        add(pluck(hz(n) * octave, d * BEAT + 0.6, bright=0.55), start + b * BEAT, gain, -0.35)
play_lick(0.0)
play_lick(28.0)  # loop back to the start

# --- guitar comping and lead ---
for b in range(1, nbars - 1):
    s0 = b * bar; ch = CH[prog[b]]
    # chord stabs on the and-of-2 and 4 (shuffled)
    for beat in [1 + 2 / 3, 3 + 2 / 3]:
        for k, n in enumerate(ch[1:]):
            add(pluck(hz(n) * 2, 0.45, bright=0.35, decay=0.993), s0 + beat * BEAT + k * 0.012, 0.16, -0.45)
    # noodly lead from the Wharf Shop stop on, higher and busier on the swoop
    if s0 >= 10:
        scale = ['E4', 'F#4', 'G#4', 'A4', 'B4', 'C#5', 'D5', 'E5', 'F#5', 'G#5']
        lvl = 0 if s0 < 13.5 else 2
        steps = 8 if s0 < 13.5 else 12
        idx = 3 + lvl
        for k in range(steps):
            st = s0 + k * bar / steps + (0.04 if k % 2 else 0)
            idx = int(np.clip(idx + rng.choice([-2, -1, 1, 1, 2]), 0, len(scale) - 1))
            add(pluck(hz(scale[idx]), 0.5, bright=0.6), st, 0.32 + 0.12 * trip_at(st), -0.2)

# --- organ pads: swell into the Wharf Shop, sustain through the swoop, huge chord at the spout ---
for b in range(nbars):
    s0 = b * bar
    g = 0.10 + 0.10 * trip_at(s0) + 0.12 * float(10.5 <= s0 < 13.5)
    add(organ([hz(n) for n in CH[prog[b]]], bar), s0, g, 0.4)
big = organ([hz(n) for n in ['E2', 'B2', 'E3', 'G#3', 'B3', 'D4', 'E4', 'G#4']], 5.0, trem=6.8)
add(big, 22.4, 0.55, 0.0)

# --- walking bass ---
for b in range(nbars):
    s0 = b * bar; root = CH[prog[b]][0]
    r = hz(root) / 2
    nxt = hz(CH[prog[(b + 1) % len(prog)]][0]) / 2
    walk = [r, r * 2 ** (4 / 12), r * 2 ** (7 / 12), nxt * 2 ** (-1 / 12)]
    for k, f in enumerate(walk):
        add(bass(f, BEAT * 0.95), s0 + k * BEAT, 0.42, 0.0)

# --- shuffle drums ---
for b in range(nbars):
    s0 = b * bar
    for beat in range(4):
        st = s0 + beat * BEAT
        if beat in (0, 2): add(kick(), st, 0.75)
        if beat in (1, 3): add(snare(), st, 0.35, 0.1)
        add(hat(), st, 0.12, 0.5); add(hat(), st + BEAT * 2 / 3, 0.09, 0.5)
        if 13.5 <= st < 20.5: add(hat(True), st + BEAT / 3, 0.06, 0.55)   # busier ride on the swoop
# snare roll build into the swoop
for k in range(24):
    st = 12.0 + k * 1.5 / 24
    add(snare(), st, 0.08 + 0.3 * k / 24, 0.1)
add(crash(), 13.5, 0.35, -0.2)
add(crash(), 22.4, 0.5, 0.2)
add(kick(), 22.4, 1.0)

mix = np.stack([L, Rt])

# --- tape wobble: modulated delay that deepens with the trip ---
def vdelay(x, d):
    idx = np.arange(N) - d * SR
    i0 = np.clip(np.floor(idx).astype(int), 0, N - 1); fr = idx - np.floor(idx)
    i1 = np.clip(i0 + 1, 0, N - 1)
    return x[i0] * (1 - fr) + x[i1] * fr
wob = 0.004 + 0.0025 * trip * (np.sin(2 * np.pi * 0.7 * t) + 0.4 * np.sin(2 * np.pi * 3.1 * t))
mix = np.stack([vdelay(ch, wob) for ch in mix])
# --- phaser-ish sweep: short swept comb mixed with dry, depth follows the trip ---
sweep = 0.0008 + 0.0022 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t))
mix = np.stack([ch + 0.55 * trip * vdelay(ch, sweep + 0.0003 * k) * (-1) ** k for k, ch in enumerate(mix)])
# gentle fade-in safety and loop seam
mix *= np.minimum(1, t / 0.01) * np.minimum(1, (T - t) / 0.03)
mix /= np.max(np.abs(mix)) * 1.05
pcm = (mix.T * 32767).astype(np.int16)
w = wave.open(out_path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('wrote', out_path, f'{T}s stereo {SR} Hz')
