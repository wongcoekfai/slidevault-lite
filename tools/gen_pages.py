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
        r'\{\s*slug:\s*"([^"]+)",\s*title:\s*"([^"]+)",\s*tag:\s*"([^"]*)",\s*'
        r'cat:\s*"([^"]*)",\s*desc:\s*"([^"]*)",\s*img:\s*"([^"]*)",\s*'
        r'file:\s*"([^"]*)"', src):
        items.append(dict(zip(
            ("slug", "title", "tag", "cat", "desc", "img", "file"), m.groups())))
    if not items:
        sys.exit("!! could not parse assets/templates.js")
    return items


def write_catalog(items):
    lines = ["// Template catalog. Edit here, then run: python3 tools/gen_pages.py",
             "// gallery[] is filled automatically from assets/img/gallery/<slug>/"]
    for it in items:
        lines.append(
            '  { slug: "%s", title: "%s", tag: "%s", cat: "%s", desc: "%s", img: "%s", file: "%s", gallery: [%s] },'
            % (it["slug"], it["title"], it["tag"], it["cat"], it["desc"], it["img"],
               it["file"], ", ".join('"%s"' % g for g in it["gallery"])))
    open(os.path.join(ROOT, "assets", "templates.js"), "w", encoding="utf-8").write(
        "window.TEMPLATES = [\n" + "\n".join(lines) + "\n];\n")


# ---------------------------------------------------------------- detail page

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title} — Free PowerPoint Template | Slide Vault</title>
<meta name="description" content="{desc}" />
<meta name="keywords" content="{kw}" />
<meta property="og:title" content="{title} — Free PowerPoint Template" />
<meta property="og:description" content="{desc}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{site}/templates/{slug}/" />
<meta property="og:image" content="{ogimg}" />
<link rel="canonical" href="{site}/templates/{slug}/" />
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title} — Free PowerPoint Template" />
<meta name="twitter:description" content="{desc}" />
<meta name="twitter:image" content="{ogimg}" />
<link rel="stylesheet" href="/assets/style.css?v=2" />
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"SoftwareApplication","name":"{title}","url":"{site}/templates/{slug}/","description":"{desc}","image":"{ogimg}","applicationCategory":"BusinessApplication","operatingSystem":"Any","offers":{{"@type":"Offer","price":"0","priceCurrency":"USD"}}}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"{site}/"}},{{"@type":"ListItem","position":2,"name":"Templates","item":"{site}/#templates"}},{{"@type":"ListItem","position":3,"name":"{title}"}}]}}
</script>

<!-- ===== Monetization: Google AdSense =====
     AdSense publisher ID configured: ca-pub-6730005742175239 (from AdSense Account Information).
     Enable "Auto Ads" in the AdSense dashboard — ads are placed automatically, no unit IDs needed. -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6730005742175239" crossorigin="anonymous"></script>

<!-- FAQ rich result: captures long-tail queries like "is X free?" / "does X work in Google Slides?" -->
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{{"@type":"Question","name":"Is the {title} free?","acceptedAnswer":{{"@type":"Answer","text":"Yes. This template is 100% free for personal and commercial use. Download the .pptx, no signup required."}}}},{{"@type":"Question","name":"Does the {title} work in Google Slides?","acceptedAnswer":{{"@type":"Answer","text":"Yes. Open the .pptx in Google Slides and all layouts, fonts and colors stay fully editable."}}}}]}}
</script>
</head>
<body>
<header class="site-header">
  <div class="container nav">
    <a class="brand" href="/">Slide<span>Vault</span></a>
    <nav>
      <a href="/#templates">Templates</a>
      <a href="/blog/">Blog</a>
      <a href="/#faq">FAQ</a>
      <a href="/#about">About</a>
      <a class="btn btn-ghost" href="/#subscribe">Subscribe</a>
    </nav>
  </div>
</header>
<main class="container detail">
  <p class="crumbs"><a href="/#templates">Templates</a> / {cat_label} / <b>{title}</b></p>
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
    <p>Works with <b>PowerPoint</b> and <b>Google Slides</b>. Fully editable - change colors, fonts, text and images freely. Free for personal and commercial use.</p>
  </section>
  <section class="prose">
    <h2>Related templates</h2>
    <div class="grid related">{related}</div>
  </section>
</main>

<div class="lightbox" id="lightbox" hidden>
  <button class="lightbox-close" type="button" aria-label="Close">&#215;</button>
  <button class="lightbox-nav prev" type="button" aria-label="Previous">&#8249;</button>
  <img src="" alt="" />
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
      <a href="/blog/">Blog</a>
      <a href="/tools/merge-ppt/">Merge PPT</a>
      <a href="/#faq">FAQ</a>
      <a href="/#subscribe">Subscribe</a>
      <a href="/privacy/">Privacy</a>
        <a href="https://tools.slidevaulte.com/">Drainage Calculators</a>
    </div>
  </div>
  <div class="container"><p class="hint copyright">&copy; 2026 SLIDE VAULT &middot; Hosted statically on Cloudflare Pages.</p></div>
</footer>
<script src="/assets/gallery.js"></script>
<script>
fetch('/downloads?file={file}').then(r=>r.json()).then(d=>{{
  var el=document.getElementById('dl-count');
  if(el&&typeof d.count==='number'&&d.count>0) el.textContent=d.count+' downloads';
}}).catch(()=>{{}});
</script>
</body>
</html>
"""


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

        kw = "%s, %s, %s, free ppt template, free powerpoint template, download ppt free, google slides template" % (
            it["title"], it["tag"], it["cat"].capitalize())

        html = PAGE.format(
            title=it["title"], desc=it["desc"], kw=kw, slug=it["slug"], site=SITE,
            tag=it["tag"], cat_label=it["cat"].capitalize(), file=it["file"],
            size=file_size(it["file"]),
            slide_count='<span class="tag slides">%d slides</span>' % n if n > 1 else "",
            ogimg=(SITE + it["gallery"][0]) if it["gallery"] else "",
            stage_inner=stage_inner,
            thumbs=thumbs,
            related="".join(card(t) for t in related))

        d = os.path.join(ROOT, "templates", it["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)

    # sitemap
    urls = [("/", "1.0", "weekly"), ("/privacy/", "0.3", "yearly")]
    urls += [("/templates/%s/" % it["slug"], "0.8", "monthly") for it in items]
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
