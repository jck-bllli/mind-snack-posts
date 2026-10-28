# MindSnack daily Reels

Posts one trivia Reel a day to [@mindsnackhere](https://www.instagram.com/mindsnackhere/) via the official Instagram API.

- `videos/` – rendered Reels (public, so Instagram can fetch them)
- `queue.json` – posting order and captions
- `posted.json` – what has been posted (updated automatically)
- `.github/workflows/post.yml` – runs daily at 23:17 UTC; can also be run by hand (Actions tab → Post daily Reel → Run workflow → check / post)

The Instagram token lives only in the repo secret `IG_ACCESS_TOKEN`. Never commit it.
