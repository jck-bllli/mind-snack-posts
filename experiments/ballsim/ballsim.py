"""Gravity ball race videos, kept very simple.

Two boxes, one ball each. The ball falls under gravity and every bounce on
the floor deals damage to the top HP bar. Bars break one by one; when the
last one breaks the ball drops out and that ball is done. Each ball has its
own damage rule. The script tries many seeded runs headless, keeps the one
with the closest finish (lead must change hands), then renders that run.

    python ballsim.py --video all --out out
    python ballsim.py --video fib_vs_doubling --search-only
"""
import argparse
import json
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "..", "..", "generator", "fonts")

W, H, FPS = 1080, 1920, 30
SUB = 4
DT = 1.0 / (FPS * SUB)
G = 1500.0                     # gravity px/s^2
BX, BW = 60, 960               # box x and width
PLAY_H = 420                   # open area above the bars
BAR_H = 88
CHECK_H = 28
TOP = (130, 970)               # box top y for ball A and ball B

BG = (220, 208, 182)
BOX = (250, 246, 236)
INK = (20, 20, 20)
COLORS = {"red": (214, 72, 40), "blue": (36, 104, 168), "green": (52, 132, 60), "gold": (204, 140, 20),
          "pink": (214, 76, 128)}

RULES = {
    "fib": dict(name="FIBONACCI BALL", color="red", op="fib", r=26, apex=(90, 170)),
    "doubling": dict(name="DOUBLING BALL", color="blue", op="mul", k=2, r=26, apex=(200, 330)),
    "grower": dict(name="GROWING BALL", color="gold", op="add", k=1, r=16, apex=(140, 300), grow=1.0, rmax=110),
    "splitter": dict(name="SPLITTING BALL", color="green", op="const", d0=1, r=12, apex=(140, 300), split=40),
    "fast": dict(name="FAST BALL", color="red", op="add", k=1, r=16, apex=(10, 28)),
    "strong": dict(name="STRONG BALL", color="blue", op="pow", k=2, r=40, apex=(320, 380)),
    # extra archetypes for the automatic daily picker
    "tripling": dict(name="TRIPLING BALL", color="pink", op="mul", k=3, r=30, apex=(300, 400)),
    "squares": dict(name="SQUARE BALL", color="green", op="pow", k=2, r=24, apex=(120, 240)),
    "cube": dict(name="CUBE BALL", color="gold", op="pow", k=3, r=28, apex=(260, 380)),
    "counting": dict(name="COUNTING BALL", color="blue", op="add", k=1, r=20, apex=(30, 70)),
    "shrinking": dict(name="SHRINKING BALL", color="pink", op="add", k=2, r=70, apex=(120, 260),
                      grow=-0.6, rmin=8, rmax=70),
    "heavy": dict(name="HEAVY BALL", color="gold", op="add", k=5, r=60, apex=(330, 390)),
}

# layers: HP of the 3 bars as fractions of the bottom bar (top bar breaks first)
VIDEOS = {
    "fib_vs_doubling": dict(balls=("fib", "doubling"), layers=(1e-12, 1e-5, 1)),
    "grower_vs_splitter": dict(balls=("grower", "splitter"), layers=(0.01, 0.1, 1)),
    "fast_vs_strong": dict(balls=("fast", "strong"), layers=(0.01, 0.1, 1)),
}
TARGET = 62.0
NICE = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 7.5]


def fmt(n):
    return f"{int(round(n)):,}"


