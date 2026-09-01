(function () {
  const box = document.querySelector("[data-toc]");
  if (!box) return;

  const heads = Array.from(document.querySelectorAll("main h2"));
  if (heads.length < 2) { box.remove(); return; }

  const slug = (t) => t.toLowerCase().replace(/[^\w]+/g, "-").replace(/^-|-$/g, "");

  const links = heads.map((h) => {
    if (!h.id) h.id = slug(h.textContent);
    const a = document.createElement("a");
    a.href = "#" + h.id;
    a.textContent = h.textContent;
    return a;
  });

  const label = document.createElement("p");
  label.className = "toc-label";
  label.textContent = "On this page";
  box.append(label, ...links);

  const spy = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        links.forEach((l) => l.classList.toggle("active", l.hash === "#" + e.target.id));
      });
    },
    { rootMargin: "0px 0px -70% 0px" }
  );
  heads.forEach((h) => spy.observe(h));
})();
