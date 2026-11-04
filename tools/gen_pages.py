#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerates the Slide Vault static site from assets/templates.js.

Run this after you:
  1. drop new preview photos into  assets/img/gallery/<slug>/
  2. OR edit metadata in           assets/templates.js

  python3 tools/gen_pages.py            # regenerate detail pages + sitemap
  python3 tools/gen_pages.py --resize   # also downscale photos > 1600px wide

Photos are discovered automatically by filename order inside each slug folder,
so name them  01.jpg  02.jpg  03.jpg  ...  to control slide order.
"""
import argparse
import html
import zipfile
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://slidevaulte.com"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
MAX_WIDTH = 1600


# ---------------------------------------------------------------- utilities

def natural_key(s):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]


def abspath(p):
    """Always emit site-root-absolute paths: detail pages live one level deep,
    so relative 'assets/...' would resolve to /templates/<slug>/assets/... (404)."""
    if not p:
        return p
    return p if p.startswith("/") else "/" + p


def scan_gallery(slug, resize=False):
    """Return sorted list of site-relative image paths for this template."""
    d = os.path.join(ROOT, "assets", "img", "gallery", slug)
    if not os.path.isdir(d):
        return []
    files = [f for f in os.listdir(d) if f.lower().endswith(IMG_EXT)]
    files.sort(key=natural_key)

    out = []
    for f in files:
        rel = "/assets/img/gallery/%s/%s" % (slug, f)
        if resize:
            shrink(os.path.join(ROOT, rel.lstrip("/")))
        out.append(rel)
    return out


def shrink(path):
    """Downscale an oversized photo in place using macOS sips (no-op elsewhere)."""
    try:
        w = subprocess.run(["sips", "-g", "pixelWidth", path], capture_output=True,
                           text=True).stdout
        width = int(re.search(r"pixelWidth:\s*(\d+)", w).group(1))
        if width > MAX_WIDTH:
            subprocess.run(["sips", "--resampleWidth", str(MAX_WIDTH), path],
                           capture_output=True)
            print("    resized ->", os.path.basename(path))
    except Exception:
        pass  # non-macOS or non-image: silently skip


def parse_catalog():
    """Read existing assets/templates.js into a list of dicts (ignore old gallery)."""
    src = open(os.path.join(ROOT, "assets", "templates.js"), encoding="utf-8").read()
    items = []
    for m in re.finditer(
        r'\{\s*slug:\s*"([^"]+)",\s*title:\s*"([^"]+)",\s*seo:\s*"([^"]*)",\s*'
        r'tag:\s*"([^"]*)",\s*cat:\s*"([^"]*)",\s*desc:\s*"([^"]*)",\s*'
        r'body:\s*"([^"]*)",\s*img:\s*"([^"]*)",\s*file:\s*"([^"]*)"', src):
        items.append(dict(zip(
            ("slug", "title", "seo", "tag", "cat", "desc", "body", "img", "file"),
            m.groups())))
    if not items:
        sys.exit("!! could not parse assets/templates.js")
    return items


def write_catalog(items):
    lines = ["// Template catalog. Edit here, then run: python3 tools/gen_pages.py",
             "// gallery[] is filled automatically from assets/img/gallery/<slug>/",
             "// seo = <title> + og:title (long-tail), desc = meta description, body = on-page paragraph"]
    for it in items:
        lines.append(
            '  { slug: "%s", title: "%s", seo: "%s", tag: "%s", cat: "%s", desc: "%s", body: "%s", img: "%s", file: "%s", gallery: [%s] },'
            % (it["slug"], it["title"], it["seo"], it["tag"], it["cat"], it["desc"],
               it["body"], it["img"], it["file"],
               ", ".join('"%s"' % g for g in it["gallery"])))
    open(os.path.join(ROOT, "assets", "templates.js"), "w", encoding="utf-8").write(
        "window.TEMPLATES = [\n" + "\n".join(lines) + "\n];\n")


# ---------------------------------------------------------------- detail page

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{page_title}</title>
<meta name="description" content="{desc}" />
<meta name="keywords" content="{kw}" />
<meta property="og:title" content="{seo}" />
<meta property="og:description" content="{desc}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{site}/templates/{slug}/" />
<meta property="og:image" content="{ogimg}" />
<link rel="canonical" href="{site}/templates/{slug}/" />
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{seo}" />
<meta name="twitter:description" content="{desc}" />
<meta name="twitter:image" content="{ogimg}" />
<link rel="stylesheet" href="/assets/style.css?v={cssver}" />
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"SoftwareApplication","name":"{title}","url":"{site}/templates/{slug}/","description":"{desc}","image":"{ogimg}","applicationCategory":"BusinessApplication","operatingSystem":"Any","offers":{{"@type":"Offer","price":"0","priceCurrency":"USD"}}}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"{site}/"}},{{"@type":"ListItem","position":2,"name":"Templates","item":"{site}/#templates"}},{{"@type":"ListItem","position":3,"name":"{cat_label} Templates","item":"{site}/templates/{cat}/"}},{{"@type":"ListItem","position":4,"name":"{title}"}}]}}
</script>

<!-- ===== Monetization: Google AdSense =====
     AdSense publisher ID configured: ca-pub-6730005742175239 (from AdSense Account Information).
     Enable "Auto Ads" in the AdSense dashboard — ads are placed automatically, no unit IDs needed. -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6730005742175239" crossorigin="anonymous"></script>

<!-- FAQ rich result: questions are mirrored as visible copy further down the page -->
{faq_schema}
</head>
<body>
<header class="site-header">
  <div class="container nav">
    <a class="brand" href="/">Slide<span>Vault</span></a>
    <nav>
      <a href="/#templates">Templates</a>
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
<main class="container detail">
  <p class="crumbs"><a href="/#templates">Templates</a> / <a href="/templates/{cat}/">{cat_label}</a> / <b>{title}</b></p>
  <h1>{title}</h1>
  <div class="meta-row">
    <span class="tag">{tag}</span>
    <span class="tag cat">{cat_label}</span>
    <span class="tag free">Free</span>
    <span class="tag free">{size}</span>
    {slide_count}
    <span class="dl-count" id="dl-count"></span>
  </div>

  <section class="gallery" id="gallery">
    <div class="gallery-stage">
      <button class="gallery-nav prev" type="button" aria-label="Previous slide">&#8249;</button>
      {stage_inner}
      <button class="gallery-nav next" type="button" aria-label="Next slide">&#8250;</button>
      <span class="gallery-counter" id="gallery-counter"></span>
    </div>
    <div class="gallery-thumbs" id="gallery-thumbs">{thumbs}</div>
  </section>

  <div class="detail-actions">
    <a class="btn btn-primary" href="/download?file={file}" rel="nofollow">&#11015; Download .pptx</a>
    <a class="btn btn-ghost" href="/#templates">Browse all templates</a>
  </div>

  <!-- ===== Monetization: Affiliate recommendations + Lead magnet ===== -->
  <section class="affiliate-box">
    <h2>Finish your deck faster</h2>
    <p>Free template + the right tools = done in minutes. These are the tools we actually use:</p>
    <div class="aff-row">
      <a class="aff-btn" href="https://www.canva.com/?YOUR_CANVA_AFF_PARAMS" target="_blank" rel="sponsored noopener">Try Canva Pro<span>design anywhere</span></a>
      <a class="aff-btn alt" href="https://1.envato.market/YOUR_ENVATO_AFF_ID" target="_blank" rel="sponsored noopener">Millions of assets on Envato<span>photos, fonts, video</span></a>
    </div>
    <p class="hint">As an affiliate we may earn a commission at no extra cost to you.</p>
  </section>

  <section class="lead-magnet">
    <h2>📦 Get the full free template bundle</h2>
    <p>Join our list and we'll send you every Slide Vault deck in one drop — plus new releases.</p>
    <form action="/subscribe" method="POST" class="subscribe compact">
      <input type="hidden" name="source" value="bundle_detail" />
      <input type="email" name="email" placeholder="you@company.com" required />
      <button class="btn btn-primary" type="submit">Send me the bundle</button>
      <input type="text" name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true" />
    </form>
    <p class="hint">No spam. Unsubscribe anytime. Stored only in our Cloudflare account.</p>
  </section>

  <section class="prose">
    <h2>About this template</h2>
    <p>{desc}</p>
    <p>{body}</p>
    <p>Works with <b>PowerPoint</b> and <b>Google Slides</b>. Fully editable - change colors, fonts, text and images freely. Free for personal and commercial use. No signup required.</p>
  </section>

  <section class="prose">
    <h2>What is in the {title}</h2>
    <p>{lead}</p>
    <ul class="checklist">{inside}</ul>
    <p>{quality}</p>
  </section>

  <section class="prose">
    <h2>How to customize it in five minutes</h2>
    <ol class="steps">{steps}</ol>
  </section>

  <section class="prose">
    <h2>File details</h2>
    <ul class="facts">{facts}</ul>
  </section>

  <section class="prose">
    <h2>Frequently asked questions</h2>
    <div class="faq">{faq}</div>
  </section>

  <section class="prose">
    <h2>Related reading</h2>
    <ul class="checklist">{reading}</ul>
  </section>
  <section class="prose">
    <h2>More {cat_label} templates</h2>
    <p>Browse all <a href="/templates/{cat}/">{low} presentation templates</a> in this category.</p>
  </section>
  <section class="prose">
    <h2>Related templates</h2>
    <div class="grid related">{related}</div>
  </section>
</main>

<div class="lightbox" id="lightbox" hidden>
  <button class="lightbox-close" type="button" aria-label="Close">&#215;</button>
  <button class="lightbox-nav prev" type="button" aria-label="Previous">&#8249;</button>
  <img alt="Full-size slide preview" />
  <button class="lightbox-nav next" type="button" aria-label="Next">&#8250;</button>
</div>

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
<script src="/assets/gallery.js"></script>
<script src="/assets/nav.js?v=1" defer></script>
<script>
fetch('/downloads?file={file}').then(r=>r.json()).then(d=>{{
  var el=document.getElementById('dl-count');
  if(el&&typeof d.count==='number'&&d.count>0) el.textContent=d.count+' downloads';
}}).catch(()=>{{}});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------- category hubs

# (cat, label, seo_title, h1, meta_desc, lead, howto, hub_intro)
CATS = [
    ("business", "Business",
     "Free Business Presentation Templates - 25 Editable Corporate Decks",
     "Free Business Presentation Templates",
     "25 free business presentation templates for corporate reviews, board meetings and strategy offsites. Editable PowerPoint and Google Slides decks, no signup.",
     "Twenty-five editable business presentation templates for corporate reviews, board meetings, strategy offsites and team updates. Every deck is a real .pptx file that opens cleanly in PowerPoint and Google Slides. No signup, no watermark, and free for personal and commercial use.",
     "If you are presenting to a board, start with the annual report or corporate template. For internal planning, the strategy or OKR deck fits better. For client-facing work, the proposal decks in the Sales category are a closer match. Every template is fully editable, so rebranding colours, fonts and layouts takes a few minutes.",
     "Board decks, quarterly reviews, strategy offsites and all-hands updates all live here."),
    ("startup", "Startup",
     "Free Startup Pitch Deck Templates - 5 Investor-Ready Decks",
     "Free Startup Pitch Deck Templates",
     "5 free startup pitch deck templates for pre-seed to Series A fundraising, plus a business plan deck. Problem, traction, market and ask slides, ready to edit.",
     "Five investor-ready pitch deck templates for pre-seed through Series A fundraising, plus a business plan deck for bank and partner conversations. Each follows the structure investors actually screen for: problem, solution, market, traction and the ask.",
     "Choose the dark pitch deck for demo days and stage presentations, or the light version if you are sending a PDF and want to keep ink low. If you are writing a fuller plan for a bank or grant application, use the business plan template instead. Once you have raised, the investor update deck keeps your monthly reporting consistent.",
     "Fundraising decks and the investor communication that follows the round."),
    ("marketing", "Marketing",
     "Free Marketing Presentation Templates - 9 Campaign and Report Decks",
     "Free Marketing Presentation Templates",
     "9 free marketing presentation templates: monthly reports, agency proposals, brand and product launches, media kits and event plans. Editable in PowerPoint.",
     "Nine marketing presentation templates covering monthly reports, agency proposals, brand and product launches, media kits and event plans. Built for the decks marketing teams rebuild every quarter, with the slides you always end up making by hand.",
     "For recurring reporting, start with the marketing report template. For new business, the agency proposal and digital agency decks are built for pitches. For a one-off campaign, use the product or brand launch template, since both assume a channel plan and a timeline.",
     "Campaign reporting, pitches, launches and the brand assets that go with them."),
    ("sales", "Sales",
     "Free Sales Presentation Templates - 3 Proposal and Performance Decks",
     "Free Sales Presentation Templates",
     "3 free sales presentation templates for client proposals, project scoping and performance reviews. Pricing, pipeline and forecast slides ready to edit.",
     "Three sales presentation templates for proposals, project scoping and performance reviews. Each is structured around the decision your buyer or leadership team needs to make, rather than around your product features.",
     "Use the sales proposal template after discovery, when the buyer needs pricing options and a clear next step. The project proposal deck fits internal approval and scoping. For recurring reporting to leadership, use the sales performance template.",
     "Proposals that close, scoping that gets approved, and the reviews that follow."),
]

CSS_VER = "6"

# ---------------------------------------------------------------- detail-page copy
# Per-category editorial blocks. AdSense rejects sites whose template pages are
# 200-word download shells with identical boilerplate, so every detail page gets
# an audience note, a contents list, a quality note, an editing walkthrough,
# file facts and a visible FAQ that matches the FAQPage schema.

CAT_COPY = {
    "business": {
        "quality": (
            "A business deck earns its screen time in the first two minutes. Put the recommendation "
            "on slide two, keep one idea per slide, and push supporting detail into an appendix. The "
            "layouts here follow that order, so you can drop your own content in without rebuilding "
            "the structure from scratch."),
    },
    "marketing": {
        "quality": (
            "Marketing decks usually carry two kinds of content, the story and the numbers, and they "
            "read badly when mixed. Keep the campaign narrative on one set of slides and the KPI "
            "evidence on another, and put the channel result before the explanation of how you got "
            "it. The layouts here keep those two tracks separate by default."),
    },
    "startup": {
        "quality": (
            "Investors spend under three minutes on the first pass. Keep one claim per slide, put the "
            "metric that proves it in the headline, and leave the detail for an appendix. The layouts "
            "here are sized for that habit: large headline, one chart, short caption, nothing else "
            "competing for attention."),
    },
    "sales": {
        "quality": (
            "A proposal deck is read, not presented. Write for the person who opens it on a phone at "
            "9pm: short headlines, price on one page, next step on the last one. The layouts here "
            "keep to that rule, so the buyer never has to hunt for the number they actually care "
            "about."),
    },
}

GUIDE_STEPS = [
    "Download the .pptx and open it in PowerPoint, or upload it to Google Slides with "
    "File &rarr; Import slides. Layouts and theme colours come through on both.",
    "Replace the placeholder copy. Every headline, caption and number is a normal text box, so "
    "you can restyle a single slide without breaking the rest of the deck.",
    "Apply your brand colours from Design &rarr; Variants &rarr; Colors. The deck is built on a "
    "handful of theme colours, so one click recolours every slide consistently.",
    "Swap the images with right-click &rarr; Change Picture and keep the crop. Placeholders are "
    "sized for 16:9, so replacements fill the frame without shifting the layout.",
    "Delete the slides you do not need, duplicate a layout for extra content, then export to PDF "
    "if you are sending the deck ahead of the meeting.",
]

READING = {
    "business": [("/blog/how-to-create-a-business-presentation/",
                  "How to structure a business presentation"),
                 ("/blog/how-to-structure-a-quarterly-business-review/",
                  "Structuring a quarterly business review")],
    "marketing": [("/blog/what-to-include-in-a-marketing-report/",
                   "What to include in a marketing report"),
                  ("/blog/how-to-create-a-business-presentation/",
                   "How to structure a business presentation")],
    "startup": [("/blog/how-to-make-a-pitch-deck/", "How to make a pitch deck"),
                ("/blog/investor-pitch-deck-slides/", "The slides investors expect to see")],
    "sales": [("/blog/how-to-write-a-sales-proposal/", "How to write a sales proposal"),
              ("/blog/how-to-write-a-project-proposal/",
               "Writing a project proposal that gets approved")],
}


def faq_pairs(title):
    """Visible FAQ + schema share one source so rich results never mismatch."""
    return [
        ("Is the %s really free?" % title,
         "Yes. Download the .pptx directly, with no signup, no email and no watermark. It is free "
         "for personal and commercial use, including client work. The only restriction is that you "
         "cannot resell or redistribute the template file itself."),
        ("Does the %s work in Google Slides?" % title,
         "Yes. Upload the .pptx to Google Drive and open it with Google Slides; layouts, fonts and "
         "colours stay editable. If the deck uses a typeface Google does not host, swap it for a "
         "Google font from the toolbar and the layout holds."),
        ("Can I use the %s for client work?" % title,
         "Yes. Commercial use is allowed, and you can change the copy, colours and imagery freely. "
         "What you may not do is sell the file as a template product or bundle it into a paid "
         "template pack."),
        ("Do I need design skills to edit the %s?" % title,
         "No. Every slide is built from standard shapes and text boxes on a 16:9 canvas, so editing "
         "means typing over text and picking theme colours. If you can use PowerPoint or Google "
         "Slides at all, you can finish this deck."),
    ]


# Placeholder fragments that tail real slide titles, e.g. "Revenue X X% X".
_PLACEHOLDER = re.compile(
    r"^(?:[xX](?:%|\+)?|x[mk]|[nN]|%|\+?[\d.,]+\s?%?|\d{1,2}|currency|currency\s?\w+|"
    r"\$[\d.,]+\s?[a-zA-Z]?|[Xx]\.[Xx])$")


def clean_title(t):
    t = html.unescape(re.sub(r"\s+", " ", t or "")).strip()
    t = re.sub(r"\{\{|\}\}", "", t).strip(" :-")
    toks = t.split()
    while toks and _PLACEHOLDER.match(toks[-1].strip(".,;:")):
        toks.pop()
    return " ".join(toks).strip(" -:|")


def slide_outline(path, limit=8):
    """Read the real slide titles out of a .pptx so the outline printed on the
    page is what actually ships in the file. Returns (slide_count, titles)."""
    try:
        z = zipfile.ZipFile(path)
    except Exception:
        return 0, []
    names = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
    names.sort(key=lambda s: int(re.search(r"(\d+)\.xml$", s).group(1)))
    out = []
    for name in names:
        x = z.read(name).decode("utf-8", "ignore")
        runs = []
        for blk in re.findall(r"<a:r>(.*?)</a:r>", x, re.S):
            size = re.search(r'sz="(\d+)"', blk)
            txt = re.search(r"<a:t>(.*?)</a:t>", blk, re.S)
            if txt and txt.group(1).strip():
                runs.append((int(size.group(1)) if size else 0, txt.group(1)))
        if not runs:
            continue
        biggest = max(r[0] for r in runs)
        best = clean_title(" ".join(t for s, t in runs if s == biggest))
        if len(best) < 3 or best.lower() in [o.lower() for o in out]:
            continue
        out.append(best[:70])
        if len(out) >= limit:
            break
    return len(names), out


def section_html(it):
    """Builds the long-form body sections for one detail page."""
    cat = it["cat"]
    copy = CAT_COPY[cat]
    n = it.get("slides_n") or 0
    outline = it.get("outline") or []
    if outline:
        inside = "".join("<li>%s</li>" % b for b in outline)
        lead = (
            "This deck ships with %d slides on a 16:9 canvas. The outline below is read straight "
            "from the source file, so the sections listed here are the sections you get after "
            "download - the five previews above are the opening slides. Anything shown in double "
            "curly brackets is placeholder copy waiting for your own text." % n)
    else:
        inside = "".join("<li>%s</li>" % b for b in (
            "A cover slide you can rebrand in one click",
            "Section dividers and an agenda slide",
            "Content layouts for text, comparison and timelines",
            "A closing slide with next steps"))
        lead = ("This deck is built from editable layouts on a 16:9 canvas, so it can be adapted to "
                "your own content without rebuilding the structure.")
    steps = "".join("<li>%s</li>" % s for s in GUIDE_STEPS)
    faq = faq_pairs(it["title"])
    faq_html = "".join(
        '<div class="faq-item"><h3>%s</h3><p>%s</p></div>' % (q, a) for q, a in faq)
    reading = "".join('<li><a href="%s">%s</a></li>' % (u, t) for u, t in READING[cat])
    facts = [
        ("Format", "Microsoft PowerPoint (.pptx) — also opens in Google Slides and Keynote"),
        ("Slides", ("%d slides, 16:9 widescreen" % n) if n else "16:9 widescreen canvas"),
        ("File size", it["size"] or "under 10 MB"),
        ("Editing", "Standard shapes and text boxes, no locked master slides"),
        ("Licence", "Free for personal and commercial use, no attribution required"),
        ("Download", "Direct .pptx, no account or email address needed"),
    ]
    facts_html = "".join("<li><b>%s</b><span>%s</span></li>" % f for f in facts)
    return dict(inside=inside, steps=steps, faq=faq_html, reading=reading,
                facts=facts_html, lead=lead, quality=copy["quality"])

CAT_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{page_title}</title>
<meta name="description" content="{meta_desc}" />
<meta name="keywords" content="{label} presentation templates, free {low} ppt template, {label} powerpoint template, {label} slide deck, free google slides template" />
<meta property="og:title" content="{seo_title}" />
<meta property="og:description" content="{meta_desc}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{site}/templates/{cat}/" />
<meta property="og:image" content="{ogimg}" />
<link rel="canonical" href="{site}/templates/{cat}/" />
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{seo_title}" />
<meta name="twitter:description" content="{meta_desc}" />
<meta name="twitter:image" content="{ogimg}" />
<link rel="stylesheet" href="/assets/style.css?v={cssver}" />
{schema}
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6730005742175239" crossorigin="anonymous"></script>
</head>
<body>
<header class="site-header">
  <div class="container nav">
    <a class="brand" href="/">Slide<span>Vault</span></a>
    <nav>
      <a href="/#templates">Templates</a>
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
<main class="container cat-page">
  <p class="crumbs"><a href="/">Home</a> / <a href="/#templates">Templates</a> / <b>{label}</b></p>
  <header class="cat-hero">
    <h1>{h1}</h1>
    <p class="cat-lead">{lead}</p>
    <p class="cat-stats"><b>{n}</b> templates &middot; PowerPoint &amp; Google Slides &middot; 100% free &middot; no signup</p>
  </header>

  <div class="grid">{cards}</div>

  <section class="prose">
    <h2>How to choose a {low} template</h2>
    <p>{howto}</p>
    <p>{hub_intro} Every file is a standard .pptx, so you can open it in PowerPoint, Google Slides or Keynote and edit freely. If you only need one deck, downloading directly from any template page is faster than browsing.</p>
  </section>

  <section class="cat-switch">
    <h2>Browse other categories</h2>
    <div class="cat-chips">{chips}</div>
  </section>

  <section class="lead-magnet">
    <h2>Get the full free template bundle</h2>
    <p>Join our list and we will send every Slide Vault deck in one drop, plus new releases.</p>
    <form action="/subscribe" method="POST" class="subscribe compact">
      <input type="hidden" name="source" value="cat_{cat}" />
      <input type="email" name="email" placeholder="you@company.com" required />
      <button class="btn btn-primary" type="submit">Send me the bundle</button>
      <input type="text" name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true" />
    </form>
    <p class="hint">No spam. Unsubscribe anytime. Stored only in our Cloudflare account.</p>
  </section>
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
      <a href="/blog/">Blog</a>
      <a href="/tools/">PPT Tools</a>
      <a href="/about/">About</a>
      <a href="/contact/">Contact</a>
      <a href="/privacy/">Privacy</a>
    </div>
  </div>
  <div class="container"><p class="hint copyright">&copy; 2026 SLIDE VAULT &middot; Hosted statically on Cloudflare Pages.</p></div>
</footer>
<script src="/assets/nav.js?v=1" defer></script>
</body>
</html>
"""


