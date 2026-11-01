"""Trivia text styles without the 'AI template' card. 3 styles x (question, reveal).
Run on the home PC: python experiments/mockups/make_trivia_v2.py -> experiments/mockups/out/trivia_v2_*
"""
import io, json, os, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
LIL = os.path.join(ROOT, "generator/fonts/LilitaOne.woff")
NUN = os.path.join(ROOT, "generator/fonts/NunitoBlack.woff")
MER = os.path.join(HERE, "assets/Merri900.woff")
FRA = os.path.join(HERE, "assets/Franklin800.woff")
WHITE, BLACK, YEL, GRN = (255, 255, 255), (0, 0, 0), (255, 214, 64), (70, 230, 130)
Q, A, B, FACT = ("Which lived closer in time to T. rex?", "Stegosaurus", "Humans",
                 "Stegosaurus was gone 80 million years before T. rex. T. rex is 66 million years from you.")


def f(p, s):
    return ImageFont.truetype(p, s)


def commons(query):
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrsearch": query,
        "gsrlimit": 5, "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": 1600})
    hdr = {"User-Agent": "mindsnack-mockups/1.0 (github.com/jck-bllli)"}
    try:
        pages = sorted(json.load(urllib.request.urlopen(urllib.request.Request(api, headers=hdr), timeout=20))
                       ["query"]["pages"].values(), key=lambda p: p.get("index", 99))
        for p in pages:
            ii = p["imageinfo"][0]
            if ii.get("mime") in ("image/jpeg", "image/png"):
                raw = urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=hdr), timeout=30).read()
                return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        print("no photo", query, e)
    return None


def cover(img, zoom=1.0, box=(W, H)):
    bw, bh = box
    if img is None:
        return Image.new("RGB", box, (40, 50, 40))
    s = max(bw / img.width, bh / img.height) * zoom
    img = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    l, t = (img.width - bw) // 2, (img.height - bh) // 2
    return img.crop((l, t, l + bw, t + bh))


def darken(img, a):
    return Image.blend(img, Image.new("RGB", img.size, BLACK), a)


