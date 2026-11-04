/* Slide Vault — Clean Metadata tool: strips author/company info from .pptx.
 * Logic exported for Node tests; UI wires up when a DOM is present.
 * Requires /assets/tools/pptx-lite.js (window.PPTXLite).
 */
(function () {
  "use strict";

  function toStr(u8) { return new TextDecoder().decode(u8); }
  function toU8(s) { return new TextEncoder().encode(s); }

  function blankTag(xml, tag) {
    var re = new RegExp("<" + tag + "(\\s[^>]*)?>[\\s\\S]*?<\\/" + tag + ">", "g");
    var selfClosing = new RegExp("<" + tag + "(\\s[^>]*)?\\/>", "g");
    var found = xml.match(re) || xml.match(selfClosing);
    xml = xml.replace(re, "<" + tag + "></" + tag + ">").replace(selfClosing, "<" + tag + "></" + tag + ">");
    return { xml: xml, value: found ? found[0].replace(/<[^>]*>/g, "").trim() : "" };
  }

  /* Blank creator / last-modified-by / company / manager and drop custom
   * properties. Returns the cleaned entries plus a report of what was found. */
  async function cleanMetadata(entries) {
    var out = [];
    var report = [];
    var hasCustom = entries.some(function (e) { return e.name === "docProps/custom.xml"; });
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      if (e.name === "docProps/custom.xml") continue;
      if (e.name === "_rels/.rels" && hasCustom) {
        out.push({ name: e.name, data: toU8(toStr(e.data).replace(
          /<Relationship[^>]*Target="docProps\/custom\.xml"[^>]*\/>\s*/g, "")) });
        continue;
      }
      if (e.name === "[Content_Types].xml" && hasCustom) {
        out.push({ name: e.name, data: toU8(toStr(e.data).replace(
          /<Override[^>]*PartName="\/docProps\/custom\.xml"[^>]*\/>\s*/g, "")) });
        continue;
      }
      if (e.name === "docProps/core.xml") {
        var xml = toStr(e.data);
        var r1 = blankTag(xml, "dc:creator");
        var r2 = blankTag(r1.xml, "cp:lastModifiedBy");
        if (r1.value) report.push("Author: " + r1.value);
        if (r2.value) report.push("Last saved by: " + r2.value);
        out.push({ name: e.name, data: toU8(r2.xml) });
        continue;
      }
      if (e.name === "docProps/app.xml") {
        var axml = toStr(e.data);
        var r3 = blankTag(axml, "Company");
        var r4 = blankTag(r3.xml, "Manager");
        if (r3.value) report.push("Company: " + r3.value);
        if (r4.value) report.push("Manager: " + r4.value);
        out.push({ name: e.name, data: toU8(r4.xml) });
        continue;
      }
      out.push(e);
    }
    if (hasCustom) report.push("Custom properties: removed");
    return { entries: out, report: report };
  }

  var Logic = { cleanMetadata: cleanMetadata };
  if (typeof document === "undefined") {
    if (typeof module !== "undefined" && module.exports) module.exports = Logic;
    else globalThis.SlideMetaLogic = Logic;
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
  var reportEl = document.getElementById("reportList");
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
      : busy ? "Working..." : "Clean " + files.length + " file" + (files.length > 1 ? "s" : "");
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
    reportEl.innerHTML = "";
    render();
    try {
      var outputs = [];
      var allReports = [];
      for (var i = 0; i < files.length; i++) {
        var f = files[i];
        setStatus("Processing " + f.name + " (" + (i + 1) + "/" + files.length + ")...");
        var entries = await zip.readZIP(await f.arrayBuffer());
        var res = await cleanMetadata(entries);
        allReports.push({ file: f.name, report: res.report });
        var outName = f.name.replace(/\.pptx$/i, "") + "-clean.pptx";
        outputs.push({ name: outName, entries: res.entries });
      }
      var blob;
      var label;
      if (outputs.length === 1) {
        blob = await zip.writeZIP(outputs[0].entries);
        label = outputs[0].name;
      } else {
        var zipEntries = [];
        outputs.forEach(function (o) {
          o.entries.forEach(function (e) { zipEntries.push({ name: o.name + "/" + e.name, data: e.data }); });
        });
        blob = await zip.writeZIP(zipEntries);
        label = "cleaned-files.zip";
      }
      allReports.forEach(function (r) {
        var li = document.createElement("li");
        li.innerHTML = "<b></b>";
        li.firstChild.textContent = r.file;
        var ul = document.createElement("ul");
        if (r.report.length) {
          r.report.forEach(function (item) {
            var sub = document.createElement("li");
            sub.textContent = item;
            ul.appendChild(sub);
          });
        } else {
          var sub = document.createElement("li");
          sub.textContent = "No personal metadata found";
          ul.appendChild(sub);
        }
        li.appendChild(ul);
        reportEl.appendChild(li);
      });
      var url = URL.createObjectURL(blob);
      downloadBtn.href = url;
      downloadBtn.download = label;
      downloadBtn.textContent = "\u2B07 Download " + label;
      resultMeta.textContent = "Output size " + fmtSize(blob.size);
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
