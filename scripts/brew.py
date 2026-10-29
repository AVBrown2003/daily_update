"""Write data/today.json: the content of today's Daily Update.

One Claude API call with the web_search tool researches the daily knowledge,
the market pulse, the three stocks of the day and the biggest news story. The
YouTube link is checked against YouTube's oEmbed endpoint so a made-up video
never reaches the page. Needs ANTHROPIC_API_KEY in the environment.

Usage: python scripts/brew.py
"""

import datetime as dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic

MODEL = os.environ.get("MODEL", "claude-opus-5-5")
TZ = ZoneInfo("America/Chicago")
OUT = Path(__file__).resolve().parent.parent / "data" / "today.json"

SCHEMA = """{
  "date": "YYYY-MM-DD",
  "quote": {"text": "...", "author": "...", "from": "person's field or the book/film/show it comes from"},
  "daily_knowledge": {
    "title": "short title of the person, fact or event",
    "text": "3-4 sentences",
    "video_title": "exact title of the YouTube video",
    "video_url": "https://www.youtube.com/watch?v=..."
  },
  "markets": {
    "us": "3-4 sentences on today's U.S. market pulse: S&P 500, Dow, Nasdaq moves and what drove them",
    "global": "3-4 sentences on Europe, Asia and other major markets"
  },
  "stocks": {
    "small_cap": {"ticker": "...", "company": "...", "market_cap": "$0.0B",
                  "what_they_do": "1-2 sentences", "why_notable": "2-3 sentences on why it is notable today",
                  "more": "any other relevant information"},
    "mid_cap": {"same keys as small_cap": ""},
    "large_cap": {"same keys as small_cap": ""}
  },
  "big_story": {"headline": "...", "summary": "3-4 sentences", "source": "publication", "url": "https://..."}
}"""

SYSTEM = """You write the content of "Daily Update", a personal morning page for \
someone on a self-improvement journey who wants to be better informed.

Hard rules:
- Use web_search for everything time-sensitive (markets, stocks, news). Never \
invent a price, percentage, source, URL or date.
- The quote must be real and correctly attributed, from a historical figure or \
a well-known work of fiction.
- video_url must be a real YouTube watch link you found with web_search.
- Describe market moves only as far as your sources support.
- Your whole response is one JSON object, no prose, no code fences."""


def prompt(now: dt.datetime, recent: list[str]) -> str:
    return f"""Today is {now:%A, %B} {now.day}, {now.year} (U.S. Central). It is early morning, \
so "today" and "yesterday's close" are what the markets have to report.

Build today's edition.

QUOTE: an inspirational quote from a historical figure or a popular fictional work. \
Not one of these recent ones: {'; '.join(recent) or 'none'}.

DAILY KNOWLEDGE: one interesting person, fact or historical event worth learning about today \
(an anniversary of today's date is a good choice but not required). Not one of these recent \
titles: {'; '.join(recent) or 'none'}. Include a good YouTube video on it.

MARKETS: the general U.S. market pulse and the global market pulse.

STOCKS OF THE DAY: exactly one small-cap (under $2B), one mid-cap ($2B-$10B) and one large-cap \
(over $10B) U.S.-listed stock that is notable today (earnings, news, big move). Say what the company does \
and why it is notable today.

BIG STORY: the single biggest news story in the world today, with a link to a direct article.

Return ONLY this JSON:
{SCHEMA}"""


def extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in the response")
    return json.loads(text[start : end + 1])


def youtube_ok(url: str) -> bool:
    if not re.match(r"https://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}", url or ""):
        return False
    api = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe="")
    try:
        with urllib.request.urlopen(api, timeout=20) as r:
            return r.status == 200
    except urllib.error.URLError:
        return False


def generate(client: anthropic.Anthropic, now: dt.datetime, recent: list[str]) -> dict:
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 20}]
    messages = [{"role": "user", "content": prompt(now, recent)}]
    for _ in range(10):  # resume if the server pauses a long turn
        msg = client.messages.create(
            model=MODEL, max_tokens=16000, system=SYSTEM, tools=tools, messages=messages
        )
        if msg.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": msg.content})
    text = "".join(b.text for b in msg.content if b.type == "text")
    return extract_json(text)


def main() -> None:
    now = dt.datetime.now(TZ)
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    recent = [e for e in (old.get("history") or [])][-30:]

    client = anthropic.Anthropic()
    for attempt in range(3):
        data = generate(client, now, recent)
        if youtube_ok(data["daily_knowledge"]["video_url"]):
            break
        print(f"attempt {attempt + 1}: YouTube link failed the check, retrying")
    else:
        raise SystemExit("could not get a working YouTube link; keeping yesterday's page")

    data["date"] = now.date().isoformat()
    data["updated"] = now.strftime("%Y-%m-%d %H:%M %Z")
    data["history"] = (recent + [data["quote"]["text"][:60], data["daily_knowledge"]["title"]])[-60:]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
