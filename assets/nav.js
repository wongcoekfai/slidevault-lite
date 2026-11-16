/* Slide Vault — nav dropdowns (hover on desktop, tap on touch devices). */
(function () {
  "use strict";

  function all() { return document.querySelectorAll(".nav-drop"); }

  function setState(drop, open) {
    drop.classList.toggle("open", open);
    var btn = drop.querySelector(".nav-drop-btn");
    if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function closeOthers(except) {
    all().forEach(function (d) { if (d !== except) setState(d, false); });
  }

  /* Keep the panel inside the viewport on narrow screens. */
  function place(drop) {
    var menu = drop.querySelector(".nav-menu");
    if (!menu) return;
    menu.style.left = "";
    menu.style.transform = "";

    var wasHidden = menu.getBoundingClientRect().width === 0;
    if (wasHidden) { menu.style.display = "block"; menu.style.visibility = "hidden"; }

    var m = menu.getBoundingClientRect();
    var vw = document.documentElement.clientWidth;
    var pad = 12;
    var shift = 0;
    if (m.left < pad) shift = pad - m.left;
    else if (m.right > vw - pad) shift = (vw - pad) - m.right;

    if (shift) {
      menu.style.left = (menu.offsetLeft + shift) + "px";
      menu.style.transform = "none";
    }

    if (wasHidden) { menu.style.display = ""; menu.style.visibility = ""; }
  }

  document.addEventListener("click", function (e) {
    var drop = e.target.closest(".nav-drop");
    closeOthers(drop);
    if (!drop) return;

    if (e.target.closest(".nav-drop-btn")) {
      var open = !drop.classList.contains("open");
      setState(drop, open);
      if (open) place(drop);
      return;
    }
    if (e.target.closest(".nav-menu a")) setState(drop, false);
  });

  all().forEach(function (drop) {
    drop.addEventListener("mouseenter", function () { place(drop); });
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    all().forEach(function (d) {
      if (!d.classList.contains("open")) return;
      setState(d, false);
      var btn = d.querySelector(".nav-drop-btn");
      if (btn) btn.focus();
    });
  });

  window.addEventListener("resize", function () {
    all().forEach(function (d) { if (d.classList.contains("open")) place(d); });
  });
})();
