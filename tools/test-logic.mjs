/* Node test harness for the three new tools' logic. Run: node tools/test-logic.mjs */
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import os from "os";
import { execSync } from "child_process";

const require2 = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const LITE = require2(path.join(ROOT, "assets/tools/pptx-lite.js"));
const notesLogic = require2(path.join(ROOT, "assets/tools/remove-notes.js"));
const metaLogic = require2(path.join(ROOT, "assets/tools/clean-metadata.js"));
const statsLogic = require2(path.join(ROOT, "assets/tools/ppt-stats.js"));

const SAMPLES = [
  "files/Brand-Launch-Template.pptx",
  "files/Annual-Report-Template.pptx",
  "files/AETHER-Financial-Consulting-Template-1.pptx",
  "files/Training-Course-Template.pptx",
];

function toArrayBuffer(buf) {
  return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
}

async function roundtrip(entries, outFile) {
  const blob = await LITE.writeZIP(entries);
  const arr = new Uint8Array(await blob.arrayBuffer());
  fs.writeFileSync(outFile, arr);
  return arr.length;
}

let failed = 0;
function check(name, cond) {
  console.log((cond ? "  PASS" : "  FAIL") + "  " + name);
  if (!cond) failed++;
}

for (const rel of SAMPLES) {
  const file = path.join(ROOT, rel);
  const base = path.basename(rel, ".pptx");
  console.log("== " + base);
  const buf = fs.readFileSync(file);
  const entries = await LITE.readZIP(toArrayBuffer(buf));
  check("read: entries > 20", entries.length > 20);
  check("read: no directory entries", !entries.some((e) => e.name.endsWith("/")));

  // CRC check on one entry vs python? trust; verify slide content survived
  const slide = entries.find((e) => e.name === "ppt/slides/slide1.xml");
  check("read: slide1.xml has <a:t>", slide && toS(slide.data).includes("<a:t>"));

  // --- stats ---
  const st = await statsLogic.collectStats(entries);
  check("stats: slides >= 8", st.slides >= 8);
  check("stats: words > 10", st.words > 10);
  console.log("   stats:", JSON.stringify(st));

  // --- remove notes ---
  const hadNotes = entries.some((e) => e.name.startsWith("ppt/notesSlides/"));
  const rn = await notesLogic.removeNotes(entries);
  check("notes: removed parts " + rn.removedParts, !hadNotes || rn.removedParts > 0);
  check("notes: no notesSlides left", !rn.entries.some((e) => e.name.startsWith("ppt/notesSlides/")));
  const ct = rn.entries.find((e) => e.name === "[Content_Types].xml");
  check("notes: content-types clean", !toS(ct.data).includes("/ppt/notesSlides/"));
  for (const e of rn.entries) {
    if (/^ppt\/slides\/_rels\/.+\.rels$/.test(e.name))
      check("notes: rels clean " + e.name, !toS(e.data).includes("../notesSlides/"));
  }
  const rnSize = await roundtrip(rn.entries, path.join(os.tmpdir(), base + "-no-notes.pptx"));
  check("notes: output size sane", rnSize > 10000);

  // --- metadata ---
  const cm = await metaLogic.cleanMetadata(entries);
  const core = cm.entries.find((e) => e.name === "docProps/core.xml");
  const coreXml = toS(core.data);
  check("meta: creator blank", !/<dc:creator>[^<]/.test(coreXml));
  check("meta: lastModifiedBy blank", !/<cp:lastModifiedBy>[^<]/.test(coreXml));
  const app = cm.entries.find((e) => e.name === "docProps/app.xml");
  const appXml = toS(app.data);
  check("meta: company blank", !/<Company>[^<]/.test(appXml));
  check("meta: custom.xml dropped", !cm.entries.some((e) => e.name === "docProps/custom.xml"));
  const rels = cm.entries.find((e) => e.name === "_rels/.rels");
  check("meta: root rels clean", !toS(rels.data).includes("custom.xml"));
  await roundtrip(cm.entries, path.join(os.tmpdir(), base + "-clean.pptx"));
}

function toS(u8) { return new TextDecoder().decode(u8); }

// --- LibreOffice validity check on processed outputs ---
if (process.env.SKIP_LO !== "1") {
  console.log("== LibreOffice validity");
  for (const base of SAMPLES.map((s) => path.basename(s, ".pptx"))) {
    for (const suffix of ["-no-notes", "-clean"]) {
      const f = path.join(os.tmpdir(), base + suffix + ".pptx");
      try {
        execSync(
          `soffice --headless --convert-to pdf --outdir ${os.tmpdir()} ${f}`,
          { stdio: "pipe", timeout: 120000 });
        const pdf = f.replace(/\.pptx$/, ".pdf");
        check(`${base}${suffix} converts to PDF`, fs.existsSync(pdf) && fs.statSync(pdf).size > 5000);
      } catch (e) {
        check(`${base}${suffix} converts to PDF (error)`, false);
      }
    }
  }
}

console.log(failed ? `\n${failed} CHECK(S) FAILED` : "\nALL CHECKS PASSED");
process.exit(failed ? 1 : 0);
