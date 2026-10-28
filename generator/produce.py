#!/usr/bin/env python3
"""Turn quizzes in questions.json into voiced, queued Reels.

  python generator/produce.py --new            # every quiz not yet in queue.json
  python generator/produce.py --start 8 --end 14
  python generator/produce.py --start 0 --end 0 --dry-run   # render to /tmp only, touch nothing

Steps per quiz: build the voice script -> voice it (Kokoro, matched 'Option A' voice)
-> render the video -> copy to videos/ -> append to queue.json with a caption.
Run generator/setup.sh once per machine first.
"""
import argparse
import json
import os
import random
import re
import shutil
import sys
import tempfile

GEN = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(GEN)
sys.path.insert(0, GEN)

ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
        "fifteen sixteen seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def int_words(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + int_words(n % 100))
    for size, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= size:
            rest = n % size
            return int_words(n // size) + " " + name + ("" if rest == 0 else " " + int_words(rest))
    return str(n)


def year_words(y):
    if 2000 <= y < 2010:
        return "two thousand" + ("" if y == 2000 else " " + ONES[y - 2000])
    hi, lo = divmod(y, 100)
    if lo == 0:
        return int_words(hi) + " hundred"
    return int_words(hi) + " " + (("oh " + ONES[lo]) if lo < 10 else int_words(lo))


def speakable(text):
    """Write numbers out so the voice reads them right."""
    def num(m):
        s = m.group(0)
        if re.fullmatch(r"1[0-9]{3}s|20[0-9]{2}s", s):
            w = year_words(int(s[:4]))
            return (w[:-1] + "ies") if w.endswith("y") else w + "s"
        if re.fullmatch(r"(1[0-9]{3}|20[0-9]{2})", s):
            return year_words(int(s))
        if "." in s:
            a, b = s.replace(",", "").split(".")
            return int_words(int(a)) + " point " + " ".join(ONES[int(d)] for d in b)
        return int_words(int(s.replace(",", "")))
    text = re.sub(r"(\d+)\+", lambda m: "over " + m.group(1), text)
    text = re.sub(r"(\d+)°C", lambda m: m.group(1) + " degrees Celsius", text)
    text = re.sub(r"(\d+)%", lambda m: m.group(1) + " percent", text)
    return re.sub(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?s?", num, text)


REVEALS = ["It's {a}!", "The answer is {a}!", "{a}!", "Yep, it's {a}!", "It's {a}!"]
NUMS = ["one", "two", "three", "four"]


def build_lines(quiz, n):
    rng = random.Random(1000 + n)
    lines = [{"id": "intro", "text": f"{quiz['theme']} trivia! Can you get five out of five? Let's go!"}]
    for i, q in enumerate(quiz["questions"][:5]):
        # optional overrides: "answer_say" / "fact_say" / "q_say" let the voice word things naturally
        a = q.get("answer_say") or speakable(q["options"][q["answer"]])
        lines += [
            {"id": f"q{i + 1}_num", "text": f"Question {NUMS[i]}!" if i < 4 else "Last one, and it's a hard one!"},
            {"id": f"q{i + 1}_question", "text": q.get("q_say") or speakable(q["q"])},
            {"id": f"q{i + 1}_answer", "text": (lambda t: t[:1].upper() + t[1:])(rng.choice(REVEALS).format(a=a))},
            {"id": f"q{i + 1}_fact", "text": q.get("fact_say") or speakable(q["fact"])},
        ]
    lines.append({"id": "outro", "text": "So, how many did you get? Comment your score below!"})
    return {"quiz": n, "theme": quiz["theme"], "lines": lines}


def validate(quiz, n):
    qs = quiz.get("questions", [])
    assert len(qs) == 5, f"quiz {n}: needs exactly 5 questions"
    for i, q in enumerate(qs):
        assert len(q["options"]) == 3, f"quiz {n} q{i + 1}: needs 3 options"
        assert 0 <= q["answer"] <= 2, f"quiz {n} q{i + 1}: answer must be 0-2"
        assert q["level"] in ("easy", "medium", "hard"), f"quiz {n} q{i + 1}: bad level"


def caption(quiz, handle):
    tag = re.sub(r"[^a-z0-9]", "", quiz["theme"].lower())
    return (f"{quiz['theme']} trivia: can you get 5/5? 🧠\n"
            "Comment your score below 👇 Send this to someone who thinks they know everything.\n\n"
            f"Follow {handle} for a new quiz every day.\n\n"
            f"#trivia #quiz #triviachallenge #funfacts #{tag}trivia #brainteaser")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int)
    ap.add_argument("--end", type=int)
    ap.add_argument("--new", action="store_true", help="every quiz not yet in queue.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--handle", default="@mindsnackhere")
    a = ap.parse_args()

    import make_video
    import voice_echo

    quizzes = json.load(open(os.path.join(GEN, "questions.json")))
    queue_path = os.path.join(ROOT, "queue.json")
    queue = json.load(open(queue_path))
    queued = {q["id"] for q in queue}
    if a.new:
        ids = [n for n in range(len(quizzes)) if f"quiz_{n}" not in queued]
    else:
        ids = list(range(a.start, (a.end if a.end is not None else a.start) + 1))
    if not ids:
        print("Nothing new to produce.")
        return
    for n in ids:
        validate(quizzes[n], n)

    work = tempfile.mkdtemp(prefix="mindsnack_")
    lines = [build_lines(quizzes[n], n) for n in ids]
    lines_path = os.path.join(work, "lines.json")
    json.dump(lines, open(lines_path, "w"), indent=2)
    voice_dir = os.path.join(work, "voice")
    voice_echo.main(lines_path, voice_dir)

    out_dir = os.path.join(work, "out")
    for n in ids:
        mp4 = make_video.render(quizzes[n], n, a.handle, out_dir, voice_dir, True)
        print("rendered", mp4, flush=True)
        if a.dry_run:
            continue
        dest = os.path.join(ROOT, "videos", f"quiz_{n}.mp4")
        shutil.copy(mp4, dest)
        if f"quiz_{n}" not in queued:
            queue.append({"id": f"quiz_{n}", "video": f"videos/quiz_{n}.mp4",
                          "caption": caption(quizzes[n], a.handle), "thumb_offset_ms": 1000})
            queued.add(f"quiz_{n}")
    if not a.dry_run:
        json.dump(queue, open(queue_path, "w"), indent=2, ensure_ascii=False)
        print(f"Queued {len(ids)} quiz(zes). Work files: {work}")
    else:
        print(f"Dry run done. Output in {out_dir}")


if __name__ == "__main__":
    main()