class Ball:
    def __init__(self, rule, seed):
        self.rule = rule
        self.rng = np.random.default_rng(seed)
        r = rule["r"]
        self.r = float(r)
        self.pos = np.array([[self.rng.uniform(r + 40, BW - r - 40), self.rng.uniform(r + 10, 120)]])
        self.vel = np.array([[self.rng.uniform(140, 320) * self.rng.choice([-1, 1]), 0.0]])
        self.v0 = np.array([self._launch()])
        self.hits = 0
        self.dmg = float(rule.get("d0", 1))
        self.fib = (0, 1)
        self.cum = 0.0
        self.floor = PLAY_H
        self.done = False

    def _launch(self):
        return math.sqrt(2 * G * self.rng.uniform(*self.rule["apex"]))

    def _next(self):
        op = self.rule["op"]
        self.hits += 1
        n = self.hits
        if op == "pow":
            self.dmg = float(n ** self.rule["k"])
        elif op == "mul":
            self.dmg = 1.0 if n == 1 else self.dmg * self.rule["k"]
        elif op == "add":
            self.dmg = 1.0 + (n - 1) * self.rule["k"]
        elif op == "fib":
            a, b = self.fib
            self.fib = (b, a + b)
            self.dmg = float(b)
        return self.dmg

    def step(self, events=None, t=0.0):
        p, v, r = self.pos, self.vel, self.r
        v[:, 1] += G * DT
        p += v * DT
        lo = p[:, 0] < r
        hi = p[:, 0] > BW - r
        p[lo, 0] = r
        p[hi, 0] = BW - r
        v[lo | hi, 0] *= -1
        top = p[:, 1] < r
        p[top, 1] = r
        v[top, 1] = np.abs(v[top, 1])
        if self.done:
            return
        hit = (p[:, 1] > self.floor - r) & (v[:, 1] > 0)
        if not hit.any():
            return
        idx = np.nonzero(hit)[0]
        p[idx, 1] = self.floor - r
        v[idx, 1] = -self.v0[idx]
        k = len(idx)
        if self.rule["op"] == "const":
            self.hits += k
            dealt = [self.dmg] * k
            self.cum += self.dmg * k
        else:
            dealt = [self._next() for _ in range(k)]
            self.cum += sum(dealt)
        if events is not None:
            for i, dv in zip(idx[:2], dealt[:2]):
                events.append((t, float(p[i, 0]), float(self.floor), dv))
        if self.rule.get("grow"):
            self.r = min(self.rule["rmax"], max(self.rule.get("rmin", 4), self.r + self.rule["grow"] * k))
        cap = self.rule.get("split")
        if cap and len(p) < cap:
            idx = idx[: cap - len(p)]
            nv = v[idx].copy()
            nv[:, 0] = self.rng.uniform(140, 360, len(idx)) * self.rng.choice([-1, 1], len(idx))
            self.pos = np.vstack([p, p[idx]])
            self.vel = np.vstack([v, nv])
            self.v0 = np.concatenate([self.v0, [self._launch() for _ in idx]])


def curve(rule, seed, seconds):
    b = Ball(rule, seed)
    n = int(seconds / DT)
    out = np.empty(n)
    for i in range(n):
        b.step()
        out[i] = b.cum
    return out


def auto_layers(m, e):
    """Ref style: small top bar, middle bar, huge bottom bar (1,000 / 10B / 1e15)."""
    a = max(1, round(e * 0.2))
    b = max(a + 1, round(e * 0.67))
    if b >= e:
        b = e - 1
    return [m * 10 ** a, m * 10 ** b, m * 10 ** e]


def layer_sets(spec, lo, hi):
    f = spec.get("layers")
    e = max(2, int(math.floor(math.log10(max(lo, 1)))) - 1)
    while True:
        for m in NICE:
            l3 = m * 10 ** e
            layers = [max(1.0, round(l3 * x)) for x in f] if f else auto_layers(m, e)
            tot = sum(layers)
            if tot > hi:
                return
            if tot >= lo:
                yield layers, tot
        e += 1


def rules_of(spec):
    return spec.get("rules") or tuple(RULES[k] for k in spec["balls"])


def search(spec, tries=160, offset=0):
    ra, rb = rules_of(spec)
    win = (TARGET - 7, TARGET + 7)
    best = None
    for s in range(tries):
        sa, sb = 1000 + offset + s * 7, 5000 + offset + s * 13
        ca, cb = curve(ra, sa, win[1] + 4), curve(rb, sb, win[1] + 4)
        i0, i1 = int(win[0] / DT), int(win[1] / DT)
        for layers, tot in layer_sets(spec, min(ca[i0], cb[i0]), max(ca[i1], cb[i1])):
            ta, tb = np.searchsorted(ca, tot) * DT, np.searchsorted(cb, tot) * DT
            if not (win[0] <= min(ta, tb) <= win[1]) or max(ta, tb) > win[1] + 3.9:
                continue
            gap = abs(ta - tb)
            if gap < 0.04:
                continue
            i = int(min(ta, tb) / DT)
            loser_a = ta > tb
            d = (ca[:i] - cb[:i]) * (1 if loser_a else -1)
            swap = bool((d > 0).any())          # the loser led at some point
            score = gap - (0.3 if swap else 0)
            if best is None or score < best["score"]:
                best = dict(score=score, seed_a=sa, seed_b=sb, layers=layers, total=tot,
                            ta=float(ta), tb=float(tb), gap=float(gap), swap=swap)
    return best


