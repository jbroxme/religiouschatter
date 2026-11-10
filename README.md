# Ink and Chatter

A generative artwork. Figures shared by the Torah, the Bible, the Quran and the Book of Mormon sit in a field between those texts, placed by how often each text names them. Five shared ideas also reach Hinduism, Buddhism, Scientology and Effective Altruism. Each text turns through its own religious calendar, pulling figures closer when their stories are read or remembered. Live Bluesky posts that name a figure fall onto it like rain.

It's a single static page. There's no build step and no server.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The whole site: page, styles and script. |
| `leaders.json` | Official accounts to treat as religious leaders (empty to start). |
| `scripts/count_names.py` | Rebuilds the verse counts from the source texts. |
| `data/counts.json` | Output of the script. The same numbers are in the `REAL` table in `index.html`. |

## Run it locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000. Opening `index.html` straight from disk also works, but `leaders.json` only loads over http.

## Deploy

Any static host works. With GitHub Pages: push this folder to a repository, then go to Settings > Pages and choose "Deploy from a branch" with the `main` branch and `/ (root)` folder. Netlify and Vercel work the same way: point them at the repository, with no build command and the root folder as the output.

## The live feed

The page connects from the visitor's browser to Bluesky's public Jetstream service (`wss://jetstream2.us-east.bsky.network`, with three fallbacks) and reads every new post. It keeps posts that name a figure, an idea or a text, in English, Hebrew, Arabic and a few European languages. Common names such as David, Mary, Jacob or Joseph only count when a religious word appears in the same post. The name lists live in the `FORMS`, `TEXTREF` and `CTX` tables in `index.html`.

- No API key or account is needed. Jetstream and the public profile API (`public.api.bsky.app`) are open.
- Posts carrying adult or abusive labels, or matching a short word blocklist (`NOPE`), are skipped. No filter is perfect, so the Design board has "Show the text of live posts" to show only the drops.
- Each post links back to bsky.app. Handles of ordinary posters are not shown.
- If the browser can't connect within about 12 seconds, the page switches to simulated posts and says so.

### Religious leaders

A live post counts as a leader's in two cases:

1. The account's Bluesky profile describes them as clergy (rabbi, pastor, priest, bishop, imam, sheikh, swami, Buddhist monk, lama and so on). These are self-described and unverified. The patterns are in `CLERGY` in `index.html`.
2. The account is listed in `leaders.json`. Use this for official accounts you have checked yourself:

```json
[
  { "handle": "example.bsky.social", "role": "Diocese of Example", "tradition": "bible" }
]
```

`tradition` is one of `torah`, `bible`, `quran`, `mormon`, `scientology`, `ea`, `hinduism` or `buddhism`. Every post from a listed account appears, falling toward that tradition.

The Pope's main account (@Pontifex) is on X, which has no free public stream, so it can't be read here.

## Rebuilding the counts

```bash
python3 scripts/count_names.py
```

The script downloads its sources into `data/sources/` (about 50 MB, git-ignored) and writes `data/counts.json`. If you change the rules, copy the new numbers into the `REAL` table in `index.html`.

- **Bible:** Theographic Bible Metadata (KJV), which links each verse to the distinct people it names. Jacob is counted by name, because Theographic merges him with the nation of Israel. Satan includes "the devil".
- **Quran:** Quranic Arabic Corpus morphology (word-by-word lemmas). Satan is Iblis plus the singular al-Shaytan. Jesus includes al-Masih.
- **Book of Mormon:** scriptures-json, with wording rules that skip its own Jacob, Joseph, Aaron and Noah.

Counts are verses that name the figure, shown as a rate per 1,000 verses.
