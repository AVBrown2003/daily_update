# Daily Update

A personal one-page morning update, live at https://avbrown2003.github.io/daily_update/

Every day at 7:00 AM Central a GitHub Actions workflow asks Claude (with web search) to write the day's content, saves it as `data/today.json`, and commits it. GitHub Pages then serves the new page.

The page has, in order: an inspirational quote, a "daily knowledge" item with a YouTube video, a self-improvement checklist (ticks are saved in your browser for that day), a financial section (U.S. and global market pulse plus a small-, mid- and large-cap stock of the day), and the biggest news story of the day with a link.

## Where the content comes from

Claude's web search, run by `scripts/brew.py`. Quotes are attributed by the model. The YouTube link is checked against YouTube's oEmbed endpoint before it is saved. Market and stock details are not investment advice. There is no dataset; the checklist is fixed in `assets/app.js`.

## Files

| File | What it does |
|---|---|
| `index.html` | The page: its sections are empty and filled in by `app.js`. |
| `assets/style.css` | Fonts, colors and layout. |
| `assets/app.js` | Loads `data/today.json`, draws the page, and keeps the checklist ticks in the browser's local storage. |
| `data/today.json` | Today's content. Written by the workflow; does not exist until the first run. |
| `scripts/brew.py` | Calls the Claude API with web search, checks the YouTube link, and writes `data/today.json`. |
| `.github/workflows/daily.yml` | Runs `brew.py` at 7:00 AM Central (cron at 12:00 and 13:00 UTC, with a guard for daylight saving), then commits the result. Can also be run by hand from the Actions tab. |

## Setup

The workflow needs a repository secret named `ANTHROPIC_API_KEY` (Settings, Secrets and variables, Actions).
