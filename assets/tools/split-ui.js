/* Slide Vault — Split PPT tool UI. Requires /assets/tools/split.bundle.js (window.SlideSplit). */
(function () {
  "use strict";

  var file = null; // { file: File }
  var busy = false;

  var dropzone = document.getElementById("dropzone");
  var fileInput = document.getElementById("fileInput");
  var fileRow = document.getElementById("fileRow");
  var fileNameEl = document.getElementById("fileName");
  var fileSizeEl = document.getElementById("fileSize");
  var removeBtn = document.getElementById("removeFile");
  var splitBtn = document.getElementById("splitBtn");
  var modeSingle = document.getElementById("modeSingle");
  var modeChunk = document.getElementById("modeChunk");
  var chunkSize = document.getElementById("chunkSize");
  var chunkSizeWrap = document.getElementById("chunkSizeWrap");
  var statusEl = document.getElementById("status");
  var resultEl = document.getElementById("result");
  var downloadBtn = document.getElementById("downloadBtn");
  var resultMeta = document.getElementById("resultMeta");

  function fmtSize(bytes) {
    if (bytes > 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + " MB";
    return Math.max(1, Math.round(bytes / 1024)) + " KB";
  }

  function render() {
    var has = !!file;
    fileRow.style.display = has ? "flex" : "none";
    if (has) {
      fileNameEl.textContent = file.name;
      fileNameEl.title = file.name;
      fileSizeEl.textContent = fmtSize(file.size);
    }
    var mode = modeChunk.checked ? "chunk" : "single";
    chunkSizeWrap.style.display = mode === "chunk" ? "flex" : "none";
    splitBtn.disabled = !has || busy;
    splitBtn.textContent = !has
      ? "Select a .pptx file"
      : busy
        ? "Working..."
        : "Split into " + (mode === "single" ? "single slides" : "parts of " + chunkSize.value + " slides");
  }

  function addFile(f) {
    if (!/\.pptx$/i.test(f.name)) {
      setStatus("Only .pptx files are supported (legacy .ppt is not).", true);
      return;
    }
    file = { file: f };
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

  function split() {
    if (busy || !file) return;
    if (!window.SlideSplit) {
      setStatus("Split engine is still loading, please wait a second and try again.", true);
      return;
    }
    var opts = modeChunk.checked
      ? { mode: "chunk", chunkSize: parseInt(chunkSize.value, 10) || 5 }
      : { mode: "single" };
    busy = true;
    splitBtn.disabled = true;
    resultEl.hidden = true;
    setStatus("Reading file...");

    file.file.arrayBuffer().then(function (buf) {
      return window.SlideSplit.split(
        { name: file.file.name, buffer: new Uint8Array(buf) },
        opts,
        setProgress
      );
    }).then(function (out) {
      var url = URL.createObjectURL(out.blob);
      downloadBtn.href = url;
      downloadBtn.download = file.file.name.replace(/\.pptx$/i, "") + "-split.zip";
      resultMeta.textContent = out.totalSlides + " slides \u2192 " + out.parts +
        " file" + (out.parts > 1 ? "s" : "") + " \u00B7 " + fmtSize(out.blob.size) +
        " \u00B7 nothing was uploaded \u2014 split on your device.";
      resultEl.hidden = false;
      setStatus("Done! Your ZIP is ready.");
      resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }).catch(function (err) {
      setStatus((err && err.message) ? err.message : "Split failed. Make sure the file is a valid .pptx presentation.", true);
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

  removeBtn.addEventListener("click", function () { file = null; render(); });
  modeSingle.addEventListener("change", render);
  modeChunk.addEventListener("change", render);
  chunkSize.addEventListener("change", render);
  splitBtn.addEventListener("click", split);
  render();
})();