def wrap(d, text, fnt, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            out.append(cur); cur = w
    return out + [cur]


def save(im, name, frames):
    im.save(os.path.join(OUT, f"trivia_v2_{name}.png")); frames.append(im); print("wrote", name)


steg = commons("Stegosaurus skeleton museum")
frames = []

# ---- Style 1: Instagram-native text (tight per-line highlight, like the in-app text tool) ----
def native_lines(d, x, y, lines, fnt, bg, fg, pad=18, gap=6):
    for ln in lines:
        tw = d.textlength(ln, font=fnt)
        d.rounded_rectangle((x - tw / 2 - pad, y, x + tw / 2 + pad, y + fnt.size + pad * 1.3), radius=14, fill=bg)
        d.text((x, y + pad * 0.45), ln, font=fnt, fill=fg, anchor="ma")
        y += fnt.size + pad * 1.3 + gap
    return y

for reveal in (False, True):
    im = darken(cover(steg, 1.18 if reveal else 1.0), 0.15)
    d = ImageDraw.Draw(im)
    fq = f(NUN, 70)
    y = native_lines(d, W // 2, 420, wrap(d, Q, fq, 820), fq, WHITE, BLACK)
    fo = f(NUN, 64)
    for i, (k, t) in enumerate([("A", A), ("B", B)]):
        right = reveal and k == "B"
        wrong = reveal and k == "A"
        bg = GRN if right else ((0, 0, 0) if not wrong else (60, 60, 60))
        fg = BLACK if right else ((255, 255, 255) if not wrong else (150, 150, 150))
        native_lines(d, W // 2, y + 90 + i * 130, [f"{k}. {t}"], fo, bg, fg)
    if reveal:
        ff = f(NUN, 46)
        native_lines(d, W // 2, 1250, wrap(d, FACT, ff, 860), ff, YEL, BLACK, pad=14, gap=4)
    else:
        d.text((W // 2, 1300), "3", font=f(LIL, 220), fill=WHITE, anchor="ma", stroke_width=10, stroke_fill=BLACK)
    save(im, f"1_native_{'reveal' if reveal else 'question'}", frames)

# ---- Style 2: editorial, no boxes; big type straight on the photo ----
for reveal in (False, True):
    im = cover(steg, 1.18 if reveal else 1.0)
    grad = Image.linear_gradient("L").resize((W, H))  # dark at bottom
    im = Image.composite(Image.new("RGB", (W, H), (8, 10, 8)), im, grad.point(lambda v: int(v * 0.92)))
    d = ImageDraw.Draw(im)
    d.text((80, 900), "NO. 1 / DINOSAURS", font=f(FRA, 34), fill=YEL)
    fq = f(MER, 82); y = 960
    for ln in wrap(d, Q, fq, 920):
        d.text((80, y), ln, font=fq, fill=WHITE); y += 104
    y += 40
    for k, t in [("A", A), ("B", B)]:
        right, wrong = reveal and k == "B", reveal and k == "A"
        col = GRN if right else ((110, 110, 110) if wrong else WHITE)
        d.line((80, y, W - 80, y), fill=(255, 255, 255, 120), width=2)
        d.text((80, y + 28), k, font=f(FRA, 60), fill=YEL if not wrong else col)
        d.text((170, y + 24), t, font=f(MER, 64), fill=col)
        if wrong:
            tw = d.textlength(t, font=f(MER, 64)); d.line((170, y + 66, 170 + tw, y + 66), fill=col, width=6)
        y += 120
    if reveal:
        ff = f(FRA, 40)
        for ln in wrap(d, FACT, ff, 900):
            d.text((80, y + 40), ln, font=ff, fill=(220, 220, 220)); y += 52
    else:
        d.text((W - 80, 860), "3", font=f(MER, 90), fill=YEL, anchor="rs")
    save(im, f"2_editorial_{'reveal' if reveal else 'question'}", frames)

# ---- Style 3: split screen, tap a side (photo top, answers as two color halves) ----
for reveal in (False, True):
    im = Image.new("RGB", (W, H))
    im.paste(darken(cover(steg, 1.0, (W, 760)), 0.2), (0, 0))
    halves = [((230, 70, 110), A), ((60, 120, 240), B)]
    for i, (c, t) in enumerate(halves):
        right, wrong = reveal and i == 1, reveal and i == 0
        col = GRN if right else ((45, 45, 45) if wrong else c)
        im.paste(Image.new("RGB", (W, 580), col), (0, 760 + i * 580))
    d = ImageDraw.Draw(im)
    for i, (c, t) in enumerate(halves):
        wrong = reveal and i == 0
        d.text((W // 2, 760 + i * 580 + 290), t.upper(), font=f(LIL, 120),
               fill=(120, 120, 120) if wrong else WHITE, anchor="mm", stroke_width=0 if wrong else 6, stroke_fill=BLACK)
    fq = f(LIL, 78)
    y = 140
    for ln in wrap(d, Q.upper(), fq, 900):
        d.text((W // 2, y), ln, font=fq, fill=WHITE, anchor="ma", stroke_width=7, stroke_fill=BLACK); y += 92
    d.ellipse((W // 2 - 80, 1260, W // 2 + 80, 1420), fill=WHITE, outline=BLACK, width=8)
    d.text((W // 2, 1340), "OR" if not reveal else "B", font=f(LIL, 70), fill=BLACK, anchor="mm")
    if reveal:
        ff = f(NUN, 40)
        y += 40
        for ln in wrap(d, FACT, ff, 900):
            d.text((W // 2, y), ln, font=ff, fill=WHITE, anchor="ma", stroke_width=4, stroke_fill=BLACK); y += 52
    save(im, f"3_split_{'reveal' if reveal else 'question'}", frames)

tw, th = 300, 533
sheet = Image.new("RGB", (tw * 6 + 70, th + 20), (15, 15, 15))
for i, fr in enumerate(frames):
    sheet.paste(fr.resize((tw, th), Image.LANCZOS), (10 + i * (tw + 10), 10))
sheet.save(os.path.join(OUT, "trivia_v2_sheet.jpg"), quality=88)
print("done")
