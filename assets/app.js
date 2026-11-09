// Renders the template grid from window.TEMPLATES. No framework, no build step.
(function () {
  if (!window.TEMPLATES) return;

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function card(t) {
    var thumb = t.img
      ? '<img class="thumb" src="' + esc(t.img) + '" alt="' + esc(t.title) + ' preview" loading="lazy">'
      : '<div class="thumb thumb-fallback"></div>';
    return (
      '<article class="card" data-cat="' + esc(t.cat) + '">' + thumb +
        '<div class="body">' +
          '<span class="tag">' + esc(t.tag || "Template") + "</span>" +
          "<h3>" + esc(t.title) + "</h3>" +
          (t.desc ? "<p>" + esc(t.desc) + "</p>" : "") +
          '<div class="actions">' +
            '<a class="btn btn-primary" href="/download?file=' + encodeURIComponent(t.file) + '" rel="nofollow" download>Download</a>' +
            '<a class="btn btn-ghost" href="/templates/' + esc(t.slug) + '/">Details</a>' +
          "</div>" +
        "</div>" +
      "</article>"
    );
  }

  // Most-downloaded templates (real D1 download counts, updated Nov 2026).
  // Keep this list ordered by count; update when the numbers shift meaningfully.
  var POPULAR_SLUGS = [
    "saas-startup-pitch-deck-template",
    "light-startup-pitch-deck-template",
    "professional-corporate-presentation-template-2",
    "professional-business-presentation-template",
    "nova-medical-healthcare-template",
    "sales-proposal-template"
  ];

  function render(cat) {
    var grid = document.getElementById("template-grid");
    if (!grid) return;
    var list = cat === "all" ? window.TEMPLATES : window.TEMPLATES.filter(function (t) { return t.cat === cat; });
    grid.innerHTML = list.map(card).join("");
  }

  function renderPopular() {
    var pgrid = document.getElementById("popular-grid");
    if (!pgrid) return;
    var list = POPULAR_SLUGS.map(function (slug) {
      return window.TEMPLATES.filter(function (t) { return t.slug === slug; })[0];
    }).filter(Boolean);
    pgrid.innerHTML = list.map(card).join("");
  }

  render("all");
  renderPopular();

  // Category filter buttons
  document.querySelectorAll(".filter-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".filter-btn").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      render(btn.getAttribute("data-filter"));
    });
  });
})();
