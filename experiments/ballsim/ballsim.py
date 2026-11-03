"""Bouncing ball race videos: two balls, each in its own box, drain an HP bar.

Every wall bounce deals damage. Each ball has its own rule (cube, compound,
grow, split...). The script runs many seeded simulations headless and keeps
the one with the closest finish, then renders that exact run to video.

    python ballsim.py --video cube_vs_compound --out out
    python ballsim.py --video all --out out
    python ballsim.py --video cube_vs_compound --search-only   # no frames
"""
import argparse
import json
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "..", "..", "generator", "fonts")

W, H, FPS = 1080, 1920, 30
SUB = 4                      # physics substeps per frame
DT = 1.0 / (FPS * SUB)
BOX_W, BOX_H = 860, 440      # inner box size in px
BOX_X = 70
BOX_Y = (240, 970)           # top-left y of box A and box B
BAR_H = 70

BG = (243, 238, 228)
INK = (27, 27, 27)
WHITE = (255, 255, 255)
GREY = (205, 198, 186)
COLORS = {
    "red": (228, 87, 46),
    "teal": (31, 122, 140),
    "yellow": (226, 160, 30),
    "green": (59, 139, 59),
}

# ---------- rules ----------
RULES = {
    "cube": dict(name="CUBE BALL", desc="damage = bounces cubed", color="red",
                 op="pow", k=3, r=26),
    "compound": dict(name="COMPOUND BALL", desc="damage x1.2 every bounce", color="teal",
                     op="mul", k=1.2, r=26),
    "grower": dict(name="GROWER BALL", desc="+1 damage and bigger every bounce", color="yellow",
                   op="add", k=1, r=18, grow=1.6, rmax=200),
    "splitter": dict(name="SPLITTER BALL", desc="splits in two every bounce (max 64)", color="green",
                     op="const", k=0, d0=1, r=14, split=64),
    "squares": dict(name="SQUARE BALL", desc="damage = bounces squared", color="red",
                    op="pow", k=2, r=26),
    "fib": dict(name="FIBONACCI BALL", desc="damage follows Fibonacci", color="teal",
                op="fib", k=0, r=26),
}

VIDEOS = {
    "cube_vs_compound": dict(kind="duel", balls=("cube", "compound"), target=24.0),
    "grower_vs_splitter": dict(kind="duel", balls=("grower", "splitter"), target=24.0),
    "bracket": dict(kind="bracket", balls=("squares", "splitter", "cube", "fib"), target=8.0,
                    colors={"squares": "red", "splitter": "green", "cube": "yellow", "fib": "teal"}),
}

NICE = [1, 1.2, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 7.5, 8]


def fmt(n):
    return f"{int(round(n)):,}"


# ---------- physics ----------
class Box:
    def __init__(self, rule, seed, speed):
        self.rule = rule
        self.rng = np.random.default_rng(seed)
        r = rule["r"]
        a = self.rng.uniform(0.25, 1.3) * self.rng.choice([-1, 1]) + self.rng.choice([0, math.pi])
        self.pos = np.array([[self.rng.uniform(r, BOX_W - r), self.rng.uniform(r, BOX_H - r)]])
        self.vel = np.array([[math.cos(a), math.sin(a)]]) * speed
        self.r = float(r)
        self.hits = 0
        self.dmg = float(rule.get("d0", 1))
        self.fib = (0, 1)
        self.cum = 0.0
        self.done = False

    def _next_damage(self):
        op, k = self.rule["op"], self.rule["k"]
        self.hits += 1
        n = self.hits
        if op == "pow":
            self.dmg = float(n ** k)
        elif op == "mul":
            self.dmg = 1.0 if n == 1 else self.dmg * k
        elif op == "add":
            self.dmg = 1.0 + (n - 1) * k
        elif op == "fib":
            a, b = self.fib
            self.fib = (b, a + b)
            self.dmg = float(b)
        return self.dmg

    def step(self, events=None, t=0.0):
        if self.done:
            return
        p, v, r = self.pos, self.vel, self.r
        p += v * DT
        lo = p < r
        hi = p > np.array([BOX_W - r, BOX_H - r])
        hit = lo | hi
        if not hit.any():
            return
        p[lo] = r
        p[:, 0][hi[:, 0]] = BOX_W - r
        p[:, 1][hi[:, 1]] = BOX_H - r
        v[hit] *= -1
        who = np.nonzero(hit.any(axis=1))[0]
        k = int(hit.sum())
        if self.rule["op"] == "const":
            self.hits += k
            dealt = [self.dmg] * k
            self.cum += self.dmg * k
        else:
            dealt = [self._next_damage() for _ in range(k)]
            self.cum += sum(dealt)
        if events is not None:
            for i, d in zip(who[:2], dealt[:2]):
                events.append((t, float(p[i, 0]), float(p[i, 1]), d))
        g = self.rule.get("grow")
        if g:
            self.r = min(self.rule["rmax"], self.r + g * k)
            np.clip(self.pos, self.r, [BOX_W - self.r, BOX_H - self.r], out=self.pos)
        cap = self.rule.get("split")
        if cap and len(self.pos) < cap:
            who = who[: cap - len(self.pos)]
            ang = self.rng.uniform(0.4, 1.2, len(who)) * self.rng.choice([-1, 1], len(who))
            c, s = np.cos(ang), np.sin(ang)
            vv = v[who]
            nv = np.stack([vv[:, 0] * c - vv[:, 1] * s, vv[:, 0] * s + vv[:, 1] * c], axis=1)
            self.pos = np.vstack([self.pos, self.pos[who]])
            self.vel = np.vstack([self.vel, nv])


