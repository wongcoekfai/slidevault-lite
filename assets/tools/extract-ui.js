/* Slide Vault — Extract Images tool UI. Requires /assets/tools/extract.bundle.js (window.SlideExtract). */
(function () {
  "use strict";

  var file = null;
  var busy = false;

  var dropzone = document.getElementById("dropzone");
  var fileInput = document.getElementById("fileInput");
  var fileRow = document.getElementById("fileRow");
  var fileNameEl = document.getElementById("fileName");
  var fileSizeEl = document.getElementById("fileSize");
  var removeBtn = document.getElementById("removeFile");
  var extractBtn = document.getElementById("extractBtn");
  var includeVector = document.getElementById("includeVector");
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
    extractBtn.disabled = !has || busy;
    extractBtn.textContent = !has ? "Select a .pptx file" : busy ? "Working..." : "Extract images";
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

  function extract() {
    if (busy || !file) return;
    if (!window.SlideExtract) {
      setStatus("The extraction engine is still loading, please wait a second and try again.", true);
      return;
    }
    busy = true;
    extractBtn.disabled = true;
    resultEl.hidden = true;
    setStatus("Reading file...");

    file.file.arrayBuffer().then(function (buf) {
      return window.SlideExtract.extract(
        { name: file.file.name, buffer: new Uint8Array(buf) },
        { includeVector: includeVector.checked },
        setProgress
      );
    }).then(function (out) {
      var url = URL.createObjectURL(out.blob);
      downloadBtn.href = url;
      downloadBtn.download = out.suggestedName;
      var exts = Object.keys(out.byExt).map(function (e) { return out.byExt[e] + " \u00D7 ." + e; }).join(", ");
      resultMeta.textContent = out.count + " image" + (out.count > 1 ? "s" : "") +
        " (" + exts + ") \u00B7 " + fmtSize(out.blob.size) +
        " \u00B7 nothing was uploaded \u2014 extracted on your device.";
      resultEl.hidden = false;
      setStatus("Done! Your ZIP is ready.");
      resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }).catch(function (err) {
      setStatus((err && err.message) ? err.message : "Extraction failed. Make sure the file is a valid .pptx presentation.", true);
    }).finally(function () {
      busy = false;
      render();
    });
  }

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
  includeVector.addEventListener("change", render);
  extractBtn.addEventListener("click", extract);
  render();
})();
