// Renders the template grid from window.TEMPLATES. No framework, no build step.
(function () {
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // "Complete a kit" cards. Data comes from assets/kits.js, which is generated
  // from tools/kits.py together with the Bundle ZIPs — no manual duplication.
  function renderKits() {
    var box = document.getElementById("kit-grid");
    if (!box || !window.KITS) return;
    box.innerHTML = window.KITS.map(function (k) {
      var decks = k.decks.map(function (d, i) {
        return '<li><span class="kit-grid-num">' + (i + 1) + '</span>' +
          '<a href="' + esc(d.url) + '">' + esc(d.title) + '</a></li>';
      }).join("");
      return '<article class="kit-card">' +
        '<p class="kit-eyebrow">' + esc(k.eyebrow) + '</p>' +
        '<h3>' + esc(k.name) + '</h3>' +
        '<p class="kit-card-desc">' + esc(k.desc) + '</p>' +
        '<ol class="kit-card-decks">' + decks + '</ol>' +
        '<a class="btn btn-primary" href="/?kit=' + encodeURIComponent(k.id) +
          '#subscribe">Get all ' + k.decks.length + ' decks in one ZIP</a>' +
        '</article>';
    }).join("");
  }
  renderKits();

  // Kit cards link to /?kit=<id>#subscribe; preselect that kit in the form.
  try {
    var picked = new URLSearchParams(window.location.search).get("kit");
    if (picked && window.KITS) {
      var ok = window.KITS.some(function (k) { return k.id === picked; });
      var sel = document.getElementById("kit-select");
      if (ok && sel) {
        sel.value = picked;
        sel.dataset.picked = picked; // also visible in the DOM for styling / QA
      }
    }
  } catch (e) { /* older browser: the static select still works */ }

  if (!window.TEMPLATES) return;

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
