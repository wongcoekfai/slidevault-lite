// Renders the template grid from window.TEMPLATES. No framework, no build step.
(function () {
  var grid = document.getElementById("template-grid");
  if (!grid || !window.TEMPLATES) return;
  var html = window.TEMPLATES.map(function (t) {
    var thumb = t.img
      ? '<img class="thumb" src="' + t.img + '" alt="' + t.title + '" loading="lazy">'
      : '<div class="thumb thumb-fallback"></div>';
    return (
      '<article class="card">' + thumb +
        '<div class="body">' +
          '<span class="tag">' + (t.tag || "Template") + "</span>" +
          "<h3>" + t.title + "</h3>" +
          (t.desc ? "<p>" + t.desc + "</p>" : "") +
          '<div class="actions">' +
            '<a class="btn btn-primary" href="' + t.download + '" download>Download</a>' +
          "</div>" +
        "</div>" +
      "</article>"
    );
  }).join("");
  grid.innerHTML = html;
})();
