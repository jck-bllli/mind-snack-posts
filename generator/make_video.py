#!/usr/bin/env python3
"""Make a 5-question trivia Reel (1080x1920, 30fps, H.264 + AAC).

Usage:
    python3 make_video.py --set 0                 # render quiz #0 from questions.json
    python3 make_video.py --all                   # render every quiz
    python3 make_video.py --set 0 --handle @you   # change the handle shown

Outputs go to ./out/: quiz_<n>.mp4, quiz_<n>_cover.jpg, quiz_<n>_caption.txt
Needs: Python 3, Pillow, numpy, ffmpeg.
"""
import argparse
import json
import math
import os
import subprocess
import wave
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
SS = 2  # supersampling for smooth edges

# Timing (seconds)
INTRO, THINK, REVEAL = 0.6, 3.0, 2.6
QDUR = INTRO + THINK + REVEAL
END = 3.8

OPT_H, OPT_GAP = 130, 16
COL_LEFT = 90          # left edge of the main 900px column
HEADER_BOTTOM = 492    # body starts below the title sticker
SAFE_BOTTOM = 1620     # keep clear of the caption and buttons at the bottom
INK = (20, 20, 28)
WHITE = (255, 255, 255)
GREEN = (52, 211, 120)
YELLOW = (255, 206, 46)
RED = (255, 84, 84)
LEVEL_COLORS = {"easy": GREEN, "medium": YELLOW, "hard": RED}

# Bright, playful palettes: background, dot pattern, sticker accent
PALETTES = [
    dict(bg=(255, 210, 63), dot=(255, 196, 22), accent=(255, 99, 146)),
    dict(bg=(84, 205, 245), dot=(62, 190, 236), accent=(255, 210, 63)),
    dict(bg=(255, 99, 146), dot=(242, 80, 130), accent=(255, 230, 90)),
    dict(bg=(170, 240, 70), dot=(152, 226, 46), accent=(255, 99, 146)),
    dict(bg=(255, 145, 72), dot=(246, 128, 50), accent=(84, 205, 245)),
    dict(bg=(185, 160, 255), dot=(168, 140, 250), accent=(170, 240, 70)),
]

FONTS = {
    "display": os.path.join(HERE, "fonts", "LilitaOne.woff"),
    "black": os.path.join(HERE, "fonts", "NunitoBlack.woff"),
    "bold": os.path.join(HERE, "fonts", "NunitoExtraBold.woff"),
}


@lru_cache(maxsize=256)
def font(kind, size):
    return ImageFont.truetype(FONTS[kind], size)


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_out(t):
    return 1 - (1 - t) ** 3


# ---------- drawing helpers (everything drawn at SS scale, then shrunk) ----------
def wrap(text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if fnt.getlength(test) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(text, kind, size, max_w, max_lines):
    """Shrink font until text fits in max_lines."""
    while size > 20:
        f = font(kind, size)
        lines = wrap(text, f, max_w)
        if len(lines) <= max_lines and all(f.getlength(l) <= max_w for l in lines):
            return f, lines
        size -= 2
    f = font(kind, size)
    return f, wrap(text, f, max_w)


def card(w, h, fill, radius=34, outline=INK, ow=7, shadow=12):
    """RGBA card with a hard offset shadow, at SS scale. Returns (img, draw)."""
    s = SS
    im = Image.new("RGBA", ((w + shadow) * s, (h + shadow) * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        d.rounded_rectangle((shadow * s, shadow * s, (w + shadow) * s - 1, (h + shadow) * s - 1),
                            radius * s, fill=INK)
    d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), radius * s, fill=fill,
                        outline=outline, width=ow * s)
    return im, d


def shrink(im):
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)


def draw_lines(d, lines, fnt, cx, top, line_h, fill):
    for i, line in enumerate(lines):
        d.text((cx, top + i * line_h), line, font=fnt, fill=fill, anchor="mt")