def build_category_pages(items):
    """Emit /templates/<cat>/ hub pages. Returns list of sitemap tuples."""
    by_cat = {}
    for it in items:
        by_cat.setdefault(it["cat"], []).append(it)

    out = []
    for cat, label, seo_title, h1, meta_desc, lead, howto, hub_intro in CATS:
        group = by_cat.get(cat, [])
        if not group:
            continue

        elems = [{"@type": "ListItem", "position": i + 1,
                  "name": t["title"], "url": "%s/templates/%s/" % (SITE, t["slug"])}
                 for i, t in enumerate(group)]
        lp = {"@context": "https://schema.org", "@type": "CollectionPage",
              "name": h1, "description": meta_desc,
              "url": "%s/templates/%s/" % (SITE, cat),
              "mainEntity": {"@type": "ItemList", "numberOfItems": len(group),
                             "itemListElement": elems}}
        faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": "Are these %s templates really free?" % label.lower(),
             "acceptedAnswer": {"@type": "Answer", "text":
                                "Yes. Every template on Slide Vault is free for personal and commercial use. Download the .pptx directly, no signup, no watermark and no attribution required."}},
            {"@type": "Question", "name": "Do these %s templates work in Google Slides?" % label.lower(),
             "acceptedAnswer": {"@type": "Answer", "text":
                                "Yes. Open the .pptx in Google Slides and all layouts, fonts and colours stay editable. The same files also work in PowerPoint 2016 or later, and in Keynote after conversion."}},
            {"@type": "Question", "name": "Can I use a %s template for client work?" % label.lower(),
             "acceptedAnswer": {"@type": "Answer", "text":
                                "Yes. Commercial use is allowed, including client projects and paid presentations. You may not resell or redistribute the template files themselves as a template product."}}]}
        schema = ('<script type="application/ld+json">\n%s\n</script>\n'
                  '<script type="application/ld+json">\n%s\n</script>' % (
                      json.dumps(lp, ensure_ascii=False, indent=1),
                      json.dumps(faq, ensure_ascii=False, indent=1)))

        chips = ['<a class="chip" href="/#templates">All templates</a>']
        for c2, l2, *_ in CATS:
            if c2 == cat:
                continue
            chips.append('<a class="chip" href="/templates/%s/">%s templates</a>' % (c2, l2))

        html = CAT_PAGE.format(
            seo_title=seo_title,
            page_title=(seo_title + " | Slide Vault") if len(seo_title) <= 52 else seo_title,
            h1=h1, meta_desc=meta_desc, lead=lead,
            howto=howto, hub_intro=hub_intro, label=label, low=label.lower(),
            cat=cat, site=SITE, n=len(group), cssver=CSS_VER,
            ogimg=SITE + group[0]["img"] if group[0]["img"] else SITE + "/assets/favicon.svg",
            schema=schema,
            cards="".join(card(t) for t in group),
            chips="".join(chips))

        d = os.path.join(ROOT, "templates", cat)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
        out.append(("/templates/%s/" % cat, "0.9", "weekly"))
        print("  category hub /templates/%s/  (%d templates)" % (cat, len(group)))
    return out


