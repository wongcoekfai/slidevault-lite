/* Slide Vault — PPT Stats tool: read-only inspection of a .pptx file.
 * Logic exported for Node tests; UI wires up when a DOM is present.
 * Requires /assets/tools/pptx-lite.js (window.PPTXLite).
 */
(function () {
  "use strict";

  function toStr(u8) { return new TextDecoder().decode(u8); }

  function slideNo(name) {
    var m = name.match(/slide(\d+)\.xml$/);
    return m ? parseInt(m[1], 10) : 0;
  }

  /* Read-only analysis. Never rewrites the file. */
  async function collectStats(entries) {
    var slideNames = [];
    var notesWords = 0;
    var words = 0;
    var chars = 0;
    var tables = 0;
    var media = { images: 0, videos: 0, audio: 0, fonts: 0 };
    var mediaBytes = 0;
    var charts = 0;
    var embedded = 0;

    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      if (/^ppt\/slides\/slide\d+\.xml$/.test(e.name)) {
        slideNames.push(e.name);
        var xml = toStr(e.data);
        var texts = xml.match(/<a:t>[\s\S]*?<\/a:t>/g) || [];
        for (var t = 0; t < texts.length; t++) {
          var s = texts[t].replace(/<\/?a:t>/g, "");
          chars += s.length;
          words += (s.trim().match(/\S+/g) || []).length;
        }
        tables += (xml.match(/<a:tbl>/g) || []).length;
        continue;
      }
      if (/^ppt\/notesSlides\/notesSlide\d+\.xml$/.test(e.name)) {
        var nxml = toStr(e.data);
        var ntexts = nxml.match(/<a:t>[\s\S]*?<\/a:t>/g) || [];
        for (var n = 0; n < ntexts.length; n++) {
          var ns = ntexts[n].replace(/<\/?a:t>/g, "");
          notesWords += (ns.trim().match(/\S+/g) || []).length;
        }
        continue;
      }
      if (/^ppt\/media\//.test(e.name)) {
        mediaBytes += e.data.length;
        if (/\.(png|jpe?g|gif|webp|bmp|tiff?)$/i.test(e.name)) media.images++;
        else if (/\.(mp4|m4v|mov|avi|wmv|webm)$/i.test(e.name)) media.videos++;
        else if (/\.(mp3|wav|m4a|wma|aac)$/i.test(e.name)) media.audio++;
        else if (/\.(ttf|otf|fntdata|woff2?)$/i.test(e.name)) media.fonts++;
        continue;
      }
      if (/^ppt\/charts\/chart\d+\.xml$/.test(e.name)) charts++;
      if (/^ppt\/embeddings\//.test(e.name)) embedded++;
    }

    var counts = {};
    var maxSlide = 0;
    for (var s = 0; s < slideNames.length; s++) {
      var no = slideNo(slideNames[s]);
      counts[no] = true;
      if (no > maxSlide) maxSlide = no;
    }
    var realSlides = 0;
    for (var k in counts) realSlides++;
    // gaps mean hidden/deleted numbering; use max index as the canonical count
    var slideCount = maxSlide || slideNames.length;

    return {
      slides: slideCount,
      words: words,
      chars: chars,
      notesWords: notesWords,
      tables: tables,
      charts: charts,
      embedded: embedded,
      images: media.images,
      videos: media.videos,
      audio: media.audio,
      fonts: media.fonts,
      mediaBytes: mediaBytes
    };
  }

  var Logic = { collectStats: collectStats };
  if (typeof document === "undefined") {
    if (typeof module !== "undefined" && module.exports) module.exports = Logic;
    else globalThis.SlideStatsLogic = Logic;
    return;
  }

  /* ------------------------------ UI ------------------------------ */
  var busy = false;
  var zip = window.PPTXLite;

  var dropzone = document.getElementById("dropzone");
  var fileInput = document.getElementById("fileInput");
  var fileList = document.getElementById("fileList");
  var goBtn = document.getElementById("goBtn");
  var clearBtn = document.getElementById("clearBtn");
  var statusEl = document.getElementById("status");
  var resultEl = document.getElementById("result");
  var reportEl = document.getElementById("report");

  function fmtSize(b) {
    if (b > 1048576) return (b / 1048576).toFixed(1) + " MB";
    return Math.max(1, Math.round(b / 1024)) + " KB";
  }
  function setStatus(msg, isError) {
    statusEl.textContent = msg || "";
    statusEl.className = isError ? "tool-status tool-error" : "tool-status";
  }
  function render() {
    goBtn.disabled = !fileList.children.length || busy;
    goBtn.textContent = !fileList.children.length ? "Select at least one .pptx file"
      : busy ? "Analyzing..." : "Analyze " + fileList.children.length + " file" + (fileList.children.length > 1 ? "s" : "");
  }
  function addFiles(list) {
    for (var i = 0; i < list.length; i++) {
      if (/\.pptx$/i.test(list[i].name)) {
        var row = document.createElement("div");
        row.className = "file-row";
        row.dataset.name = list[i].name;
        var icon = document.createElement("span");
        icon.textContent = "\uD83D\uDCC4";
        var nm = document.createElement("span");
        nm.className = "file-name";
        nm.textContent = list[i].name;
        var sz = document.createElement("span");
        sz.className = "file-size";
        sz.textContent = fmtSize(list[i].size);
        var rm = document.createElement("button");
        rm.type = "button";
        rm.className = "mini-btn mini-danger";
        rm.setAttribute("aria-label", "Remove file");
        rm.textContent = "\u2715";
        rm.onclick = function () { this.closest(".file-row").remove(); render(); };
        row.appendChild(icon); row.appendChild(nm); row.appendChild(sz); row.appendChild(rm);
        fileList.appendChild(row);
        row._file = list[i];
      } else {
        setStatus("Skipped " + list[i].name + " — only .pptx files are supported.", true);
      }
    }
    render();
  }

  function reportTable(name, st) {
    var rows = [
      ["Slides", st.slides],
      ["Words on slides", st.words.toLocaleString()],
      ["Characters", st.chars.toLocaleString()],
      ["Words in speaker notes", st.notesWords.toLocaleString()],
      ["Images", st.images],
      ["Charts", st.charts],
      ["Tables", st.tables],
      ["Videos / audio", st.videos + " / " + st.audio],
      ["Embedded objects", st.embedded],
      ["Embedded fonts", st.fonts],
      ["Media weight", fmtSize(st.mediaBytes)]
    ];
    var wrap = document.createElement("div");
    wrap.className = "stat-card";
    var h = document.createElement("h3");
    h.textContent = name;
    wrap.appendChild(h);
    var ul = document.createElement("ul");
    ul.className = "facts";
    rows.forEach(function (r) {
      var li = document.createElement("li");
      var b = document.createElement("b");
      b.textContent = r[0];
      var sp = document.createElement("span");
      sp.textContent = String(r[1]);
      li.appendChild(b); li.appendChild(sp);
      ul.appendChild(li);
    });
    wrap.appendChild(ul);
    return wrap;
  }

  async function run() {
    var rows = fileList.children;
    if (!rows.length || busy) return;
    busy = true;
    resultEl.hidden = true;
    reportEl.innerHTML = "";
    render();
    try {
      for (var i = 0; i < rows.length; i++) {
        var f = rows[i]._file;
        setStatus("Analyzing " + f.name + " (" + (i + 1) + "/" + rows.length + ")...");
        var entries = await zip.readZIP(await f.arrayBuffer());
        var st = await collectStats(entries);
        reportEl.appendChild(reportTable(f.name, st));
      }
      resultEl.hidden = false;
      setStatus("");
    } catch (err) {
      setStatus(err && err.message ? err.message : "Something went wrong reading this file.", true);
    }
    busy = false;
    render();
  }

  dropzone.addEventListener("click", function () { fileInput.click(); });
  dropzone.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); fileInput.click(); }
  });
  dropzone.addEventListener("dragover", function (ev) { ev.preventDefault(); dropzone.classList.add("dragging"); });
  dropzone.addEventListener("dragleave", function () { dropzone.classList.remove("dragging"); });
  dropzone.addEventListener("drop", function (ev) {
    ev.preventDefault();
    dropzone.classList.remove("dragging");
    if (ev.dataTransfer && ev.dataTransfer.files) addFiles(ev.dataTransfer.files);
  });
  fileInput.addEventListener("change", function () {
    if (fileInput.files) addFiles(fileInput.files);
    fileInput.value = "";
  });
  goBtn.addEventListener("click", run);
  clearBtn.addEventListener("click", function () { fileList.innerHTML = ""; resultEl.hidden = true; setStatus(""); render(); });
  render();
})();
