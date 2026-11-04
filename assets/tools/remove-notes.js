/* Slide Vault — Remove Speaker Notes tool.
 * Logic is exported for Node tests; UI wires up when a DOM is present.
 * Requires /assets/tools/pptx-lite.js (window.PPTXLite).
 */
(function () {
  "use strict";

  function toStr(u8) { return new TextDecoder().decode(u8); }
  function toU8(s) { return new TextEncoder().encode(s); }

  /* Remove every ppt/notesSlides/* part plus the references that point at it.
   * Slide XML never links to notes directly — only slide rels and
   * [Content_Types].xml do — so patching those two keeps the file valid.
   * The notes master is kept on purpose (presentation.xml still references it). */
  async function removeNotes(entries) {
    var out = [];
    var removed = 0;
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      if (/^ppt\/notesSlides\//.test(e.name)) { removed++; continue; }
      if (e.name === "[Content_Types].xml") {
        var ct = toStr(e.data).replace(
          /<Override[^>]*PartName="\/ppt\/notesSlides\/[^"]*"[^>]*\/>\s*/g, "");
        out.push({ name: e.name, data: toU8(ct) });
        continue;
      }
      if (/^ppt\/slides\/_rels\/.+\.rels$/.test(e.name)) {
        var rels = toStr(e.data).replace(
          /<Relationship[^>]*Target="\.\.\/notesSlides\/[^"]*"[^>]*\/>\s*/g, "");
        out.push({ name: e.name, data: toU8(rels) });
        continue;
      }
      out.push(e);
    }
    return { entries: out, removedParts: removed };
  }

  var Logic = { removeNotes: removeNotes };
  if (typeof document === "undefined") {
    if (typeof module !== "undefined" && module.exports) module.exports = Logic;
    else globalThis.SlideNotesLogic = Logic;
    return;
  }

  /* ------------------------------ UI ------------------------------ */
  var files = [];
  var busy = false;
  var zip = window.PPTXLite;

  var dropzone = document.getElementById("dropzone");
  var fileInput = document.getElementById("fileInput");
  var fileList = document.getElementById("fileList");
  var goBtn = document.getElementById("goBtn");
  var clearBtn = document.getElementById("clearBtn");
  var statusEl = document.getElementById("status");
  var resultEl = document.getElementById("result");
  var resultMeta = document.getElementById("resultMeta");
  var downloadBtn = document.getElementById("downloadBtn");

  function fmtSize(b) {
    if (b > 1048576) return (b / 1048576).toFixed(1) + " MB";
    return Math.max(1, Math.round(b / 1024)) + " KB";
  }

  function setStatus(msg, isError) {
    statusEl.textContent = msg || "";
    statusEl.className = isError ? "tool-status tool-error" : "tool-status";
  }

  function render() {
    fileList.innerHTML = "";
    files.forEach(function (f, idx) {
      var row = document.createElement("div");
      row.className = "file-row";
      var icon = document.createElement("span");
      icon.textContent = "\uD83D\uDCC4";
      var nm = document.createElement("span");
      nm.className = "file-name";
      nm.textContent = f.name;
      nm.title = f.name;
      var sz = document.createElement("span");
      sz.className = "file-size";
      sz.textContent = fmtSize(f.size);
      var rm = document.createElement("button");
      rm.type = "button";
      rm.className = "mini-btn mini-danger";
      rm.setAttribute("aria-label", "Remove file");
      rm.textContent = "\u2715";
      rm.onclick = function () { files.splice(idx, 1); render(); };
      row.appendChild(icon); row.appendChild(nm); row.appendChild(sz); row.appendChild(rm);
      fileList.appendChild(row);
    });
    goBtn.disabled = !files.length || busy;
    goBtn.textContent = !files.length ? "Select at least one .pptx file"
      : busy ? "Working..." : "Strip notes from " + files.length + " file" + (files.length > 1 ? "s" : "");
  }

  function addFiles(list) {
    for (var i = 0; i < list.length; i++) {
      if (/\.pptx$/i.test(list[i].name)) files.push(list[i]);
      else setStatus("Skipped " + list[i].name + " — only .pptx files are supported.", true);
    }
    render();
  }

  async function run() {
    if (!files.length || busy) return;
    busy = true;
    resultEl.hidden = true;
    render();
    setStatus("Reading files...");
    try {
      var outputs = [];
      var totalRemoved = 0;
      for (var i = 0; i < files.length; i++) {
        var f = files[i];
        setStatus("Processing " + f.name + " (" + (i + 1) + "/" + files.length + ")...");
        var entries = await zip.readZIP(await f.arrayBuffer());
        var res = await removeNotes(entries);
        totalRemoved += res.removedParts;
        var outName = f.name.replace(/\.pptx$/i, "") + "-no-notes.pptx";
        outputs.push({ name: outName, entries: res.entries });
      }
      var blob;
      var label;
      if (outputs.length === 1) {
        blob = await zip.writeZIP(outputs[0].entries);
        label = outputs[0].name;
      } else {
        var zipEntries = [];
        var used = {};
        outputs.forEach(function (o) {
          var n = used[o.name] ? o.name.replace(/\.pptx$/, "-" + (++used[o.name]) + ".pptx")
                               : (used[o.name] = 1, o.name);
          o.entries.forEach(function (e) { zipEntries.push({ name: n + "/" + e.name, data: e.data }); });
        });
        blob = await zip.writeZIP(zipEntries);
        label = "no-notes-files.zip";
      }
      var url = URL.createObjectURL(blob);
      downloadBtn.href = url;
      downloadBtn.download = label;
      downloadBtn.textContent = "\u2B07 Download " + label;
      resultMeta.textContent = "Removed " + totalRemoved + " notes slide" + (totalRemoved === 1 ? "" : "s") +
        " \u00B7 output " + fmtSize(blob.size);
      resultEl.hidden = false;
      setStatus("");
    } catch (err) {
      setStatus(err && err.message ? err.message : "Something went wrong processing this file.", true);
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
  clearBtn.addEventListener("click", function () { files = []; resultEl.hidden = true; setStatus(""); render(); });
  render();
})();
