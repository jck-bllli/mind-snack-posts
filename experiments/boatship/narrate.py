"""Narration (Chatterbox Turbo, the accounts' built-in voice) + word timing + sfx for the full video."""
import os, sys, json, subprocess, tempfile
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "generator"))
import chatterbox_voice as cv

SR = 48000
SENT = [
 "I fold a paper boat and put it on the river. A boat as sturdy as soggy toast.",
 "Your friend Dave climbs aboard. Splash. Dave is now a swimmer.",
 "So you build a wooden hull. Dave floats. Unfortunately, he now thinks he is a captain.",
 "Then a wave flips the whole thing. Some poor fisherman just caught a boat.",
 "So you add a keel, a heavy fin underneath that stops your boat from rolling over like a bored dog.",
 "Now your neighbor wants to cross the ocean. So you swap wood for steel and add an engine.",
 "Dave offers to steer. Dave has capsized a paper boat. Dave is now cargo.",
 "Then someone loads ten thousand containers. A sign says maximum weight. He read it upside down.",
 "The ship rides low, and the first storm bends it like a taco. So you add bulkheads, walls inside that stop one leak from sinking everything.",
 "Add radar, a crew, a flag and a port fee. Congratulations, you built a cargo ship.",
 "You started because you did not want wet shoes. Now you have spent six million dollars and Dave is suing for emotional damage.",
 "I fold a paper boat.",
]
TEMPO = 1.2

def tempo(a, f):
    with tempfile.TemporaryDirectory() as td:
        sf.write(td + "/i.wav", a, SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", td + "/i.wav", "-af", f"atempo={f}", td + "/o.wav"], check=True)
        o, _ = sf.read(td + "/o.wav", dtype="float32")
    return o

clips = []
for s in SENT:
    print("say:", s, flush=True)
    clips.append(tempo(cv.say(s, "turbo"), TEMPO))
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
    pos += d + 0.2
end = pos
total = end + 0.6

KEYS = [("land", "river."), ("sag", "sturdy"), ("toast", "toast."), ("swim", "swimmer."), ("hull", "hull."),
        ("floats", "floats."), ("captain", "captain."), ("wave", "wave"), ("fisher", "fisherman"), ("keel", "keel,"),
        ("ocean", "ocean."), ("steel", "steel"), ("engine", "engine."), ("steer", "steer."), ("cargo", "cargo."),
        ("cont", "containers."), ("sign", "sign"), ("upside", "upside"), ("storm", "storm"), ("bulk", "bulkheads,"),
        ("radar", "radar,"), ("crew", "crew,"), ("flag", "flag"), ("fee", "fee."), ("million", "million"), ("sue", "suing")]
T, last = {}, 0.0
for name, pre in KEYS:
    hit = [w["t"] for w in words if w["w"].lower().startswith(pre) and w["t"] >= last]
    assert hit, f"word not found: {pre}"
    T[name] = hit[0]
    last = hit[0] - 0.01
T["land"] += 0.1
T["final"] = [w["t"] for w in words if w["w"].lower().startswith("fold")][-1] - 0.1

n = int(SR * (total + 0.2))
out = np.zeros(n, np.float32)
def add(st, sig):
    i = int(st * SR)
    m = min(len(sig), n - i)
    if m > 0: out[i:i + m] += sig[:m].astype(np.float32)
for st, c in segs: add(st, c)
rng = np.random.default_rng(5)
def tt(d): return np.arange(int(SR * d)) / SR
def noise(d): return rng.standard_normal(int(SR * d))
def lowp(x, k): return np.convolve(x, np.ones(k) / k, "same")
def splash(st, g=0.4):
    x = tt(0.4); add(st, g * np.sin(2 * np.pi * (420 - 600 * x) * x) * np.exp(-x * 12) + 0.1 * noise(0.4) * np.exp(-x * 14))
def thud(st, f=90, g=0.4, d=0.4):
    x = tt(d); add(st, g * np.sin(2 * np.pi * f * x) * np.exp(-x * 9))
def clang(st, g=0.3):
    x = tt(0.7); add(st, g * (np.sin(2 * np.pi * 660 * x) + 0.6 * np.sin(2 * np.pi * 1190 * x) + 0.3 * np.sin(2 * np.pi * 1730 * x)) * np.exp(-x * 6))
def ding(st, f=1318, g=0.25):
    x = tt(1.0); add(st, g * (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(2 * np.pi * 2 * f * x)) * np.exp(-x * 4))
x = tt(0.14); add(0.45, 0.12 * noise(0.14) * np.exp(-x * 30))                 # paper fold
add(T["final"] + 0.2, 0.12 * noise(0.14) * np.exp(-x * 30))
splash(T["land"] - 0.02); splash(T["swim"], 0.5)
x = tt(0.6); add(T["sag"], 0.5 * lowp(noise(0.6), 300) * (1 + np.sin(x * 40)) * np.exp(-x * 4))  # soggy squelch
thud(T["toast"]); thud(T["hull"], 120, 0.5); thud(T["floats"], 70, 0.2)
x = tt(1.4); add(T["wave"] - 0.5, 0.6 * lowp(noise(1.4), 120) * np.sin(np.pi * x / 1.4))       # wave whoosh
thud(T["wave"] + 0.2, 60, 0.5); splash(T["wave"] + 0.6, 0.4)
clang(T["keel"]); thud(T["ocean"], 50, 0.2)
x = tt(1.2); add(T["engine"], 0.2 * np.sign(np.sin(2 * np.pi * 70 * x)) * np.exp(-x * 2.2) + 0.15 * np.sin(2 * np.pi * 48 * x) * np.exp(-x * 1.5))  # horn/rumble
thud(T["cargo"], 100, 0.4)
for i in range(12): thud(T["cont"] + i * 0.09, 110 + (i % 4) * 15, 0.2, 0.2)
x = tt(0.5); add(T["sign"], 0.15 * np.sin(2 * np.pi * (300 + 150 * np.sin(x * 20)) * x) * np.exp(-x * 5))  # creak
thud(T["upside"], 150, 0.2, 0.3)
x = tt(2.0); add(T["storm"] + 0.3, 0.7 * lowp(noise(2.0), 400) * np.exp(-x * 1.6))             # thunder
x = tt(T["bulk"] + 1.0 - T["storm"]); add(T["storm"], 0.03 * noise(len(x) / SR))                 # rain hiss
clang(T["bulk"]); clang(T["bulk"] + 0.15, 0.2)
ding(T["radar"], 1760, 0.15); ding(T["fee"]); ding(T["million"], 1568, 0.2)
thud(T["sue"] + 0.6, 220, 0.5, 0.15); thud(T["sue"] + 0.75, 220, 0.5, 0.15)                   # gavel
pk = np.abs(out).max()
if pk > 0.9: out *= 0.9 / pk
sf.write("final.wav", out, SR)
json.dump({"words": words, "total": round(total, 3), "T": {k: round(v, 3) for k, v in T.items()}}, open("godot/timing.json", "w"))
print("narration end", round(end, 2), "total", round(total, 2))
