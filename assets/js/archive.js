(function () {
  const cardsEl = document.querySelector("[data-cards]");
  if (!cardsEl) return;
  const chipsEl = document.querySelector("[data-chips]");
  const countEl = document.querySelector("[data-count]");
  const searchEl = document.querySelector("[data-search]");
  const sortEl = document.querySelector("[data-sort]");

  let items = [];
  let q = "", cat = "all", sort = "new";

  fetch("/assets/writeups.json")
    .then((r) => r.json())
    .then((data) => { items = data; buildChips(); render(); })
    .catch(() => { cardsEl.textContent = "Could not load the writeup index."; });

  function buildChips() {
    const counts = {};
    items.forEach((it) => { counts[it.category] = (counts[it.category] || 0) + 1; });
    const make = (key, label, n) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip" + (key === cat ? " on" : "");
      b.dataset.cat = key;
      b.append(document.createTextNode(label));
      const c = document.createElement("span");
      c.className = "chip-n";
      c.textContent = n;
      b.append(c);
      b.addEventListener("click", () => { cat = key; updateChips(); render(); });
      return b;
    };
    chipsEl.append(make("all", "All", items.length));
    Object.keys(counts).sort().forEach((k) => chipsEl.append(make(k, k, counts[k])));
  }

  function updateChips() {
    chipsEl.querySelectorAll(".chip").forEach((b) =>
      b.classList.toggle("on", b.dataset.cat === cat));
  }

  const norm = (s) => (s || "").toLowerCase();

  function render() {
    let list = items.slice();
    if (cat !== "all") list = list.filter((it) => it.category === cat);
    if (q) {
      const s = norm(q);
      list = list.filter((it) =>
        norm([it.title, it.category, it.difficulty, (it.tags || []).join(" "), it.summary].join(" ")).includes(s));
    }
    list.sort((a, b) => {
      if (sort === "az") return a.title.localeCompare(b.title);
      const cmp = String(b.date || "").localeCompare(String(a.date || ""));
      return sort === "old" ? -cmp : cmp;
    });

    cardsEl.textContent = "";
    if (!list.length) {
      const p = document.createElement("p");
      p.className = "archive-empty";
      p.textContent = "No writeups match.";
      cardsEl.append(p);
    } else {
      list.forEach((it) => cardsEl.append(card(it)));
    }
    if (countEl) countEl.textContent = list.length + (list.length === 1 ? " writeup" : " writeups");
  }

  function card(it) {
    const a = document.createElement("a");
    a.className = "wu-card";
    a.href = it.url;
    const tag = document.createElement("span");
    tag.className = "wu-tag";
    tag.textContent = it.category + (it.difficulty ? " // " + it.difficulty : "");
    const h = document.createElement("span");
    h.className = "wu-title";
    h.textContent = it.title;
    a.append(tag, h);
    if (it.summary) {
      const p = document.createElement("span");
      p.className = "wu-desc";
      p.textContent = it.summary;
      a.append(p);
    }
    if (it.date) {
      const d = document.createElement("span");
      d.className = "wu-date";
      d.textContent = it.date;
      a.append(d);
    }
    return a;
  }

  if (searchEl) searchEl.addEventListener("input", () => { q = searchEl.value; render(); });
  if (sortEl) sortEl.addEventListener("change", () => { sort = sortEl.value; render(); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && searchEl && document.activeElement !== searchEl) {
      e.preventDefault();
      searchEl.focus();
    }
  });
})();