def cum_curve(rule, seed, speed, seconds):
    b = Box(rule, seed, speed)
    n = int(seconds / DT)
    out = np.empty(n)
    for i in range(n):
        b.step()
        out[i] = b.cum
    return out


def nice_values(lo, hi):
    vals = []
    e = int(math.floor(math.log10(max(lo, 1))))
    while True:
        for m in NICE:
            x = m * 10 ** e
            if x > hi:
                return vals
            if x >= lo:
                vals.append(x)
        e += 1


def search(ra, rb, target, tries=60, speeds=(900, 1150, 1400, 1700)):
    """Find seed, speed and a round HP that give the closest real finish."""
    best = None
    win = (target - 2.5, target + 2.5)
    for speed in speeds:
        for s in range(tries):
            sa, sb = 1000 + s * 7, 5000 + s * 13
            ca = cum_curve(ra, sa, speed, win[1] + 4)
            cb = cum_curve(rb, sb, speed, win[1] + 4)
            i0, i1 = int(win[0] / DT), int(win[1] / DT)
            lo = min(ca[i0], cb[i0])
            hi = max(ca[i1], cb[i1])
            for hp in nice_values(max(lo, 10), hi):
                ta = np.searchsorted(ca, hp) * DT
                tb = np.searchsorted(cb, hp) * DT
                if not (win[0] <= min(ta, tb) <= win[1]) or max(ta, tb) > win[1] + 3.9:
                    continue
                gap = abs(ta - tb)
                if gap < 0.04:          # needs a visible winner
                    continue
                # did the lead swap? (loser was ahead earlier)
                i = int(min(ta, tb) / DT)
                diff = ca[: i] - cb[: i]
                swap = bool((diff > 0).any() and (diff < 0).any() and abs(diff[: int(i * 0.8)]).max() > 0)
                score = gap - (0.15 if swap else 0) + abs(min(ta, tb) - target) * 0.01
                if best is None or score < best["score"]:
                    best = dict(score=score, seed_a=sa, seed_b=sb, speed=speed, hp=hp,
                                ta=float(ta), tb=float(tb), gap=float(gap), swap=swap)
        if best and best["gap"] < 0.25 and best["swap"]:
            break
    return best


# ---------- drawing ----------
def font(name, size, _cache={}):
    key = (name, size)
    if key not in _cache:
        f = {"display": "LilitaOne.woff", "black": "NunitoBlack.woff", "bold": "NunitoExtraBold.woff"}[name]
        _cache[key] = ImageFont.truetype(os.path.join(FONT_DIR, f), size)
    return _cache[key]


def text_c(d, xy, s, f, fill):
    d.text(xy, s, font=f, fill=fill, anchor="mm")


