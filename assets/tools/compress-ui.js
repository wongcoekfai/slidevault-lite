/* Slide Vault — Compress PPT tool UI. Requires /assets/tools/compress.bundle.js (window.SlideCompress). */
(function () {
  "use strict";

  var file = null; // selected File
  var busy = false;

  var dropzone = document.getElementById("dropzone");
  var fileInput = document.getElementById("fileInput");
  var listEl = document.getElementById("fileList");
  var compressBtn = document.getElementById("compressBtn");
  var statusEl = document.getElementById("status");
  var resultEl = document.getElementById("result");
  var downloadBtn = document.getElementById("downloadBtn");
  var resultMeta = document.getElementById("resultMeta");
  var levelRadios = document.querySelectorAll('input[name="level"]');

  function fmtSize(bytes) {
    if (bytes > 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + " MB";
    return Math.max(1, Math.round(bytes / 1024)) + " KB";
  }

  function render() {
    listEl.innerHTML = "";
    if (file) {
      var li = document.createElement("li");
      li.className = "file-row";
      li.innerHTML =
        '<span class="file-order">&#128196;</span>' +
        '<span class="file-name" title="' + file.name.replace(/"/g, "&quot;") + '">' +
          file.name.replace(/&/g, "&amp;").replace(/</g, "&lt;") +
        "</span>" +
        '<span class="file-size">' + fmtSize(file.size) + "</span>" +
        '<span class="file-actions">' +
          '<button type="button" class="mini-btn mini-danger" data-act="remove" aria-label="Remove">&#10005;</button>' +
        "</span>";
      li.querySelector('[data-act="remove"]').addEventListener("click", function () {
        file = null;
        render();
      });
      listEl.appendChild(li);
    }
    compressBtn.disabled = !file || busy;
    compressBtn.textContent = file ? "Compress file" : "Select a .pptx file";
  }

  function addFile(f) {
    if (!/\.pptx$/i.test(f.name)) {
      setStatus("Only .pptx files are supported (legacy .ppt is not).", true);
      return;
    }
    file = f;
    setStatus("");
    render();
  }

  function setStatus(msg, isError) {
    statusEl.textContent = msg || "";
    statusEl.className = isError ? "tool-status tool-error" : "tool-status";
  }

  function setProgress(msg) {
    statusEl.textContent = msg;
    statusEl.className = "tool-status";
  }

  function compress() {
    if (busy || !file) return;
    if (!window.SlideCompress) {
      setStatus("Compression engine is still loading, please wait a second and try again.", true);
      return;
    }
    busy = true;
    compressBtn.disabled = true;
    resultEl.hidden = true;
    setStatus("Reading file...");

    var level = "basic";
    levelRadios.forEach(function (r) { if (r.checked) level = r.value; });
    var opts = level === "strong" ? { maxDim: 1280, jpegQuality: 70 } : { maxDim: 1920, jpegQuality: 82 };

    file.arrayBuffer().then(function (buf) {
      return window.SlideCompress.compress(new Uint8Array(buf), opts, setProgress);
    }).then(function (out) {
      var url = URL.createObjectURL(out.blob);
      downloadBtn.href = url;
      downloadBtn.download = file.name.replace(/\.pptx$/i, "") + "-compressed.pptx";
      var saved = out.originalSize - out.newSize;
      var pct = out.originalSize > 0 ? Math.round((saved / out.originalSize) * 100) : 0;
      var detail = out.imagesOptimized > 0
        ? out.imagesOptimized + " image" + (out.imagesOptimized > 1 ? "s" : "") + " optimized" +
          (out.pngsConverted > 0 ? " (" + out.pngsConverted + " PNG converted to JPEG)" : "")
        : "no images needed optimizing — gain is from repacking";
      resultMeta.textContent = fmtSize(out.originalSize) + " \u2192 " + fmtSize(out.newSize) +
        " \u00B7 saved " + fmtSize(saved) + " (" + pct + "%) \u00B7 " + detail +
        " \u00B7 nothing was uploaded — compressed on your device.";
      resultEl.hidden = false;
      setStatus("Done! Your compressed file is ready.");
      resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }).catch(function (err) {
      setStatus((err && err.message) ? err.message : "Compression failed. Make sure the file is a valid .pptx presentation.", true);
    }).finally(function () {
      busy = false;
      render();
    });
  }

  // Dropzone events
  dropzone.addEventListener("click", function () { fileInput.click(); });
  fileInput.addEventListener("change", function () {
    if (fileInput.files && fileInput.files[0]) addFile(fileInput.files[0]);
    fileInput.value = "";
  });
  ["dragenter", "dragover"].forEach(function (ev) {
    dropzone.addEventListener(ev, function (e) { e.preventDefault(); dropzone.classList.add("dragging"); });
  });
  ["dragleave", "drop"].forEach(function (ev) {
    dropzone.addEventListener(ev, function (e) { e.preventDefault(); dropzone.classList.remove("dragging"); });
  });
  dropzone.addEventListener("drop", function (e) {
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) addFile(e.dataTransfer.files[0]);
  });

  compressBtn.addEventListener("click", compress);
  render();
})();
