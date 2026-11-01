"""Still mockup frames for the 'less AI slop' redesign (both accounts).
Run on the home PC: python experiments/mockups/make_frames.py
Writes PNGs + a contact sheet to experiments/mockups/out/.
Background photos come from Wikimedia Commons (reference mockups only, check license before posting).
"""
import io, json, os, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
F = {
    "lilita": os.path.join(ROOT, "generator/fonts/LilitaOne.woff"),
    "nunito": os.path.join(ROOT, "generator/fonts/NunitoBlack.woff"),
    "merri": os.path.join(HERE, "assets/Merri900.woff"),
    "franklin": os.path.join(HERE, "assets/Franklin800.woff"),
}
WHITE, YELLOW, GREEN, DIM = (255, 255, 255), (255, 214, 64), (60, 220, 120), (255, 255, 255, 90)


def font(name, size):
    return ImageFont.truetype(F[name], size)


def commons(query):
    """First Commons image for a search, scaled to ~1600px. None if offline."""
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": query, "gsrlimit": 5, "prop": "imageinfo", "iiprop": "url|mime",
        "iiurlwidth": 1600})
    hdr = {"User-Agent": "mindsnack-mockups/1.0 (github.com/jck-bllli)"}
    try:
        data = json.load(urllib.request.urlopen(urllib.request.Request(api, headers=hdr), timeout=20))
        pages = sorted(data["query"]["pages"].values(), key=lambda p: p.get("index", 99))
        for p in pages:
            ii = p["imageinfo"][0]
            if ii.get("mime") in ("image/jpeg", "image/png"):
                raw = urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=hdr), timeout=30).read()
                print("photo:", p["title"])
                return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:  # mockups still render without photos
        print("no photo for", query, e)
    return None


def cover(img, zoom=1.0, fallback=(30, 30, 60)):
    if img is None:
        return Image.new("RGB", (W, H), fallback)
    s = max(W / img.width, H / img.height) * zoom
    img = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    l, t = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((l, t, l + W, t + H))


