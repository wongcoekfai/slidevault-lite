#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generates the three newer tool pages (remove-notes, clean-metadata, ppt-stats)
from one shared template. Run after editing the TOOLS config:

  python3 tools/gen_tool_pages.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://slidevaulte.com"

TOOLS = [
    dict(
        slug="remove-notes",
        h1="Remove Speaker Notes from PowerPoint",
        title="Remove Speaker Notes from PowerPoint Online Free — Strip PPTX Notes",
        desc="Strip all speaker notes from one or many .pptx files right in your "
             "browser. Free, no sign-up, no upload — your presentations never leave "
             "your device.",
        kw="remove speaker notes from powerpoint, delete notes pptx, strip notes "
           "powerpoint online, clear speaker notes ppt, pptx remove notes free, "
           "presentation notes remover",
        og="Strip every speaker note from a .pptx deck in your browser. No upload, "
           "no sign-up.",
        lead="Delete every speaker note from one or many <b>.pptx</b> decks — free, "
             "no sign-up, and no upload. Everything happens inside your browser.",
        icon="&#128221;",
        card="Strip all speaker notes out of one or many decks before sharing, in "
             "seconds — without opening PowerPoint.",
        card_btn="Remove notes &rarr;",
        steps=[
            "<b>Add your decks.</b> Click the box (or drag &amp; drop) and pick one or "
            "several .pptx presentations.",
            "<b>Strip the notes.</b> Press the button — every notes page is removed "
            "from the file structure, not just hidden.",
            "<b>Download.</b> Grab the cleaned file, or a ZIP when you dropped in "
            "several decks at once.",
        ],
        why="Speaker notes are easy to forget: rehearsal cues, salary numbers, "
            "half-written jokes, feedback from colleagues. Cloud-based converters "
            "mean uploading those notes to someone else's server before you can "
            "clean them. This tool works <b>directly on your device</b> — the deck "
            "is unpacked in your browser's memory, the notes parts are removed from "
            "the file, and the result is handed straight back to you. Nothing is "
            "transmitted, stored, or logged.",
        extra="The tool removes the notes content itself, not just the view: notes "
              "pages are deleted from the package, so the text cannot reappear "
              "through \"show notes\" or a different viewer. Slide visuals, "
              "animations and layouts are untouched.",
        faq=[
            ("Does removing notes change the slides?",
             "No. Only the notes pages are removed. Slide layouts, fonts, colours, "
             "animations and media are untouched, and the deck still opens normally "
             "in PowerPoint, Google Slides and Keynote."),
            ("Why should I remove speaker notes before sharing?",
             "Notes often contain internal remarks, pricing logic, names and "
             "half-finished thoughts. Stripping them avoids accidentally sharing "
             "something private when you send the deck to a client, student or "
             "conference organiser."),
            ("Can I clean several files at once?",
             "Yes. Drop in as many .pptx files as you like — you get back a single "
             "ZIP with one cleaned file per deck."),
            ("Is the original file modified?",
             "No. The file is read into browser memory and a new, cleaned copy is "
             "created for download. Your original stays exactly as it is on disk."),
            ("Does it work with .ppt or Google Slides files?",
             "Only .pptx is supported. In Google Slides use File &rarr; Download "
             "&rarr; Microsoft PowerPoint (.pptx) first; legacy .ppt files need a "
             "quick save-as .pptx in PowerPoint."),
        ],
    ),
    dict(
        slug="clean-metadata",
        h1="Remove Author & Metadata from PowerPoint",
        title="Remove Metadata from PowerPoint Online Free — Delete PPTX Author Info",
        desc="Remove author, company and custom metadata from .pptx files in your "
             "browser. Free, no sign-up, no upload — files never leave your device.",
        kw="remove author from powerpoint, delete powerpoint metadata, pptx remove "
           "personal information, clean pptx author, anonymous powerpoint file, "
           "remove company name pptx",
        og="Delete author, company and custom properties from a .pptx in your "
           "browser. No upload, no sign-up.",
        lead="Scrub author names, company details and custom properties out of one "
             "or many <b>.pptx</b> files — free, no sign-up, no upload. Everything "
             "happens inside your browser.",
        icon="&#129524;",
        card="Delete author, company and hidden custom properties from a deck "
             "before it leaves your organisation.",
        card_btn="Clean metadata &rarr;",
        steps=[
            "<b>Add your decks.</b> Pick one or several .pptx files — the tool shows "
            "exactly which metadata it finds.",
            "<b>Clean them.</b> Author, last-saved-by, company, manager and custom "
            "properties are removed from the file.",
            "<b>Download.</b> Save the cleaned copy, or a ZIP for multiple decks.",
        ],
        why="Every PowerPoint file quietly carries a paper trail: the author's "
             "name, the company that owns the licence, the last person who saved "
             "it, and any custom properties the first template added. For job "
             "applications, client deliverables, anonymous submissions or published "
             "templates, that trail can leak more than you intended. This tool "
             "rewrites the document properties <b>inside your browser</b> — the "
             "file is never uploaded anywhere, so sensitive names never leave your "
             "machine.",
        extra="The tool shows you a report of every value it removed, so you can "
              "verify the result before you share the file. Slide content, design "
              "and structure are not touched in any way.",
        faq=[
            ("Which properties get removed?",
             "Author (dc:creator), last-saved-by (cp:lastModifiedBy), company, "
             "manager and all custom document properties. Slide content, dates in "
             "the slide body and the deck's design are untouched."),
            ("Will PowerPoint still open the file normally?",
             "Yes. The properties are simply emptied — the file keeps a valid "
             "structure and opens in PowerPoint, Google Slides and Keynote without "
             "any warning."),
            ("Why not use PowerPoint's Document Inspector?",
             "You can — if you have PowerPoint. This tool exists for when you are "
             "on a shared or locked-down computer, want to batch-clean many files, "
             "or simply do not want to upload the deck to a web service."),
            ("Can I clean a deck I received from someone else?",
             "Yes. The tool rewrites whatever metadata the file carries, regardless "
             "of who created it. Useful before re-publishing or forwarding decks "
             "you did not make."),
            ("Does it work with .ppt or Google Slides files?",
             "Only .pptx is supported. In Google Slides use File &rarr; Download "
             "&rarr; Microsoft PowerPoint (.pptx) first; legacy .ppt files need a "
             "quick save-as .pptx in PowerPoint."),
        ],
    ),
    dict(
        slug="ppt-stats",
        h1="PowerPoint File Info — Count Slides, Words & Images",
        title="PowerPoint File Info Online Free — Count PPTX Slides, Words, Images",
        desc="Inspect a .pptx without opening PowerPoint: slide count, word count, "
             "images, charts, tables, media weight and more. Free, no upload, runs "
             "in your browser.",
        kw="powerpoint file info, count slides in pptx, pptx word count, how many "
           "slides in my powerpoint, pptx analyzer, count images in powerpoint",
        og="See what is inside a .pptx — slides, words, images, charts and media "
           "weight — without opening PowerPoint.",
        lead="Point it at a <b>.pptx</b> file and see what is inside: slide count, "
             "word count, images, charts, tables and media weight — without opening "
             "PowerPoint, and without uploading anything.",
        icon="&#128202;",
        card="Slide count, word count, image and chart inventory for any deck — "
             "handy before a pitch or a handover.",
        card_btn="Analyse a deck &rarr;",
        steps=[
            "<b>Add your decks.</b> Pick one or several .pptx files to inspect.",
            "<b>Analyse.</b> The tool reads the file structure locally and builds a "
            "fact sheet per deck.",
            "<b>Read the numbers.</b> Slides, words, images, charts, tables, media "
            "weight — no file is created or uploaded.",
        ],
        why="Word limits, slide limits and image-heavy decks come up constantly: "
             "conference CFPs ask for decks under 20 slides, style guides cap word "
             "counts per slide, and email systems reject files over 20 MB. This "
             "tool answers those questions <b>without opening PowerPoint</b> and "
             "without sending the file to a server — the deck is unpacked in your "
             "browser's memory and measured there. It is read-only: nothing is "
             "rewritten, so there is no output file to download.",
        extra="For multi-deck drops you get one fact sheet per file, which makes "
              "it easy to compare candidate decks before a pitch or to audit a "
              "folder full of presentations.",
        faq=[
            ("Is anything uploaded or changed?",
             "No on both counts. The file is read in your browser's memory, "
             "measured, and forgotten. The original file is never modified and "
             "there is no download."),
            ("How is the word count calculated?",
             "All visible text on the slides is counted — titles, body text, "
             "captions and labels. Speaker notes are counted separately so you can "
             "see both numbers."),
            ("Why do my images show as zero?",
             "Only media embedded in the file counts. Linked images (files the "
             "deck references from your disk) are not part of the .pptx package "
             "and cannot be seen."),
            ("Can it read .ppt or Google Slides files?",
             "Only .pptx. In Google Slides use File &rarr; Download &rarr; "
             "Microsoft PowerPoint (.pptx) first; legacy .ppt files need a quick "
             "save-as .pptx in PowerPoint."),
            ("Does a big file always mean many slides?",
             "Not at all. The media weight line shows how much of the file is "
             "photos, video and audio — a 5-image deck can easily outweigh a "
             "40-slide text deck. Pair it with our Compress PPT tool when the "
             "number is too high."),
        ],
    ),
]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<meta name="description" content="{desc}" />
<meta name="keywords" content="{kw}" />
<link rel="canonical" href="{site}/tools/{slug}/" />
<meta property="og:title" content="{og}" />
<meta property="og:description" content="{desc}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{site}/tools/{slug}/" />
<meta property="og:image" content="{site}/assets/img/SaaS-Startup-Pitch-Deck-Template.jpg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{og}" />
<meta name="twitter:description" content="{desc}" />
<meta name="twitter:image" content="{site}/assets/img/SaaS-Startup-Pitch-Deck-Template.jpg" />
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg" />
<link rel="stylesheet" href="/assets/style.css?v=6" />
<script type="application/ld+json">
{faq_schema}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"{site}/"}},{{"@type":"ListItem","position":2,"name":"PPT Tools","item":"{site}/tools/"}},{{"@type":"ListItem","position":3,"name":"{h1}"}}]}}
</script>
<!-- ===== Monetization: Google AdSense ===== -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6730005742175239" crossorigin="anonymous"></script>
<style>
.tool-box {{ background: var(--surface); border: 1px solid #ffffff14; border-radius: var(--radius); padding: 28px; margin: 28px 0; }}
.dropzone {{ border: 2px dashed #ffffff2e; border-radius: 12px; padding: 40px 20px; text-align: center; cursor: pointer; transition: border-color .2s, background .2s; }}
.dropzone:hover, .dropzone.dragging {{ border-color: var(--accent); background: #3b82f614; }}
.dropzone .dz-icon {{ font-size: 2rem; display: block; margin-bottom: 8px; }}
.dropzone p {{ margin: 4px 0 0; color: var(--muted); }}
#fileList {{ list-style: none; margin: 16px 0 0; padding: 0; display: grid; gap: 8px; }}
.file-row {{ display: flex; align-items: center; gap: 12px; background: var(--surface-2); border-radius: 10px; padding: 10px 14px; }}
.file-name {{ flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.file-size {{ color: var(--muted); font-size: .85rem; flex: none; }}
.mini-btn {{ background: #ffffff12; color: var(--text); border: none; border-radius: 8px; width: 30px; height: 30px; cursor: pointer; font-size: .9rem; }}
.mini-btn:hover {{ background: #ffffff22; }}
.mini-danger:hover {{ background: #ef444455; }}
.tool-actions {{ margin-top: 16px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }}
.tool-actions .btn {{ border: none; font-size: 1rem; }}
.tool-actions .btn:disabled {{ opacity: .45; cursor: not-allowed; }}
.ghost-btn {{ background: transparent; color: var(--muted); border: 1px solid #ffffff22; border-radius: 999px; padding: 8px 16px; cursor: pointer; font-size: .9rem; }}
.tool-status {{ min-height: 24px; margin-top: 14px; color: var(--muted); font-size: .95rem; }}
.tool-status.tool-error {{ color: #f87171; }}
#result {{ margin-top: 20px; background: #22c55e18; border: 1px solid #22c55e44; border-radius: 12px; padding: 18px; }}
#resultMeta {{ color: var(--muted); font-size: .9rem; margin: 8px 0 0; }}
#result .btn {{ margin-top: 12px; border: none; }}
.privacy-note {{ display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: .9rem; margin-top: 14px; }}
.steps {{ counter-reset: step; list-style: none; padding: 0; margin: 20px 0; display: grid; gap: 12px; }}
.steps li {{ background: var(--surface); border-radius: 10px; padding: 14px 16px 14px 52px; position: relative; }}
.steps li::before {{ counter-increment: step; content: counter(step); position: absolute; left: 14px; top: 14px; width: 26px; height: 26px; border-radius: 50%; background: var(--accent); color: #04122b; font-weight: 700; font-size: .85rem; display: flex; align-items: center; justify-content: center; }}
.tool-prose h2 {{ margin-top: 36px; }}
.tool-faq h3 {{ margin-bottom: 6px; }}
.tool-faq p {{ margin-top: 0; color: var(--muted); }}
#reportList, #report {{ margin: 12px 0 0; padding: 0; list-style: none; display: grid; gap: 14px; }}
#reportList b, #report h3 {{ font-size: .95rem; }}
#reportList ul, .stat-card ul {{ margin: 6px 0 0; color: var(--muted); font-size: .9rem; }}
.stat-card {{ background: var(--surface-2); border-radius: 12px; padding: 16px 18px; }}
.stat-card h3 {{ margin: 0 0 4px; }}
@media (max-width: 560px) {{ .tool-box {{ padding: 18px; }} .file-size {{ display: none; }} }}
</style>
</head>
<body>
<header class="site-header">
  <div class="container nav">
    <a class="brand" href="/">Slide<span>Vault</span></a>
    <nav>
      <a href="/#templates">Templates</a>
      <a href="/templates/business/">Business</a>
      <a href="/templates/marketing/">Marketing</a>
      <a href="/templates/startup/">Startup</a>
      <a href="/templates/sales/">Sales</a>
      <a href="/templates/education/">Education</a>
      <a href="/blog/">Blog</a>
      <div class="nav-drop">
        <button type="button" class="nav-drop-btn" aria-haspopup="true" aria-expanded="false">PPT Tools <span class="caret">&#9662;</span></button>
        <div class="nav-menu">
          <a href="/tools/">All PPT Tools</a>
          <a href="/tools/merge-ppt/">Merge PPT</a>
          <a href="/tools/compress-ppt/">Compress PPT</a>
          <a href="/tools/split-ppt/">Split PPT</a>
          <a href="/tools/extract-images/">Extract Images</a>
          <a href="/tools/remove-notes/">Remove Notes</a>
          <a href="/tools/clean-metadata/">Clean Metadata</a>
          <a href="/tools/ppt-stats/">PPT Stats</a>
        </div>
      </div>
      <a href="/about/">About</a>
      <a class="btn btn-ghost" href="/#subscribe">Subscribe</a>
    </nav>
  </div>
</header>
<main class="container tool-prose" style="max-width:820px;">
  <h1>{h1}</h1>
  <p class="muted" style="font-size:1.1rem;">{lead}</p>

  <section class="tool-box" aria-label="PPT tool">
    <div id="dropzone" class="dropzone" role="button" tabindex="0" aria-label="Choose or drop .pptx files">
      <span class="dz-icon">{icon}</span>
      <b>Choose .pptx files</b> or drop them here
      <p>Multiple files welcome — everything stays on your device.</p>
      <input type="file" id="fileInput" accept=".pptx" multiple hidden />
    </div>
    <div id="fileList"></div>
    <div class="tool-actions">
      <button id="goBtn" class="btn btn-primary" type="button" disabled>Select at least one .pptx file</button>
      <button id="clearBtn" class="ghost-btn" type="button">Clear</button>
    </div>
    <div id="status" class="tool-status" role="status" aria-live="polite"></div>
    <div id="result" hidden>
      <b>&#9989; Done</b>
      <p id="resultMeta"></p>
      <ul id="reportList"></ul>
      <div id="report"></div>
      <a id="downloadBtn" class="btn btn-primary" href="#">&#11015; Download</a>
    </div>
    <p class="privacy-note">&#128274; 100% private: your files are processed locally and never uploaded to any server.</p>
  </section>

  <h2>How it works</h2>
  <ol class="steps">{steps}</ol>

  <h2>Why do this in the browser?</h2>
  <p>{why}</p>
  <p>{extra}</p>

  <h2>FAQ</h2>
  <div class="tool-faq">{faq}</div>

  <h2>More free PowerPoint tools</h2>
  <p>Combine decks with <a href="/tools/merge-ppt/" style="color:var(--accent-2);">Merge PPT</a>, shrink heavy files with <a href="/tools/compress-ppt/" style="color:var(--accent-2);">Compress PPT</a>, break a deck into single slides with <a href="/tools/split-ppt/" style="color:var(--accent-2);">Split PPT</a>, pull out embedded pictures with <a href="/tools/extract-images/" style="color:var(--accent-2);">Extract Images</a>, or browse our <a href="/#templates" style="color:var(--accent-2);">free PowerPoint templates</a> for your next presentation.</p>

  <p style="margin-top:32px;"><a class="btn btn-ghost" href="/">&#8592; Back to Slide Vault</a></p>
</main>
<footer class="site-footer">
  <div class="container foot">
    <div>
      <b>Slide<span>Vault</span></b>
      <p class="hint">Free PowerPoint &amp; Google Slides templates for business and education.</p>
    </div>
    <div class="foot-links">
      <a href="/#templates">Templates</a>
      <a href="/templates/business/">Business</a>
      <a href="/templates/marketing/">Marketing</a>
      <a href="/templates/startup/">Startup</a>
      <a href="/templates/sales/">Sales</a>
      <a href="/templates/education/">Education</a>
      <a href="/blog/">Blog</a>
      <a href="/tools/">PPT Tools</a>
      <a href="/about/">About</a>
      <a href="/contact/">Contact</a>
      <a href="/privacy/">Privacy</a>
      <a href="https://tools.slidevaulte.com/">Drainage Calculators</a>
    </div>
  </div>
  <div class="container"><p class="hint copyright">&copy; 2026 SLIDE VAULT &middot; Hosted statically on Cloudflare Pages.</p></div>
</footer>
{scripts}
</body>
</html>
"""

# extra script tags per tool (ppt-stats has no output download but keeps the
# hidden button in the DOM harmlessly)
SCRIPTS = """<script src="/assets/tools/pptx-lite.js?v=1" defer></script>
<script src="/assets/tools/{logic}.js?v=1" defer></script>
<script src="/assets/nav.js?v=1" defer></script>"""


def main():
    for t in TOOLS:
        faq_schema = json.dumps(
            {"@context": "https://schema.org", "@type": "FAQPage",
             "mainEntity": [{"@type": "Question", "name": q,
                             "acceptedAnswer": {"@type": "Answer", "text": a}}
                            for q, a in t["faq"]]}, ensure_ascii=False)
        steps = "".join("<li>%s</li>" % s for s in t["steps"])
        faq = "".join('<h3>%s</h3><p>%s</p>' % (q, a) for q, a in t["faq"])
        html = PAGE.format(
            title=t["title"], desc=t["desc"], kw=t["kw"], og=t["og"],
            slug=t["slug"], site=SITE, h1=t["h1"], lead=t["lead"], icon=t["icon"],
            steps=steps, why=t["why"], extra=t["extra"], faq=faq,
            faq_schema=faq_schema,
            scripts=SCRIPTS.format(logic=t["slug"]))
        d = os.path.join(ROOT, "tools", t["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
        print("  /tools/%s/  (%d faq, %d steps)" % (t["slug"], len(t["faq"]), len(t["steps"])))
    print("done.")


if __name__ == "__main__":
    main()