def draw_match(img, boxes, rules, hp, t, popups, finish, lead_ok, header):
    d = ImageDraw.Draw(img)
    if header:
        text_c(d, (W // 2, 120), header, font("display", 44), INK)
    for j, (b, ru) in enumerate(zip(boxes, rules)):
        col = COLORS[ru["color"]]
        y0 = BOX_Y[j]
        d.text((BOX_X, y0 - 98), ru["name"], font=font("display", 52), fill=col)
        d.text((BOX_X, y0 - 44), ru["desc"], font=font("bold", 30), fill=INK, anchor="lm")
        dm = "DAMAGE " + fmt(b.dmg)
        d.text((BOX_X + BOX_W, y0 - 44), dm, font=font("black", 30), fill=INK, anchor="rm")
        lead = lead_ok and not any(x.done for x in boxes) and b.cum > boxes[1 - j].cum
        if lead:
            tw = d.textlength(ru["name"], font=font("display", 52))
            x = BOX_X + tw + 20
            d.rounded_rectangle((x, y0 - 92, x + 150, y0 - 52), 10, fill=col)
            text_c(d, (x + 75, y0 - 72), "LEADING", font("black", 24), WHITE)
        # box
        d.rectangle((BOX_X - 6, y0 - 6, BOX_X + BOX_W + 6, y0 + BOX_H + 6), fill=INK)
        d.rectangle((BOX_X, y0, BOX_X + BOX_W, y0 + BOX_H), fill=WHITE)
        for (px, py) in b.pos:
            x, y, r = BOX_X + px, y0 + py, b.r
            d.ellipse((x - r, y - r, x + r, y + r), fill=col, outline=INK, width=4 if r > 10 else 2)
        for (pt, px, py, dv) in popups[j]:
            age = t - pt
            if 0 <= age < 0.6:
                c = tuple(int(a + (b2 - a) * age / 0.6) for a, b2 in zip(INK, WHITE))
                d.text((BOX_X + px, y0 + py - 40 - age * 60), "-" + fmt(dv), font=font("black", 34),
                       fill=c, anchor="mm")
        # hp bar
        by = y0 + BOX_H + 22
        left = max(0.0, hp - b.cum)
        d.rectangle((BOX_X - 6, by - 6, BOX_X + BOX_W + 6, by + BAR_H + 6), fill=INK)
        d.rectangle((BOX_X, by, BOX_X + BOX_W, by + BAR_H), fill=GREY)
        d.rectangle((BOX_X, by, BOX_X + int(BOX_W * left / hp), by + BAR_H), fill=col)
        label = fmt(left) + " HP" if left > 0 else "DONE  " + f"{finish[j]:.2f}s"
        text_c(d, (BOX_X + BOX_W // 2, by + BAR_H // 2), label, font("black", 40), WHITE if left > 0 else INK)
    text_c(d, (W // 2, (BOX_Y[0] + BOX_H + 22 + BAR_H + BOX_Y[1] - 98) // 2), "VS", font("display", 56), INK)
    text_c(d, (W // 2, 1600), f"{t:05.2f}s", font("black", 44), INK)


def overlay(img, lines, alpha=200):
    ov = Image.new("RGBA", (W, H), (27, 27, 27, alpha))
    d = ImageDraw.Draw(ov)
    y = 820 - 60 * (len(lines) - 1)
    for s, size, col in lines:
        text_c(d, (W // 2, y), s, font("display", size), col)
        y += int(size * 1.5)
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"))


# ---------- audio ----------
SR = 44100


def ping(freq, dur=0.09, amp=0.22):
    t = np.arange(int(SR * dur)) / SR
    return amp * np.sin(2 * np.pi * freq * t) * np.exp(-t * 38)


def chord(freqs, dur=1.2):
    t = np.arange(int(SR * dur)) / SR
    return sum(0.16 * np.sin(2 * np.pi * f * t) for f in freqs) * np.exp(-t * 2.5)


# ---------- match rendering ----------
def render_match(frames_out, audio, t_off, ra, rb, found, header, intro=1.5, outro=2.2, lead_ok=True):
    boxes = [Box(ra, found["seed_a"], found["speed"]), Box(rb, found["seed_b"], found["speed"])]
    hp = found["hp"]
    rules = (ra, rb)
    popups = ([], [])
    finish = [None, None]
    base = [392.0, 523.25]
    # intro: balls still, pick-one prompt
    for f in range(int(intro * FPS)):
        img = Image.new("RGB", (W, H), BG)
        draw_match(img, boxes, rules, hp, 0.0, popups, finish, False, header)
        n = 3 - int(f / (intro * FPS) * 3)
        overlay(img, [("PICK ONE", 110, WHITE), (str(n), 150, WHITE)], 150)
        frames_out(img)
    t_off += intro
    t = 0.0
    winner = None
    end_t = None
    while True:
        for _ in range(SUB):
            t += DT
            for j, b in enumerate(boxes):
                ev = []
                b.step(ev, t)
                for e in ev:
                    popups[j].append(e)
                    i = int((t_off + t) * SR)
                    snd = ping(base[j] * 2 ** (min(math.log10(e[3] + 1), 15) / 7.5))
                    audio[i:i + len(snd)] += snd[: max(0, len(audio) - i)]
                if not b.done and b.cum >= hp:
                    b.done = True
                    finish[j] = t
                    if winner is None:
                        winner = j
                        i = int((t_off + t) * SR)
                        c = chord([base[j], base[j] * 1.25, base[j] * 1.5])
                        audio[i:i + len(c)] += c[: max(0, len(audio) - i)]
            if all(b.done for b in boxes) and end_t is None:
                end_t = t
        for j in range(2):
            popups[j][:] = [e for e in popups[j] if t - e[0] < 0.6][-14:]
        img = Image.new("RGB", (W, H), BG)
        draw_match(img, boxes, rules, hp, t, popups, finish, lead_ok, header)
        frames_out(img)
        if end_t is not None and t - end_t > 0.4:
            break
    gap = finish[1 - winner] - finish[winner]
    for _ in range(int(outro * FPS)):
        img = Image.new("RGB", (W, H), BG)
        draw_match(img, boxes, rules, hp, t, popups, finish, False, header)
        overlay(img, [(rules[winner]["name"], 96, COLORS[rules[winner]["color"]]),
                      ("WINS BY", 70, WHITE), (f"{gap:.2f} SECONDS", 96, WHITE)], 200)
        frames_out(img)
    return t_off + t + outro, winner


def card(frames_out, lines, secs):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = 860 - 70 * (len(lines) - 1)
    for s, size, col in lines:
        text_c(d, (W // 2, y), s, font("display", size), col)
        y += int(size * 1.45)
    for _ in range(int(secs * FPS)):
        frames_out(img)


def make_video(key, outdir, search_only=False):
    spec = VIDEOS[key]
    names = spec["balls"]
    plan = []
    if spec["kind"] == "duel":
        ra, rb = RULES[names[0]], RULES[names[1]]
        found = search(ra, rb, spec["target"])
        plan.append((names[0], names[1], found))
        print(key, json.dumps(found))
        if search_only:
            return
    else:
        for k, c in spec["colors"].items():
            RULES[k] = dict(RULES[k], color=c)
        semis = [(names[0], names[1]), (names[2], names[3])]
        for a, b in semis:
            found = search(RULES[a], RULES[b], spec["target"], tries=40)
            plan.append((a, b, found))
            print(key, a, b, json.dumps(found))
        winners = [a if f["ta"] < f["tb"] else b for a, b, f in plan]
        found = min((f for T in (9, 11, 13) if (f := search(RULES[winners[0]], RULES[winners[1]], T, tries=40))),
                    key=lambda f: f["gap"] - (0.15 if f["swap"] else 0))
        plan.append((winners[0], winners[1], found))
        print(key, "final", json.dumps(found))
        if search_only:
            return

    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, key + ".mp4")
    total = sum(max(f["ta"], f["tb"]) + 1.5 + 2.2 + 0.6 for *_, f in plan) + 8
    audio = np.zeros(int(total * SR) + SR)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                             "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                             os.path.join(outdir, key + "_v.mp4")], stdin=subprocess.PIPE)
    nframes = [0]

    def emit(img):
        proc.stdin.write(img.tobytes())
        nframes[0] += 1

    t = 0.0
    if spec["kind"] == "duel":
        a, b, f = plan[0]
        t, _ = render_match(emit, audio, t, RULES[a], RULES[b], f, "WHICH BALL FINISHES FIRST?")
        card(emit, [("CLOSER THAN YOU", 80, INK), ("THOUGHT?", 80, INK), ("FOLLOW FOR", 60, INK),
                    ("TOMORROW'S RACE", 60, INK)], 1.6)
    else:
        nm = lambda k: RULES[k]["name"]
        card(emit, [("BALL BRACKET", 100, INK), (f"{nm(names[0])} vs {nm(names[1])}", 44, INK),
                    (f"{nm(names[2])} vs {nm(names[3])}", 44, INK), ("WHO TAKES IT?", 70, INK)], 2.0)
        t += 2.0
        titles = ["SEMI FINAL 1", "SEMI FINAL 2", "THE FINAL"]
        for (a, b, f), title in zip(plan, titles):
            t, _ = render_match(emit, audio, t, RULES[a], RULES[b], f, title, intro=1.0, outro=1.6)
        champ = plan[2][0] if plan[2][2]["ta"] < plan[2][2]["tb"] else plan[2][1]
        card(emit, [("CHAMPION", 80, INK), (nm(champ), 100, COLORS[RULES[champ]["color"]]),
                     ("DID YOU CALL IT?", 60, INK)], 2.0)
    proc.stdin.close()
    proc.wait()
    secs = nframes[0] / FPS
    a16 = (np.clip(audio[: int(secs * SR)], -1, 1) * 32767).astype("<i2")
    wav = os.path.join(outdir, key + ".wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(a16.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(outdir, key + "_v.mp4"),
                    "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", out], check=True)
    os.remove(os.path.join(outdir, key + "_v.mp4"))
    os.remove(wav)
    with open(os.path.join(outdir, key + ".json"), "w") as fh:
        json.dump([dict(a=a, b=b, **f) for a, b, f in plan], fh, indent=1)
    print("wrote", out, f"{secs:.1f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="all")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--search-only", action="store_true")
    args = ap.parse_args()
    keys = list(VIDEOS) if args.video == "all" else [args.video]
    for k in keys:
        make_video(k, args.out, args.search_only)
    sys.stdout.flush()
