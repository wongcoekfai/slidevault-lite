/* Slide Vault — PPT Tools dropdown toggle (touch devices). */
(function () {
  "use strict";
  document.addEventListener("click", function (e) {
    var drop = e.target.closest(".nav-drop");
    document.querySelectorAll(".nav-drop.open").forEach(function (d) {
      if (d !== drop) d.classList.remove("open");
    });
    if (drop && e.target.closest(".nav-drop-btn")) drop.classList.toggle("open");
    if (drop && e.target.closest(".nav-menu a")) drop.classList.remove("open");
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      document.querySelectorAll(".nav-drop.open").forEach(function (d) { d.classList.remove("open"); });
    }
  });
})();
