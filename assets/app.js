const CHECKLIST = [
  "Run or go to the gym",
  "Read “The Daily Stoic”",
  "Make your bed",
  "Eat well",
  "Learn something new",
  "Read from a book",
  "Do your word of the day",
  "Clean up your workspace and room, if necessary",
  "Watch a finance YouTube video",
];

const $ = (id) => document.getElementById(id);

// Only let https links through; the text comes from a generated file.
function safeUrl(url) {
  return /^https:\/\//.test(url || "") ? url : "#";
}

function setLink(id, url, label) {
  const a = $(id);
  a.href = safeUrl(url);
  a.textContent = label;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function longDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric", year: "numeric",
  });
}

function renderChecklist(date) {
  const key = "daily-update-checks-" + date;
  let done = [];
  try { done = JSON.parse(localStorage.getItem(key) || "[]"); } catch (e) {}

  const list = $("checklist");
  const update = () => {
    const n = list.querySelectorAll("input:checked").length;
    $("progress").textContent = n === CHECKLIST.length
      ? "All done. That is how a journey gets finished."
      : n + " of " + CHECKLIST.length + " done";
  };

  CHECKLIST.forEach((text, i) => {
    const label = el("label");
    const box = el("input");
    box.type = "checkbox";
    box.checked = done.includes(i);
    box.addEventListener("change", () => {
      const checked = [...list.querySelectorAll("input")]
        .map((b, j) => (b.checked ? j : -1)).filter((j) => j >= 0);
      try { localStorage.setItem(key, JSON.stringify(checked)); } catch (e) {}
      update();
    });
    label.append(box, el("span", "", text));
    const li = el("li");
    li.append(label);
    list.append(li);
  });
  update();
}

function renderStocks(stocks) {
  const names = [["large_cap", "Large cap"], ["mid_cap", "Mid cap"], ["small_cap", "Small cap"]];
  for (const [key, label] of names) {
    const s = stocks[key];
    if (!s) continue;
    const card = el("article", "stock");
    card.append(el("p", "tag", label + " · " + s.market_cap));
    card.append(el("h4", "", s.company + " (" + s.ticker + ")"));
    card.append(el("p", "", s.what_they_do));
    const why = el("p");
    why.append(el("strong", "", "Why it is notable today: "), document.createTextNode(s.why_notable));
    card.append(why);
    if (s.more) card.append(el("p", "muted", s.more));
    $("stocks").append(card);
  }
}

async function main() {
  let data;
  try {
    const res = await fetch("data/today.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(res.status);
    data = await res.json();
  } catch (e) {
    $("status").textContent = "Today's update has not been written yet. Check back after 7:00 AM.";
    return;
  }

  $("nav-date").textContent = longDate(data.date);
  $("quote-text").textContent = "“" + data.quote.text + "”";
  $("quote-author").textContent = "— " + data.quote.author + (data.quote.from ? ", " + data.quote.from : "");

  const dk = data.daily_knowledge;
  $("dk-title").textContent = dk.title;
  $("dk-text").textContent = dk.text;
  setLink("dk-video", dk.video_url, "▶ Watch: " + dk.video_title);

  renderChecklist(data.date);

  $("mk-us").textContent = data.markets.us;
  $("mk-global").textContent = data.markets.global;
  renderStocks(data.stocks);

  const bs = data.big_story;
  $("bs-headline").textContent = bs.headline;
  $("bs-text").textContent = bs.summary;
  setLink("bs-link", bs.url, "Read more at " + bs.source);

  $("updated").textContent = "Written " + data.updated + ". Market and stock details come from web sources and are not investment advice.";
  $("status").hidden = true;
  $("content").hidden = false;
}

main();