def shade(img, top=0.35, bottom=0.85, tint=(0, 0, 0)):
    """Darken with a vertical gradient so text reads."""
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(255 * (top + (bottom - top) * y / H)))
    grad = grad.resize((W, H))
    return Image.composite(Image.new("RGB", (W, H), tint), img, grad)


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def center(d, y, text, f, fill, stroke=0, maxw=940, gap=1.12):
    for line in wrap(d, text, f, maxw):
        d.text((W // 2, y), line, font=f, fill=fill, anchor="ma",
               stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += int(f.size * gap)
    return y


def pill(d, cx, y, text, f, bg, fg=(0, 0, 0), pad=22):
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((cx - tw / 2 - pad, y, cx + tw / 2 + pad, y + f.size + pad), radius=(f.size + pad) // 2, fill=bg)
    d.text((cx, y + pad // 2), text, font=f, fill=fg, anchor="ma")


def save(img, name):
    img.convert("RGB").save(os.path.join(OUT, name + ".png"))
    print("wrote", name)
    return img


frames = []
rex = commons("Tyrannosaurus rex skeleton museum")
steg = commons("Stegosaurus skeleton museum")
mal = commons("Mar-a-Lago aerial")

# ---------- mindsnack 1: hook frame (0.0s) ----------
im = shade(cover(rex), 0.25, 0.8)
d = ImageDraw.Draw(im)
pill(d, W // 2, 170, "DINOSAUR TRIVIA  ·  3 QUESTIONS", font("nunito", 34), YELLOW)
y = center(d, 560, "T. REX LIVED CLOSER TO YOU", font("lilita", 118), WHITE, stroke=6)
y = center(d, y + 10, "THAN TO STEGOSAURUS.", font("lilita", 118), YELLOW, stroke=6)
center(d, y + 70, "True or false? You get 3 seconds.", font("nunito", 52), WHITE, stroke=3)
center(d, 1480, "@mindsnackhere", font("nunito", 36), (255, 255, 255))
frames.append(save(im, "ms_1_hook"))

# ---------- mindsnack 2: question with timer ----------
im = shade(cover(steg), 0.3, 0.75, (20, 40, 10))
d = ImageDraw.Draw(im)
pill(d, W // 2, 170, "QUESTION 1 / 3", font("nunito", 36), WHITE)
d.rounded_rectangle((70, 300, W - 70, 620), radius=40, fill=WHITE)
center(d, 360, "Which lived closer in time to T. rex?", font("lilita", 84), (20, 20, 20), maxw=860)
opts = [("A", "Stegosaurus"), ("B", "Humans")]
for i, (k, t) in enumerate(opts):
    top = 700 + i * 170
    d.rounded_rectangle((110, top, W - 110, top + 130), radius=34, fill=(255, 255, 255, 235), outline=(0, 0, 0), width=5)
    d.text((170, top + 65), k, font=font("lilita", 70), fill=(230, 60, 110), anchor="mm")
    d.text((240, top + 65), t, font=font("nunito", 62), fill=(20, 20, 20), anchor="lm")
d.ellipse((W // 2 - 110, 1130, W // 2 + 110, 1350), fill=YELLOW, outline=(0, 0, 0), width=8)
d.text((W // 2, 1240), "2", font=font("lilita", 150), fill=(0, 0, 0), anchor="mm")
frames.append(save(im, "ms_2_question"))

# ---------- mindsnack 3: reveal (punch-in + answer) ----------
im = shade(cover(steg, zoom=1.18), 0.35, 0.8, (5, 40, 20))
d = ImageDraw.Draw(im)
center(d, 330, "HUMANS.", font("lilita", 210), GREEN, stroke=8)
d.rounded_rectangle((110, 700, W - 110, 830), radius=34, fill=GREEN, outline=(0, 0, 0), width=5)
d.text((W // 2, 765), "B   Humans", font=font("nunito", 66), fill=(0, 0, 0), anchor="mm")
d.rounded_rectangle((90, 920, W - 90, 1300), radius=36, fill=(255, 255, 255))
pill(d, W // 2, 890, "WAIT, WHAT?", font("nunito", 34), YELLOW)
center(d, 990, "Stegosaurus was gone about 80 million years before T. rex showed up. T. rex is only 66 million years from you.",
       font("nunito", 46), (20, 20, 20), maxw=820, gap=1.25)
frames.append(save(im, "ms_3_reveal"))

# ---------- trumpsaidtoday 1: hook = best quote, karaoke ----------
base = cover(mal, fallback=(20, 30, 70))
im = shade(base, 0.45, 0.85, (8, 14, 40))
d = ImageDraw.Draw(im)
pill(d, W // 2, 170, "OCT 31  ·  PALM BEACH", font("franklin", 38), (225, 40, 50), WHITE)
quote = "“I had 10 minutes, so I came as Donald Trump.”"
f = font("merri", 104)
lit = 6  # words spoken so far
words, y, line = quote.split(), 520, []
for ln in wrap(d, quote, f, 920):
    x = (W - d.textlength(ln, font=f)) / 2
    for w in ln.split():
        idx = len(line); line.append(w)
        col = WHITE if idx < lit else (150, 160, 200)
        if idx == lit - 1:
            col = YELLOW
        d.text((x, y), w, font=f, fill=col)
        x += d.textlength(w + " ", font=f)
    y += int(f.size * 1.25)
center(d, y + 60, "Trump, on his Halloween costume", font("franklin", 44), (200, 210, 235))
logo = Image.open(os.path.join(HERE, "assets/pfp_E.png")).convert("RGBA").resize((110, 110))
im.paste(logo, (W - 160, 1500), logo)
d.text((W - 180, 1555), "@trumpsaidtoday", font=font("franklin", 32), fill=WHITE, anchor="rm")
frames.append(save(im, "td_1_hook"))

# ---------- trumpsaidtoday 2: one quote, words land with the voice ----------
im = shade(base.filter(ImageFilter.GaussianBlur(14)), 0.6, 0.9, (8, 14, 40))
d = ImageDraw.Draw(im)
pill(d, W // 2, 170, "2 / 3", font("franklin", 38), WHITE)
center(d, 330, "On a reported legal payment to his former lawyer Alina Habba",
       font("franklin", 46), (200, 210, 235), maxw=880)
f = font("merri", 120)
y = 640
for ln, col in [("“I thought it", WHITE), ("was totally", WHITE), ("obnoxious", YELLOW)]:
    d.text((W // 2, y), ln, font=f, fill=col, anchor="ma"); y += 150
d.text((W // 2, y + 40), "Remarks · Palm Beach, Florida", font=font("franklin", 36), fill=(170, 180, 210), anchor="ma")
im.paste(logo, (W - 160, 1500), logo)
frames.append(save(im, "td_2_kinetic"))

# ---------- trumpsaidtoday 3: end card that loops back ----------
im = shade(base, 0.6, 0.9, (8, 14, 40))
d = ImageDraw.Draw(im)
center(d, 640, "That was Oct 31.", font("merri", 110), WHITE)
center(d, 820, "Every quote's source is in the caption.", font("franklin", 52), (200, 210, 235))
center(d, 1000, "Follow for tomorrow's quotes.", font("franklin", 52), YELLOW)
im.paste(logo, (W // 2 - 55, 1250), logo)
frames.append(save(im, "td_3_end"))

# ---------- contact sheet ----------
tw, th = 360, 640
sheet = Image.new("RGB", (tw * 3 + 40, th * 2 + 30), (15, 15, 15))
for i, fr in enumerate(frames):
    sheet.paste(fr.convert("RGB").resize((tw, th), Image.LANCZOS), (10 + (i % 3) * (tw + 10), 10 + (i // 3) * (th + 10)))
sheet.save(os.path.join(OUT, "contact_sheet.jpg"), quality=88)
print("done")