# ---------- elements ----------
def el_theme_chip(text):
    f = font("black", 34 * SS)
    tw = int(f.getlength(text) / SS)
    w, h = tw + 64, 62
    im, d = card(w, h, INK, radius=31, ow=0, shadow=0)
    d.text((w * SS // 2, h * SS // 2), text, font=f, fill=WHITE, anchor="mm")
    return shrink(im)


def el_title(text, accent, angle=-3):
    f = font("display", 92 * SS)
    tw = int(f.getlength(text) / SS)
    w, h = tw + 80, 132
    im, d = card(w, h, accent, radius=30)
    d.text((w * SS // 2, h * SS // 2 + 4 * SS), text, font=f, fill=INK, anchor="mm")
    return shrink(im).rotate(angle, resample=Image.BICUBIC, expand=True)


def el_progress(idx, total, level):
    w, h = 900, 64
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font("display", 50 * SS)
    d.text((0, h * SS // 2), f"QUESTION {idx + 1}/{total}", font=f, fill=INK, anchor="lm")
    # dots
    x0 = int(f.getlength(f"QUESTION {idx + 1}/{total}")) + 28 * SS
    r = 11 * SS
    for i in range(total):
        cx = x0 + i * 34 * SS + r
        cy = h * SS // 2
        if i <= idx:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=INK)
        else:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=INK, width=4 * SS)
    # difficulty chip
    label = level.upper()
    fc = font("black", 32 * SS)
    cw = int(fc.getlength(label)) + 48 * SS
    ch = 54 * SS
    x1 = w * SS - 12 * SS
    y0 = (h * SS - ch) // 2
    d.rounded_rectangle((x1 - cw + 8 * SS, y0 + 8 * SS, x1 + 8 * SS, y0 + ch + 8 * SS), ch // 2, fill=INK)
    d.rounded_rectangle((x1 - cw, y0, x1, y0 + ch), ch // 2, fill=LEVEL_COLORS[level],
                        outline=INK, width=5 * SS)
    d.text((x1 - cw // 2, y0 + ch // 2), label, font=fc, fill=INK, anchor="mm")
    return shrink(im)


def el_question(text):
    w = 900
    f, lines = fit_text(text, "display", 78 * SS, (w - 90) * SS, 3)
    line_h = int(f.size * 1.12)
    h = int((len(lines) * line_h) / SS) + 84
    im, d = card(w, h, WHITE, radius=40)
    top = (h * SS - len(lines) * line_h) // 2 + 6 * SS
    draw_lines(d, lines, f, w * SS // 2, top, line_h, INK)
    return shrink(im)


def el_option(letter, text, state, accent):
    """state: normal | correct | wrong"""
    w, h = 900, OPT_H
    fill = {"normal": WHITE, "correct": GREEN, "wrong": (236, 236, 240)}[state]
    im, d = card(w, h, fill, radius=34, shadow=10)
    s = SS
    # letter badge
    r = 44 * s
    cx, cy = 78 * s, h * s // 2
    badge = WHITE if state == "correct" else accent
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=badge, outline=INK, width=6 * s)
    if state == "correct":
        # check mark
        d.line([(cx - 17 * s, cy + 1 * s), (cx - 4 * s, cy + 15 * s), (cx + 19 * s, cy - 14 * s)],
               fill=INK, width=10 * s, joint="curve")
    else:
        d.text((cx, cy + 3 * s), letter, font=font("display", 52 * s), fill=INK, anchor="mm")
    f, lines = fit_text(text, "black", 58 * s, (w - 190) * s, 1)
    color = INK if state != "wrong" else (150, 150, 160)
    d.text((150 * s, cy + 2 * s), lines[0], font=f, fill=color, anchor="lm")
    return shrink(im)


def el_fact(text, accent):
    w = 900
    f, lines = fit_text(text, "bold", 44 * SS, (w - 80) * SS, 3)
    line_h = int(f.size * 1.25)
    h = int(len(lines) * line_h / SS) + 84
    body, _ = card(w, h, WHITE, radius=30, shadow=10)
    pad = 26  # room for the label to straddle the top edge
    im = Image.new("RGBA", (body.width, body.height + pad * SS), (0, 0, 0, 0))
    im.alpha_composite(body, (0, pad * SS))
    d = ImageDraw.Draw(im)
    fl = font("black", 30 * SS)
    lw = int(fl.getlength("FUN FACT")) + 40 * SS
    d.rounded_rectangle((30 * SS, 0, 30 * SS + lw, 52 * SS), 16 * SS, fill=accent, outline=INK, width=5 * SS)
    d.text((30 * SS + lw // 2, 27 * SS), "FUN FACT", font=fl, fill=INK, anchor="mm")
    for i, line in enumerate(lines):
        d.text((40 * SS, (pad + 50) * SS + i * line_h), line, font=f, fill=INK)
    return shrink(im)


TIMER_W, TIMER_H = 930, 132  # element size; bar + badge span 900px from the left edge


def el_timer(frac, number, pulse):
    s = SS
    bar_w, h = 800, 46
    im = Image.new("RGBA", (TIMER_W * s, TIMER_H * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y0 = (TIMER_H * s - h * s) // 2
    d.rounded_rectangle((8 * s, y0 + 8 * s, bar_w * s + 8 * s, y0 + h * s + 8 * s), h * s // 2, fill=INK)
    d.rounded_rectangle((0, y0, bar_w * s, y0 + h * s), h * s // 2, fill=WHITE, outline=INK, width=6 * s)
    color = GREEN if frac > 0.5 else (YELLOW if frac > 0.25 else RED)
    inner = int((bar_w * s - 20 * s) * frac)
    if inner > h * s // 2:
        d.rounded_rectangle((10 * s, y0 + 10 * s, 10 * s + inner, y0 + h * s - 10 * s),
                            (h * s - 20 * s) // 2, fill=color)
    # number badge
    r = int((48 + 10 * pulse) * s)
    cx, cy = 850 * s, TIMER_H * s // 2
    d.ellipse((cx - r + 6 * s, cy - r + 6 * s, cx + r + 6 * s, cy + r + 6 * s), fill=INK)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color, outline=INK, width=6 * s)
    d.text((cx, cy + 4 * s), str(number), font=font("display", int((56 + 10 * pulse) * s)), fill=INK, anchor="mm")
    return shrink(im)


def el_end(accent, handle):
    """Full end-screen overlay (transparent background)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    title1 = el_title("HOW MANY", accent, angle=-3)
    title2 = el_title("DID YOU GET?", accent, angle=2)
    tier_h, tier_gap = 150, 26
    content_h = 150 + title2.height + 40 + 3 * tier_h + 2 * tier_gap + 50 + 130 + 40 + 50
    y = 250 + max(0, (SAFE_BOTTOM - 250 - content_h) // 2)
    im.alpha_composite(title1, ((W - title1.width) // 2, y))
    im.alpha_composite(title2, ((W - title2.width) // 2, y + 150))
    y += 150 + title2.height + 40
    tiers = [("5/5", "Certified genius", GREEN), ("3-4", "Big brain energy", YELLOW), ("0-2", "Still a snack", RED)]
    for score, label, color in tiers:
        c, d = card(900, tier_h - 10, WHITE, radius=36, shadow=10)
        s = SS
        d.rounded_rectangle((26 * s, 24 * s, 206 * s, 116 * s), 26 * s, fill=color, outline=INK, width=6 * s)
        d.text((116 * s, 72 * s), score, font=font("display", 64 * s), fill=INK, anchor="mm")
        d.text((244 * s, 71 * s), label, font=font("black", 56 * s), fill=INK, anchor="lm")
        im.alpha_composite(shrink(c), (COL_LEFT, y))
        y += tier_h + tier_gap
    y += 24
    cta, d = card(900, 130, INK, radius=65, ow=0, shadow=0)
    d.text((450 * SS, 68 * SS), "COMMENT YOUR SCORE", font=font("display", 74 * SS), fill=accent, anchor="mm")
    im.alpha_composite(shrink(cta), (COL_LEFT, y))
    d2 = ImageDraw.Draw(im)
    d2.text((W // 2, y + 170), f"Follow {handle} for a new quiz every day", font=font("black", 44),
            fill=INK, anchor="mt")
    return im


# ---------- background ----------
def make_bg(pal):
    sp = 90
    big = Image.new("RGB", (W + sp, H + sp), pal["bg"])
    d = ImageDraw.Draw(big)
    for row, y in enumerate(range(0, H + sp * 2, sp)):
        off = (sp // 2) if row % 2 else 0
        for x in range(-sp, W + sp * 2, sp):
            d.ellipse((x + off - 14, y - 14, x + off + 14, y + 14), fill=pal["dot"])
    return big, sp


# ---------- compositing ----------
def paste(frame, el, cx, top, scale=1.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1.0) > 0.005:
        nw, nh = max(1, int(el.width * scale)), max(1, int(el.height * scale))
        el2 = el.resize((nw, nh), Image.BICUBIC)
        x = int(cx - nw / 2)
        y = int(top + el.height / 2 - nh / 2)
    else:
        el2, x, y = el, int(cx - el.width / 2), int(top)
    if alpha < 0.99:
        a = el2.getchannel("A").point(lambda v: int(v * alpha))
        el2 = el2.copy()
        el2.putalpha(a)
    frame.alpha_composite(el2, (x, y))


def pop(t, delay, dur=0.38):
    p = clamp((t - delay) / dur)
    return (0.6 + 0.4 * ease_out_back(p)) if p > 0 else 0.0, ease_out(p)


# ---------- audio ----------
SR = 48000


def tone(freqs, dur, decay, vol):
    t = np.arange(int(SR * dur)) / SR
    sig = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    return sig * np.exp(-t * decay) * vol


def sfx_tick(high=False):
    t = np.arange(int(SR * 0.06)) / SR
    noise = np.random.default_rng(1).uniform(-1, 1, len(t)) * np.exp(-t * 120) * 0.25
    return noise + tone([2600 if high else 1800], 0.06, 70, 0.35)


def sfx_whoosh():
    n = int(SR * 0.32)
    rng = np.random.default_rng(2)
    noise = rng.uniform(-1, 1, n)
    k = 30
    smooth = np.convolve(noise, np.ones(k) / k, mode="same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return smooth * env * 0.9


def sfx_ding():
    a = tone([880, 1318.5], 0.7, 6, 0.4)
    b = tone([1760], 0.5, 9, 0.18)
    out = np.zeros(len(a) + int(SR * 0.08))
    out[: len(a)] += a
    out[int(SR * 0.08): int(SR * 0.08) + len(b)] += b
    return out


def sfx_fanfare():
    notes = [523.25, 659.25, 783.99, 1046.5]
    out = np.zeros(int(SR * 1.2))
    for i, f in enumerate(notes):
        s = tone([f, f * 2], 0.6, 5, 0.35)
        st = int(SR * 0.11 * i)
        out[st: st + len(s)] += s
    return out


def load_voice(vdir, n):
    """Load quiz_<n>/*.wav voice lines (any sample rate) as mono float32 at SR."""
    if not vdir:
        return None
    d = os.path.join(vdir, f"quiz_{n}")
    if not os.path.isdir(d):
        print(f"  no voice folder for quiz {n}, rendering without voice")
        return None
    import soundfile as sf
    from math import gcd
    from scipy.signal import resample_poly
    v = {}
    for f in sorted(os.listdir(d)):
        if not f.endswith(".wav"):
            continue
        a, sr = sf.read(os.path.join(d, f), dtype="float32")
        if a.ndim > 1:
            a = a.mean(axis=1)
        if sr != SR:
            g = gcd(SR, sr)
            a = resample_poly(a, SR // g, sr // g).astype(np.float32)
        # trim silence at the ends so lines sit tightly
        idx = np.where(np.abs(a) > 0.01)[0]
        if len(idx):
            a = a[max(0, idx[0] - int(SR * 0.02)): idx[-1] + int(SR * 0.08)]
        v[f[:-4]] = a
    return v


def build_timeline(voice):
    """Per-question timing. With a voice, each phase stretches to fit its lines."""
    GAP = 0.18
    segs, cues, t = [], [], 0.0
    for qi in range(5):
        lt = 0.0 if qi == 0 else 0.3  # let the whoosh land before the voice
        keys = (["intro"] if qi == 0 else []) + [f"q{qi + 1}_num", f"q{qi + 1}_question"]
        if voice:
            for k in keys:
                if k in voice:
                    cues.append((t + lt, k))
                    lt += len(voice[k]) / SR + GAP
        intro = max(INTRO, lt + 0.1) if voice else INTRO
        rt = 0.2
        if voice:
            for k in [f"q{qi + 1}_answer", f"q{qi + 1}_fact"]:
                if k in voice:
                    cues.append((t + intro + THINK + rt, k))
                    rt += len(voice[k]) / SR + GAP
        reveal = max(REVEAL, rt + 0.6) if voice else REVEAL
        segs.append(dict(start=t, intro=intro, think=THINK, reveal=reveal))
        t += intro + THINK + reveal
    end_start, end = t, END
    if voice and "outro" in voice:
        cues.append((t + 0.45, "outro"))
        end = max(END, 0.45 + len(voice["outro"]) / SR + 1.4)
    return segs, end_start, end, cues


def build_audio(segs, end_start, total, path, voice=None, cues=(), with_music=True):
    n = int(SR * (total + 1))
    sfx, vo = np.zeros(n), np.zeros(n)

    def add(buf, sig, at):
        st = int(SR * at)
        if st < len(buf):
            e = min(len(buf), st + len(sig))
            buf[st:e] += sig[: e - st]

    for qi, s in enumerate(segs):
        if qi > 0:
            add(sfx, sfx_whoosh(), s["start"])
        for k in range(3):
            add(sfx, sfx_tick(high=(k == 2)), s["start"] + s["intro"] + k)
        add(sfx, sfx_ding(), s["start"] + s["intro"] + s["think"])
    add(sfx, sfx_whoosh(), end_start)
    add(sfx, sfx_fanfare(), end_start + 0.15)

    for at, key in cues:
        add(vo, voice[key] * (0.9 / (np.max(np.abs(voice[key])) + 1e-9)), at)

    mix = vo + sfx * (0.6 if voice else 1.0)
    if with_music:
        import music
        m = music.make_loop(total + 1)[:n]
        m = np.pad(m, (0, n - len(m)))
        if voice:
            w = int(SR * 0.12)
            env = np.convolve(np.abs(vo), np.ones(w) / w, mode="same")
            duck = np.where(env > 0.008, 0.32, 1.0)
            duck = np.convolve(duck, np.ones(int(SR * 0.1)) / int(SR * 0.1), mode="same")
        else:
            duck = 1.0
        mix = mix + m * 0.2 * duck
    buf = mix[: int(SR * total)]
    buf = buf / (np.max(np.abs(buf)) + 1e-9) * 0.95
    pcm = (buf * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm]).ravel()
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


# ---------- main render ----------
def render(quiz, n, handle, outdir, voice_dir=None, with_music=True):
    pal = PALETTES[n % len(PALETTES)]
    qs = quiz["questions"][:5]
    voice = load_voice(voice_dir, n)
    segs, end_start, end_dur, cues = build_timeline(voice)
    total = end_start + end_dur
    bg, sp = make_bg(pal)

    chip = el_theme_chip(f"{quiz['theme'].upper()} TRIVIA  ·  {handle}")
    title = el_title("CAN YOU GET 5/5?", pal["accent"])
    per_q = []
    for i, q in enumerate(qs):
        letters = "ABC"
        per_q.append(dict(
            progress=el_progress(i, 5, q["level"]),
            question=el_question(q["q"]),
            normal=[el_option(letters[j], o, "normal", pal["accent"]) for j, o in enumerate(q["options"])],
            final=[el_option(letters[j], o, "correct" if j == q["answer"] else "wrong", pal["accent"])
                   for j, o in enumerate(q["options"])],
            fact=el_fact(q["fact"], pal["accent"]),
        ))
        E = per_q[-1]
        # vertical layout, centered between the header and the bottom safe line
        rel = {"prog": 0, "q": 64 + 18}
        rel["timer_mid"] = rel["q"] + E["question"].height + 16 + 30
        rel["opt"] = rel["q"] + E["question"].height + 16 + 60 + 16
        rel["fact"] = rel["opt"] + 3 * OPT_H + 2 * OPT_GAP + 14
        think_h = rel["opt"] + 3 * OPT_H + 2 * OPT_GAP + 10
        body_h = rel["fact"] + E["fact"].height
        room = SAFE_BOTTOM - HEADER_BOTTOM
        top_think = HEADER_BOTTOM + max(0, (room - think_h) // 2)
        top_reveal = max(HEADER_BOTTOM, min(top_think, SAFE_BOTTOM - body_h))
        E["rel"], E["top_think"], E["top_reveal"] = rel, top_think, top_reveal
        if top_reveal + body_h > SAFE_BOTTOM:
            print(f"  warning: question {i + 1} runs {top_reveal + body_h - SAFE_BOTTOM}px into the bottom zone")
    end_overlay = el_end(pal["accent"], handle)

    os.makedirs(outdir, exist_ok=True)
    wav = os.path.join(outdir, f"quiz_{n}.wav")
    mp4 = os.path.join(outdir, f"quiz_{n}.mp4")
    build_audio(segs, end_start, total, wav, voice, cues, with_music)

    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest", mp4,
    ], stdin=subprocess.PIPE)

    cover = None
    nframes = int(total * FPS)
    for fi in range(nframes):
        t = fi / FPS
        off = int((t * 40) % sp)
        frame = bg.crop((off, off, off + W, off + H)).convert("RGBA")

        if t < end_start:
            qi = max(i for i, s in enumerate(segs) if s["start"] <= t)
            S = segs[qi]
            lt = t - S["start"]
            INTRO_, THINK_ = S["intro"], S["think"]
            E = per_q[qi]
            anim = qi > 0  # first question is fully visible on frame 1 (hook)

            rt = lt - (INTRO_ + THINK_)
            slide = ease_out(clamp(rt / 0.35)) if rt > 0 else 0.0
            top = E["top_think"] + (E["top_reveal"] - E["top_think"]) * slide
            L = {k: top + v for k, v in E["rel"].items()}
            paste(frame, chip, W / 2, 240)
            paste(frame, title, W / 2, 300)
            sc, al = pop(lt, 0.0) if anim else (1, 1)
            paste(frame, E["progress"], COL_LEFT + E["progress"].width / 2, L["prog"], 1, al)
            paste(frame, E["question"], COL_LEFT + E["question"].width / 2, L["q"], sc, al)

            # timer
            if lt < INTRO_ + THINK_:
                rem = THINK_ - max(0.0, lt - INTRO_)
                frac = rem / THINK_
                number = max(1, math.ceil(rem - 1e-6))
                since_tick = (lt - INTRO_) % 1.0 if lt >= INTRO_ else 1.0
                pulse = max(0.0, 1 - since_tick / 0.25)
                tsc, tal = pop(lt, 0.05) if anim else (1, 1)
                paste(frame, el_timer(frac, number, pulse), COL_LEFT + TIMER_W / 2,
                      L["timer_mid"] - TIMER_H / 2, tsc, tal)

            reveal_t = lt - (INTRO_ + THINK_)
            for j in range(3):
                y = L["opt"] + j * (OPT_H + OPT_GAP)
                cx = COL_LEFT + E["normal"][j].width / 2
                if reveal_t < 0:
                    s_, a_ = pop(lt, 0.1 + 0.08 * j) if anim else (1, 1)
                    paste(frame, E["normal"][j], cx, y, s_, a_)
                elif j == qs[qi]["answer"]:
                    b = clamp(reveal_t / 0.32)
                    paste(frame, E["final"][j], cx, y, 1 + 0.07 * math.sin(math.pi * b), 1)
                else:
                    paste(frame, E["final"][j], cx, y, 1, 1 - 0.55 * clamp(reveal_t / 0.2))
            if reveal_t >= 0:
                fs, fa = pop(reveal_t, 0.25)
                paste(frame, E["fact"], COL_LEFT + E["fact"].width / 2, L["fact"], fs, fa)
            if fi == int(1.0 * FPS):
                cover = frame.copy()
        else:
            et = t - end_start
            sc, al = pop(et, 0.0, 0.45)
            paste(frame, end_overlay, W / 2, 0, sc, al)

        proc.stdin.write(frame.convert("RGB").tobytes())

    proc.stdin.close()
    proc.wait()
    os.remove(wav)

    if cover is not None:
        cover.convert("RGB").save(os.path.join(outdir, f"quiz_{n}_cover.jpg"), quality=92)
    caption = (
        f"{quiz['theme']} trivia: can you get 5/5? 🧠\n"
        "Comment your score below 👇 Send this to someone who thinks they know everything.\n\n"
        f"Follow {handle} for a new quiz every day.\n\n"
        f"#trivia #quiz #triviachallenge #funfacts #{quiz['theme'].lower().replace(' ', '')}trivia #brainteaser"
    )
    with open(os.path.join(outdir, f"quiz_{n}_caption.txt"), "w") as f:
        f.write(caption)
    return mp4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--handle", default="@mindsnackhere")
    ap.add_argument("--questions", default=os.path.join(HERE, "questions.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--voice", help="folder with quiz_<n>/<line>.wav voice files (from the voice kit)")
    ap.add_argument("--no-music", action="store_true")
    a = ap.parse_args()
    quizzes = json.load(open(a.questions))
    ids = range(len(quizzes)) if a.all else [a.set]
    for n in ids:
        out = render(quizzes[n], n, a.handle, a.out, a.voice, not a.no_music)
        print("Rendering", n, quizzes[n]["theme"], "->", out)


if __name__ == "__main__":
    main()
