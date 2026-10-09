(function () {
  const box = document.querySelector("[data-toc]");
  if (!box) return;

  const sections = Array.from(document.querySelectorAll("main h2, main details.section-fold > summary"));
  if (sections.length < 2) { box.remove(); return; }

  const slug = (t) => t.toLowerCase().replace(/[^\w]+/g, "-").replace(/^-|-$/g, "");

  const links = sections.map((section) => {
    if (!section.id) section.id = slug(section.textContent);
    const a = document.createElement("a");
    a.href = "#" + section.id;
    a.textContent = section.textContent;
    if (section.tagName === "SUMMARY") {
      a.addEventListener("click", () => { section.parentElement.open = true; });
    }
    return a;
  });

  const label = document.createElement("p");
  label.className = "toc-label";
  label.textContent = "On this page";
  box.append(label, ...links);

  const openLinkedFold = () => {
    const section = sections.find((item) => "#" + item.id === window.location.hash);
    if (section?.tagName === "SUMMARY") section.parentElement.open = true;
  };
  openLinkedFold();
  window.addEventListener("hashchange", openLinkedFold);

  const spy = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        links.forEach((l) => l.classList.toggle("active", l.hash === "#" + e.target.id));
      });
    },
    { rootMargin: "0px 0px -70% 0px" }
  );
  sections.forEach((section) => spy.observe(section));
})();