SCALES = (0.25, 0.5, 1.0, 1.6)


def scaled(rule, f):
    lo, hi = rule["apex"]
    lo, hi = max(6.0, lo * f), min(400.0 - rule["r"], hi * f)
    return dict(rule, apex=(min(lo, hi - 4), hi))


def tune_search(spec, tries=12, offset=0, good=0.25):
    """Search bounce-height scales too, so any two ball types can be made to finish close."""
    ra, rb = rules_of(spec)
    best = None
    combos = sorted(((fa, fb) for fa in SCALES for fb in SCALES), key=lambda c: abs(c[0] - 1) + abs(c[1] - 1))
    for fa, fb in combos:
        sp = dict(spec, rules=(scaled(ra, fa), scaled(rb, fb)))
        f = search(sp, tries=tries, offset=offset)
        if f and (best is None or f["score"] < best[1]["score"]):
            best = (sp, dict(f, scale_a=fa, scale_b=fb))
        if best and best[1]["gap"] <= good and best[1]["swap"]:
            break
    return best or (spec, None)


# ---------- drawing ----------
def font(name, size, _c={}):
    if (name, size) not in _c:
        f = {"black": "NunitoBlack.woff", "bold": "NunitoExtraBold.woff"}[name]
        _c[(name, size)] = ImageFont.truetype(os.path.join(FONT_DIR, f), size)
    return _c[(name, size)]


CHECKER = None


