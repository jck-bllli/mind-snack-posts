# MindSnack daily Reels

Posts one trivia Reel a day to [@mindsnackhere](https://www.instagram.com/mindsnackhere/) via the official Instagram API.

- `videos/` – rendered Reels (public, so Instagram can fetch them)
- `queue.json` – posting order and captions
- `posted.json` – what has been posted (updated automatically)
- `.github/workflows/post.yml` – runs daily at 23:17 UTC; can also be run by hand (Actions tab → Post daily Reel → Run workflow → check / post)

The Instagram token lives only in the repo secret `IG_ACCESS_TOKEN`. Never commit it.

## Making more videos

```
bash generator/setup.sh                      # once per machine (Python packages + voice model)
# add new quizzes to generator/questions.json (theme + 5 questions: q, 3 options, answer 0-2, fact, level)
python3 generator/produce.py --new           # voice + render + queue every quiz not yet queued
git add -A && git commit -m "Add quizzes" && git push
```
A weekly scheduled task does this automatically (7 new quizzes a week).

## Token renewal

Each run renews the Instagram token. When Meta returns a new token, the workflow saves it into the
`IG_ACCESS_TOKEN` secret automatically, using the `GH_PAT` secret: a fine-grained GitHub token limited to this
repo with **Secrets: Read and write** permission.
