// Renders the template grid from window.TEMPLATES. No framework, no build step.
(function () {
  var grid = document.getElementById("template-grid");
  if (!grid || !window.TEMPLATES) return;

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

  function render(cat) {
    var list = cat === "all" ? window.TEMPLATES : window.TEMPLATES.filter(function (t) { return t.cat === cat; });
    grid.innerHTML = list.map(card).join("");
  }

  render("all");

  // Category filter buttons
  document.querySelectorAll(".filter-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".filter-btn").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      render(btn.getAttribute("data-filter"));
    });
  });
})();
