"""mindsnackevil mockup frames. Same layout as mindsnack, flipped colors, rival voice. Run on home PC."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
LIL = os.path.join(ROOT, "generator/fonts/LilitaOne.woff")
NUN = os.path.join(ROOT, "generator/fonts/NunitoBlack.woff")
f = lambda p, s: ImageFont.truetype(p, s)
# mindsnack: light card on photo, yellow/green/pink. Evil: flipped to black card, bone text, blood red + acid green.
BG, BONE, RED, ACID, INK = (14, 10, 12), (240, 232, 214), (225, 30, 45), (170, 255, 60), (20, 20, 20)

def wrap(d, t, ft, mw):
    out, cur = [], ""
    for w in t.split():
        c = (cur + " " + w).strip()
        if d.textlength(c, font=ft) <= mw: cur = c
        else: out.append(cur); cur = w
    return out + [cur]

def center(d, y, t, ft, fill, mw=940, gap=1.12):
    for ln in wrap(d, t, ft, mw):
        d.text((W // 2, y), ln, font=ft, fill=fill, anchor="ma"); y += int(ft.size * gap)
    return y

def pill(d, y, t, ft, bg, fg):
    tw = d.textlength(t, font=ft); p = 22
    d.rounded_rectangle((W/2 - tw/2 - p, y, W/2 + tw/2 + p, y + ft.size + p), radius=(ft.size + p)//2, fill=bg)
    d.text((W // 2, y + p // 2), t, font=ft, fill=fg, anchor="ma")

def base(stripe=True):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    if stripe:  # flat hazard stripes top and bottom, no gradients
        for x in range(-100, W + 100, 90):
            d.polygon([(x, 0), (x + 45, 0), (x + 15, 36), (x - 30, 36)], fill=RED)
            d.polygon([(x, H), (x + 45, H), (x + 15, H - 36), (x - 30, H - 36)], fill=RED)
    return im, d

def handle(d, t="@mindsnackevil"):
    d.text((W // 2, 1780), t, font=f(NUN, 36), fill=(150, 140, 130), anchor="ma")

frames = []
# 1 hook
im, d = base(); pill(d, 170, "TRIVIA, BUT BETTER", f(NUN, 34), RED, BONE)
y = center(d, 520, "OCTOPUSES HAVE 3 HEARTS.", f(LIL, 124), BONE)
y = center(d, y + 20, "MY COUSIN HAS ZERO PLANS.", f(LIL, 124), RED)
center(d, y + 70, "He posted this first. Doesn't matter. Mine's meaner.", f(NUN, 50), BONE); handle(d); frames.append(im)
# 2 question
im, d = base(); pill(d, 170, "QUESTION 1 / 3", f(NUN, 36), BONE, INK)
d.rounded_rectangle((70, 300, W - 70, 640), radius=40, fill=BONE)
center(d, 360, "How many hearts does an octopus have? Take your time. My cousin did.", f(LIL, 70), INK, mw=860, gap=1.15)
for i, (k, t) in enumerate([("A", "One"), ("B", "Three")]):
    top = 740 + i * 170
    d.rounded_rectangle((110, top, W - 110, top + 130), radius=34, fill=BG, outline=BONE, width=6)
    d.text((170, top + 65), k, font=f(LIL, 70), fill=RED, anchor="mm")
    d.text((240, top + 65), t, font=f(NUN, 62), fill=BONE, anchor="lm")
d.ellipse((W//2 - 110, 1160, W//2 + 110, 1380), fill=RED, outline=BONE, width=8)
d.text((W // 2, 1270), "2", font=f(LIL, 150), fill=BONE, anchor="mm"); handle(d); frames.append(im)
# 3 reveal
im, d = base(); center(d, 330, "THREE.", f(LIL, 230), ACID)
d.rounded_rectangle((110, 700, W - 110, 830), radius=34, fill=ACID)
d.text((W // 2, 765), "B   Three", font=f(NUN, 66), fill=INK, anchor="mm")
pill(d, 890, "YOU GOT IT? SHOCKING.", f(NUN, 34), RED, BONE)
d.rounded_rectangle((90, 990, W - 90, 1400), radius=36, fill=BONE)
center(d, 1050, "Two for the gills, one for the body. Three hearts and none of them are as cold as my cousin's thumbnails.", f(NUN, 46), INK, mw=820, gap=1.25)
handle(d); frames.append(im)
# 4 cameo hook (trumpsaidtoday)
im, d = base(); pill(d, 170, "FAMILY DRAMA", f(NUN, 34), ACID, INK)
y = center(d, 520, "WHO WON THE EMU WAR?", f(LIL, 130), BONE)
y = center(d, y + 20, "NOT THE ARMY.", f(LIL, 130), RED)
center(d, y + 70, "My other cousin @trumpsaidtoday only reads quotes. I read the casualty report.", f(NUN, 48), BONE); handle(d); frames.append(im)
# 5 cameo hook (mindsnack)
im, d = base(); pill(d, 170, "ACTUALLY HARD", f(NUN, 34), RED, BONE)
y = center(d, 520, "A BANANA IS A BERRY.", f(LIL, 130), BONE)
y = center(d, y + 20, "A STRAWBERRY ISN'T.", f(LIL, 130), ACID)
center(d, y + 70, "@mindsnackhere apologized for it. I never will.", f(NUN, 50), BONE); handle(d); frames.append(im)
# 6 profile card
im, d = base(False)
d.ellipse((W//2 - 150, 300, W//2 + 150, 600), fill=RED)
d.text((W // 2, 450), "e", font=f(LIL, 240), fill=BG, anchor="mm")
d.text((W // 2, 660), "mindsnackevil", font=f(LIL, 90), fill=BONE, anchor="ma")
y = center(d, 800, "Hating my cousin @mindsnackhere since 2026", f(NUN, 56), BONE, mw=860)
center(d, y + 40, "Same facts. Worse attitude.", f(NUN, 46), ACID, mw=860)
d.text((W // 2, 1200), "(logo is a placeholder)", font=f(NUN, 30), fill=(120, 110, 100), anchor="ma"); frames.append(im)

for i, fr in enumerate(frames): fr.save(os.path.join(OUT, f"evil_{i+1}.png"))
tw, th = 360, 640
sh = Image.new("RGB", (tw*3 + 40, th*2 + 30), (30, 30, 30))
for i, fr in enumerate(frames):
    sh.paste(fr.resize((tw, th), Image.LANCZOS), (10 + (i % 3)*(tw + 10), 10 + (i // 3)*(th + 10)))
sh.save(os.path.join(OUT, "contact_sheet.jpg"), quality=88); print("done")
