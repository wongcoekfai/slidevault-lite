/* Multi-page preview gallery on template detail pages. Zero dependencies.
   Images come from the .gallery-thumb elements rendered into the page. */
(function () {
  var stage   = document.querySelector(".gallery-stage");
  var thumbs  = [].slice.call(document.querySelectorAll(".gallery-thumb"));
  var main    = document.querySelector(".gallery-main");
  if (!stage || !main || !thumbs.length) return;

  var sources = thumbs.map(function (b) { return b.getAttribute("data-src"); });
  var counter = document.getElementById("gallery-counter");
  var prevBtn = document.querySelector(".gallery-nav.prev");
  var nextBtn = document.querySelector(".gallery-nav.next");
  var box     = document.getElementById("lightbox");
  var boxImg  = box ? box.querySelector("img") : null;
  var index   = 0;
  var single  = sources.length < 2;

  function show(i) {
    index = (i + sources.length) % sources.length;
    main.src = sources[index];
    main.setAttribute("alt", "Slide " + (index + 1) + " of " + sources.length);
    thumbs.forEach(function (b, n) { b.classList.toggle("active", n === index); });
    if (counter) counter.textContent = (index + 1) + " / " + sources.length;
    // keep the active thumbnail in view inside the scroll strip
    if (thumbs[index].scrollIntoView) {
      thumbs[index].scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
    }
    if (box && !box.hidden) boxImg.src = sources[index];
  }

  thumbs.forEach(function (b, n) {
    b.addEventListener("click", function () { show(n); });
  });

  if (single) {
    // One image only: no stepping controls, no thumbnail strip UI clutter.
    [prevBtn, nextBtn].forEach(function (b) { if (b) b.style.display = "none"; });
    if (counter) counter.style.display = "none";
    document.getElementById("gallery-thumbs").style.display = "none";
  } else {
    if (prevBtn) prevBtn.addEventListener("click", function () { show(index - 1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { show(index + 1); });
    show(0);
  }

  // ---- keyboard ----
  document.addEventListener("keydown", function (e) {
    if (box && !box.hidden) {
      if (e.key === "Escape") { closeBox(); }
      else if (e.key === "ArrowLeft") { show(index - 1); }
      else if (e.key === "ArrowRight") { show(index + 1); }
      return;
    }
    if (single || e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    if (e.key === "ArrowLeft") show(index - 1);
    if (e.key === "ArrowRight") show(index + 1);
  });

  // ---- touch swipe on the stage ----
  var x0 = null;
  stage.addEventListener("touchstart", function (e) { x0 = e.changedTouches[0].clientX; }, { passive: true });
  stage.addEventListener("touchend", function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 40) show(index + (dx < 0 ? 1 : -1));
    x0 = null;
  }, { passive: true });

  // ---- lightbox ----
  function openBox() {
    if (!box) return;
    box.hidden = false;
    document.body.style.overflow = "hidden";
    boxImg.src = sources[index];
  }
  function closeBox() {
    if (!box) return;
    box.hidden = true;
    document.body.style.overflow = "";
  }
  if (box) {
    main.style.cursor = "zoom-in";
    main.addEventListener("click", openBox);
    box.addEventListener("click", function (e) {
      if (e.target === box || e.target.classList.contains("lightbox-close")) closeBox();
    });
    [].forEach.call(box.querySelectorAll(".lightbox-nav"), function (b) {
      if (single) { b.style.display = "none"; return; }
      b.addEventListener("click", function (e) {
        e.stopPropagation();
        show(index + (b.classList.contains("next") ? 1 : -1));
      });
    });
  }
})();
