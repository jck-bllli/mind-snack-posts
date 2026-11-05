"""Narration (Chatterbox Turbo, the accounts' built-in voice) + word timing + sfx for the first beat."""
import os, sys, json, subprocess, tempfile, math
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "generator"))
import chatterbox_voice as cv

SR = 48000
SENT = ["I fold a paper boat and put it on the river.", "A boat as sturdy as soggy toast."]
TEMPO = 1.2

def tempo(a, f):
    with tempfile.TemporaryDirectory() as td:
        sf.write(td + "/i.wav", a, SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", td + "/i.wav", "-af", f"atempo={f}", td + "/o.wav"], check=True)
        o, _ = sf.read(td + "/o.wav", dtype="float32")
    return o

clips = [tempo(cv.say(s, "turbo"), TEMPO) for s in SENT]
pos = 0.25
words, segs = [], []
for s, c in zip(SENT, clips):
    d = len(c) / SR
    ws = s.split()
    wt = [len(w) + 2 for w in ws]
    acc = 0.0
    for w, x in zip(ws, wt):
        words.append({"t": round(pos + d * acc / sum(wt), 3), "w": w})
        acc += x
    segs.append((pos, c))
    pos += d + 0.18
end = pos
total = end + 0.5

def tw(prefix, fb):
    for w in words:
        if w["w"].lower().startswith(prefix):
            return w["t"]
    return fb
t_land = tw("river", 1.7) + 0.1
t_sag = tw("sturdy", 3.0)
t_toast = tw("toast", 4.0)

n = int(SR * (total + 0.2))
out = np.zeros(n, np.float32)
def add(st, sig):
    i = int(st * SR)
    m = min(len(sig), n - i)
    if m > 0: out[i:i + m] += sig[:m].astype(np.float32)
for st, c in segs: add(st, c)
rng = np.random.default_rng(5)
def tt(d): return np.arange(int(SR * d)) / SR
x = tt(0.14); add(0.45, 0.12 * rng.standard_normal(len(x)) * np.exp(-x * 30))           # paper fold
x = tt(0.35); add(t_land - 0.02, 0.4 * np.sin(2 * np.pi * (420 - 600 * x) * x) * np.exp(-x * 12) + 0.08 * rng.standard_normal(len(x)) * np.exp(-x * 18))  # plop
x = tt(0.6); k = np.ones(300) / 300; add(t_sag, 0.5 * np.convolve(rng.standard_normal(len(x)), k, "same") * (1 + np.sin(x * 40)) * np.exp(-x * 4))  # soggy squelch
x = tt(0.4); add(t_toast, 0.35 * np.sin(2 * np.pi * 90 * x) * np.exp(-x * 9))               # toast flop
pk = np.abs(out).max()
if pk > 0.9: out *= 0.9 / pk
sf.write("final.wav", out, SR)
json.dump({"words": words, "total": round(total, 3), "t_land": round(t_land, 3), "t_sag": round(t_sag, 3), "t_toast": round(t_toast, 3)},
          open("godot/timing.json", "w"))
print("narration end", round(end, 2), "total", round(total, 2))