def file_size(slug_file):
    p = os.path.join(ROOT, "files", slug_file)
    if not os.path.exists(p):
        return ""
    mb = os.path.getsize(p) / 1048576.0
    return "%.1f MB" % mb if mb >= 1 else "%d KB" % (os.path.getsize(p) / 1024)


def card(t):
    """Matches the markup assets/app.js renders on the homepage, so .card/.thumb/.body
    styles apply identically instead of raw full-size images."""
    thumb = ('<img class="thumb" src="%s" alt="%s preview" loading="lazy" />' % (t["img"], t["title"])) \
        if t["img"] else '<div class="thumb thumb-fallback"></div>'
    return ('<article class="card">' + thumb +
            '<div class="body">' +
            '<span class="tag">' + t["tag"] + "</span>" +
            "<h3>" + t["title"] + "</h3>" +
            '<div class="actions"><a class="btn btn-primary" href="/templates/' + t["slug"] + '/">View</a></div>' +
            "</div>" +
            "</article>")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resize", action="store_true", help="downscale photos wider than %dpx" % MAX_WIDTH)
    args = ap.parse_args()

    items = parse_catalog()

    print("scanning gallery photos...")
    for it in items:
        it["img"] = abspath(it["img"])
        it["gallery"] = scan_gallery(it["slug"], resize=args.resize)
        # no photos yet -> fall back to the cover image so pages never look broken
        if not it["gallery"] and it["img"]:
            it["gallery"] = [it["img"]]
        if it["gallery"]:
            print("  %-52s %d image(s)" % (it["slug"], len(it["gallery"])))

    write_catalog(items)

    for it in items:
        related = [t for t in items if t["cat"] == it["cat"] and t["slug"] != it["slug"]]
        if len(related) < 3:
            extra = [t for t in items
                     if t["slug"] not in [r["slug"] for r in related] and t["slug"] != it["slug"]]
            related += extra
        related = related[:3]

        thumbs = "".join(
            '<button class="gallery-thumb%s" type="button" data-src="%s" aria-label="Slide %d">'
            '<img src="%s" alt="%s slide %d" loading="lazy" /></button>'
            % (" active" if i == 0 else "", src, i + 1, src, it["title"], i + 1)
            for i, src in enumerate(it["gallery"]))

        n = len(it["gallery"])
        stage_inner = (
            '<img class="gallery-main" src="%s" alt="%s slide 1" />' % (it["gallery"][0], it["title"])
            if it["gallery"]
            else '<div class="gallery-empty">Preview coming soon</div>')

        kw = "%s, %s, %s, free %s template, free ppt template, free powerpoint template, google slides template" % (
            it["seo"].replace("—", ","), it["title"], it["tag"], it["tag"].lower())

        size = file_size(it["file"])
        it["size"] = size
        it["slides_n"], it["outline"] = slide_outline(
            os.path.join(ROOT, "files", it["file"]))
        sec = section_html(it)
        faq_schema = '<script type="application/ld+json">\n%s\n</script>' % json.dumps(
            {"@context": "https://schema.org", "@type": "FAQPage",
             "mainEntity": [{"@type": "Question", "name": q,
                             "acceptedAnswer": {"@type": "Answer", "text": a}}
                            for q, a in faq_pairs(it["title"])]}, ensure_ascii=False)

        html = PAGE.format(
            title=it["title"], seo=it["seo"], page_title=(it["seo"] + " | Slide Vault")
                     if len(it["seo"]) <= 52 else it["seo"],
            desc=it["desc"], body=it["body"],
            kw=kw, slug=it["slug"], site=SITE, cat=it["cat"],
            tag=it["tag"], cat_label=it["cat"].capitalize(), low=it["cat"], file=it["file"], cssver=CSS_VER,
            size=size, faq_schema=faq_schema,
            lead=sec["lead"], inside=sec["inside"], quality=sec["quality"],
            steps=sec["steps"], facts=sec["facts"], faq=sec["faq"], reading=sec["reading"],
            slide_count='<span class="tag slides">%d slides</span>' % it["slides_n"]
                        if it["slides_n"] > 1 else "",
            ogimg=(SITE + it["gallery"][0]) if it["gallery"] else "",
            stage_inner=stage_inner,
            thumbs=thumbs,
            related="".join(card(t) for t in related))

        d = os.path.join(ROOT, "templates", it["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)

    # sitemap -- keep in sync with gen_blog.py so running either one alone
    # never drops URLs (blog posts and tools pages are discovered dynamically)
    urls = [("/", "1.0", "weekly"), ("/blog/", "0.8", "weekly"),
            ("/about/", "0.4", "yearly"), ("/contact/", "0.4", "yearly"),
            ("/privacy/", "0.3", "yearly")]
    urls += build_category_pages(items)
    urls += [("/templates/%s/" % it["slug"], "0.8", "monthly") for it in items]
    # free browser tools (tools/<name>/index.html)
    tools_dir = os.path.join(ROOT, "tools")
    if os.path.isdir(tools_dir):
        if os.path.isfile(os.path.join(tools_dir, "index.html")):
            urls.append(("/tools/", "0.8", "monthly"))
        for name in sorted(os.listdir(tools_dir)):
            if os.path.isfile(os.path.join(tools_dir, name, "index.html")):
                urls.append(("/tools/%s/" % name, "0.8", "monthly"))
    blog_dir = os.path.join(ROOT, "blog", "posts")
    if os.path.isdir(blog_dir):
        posts = sorted(f[:-3] for f in os.listdir(blog_dir) if f.endswith(".md"))
        urls += [("/blog/%s/" % p, "0.7", "monthly") for p in posts]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, p, f in urls:
        sm.append("  <url><loc>%s%s</loc><changefreq>%s</changefreq><priority>%s</priority></url>"
                  % (SITE, u, f, p))
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")

    total = sum(len(it["gallery"]) for it in items)
    print("\ndone: %d detail pages | %d images total | %d sitemap urls"
          % (len(items), total, len(urls)))


if __name__ == "__main__":
    main()
