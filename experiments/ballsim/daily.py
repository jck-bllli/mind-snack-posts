"""Automatic daily ball race: pick a fresh matchup, find a near tie, render it, queue it.

No Claude needed per video. Run on the home PC:
    python daily.py --count 1            # render the next video(s) into queue/
    python daily.py --survey             # headless: which pairs can make a near tie
State lives in state.json (pairs used, pairs that never tie). Each queued item
gets a "style" key (the pair) so Otto can rank matchups once the account posts.
"""
import argparse
import itertools
import json
import os
import random

import ballsim as bs

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue")
STATE = os.path.join(HERE, "state.json")
MAX_GAP = 0.35          # seconds; a finish further apart than this is not close enough
COOLDOWN = 10           # don't repeat a pair within this many videos
PALETTE = ["red", "blue", "green", "gold", "pink"]


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {"history": [], "bad": [], "n": 0}


def save(st):
    with open(STATE, "w") as f:
        json.dump(st, f, indent=1)


def pairs():
    ps = [f"{a}__{b}" for a, b in itertools.combinations(sorted(bs.RULES), 2)]
    random.Random(7).shuffle(ps)
    return ps


def spec_for(pair, n):
    a, b = pair.split("__")
    ra, rb = dict(bs.RULES[a]), dict(bs.RULES[b])
    rnd = random.Random(n)
    if rnd.random() < 0.5:                       # random top / bottom
        ra, rb = rb, ra
    if ra["color"] == rb["color"]:
        rb["color"] = rnd.choice([c for c in PALETTE if c != ra["color"]])
    return {"rules": (ra, rb)}


def next_pair(st):
    recent = [h["pair"] for h in st["history"][-COOLDOWN:]]
    for p in pairs():
        if p not in st["bad"] and p not in recent:
            yield p
    for p in pairs():                             # everything used recently: allow repeats
        if p not in st["bad"]:
            yield p


def caption(ra, rb):
    return (f"{ra['name'].title()} vs {rb['name'].title()}. Which one finishes first? "
            "Comment your pick before the end.\n\n#ballsimulation #satisfying #physics #math #simulation")


def make_one(st):
    for pair in next_pair(st):
        uses = sum(1 for h in st["history"] if h["pair"] == pair)
        spec, found = bs.tune_search(spec_for(pair, st["n"]), offset=uses * 3000)
        if not found or found["gap"] > MAX_GAP or not found["swap"]:
            if uses == 0:
                st["bad"].append(pair)
            print("skip", pair, found and round(found["gap"], 3))
            save(st)
            continue
        st["n"] += 1
        key = f"ball_{st['n']:04d}"
        out = bs.make_video(key, QUEUE, spec=spec, found=found)
        ra, rb = spec["rules"]
        item = {"file": os.path.basename(out), "caption": caption(ra, rb), "style": pair,
                "names": [ra["name"], rb["name"]], "gap": round(found["gap"], 3),
                "seconds": round(max(found["ta"], found["tb"]) + 3, 1)}
        with open(os.path.join(QUEUE, key + ".json"), "w") as f:
            json.dump(item, f, indent=1)
        st["history"].append({"pair": pair, "key": key, "gap": item["gap"]})
        save(st)
        return item
    raise SystemExit("::error::no pair produced a near tie")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--survey", action="store_true")
    a = ap.parse_args()
    if a.survey:
        for p in pairs():
            _, f = bs.tune_search(spec_for(p, 0))
            print(p, f and round(f["gap"], 3), f and f["swap"])
    else:
        st = load()
        for _ in range(a.count):
            print(json.dumps(make_one(st)))