def checker():
    global CHECKER
    if CHECKER is None:
        im = Image.new("RGB", (BW, CHECK_H), INK)
        d = ImageDraw.Draw(im)
        s = CHECK_H // 2
        for i in range(0, BW // s + 1):
            for j in range(2):
                if (i + j) % 2 == 0:
                    d.rectangle((i * s, j * s, i * s + s - 1, j * s + s - 1), fill=(255, 255, 255))
        CHECKER = im
    return CHECKER


def draw(img, balls, rules, layers, t, popups, banner):
    d = ImageDraw.Draw(img)
    for j, (b, ru) in enumerate(zip(balls, rules)):
        col = COLORS[ru["color"]]
        y0 = TOP[j]
        d.text((W // 2, y0 - 34), ru["name"], font=font("black", 46), fill=col, anchor="mm")
        bottom = y0 + PLAY_H + BAR_H * 3
        d.rectangle((BX - 4, y0 - 4, BX + BW + 4, bottom + 4), fill=INK)
        d.rectangle((BX, y0, BX + BW, y0 + min(b.floor, PLAY_H + BAR_H * 3)), fill=BOX)
        left = b.cum
        for li, hp in enumerate(layers):
            rem = hp - min(hp, left)
            left = max(0.0, left - hp)
            ty = y0 + PLAY_H + li * BAR_H
            if rem <= 0:
                d.rectangle((BX, ty, BX + BW, ty + BAR_H), fill=BOX)
                continue
            d.rectangle((BX, ty, BX + BW, ty + BAR_H - 4), fill=col)
            d.text((W // 2, ty + BAR_H // 2 - 2), fmt(rem), font=font("black", 40), fill=INK, anchor="mm")
        img.paste(checker(), (BX, bottom + 4))
        d.text((BX + 16, y0 + 14), "DAMAGE: " + fmt(b.dmg), font=font("black", 24), fill=col)
        for (pt, px, py, dv) in popups[j]:
            age = t - pt
            if 0 <= age < 0.7:
                c = tuple(int(a + (z - a) * age / 0.7) for a, z in zip(col, BOX))
                d.text((BX + px, y0 + py - 50 - age * 40), "-" + fmt(dv), font=font("bold", 26), fill=c, anchor="mm")
        for (px, py) in b.pos:
            x, y, r = BX + px, y0 + py, b.r
            if y - r > bottom + CHECK_H + 4:
                continue
            d.ellipse((x - r, y - r, x + r, y + r), fill=col, outline=INK, width=3 if r > 9 else 2)
    vy = (TOP[0] + PLAY_H + BAR_H * 3 + CHECK_H + TOP[1] - 34) // 2 + 4
    d.text((W // 2, vy), "VS", font=font("black", 44), fill=INK, anchor="mm")
    if banner:
        name, col, sub = banner
        d.rounded_rectangle((BX + 60, 760, BX + BW - 60, 1000), 24, fill=INK)
        d.text((W // 2, 840), name + " WINS", font=font("black", 58), fill=col, anchor="mm")
        d.text((W // 2, 930), sub, font=font("black", 42), fill=(255, 255, 255), anchor="mm")


# ---------- audio ----------
SR = 44100


def ping(freq, dur=0.08, amp=0.2):
    t = np.arange(int(SR * dur)) / SR
    return amp * np.sin(2 * np.pi * freq * t) * np.exp(-t * 45)


def crack(dur=0.25):
    t = np.arange(int(SR * dur)) / SR
    rng = np.random.default_rng(1)
    return 0.35 * rng.uniform(-1, 1, len(t)) * np.exp(-t * 18)


def add(audio, t, snd):
    i = int(t * SR)
    n = max(0, min(len(snd), len(audio) - i))
    audio[i:i + n] += snd[:n]


def make_video(key, outdir, search_only=False, spec=None, found=None):
    spec = spec or VIDEOS[key]
    found = found or search(spec)
    print(key, json.dumps(found))
    if search_only or not found:
        return
    ra, rb = rules_of(spec)
    rules = (ra, rb)
    layers = found["layers"]
    balls = [Ball(ra, found["seed_a"]), Ball(rb, found["seed_b"])]
    os.makedirs(outdir, exist_ok=True)
    vtmp = os.path.join(outdir, key + "_v.mp4")
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                             "-crf", "18", "-pix_fmt", "yuv420p", vtmp], stdin=subprocess.PIPE)
    total = max(found["ta"], found["tb"]) + 6
    audio = np.zeros(int(total * SR))
    base = (330.0, 440.0)
    popups = ([], [])
    broken = [0, 0]
    finish = [None, None]
    t, n, end_t, banner = 0.0, 0, None, None
    while True:
        for _ in range(SUB):
            t += DT
            for j, b in enumerate(balls):
                ev = []
                b.step(ev, t)
                for e in ev:
                    popups[j].append(e)
                    add(audio, t, ping(base[j] * 2 ** (min(math.log10(e[3] + 1), 15) / 10)))
                while broken[j] < 3 and b.cum >= sum(layers[: broken[j] + 1]):
                    broken[j] += 1
                    b.floor = PLAY_H + BAR_H * broken[j] if broken[j] < 3 else 10 ** 9
                    add(audio, t, crack())
                if broken[j] == 3 and finish[j] is None:
                    finish[j] = t
                    b.done = True
        for j in range(2):
            popups[j][:] = [e for e in popups[j] if t - e[0] < 0.7][-10:]
        if all(f is not None for f in finish) and end_t is None:
            end_t = t
            w = 0 if finish[0] < finish[1] else 1
            banner = (rules[w]["name"], COLORS[rules[w]["color"]], f"BY {abs(finish[0] - finish[1]):.2f} SECONDS")
            add(audio, t, sum(ping(f, 1.2, 0.15) for f in (base[w], base[w] * 1.25, base[w] * 1.5)))
        img = Image.new("RGB", (W, H), BG)
        draw(img, balls, rules, layers, t, popups, banner)
        proc.stdin.write(img.tobytes())
        n += 1
        if end_t is not None and t - end_t > 3.0:
            break
    proc.stdin.close()
    proc.wait()
    secs = n / FPS
    wav = os.path.join(outdir, key + ".wav")
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(audio[: int(secs * SR)], -1, 1) * 32767).astype("<i2").tobytes())
    out = os.path.join(outdir, key + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vtmp, "-i", wav, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "128k", "-shortest", out], check=True)
    os.remove(vtmp)
    os.remove(wav)
    with open(os.path.join(outdir, key + ".json"), "w") as fh:
        json.dump(found, fh, indent=1)
    print("wrote", out, f"{secs:.1f}s")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="all")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--search-only", action="store_true")
    a = ap.parse_args()
    for k in (list(VIDEOS) if a.video == "all" else [a.video]):
        make_video(k, a.out, a.search_only)
