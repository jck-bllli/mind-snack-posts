#!/usr/bin/env python3
"""Otto, part 2: find other creators' outlier reels.

For each handle in otto/watchlist.txt (one per line, # for comments), pulls recent
media through Meta's Business Discovery API and scores each reel against that
creator's own median: outlier = (likes + comments) / creator median.
Writes otto/outliers.md and otto/outliers.json. Reads only, posts nothing.

Needs the secret FB_ACCESS_TOKEN: a Facebook Login token (Page or long-lived user)
with instagram_basic, pages_show_list, pages_read_engagement, business_management,
for a Facebook Page linked to our Instagram account. Only Business/Creator
accounts can be looked up.
"""
import json
import os
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v24.0"
TOKEN = "".join(os.environ.get("FB_ACCESS_TOKEN", "").split())  # drop any pasted spaces or line breaks
WATCHLIST = os.environ.get("OTTO_WATCHLIST", "otto/watchlist.txt")
MEDIA_FIELDS = "caption,like_count,comments_count,media_product_type,media_type,permalink,timestamp"


def get(path, params):
    params = dict(params, access_token=TOKEN)
    try:
        with urllib.request.urlopen(f"{API}/{path}?{urllib.parse.urlencode(params)}", timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode(errors="replace").replace(TOKEN, "[token]")[:400]}


def token_shape():
    """Safe diagnostics: never prints the token itself."""
    raw = os.environ.get("FB_ACCESS_TOKEN", "")
    bad = [n for n, c in (("space", " "), ("newline", "\n"), ("quote", '"'), ("apostrophe", "'")) if c in TOKEN or c in raw.strip()]
    return (f"token length {len(raw.strip())}, starts with EAA: {raw.strip().startswith('EAA')}, "
            f"non-ascii: {not raw.strip().isascii()}, stray characters inside: {bad or 'none'}")


def our_ig_id():
    if os.environ.get("IG_BUSINESS_ID"):
        return os.environ["IG_BUSINESS_ID"]
    res = get("me/accounts", {"fields": "name,instagram_business_account"})
    if "error" in res:  # a Page token: ask the Page itself
        res = get("me", {"fields": "instagram_business_account"})
        ig = res.get("instagram_business_account", {}).get("id")
    else:
        ig = next((p["instagram_business_account"]["id"] for p in res.get("data", [])
                   if p.get("instagram_business_account")), None)
    if not ig:
        print(f"::error::Token check: {token_shape()}")
        sys.exit(f"::error::No Instagram account linked to a Facebook Page for this token. {res.get('error', '')}")
    return ig


def handles():
    try:
        with open(WATCHLIST) as f:
            return [l.split("#")[0].strip().lstrip("@") for l in f if l.split("#")[0].strip()]
    except OSError:
        return []


def main():
    if not TOKEN:
        sys.exit("::error::FB_ACCESS_TOKEN is not set (see otto/competitors.py)")
    names = handles()
    if not names:
        sys.exit("::error::otto/watchlist.txt is empty")
    me = our_ig_id()
    reels, skipped = [], []
    for h in names:
        res = get(me, {"fields": f"business_discovery.username({h}){{followers_count,media.limit(40){{{MEDIA_FIELDS}}}}}"})
        bd = res.get("business_discovery")
        if not bd:
            skipped.append(f"@{h}: {res.get('error', 'not found')[:400]}")
            continue
        media = [m for m in bd.get("media", {}).get("data", []) if m.get("media_product_type") == "REELS"]
        if not media:
            skipped.append(f"@{h}: no reels")
            continue
        eng = [m.get("like_count", 0) + m.get("comments_count", 0) for m in media]
        med = statistics.median(eng) or 1
        for m, e in zip(media, eng):
            reels.append({"creator": h, "followers": bd.get("followers_count", 0), "engagement": e,
                          "outlier": round(e / med, 2), "permalink": m.get("permalink", ""),
                          "timestamp": m.get("timestamp", ""),
                          "caption": (m.get("caption") or "").split("\n")[0][:120]})
    reels.sort(key=lambda r: r["outlier"], reverse=True)

    os.makedirs("otto", exist_ok=True)
    with open("otto/outliers.json", "w") as f:
        json.dump({"reels": reels, "skipped": skipped}, f, indent=1)
    lines = ["# Otto: outlier reels from the watchlist", "",
             "Outlier = (likes + comments) / that creator's median reel. 3x+ is a proven idea.", "",
             "| Outlier | Creator | Engagement | Hook | Link |", "|---|---|---|---|---|"]
    for r in reels[:30]:
        hook = r["caption"].replace("|", "/")
        lines.append(f"| {r['outlier']}x | @{r['creator']} | {r['engagement']} | {hook} | {r['permalink']} |")
    if skipped:
        lines += ["", "Skipped (must be a public Business/Creator account):"] + [f"- {s}" for s in skipped]
    text = "\n".join(lines) + "\n"
    with open("otto/outliers.md", "w") as f:
        f.write(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
