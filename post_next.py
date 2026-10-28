#!/usr/bin/env python3
"""Post the next unposted Reel from queue.json to Instagram (Instagram API with Instagram Login).

Runs in GitHub Actions. Needs the secret IG_ACCESS_TOKEN.
  python post_next.py --check   # verify token, account, quota and the next video's public link; posts nothing
  python post_next.py           # post the next video and record it in posted.json
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.instagram.com/v26.0"
TOKEN = os.environ["IG_ACCESS_TOKEN"].strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "jck-bllli/mind-snack-posts")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")


def call(method, url, params=None):
    params = dict(params or {})
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params)
    req = (urllib.request.Request(f"{url}?{data}") if method == "GET"
           else urllib.request.Request(url, data=data.encode(), method="POST"))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace").replace(TOKEN, "[token]")
        sys.exit(f"Instagram API error {e.code}: {body}")


def summary(text):
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as f:
            f.write(text + "\n")


def next_item():
    queue = json.load(open("queue.json"))
    posted = {p["id"] for p in json.load(open("posted.json"))}
    return next((q for q in queue if q["id"] not in posted), None)


def public_url(item):
    # ?v=<commit> sidesteps GitHub's ~5 min cache of the raw file (e.g. right after a push)
    ver = os.environ.get("GITHUB_SHA", str(int(time.time())))[:12]
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{item['video']}?v={ver}"


def check_url(url):
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, int(r.headers.get("Content-Length", 0))


def keep_token_fresh():
    """Extend the 60-day token. Meta usually returns the same token with a new expiry."""
    q = urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": TOKEN})
    try:
        with urllib.request.urlopen(f"https://graph.instagram.com/refresh_access_token?{q}", timeout=30) as r:
            out = json.loads(r.read())
        days = out.get("expires_in", 0) // 86400
        if out.get("access_token") and out["access_token"] != TOKEN:
            # hand the new token to the next workflow step (which saves it as the secret); never print it
            path = os.environ.get("NEW_TOKEN_FILE")
            if path:
                with open(path, "w") as f:
                    f.write(out["access_token"])
            summary(f"Meta issued a new token (valid {days} days); saving it to the secret.")
        else:
            summary(f"Token refreshed, valid for about {days} more days.")
    except Exception as e:  # refresh is only allowed on tokens older than 24h; not fatal
        summary(f"Token refresh skipped: {e}")


def main():
    me = call("GET", f"{API}/me", {"fields": "user_id,username,account_type"})
    ig_id = me["user_id"]
    summary(f"Account: @{me.get('username')} ({me.get('account_type')})")
    quota = call("GET", f"{API}/{ig_id}/content_publishing_limit", {"fields": "quota_usage,config"})
    summary(f"Publishing quota: {quota.get('data', [{}])[0]}")

    if "--once-per-day" in sys.argv:  # scheduled runs: skip if something already went out in the last 20 hours
        done = [p for p in json.load(open("posted.json")) if p.get("posted_at")]
        if done:
            last = time.mktime(time.strptime(done[-1]["posted_at"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
            if time.time() - last < 20 * 3600:
                summary(f"Already posted {done[-1]['id']} at {done[-1]['posted_at']}; skipping this scheduled run.")
                return
    item = next_item()
    if not item:
        summary("Queue is empty. Add videos to queue.json.")
        return
    url = public_url(item)
    status, size = check_url(url)
    summary(f"Next up: {item['id']}  ({size / 1e6:.1f} MB, link status {status})")

    if "--check" in sys.argv:
        keep_token_fresh()
        summary("Check only, nothing posted.")
        return

    container = call("POST", f"{API}/{ig_id}/media", {
        "media_type": "REELS",
        "video_url": url,
        "caption": item["caption"],
        "share_to_feed": "true",
        "thumb_offset": str(item.get("thumb_offset_ms", 1000)),
    })["id"]
    for _ in range(60):  # up to ~10 minutes
        st = call("GET", f"{API}/{container}", {"fields": "status_code,status"})
        code = st.get("status_code")
        print("processing:", code)
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram could not process the video: {st}")
        time.sleep(10)
    else:
        sys.exit("Timed out waiting for Instagram to process the video")

    media = call("POST", f"{API}/{ig_id}/media_publish", {"creation_id": container})["id"]
    link = call("GET", f"{API}/{media}", {"fields": "permalink"}).get("permalink", "")
    posted = json.load(open("posted.json"))
    posted.append({"id": item["id"], "media_id": media, "permalink": link,
                   "posted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    json.dump(posted, open("posted.json", "w"), indent=2)
    summary(f"✅ Posted {item['id']}: {link}")
    keep_token_fresh()


if __name__ == "__main__":
    main()
