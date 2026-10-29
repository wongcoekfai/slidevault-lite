/* Slide Vault — Merge PPT tool UI. Requires /assets/tools/merge.bundle.js (window.SlideMerge). */
(function () {
  "use strict";

  var files = []; // { file: File, id: number }
  var nextId = 1;
  var busy = false;

  var dropzone = document.getElementById("dropzone");
  var fileInput = document.getElementById("fileInput");
  var listEl = document.getElementById("fileList");
  var mergeBtn = document.getElementById("mergeBtn");
  var statusEl = document.getElementById("status");
  var resultEl = document.getElementById("result");
  var downloadBtn = document.getElementById("downloadBtn");
  var resultMeta = document.getElementById("resultMeta");

  function fmtSize(bytes) {
    if (bytes > 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + " MB";
    return Math.max(1, Math.round(bytes / 1024)) + " KB";
  }

  function render() {
    listEl.innerHTML = "";
    files.forEach(function (item, idx) {
      var li = document.createElement("li");
      li.className = "file-row";
      li.innerHTML =
        '<span class="file-order">' + (idx + 1) + "</span>" +
        '<span class="file-name" title="' + item.file.name.replace(/"/g, "&quot;") + '">' +
          item.file.name.replace(/&/g, "&amp;").replace(/</g, "&lt;") +
        "</span>" +
        '<span class="file-size">' + fmtSize(item.file.size) + "</span>" +
        '<span class="file-actions">' +
          '<button type="button" class="mini-btn" data-act="up" aria-label="Move up"' + (idx === 0 ? " disabled" : "") + ">&#8593;</button>" +
          '<button type="button" class="mini-btn" data-act="down" aria-label="Move down"' + (idx === files.length - 1 ? " disabled" : "") + ">&#8595;</button>" +
          '<button type="button" class="mini-btn mini-danger" data-act="remove" aria-label="Remove">&#10005;</button>' +
        "</span>";
      li.querySelector('[data-act="up"]').addEventListener("click", function () { move(idx, -1); });
      li.querySelector('[data-act="down"]').addEventListener("click", function () { move(idx, 1); });
      li.querySelector('[data-act="remove"]').addEventListener("click", function () { remove(item.id); });
      listEl.appendChild(li);
    });
    mergeBtn.disabled = files.length < 2 || busy;
    mergeBtn.textContent = files.length < 2
      ? "Select at least 2 files"
      : "Merge " + files.length + " files";
  }

  function addFiles(fileList) {
    var added = 0;
    Array.prototype.forEach.call(fileList, function (f) {
      if (!/\.pptx$/i.test(f.name)) return; // silently skip non-pptx
      files.push({ file: f, id: nextId++ });
      added++;
    });
    if (added === 0) setStatus("Only .pptx files are supported (legacy .ppt is not).", true);
    else setStatus("");
    render();
  }

  function move(idx, dir) {
    var j = idx + dir;
    if (j < 0 || j >= files.length) return;
    var t = files[idx]; files[idx] = files[j]; files[j] = t;
    render();
  }

  function remove(id) {
    files = files.filter(function (item) { return item.id !== id; });
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

  function merge() {
    if (busy || files.length < 2) return;
    if (!window.SlideMerge) {
      setStatus("Merge engine is still loading, please wait a second and try again.", true);
      return;
    }
    busy = true;
    mergeBtn.disabled = true;
    resultEl.hidden = true;
    setStatus("Reading files...");

    Promise.all(files.map(function (item) {
      return item.file.arrayBuffer().then(function (buf) {
        return { name: item.file.name, buffer: new Uint8Array(buf) };
      });
    })).then(function (payload) {
      return window.SlideMerge.merge(payload, setProgress);
    }).then(function (out) {
      var url = URL.createObjectURL(out.blob);
      downloadBtn.href = url;
      downloadBtn.download = "merged-presentation.pptx";
      resultMeta.textContent = out.totalSlides + " slides combined from " +
        files.length + " files · " + fmtSize(out.blob.size) + " · nothing was uploaded — merged on your device.";
      resultEl.hidden = false;
      setStatus("Done! Your merged file is ready.");
      resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }).catch(function (err) {
      setStatus((err && err.message) ? err.message : "Merge failed. Make sure the files are valid .pptx presentations.", true);
    }).finally(function () {
      busy = false;
      render();
    });
  }

  // Dropzone events
  dropzone.addEventListener("click", function () { fileInput.click(); });
  fileInput.addEventListener("change", function () { addFiles(fileInput.files); fileInput.value = ""; });
  ["dragenter", "dragover"].forEach(function (ev) {
    dropzone.addEventListener(ev, function (e) { e.preventDefault(); dropzone.classList.add("dragging"); });
  });
  ["dragleave", "drop"].forEach(function (ev) {
    dropzone.addEventListener(ev, function (e) { e.preventDefault(); dropzone.classList.remove("dragging"); });
  });
  dropzone.addEventListener("drop", function (e) {
    if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files);
  });

  mergeBtn.addEventListener("click", merge);
  render();
})();
