#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renders the Slide Vault blog from markdown sources.

  1. Write posts in  blog/posts/<slug>.md  (front matter: title, description,
     date, image — all required except image)
  2. Run:  python3 tools/gen_blog.py

Each post becomes /blog/<slug>/index.html styled like the rest of the site,
plus /blog/index.html listing every post. The sitemap is rebuilt to include
blog URLs, so after editing templates run gen_pages.py first, then this one.
"""
import json
import os
import re
import sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://slidevaulte.com"
POSTS_DIR = os.path.join(ROOT, "blog", "posts")

HEADER = """<header class="site-header">
  <div class="container nav">
    <a class="brand" href="/">Slide<span>Vault</span></a>
    <nav>
      <a href="/#templates">Templates</a>
      <a href="/blog/">Blog</a>
      <a href="/tools/merge-ppt/">Merge PPT</a>
      <a href="/tools/compress-ppt/">Compress PPT</a>
      <a href="/tools/split-ppt/">Split PPT</a>
      <a href="/about/">About</a>
      <a class="btn btn-ghost" href="/#subscribe">Subscribe</a>
    </nav>
  </div>
</header>"""

FOOTER = """<footer class="site-footer">
  <div class="container foot">
    <div>
      <b>Slide<span>Vault</span></b>
      <p class="hint">Free PowerPoint &amp; Google Slides templates for business and education.</p>
    </div>
    <div class="foot-links">
      <a href="/#templates">Templates</a>
      <a href="/blog/">Blog</a>
      <a href="/tools/merge-ppt/">Merge PPT</a>
      <a href="/tools/compress-ppt/">Compress PPT</a>
      <a href="/tools/split-ppt/">Split PPT</a>
      <a href="/about/">About</a>
      <a href="/contact/">Contact</a>
      <a href="/privacy/">Privacy</a>
      <a href="https://tools.slidevaulte.com/">Drainage Calculators</a>
    </div>
  </div>
  <div class="container"><p class="hint copyright">&copy; 2026 SLIDE VAULT &middot; Hosted statically on Cloudflare Pages.</p></div>
</footer>"""

POST_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title} | Slide Vault Blog</title>
<meta name="description" content="{desc}" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{desc}" />
<meta property="og:type" content="article" />
<meta property="og:url" content="{site}/blog/{slug}/" />
<meta property="og:image" content="{image}" />
<meta property="article:published_time" content="{date}" />
<link rel="canonical" href="{site}/blog/{slug}/" />
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{desc}" />
<meta name="twitter:image" content="{image}" />
<link rel="stylesheet" href="/assets/style.css?v=2" />
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6730005742175239" crossorigin="anonymous"></script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BlogPosting","headline":"{title}","description":"{desc}","image":"{image}","datePublished":"{date}","dateModified":"{date}","author":{{"@type":"Organization","name":"Slide Vault","url":"{site}/"}},"publisher":{{"@type":"Organization","name":"Slide Vault","url":"{site}/"}},"mainEntityOfPage":{{"@type":"WebPage","@id":"{site}/blog/{slug}/"}}}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"{site}/"}},{{"@type":"ListItem","position":2,"name":"Blog","item":"{site}/blog/"}},{{"@type":"ListItem","position":3,"name":"{title}"}}]}}
</script>
</head>
<body>
{header}
<main class="container detail">
  <p class="crumbs"><a href="/blog/">Blog</a> / <b>{title}</b></p>
  <h1>{title}</h1>
  <div class="meta-row"><span class="tag">{date}</span><span class="tag cat">{minutes} min read</span></div>
  <section class="prose blog-post">
{content}
  </section>
  <section class="prose">
    <h2>Get the free templates</h2>
    <p>Every template mentioned here is free to download and works with PowerPoint and Google Slides.</p>
    <div class="detail-actions"><a class="btn btn-primary" href="/#templates">Browse all free templates</a><a class="btn btn-ghost" href="/blog/">More guides</a></div>
  </section>
</main>
{footer}
</body>
</html>
"""

INDEX_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Blog — Presentation Tips &amp; Guides | Slide Vault</title>
<meta name="description" content="Practical guides on building business presentations, pitch decks and reports. Every guide pairs with a free PowerPoint template." />
<meta property="og:title" content="Slide Vault Blog — Presentation Tips &amp; Guides" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{site}/blog/" />
<link rel="canonical" href="{site}/blog/" />
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg" />
<link rel="stylesheet" href="/assets/style.css?v=2" />
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6730005742175239" crossorigin="anonymous"></script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Blog","name":"Slide Vault Blog","url":"{site}/blog/","description":"Presentation tips, pitch deck guides and report writing templates."}}
</script>
</head>
<body>
{header}
<main class="container detail">
  <p class="crumbs"><a href="/">Home</a> / <b>Blog</b></p>
  <h1>Blog</h1>
  <p class="hint">Practical guides on presentations, pitch decks and reports &mdash; each one pairs with a free, editable template.</p>
  <div class="blog-list">
{cards}
  </div>
</main>
{footer}
</body>
</html>
"""


def parse_post(path):
    src = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", src, re.S)
    if not m:
        sys.exit("!! missing front matter: %s" % path)
    meta, body = m.group(1), m.group(2)
    info = dict(re.findall(r"^(\w+):\s*(.+)$", meta, re.M))
    for key in ("title", "description", "date"):
        if key not in info:
            sys.exit("!! %s missing '%s' front matter" % (path, key))
    info["slug"] = os.path.basename(path)[:-3]
    info["html"] = markdown.markdown(body, extensions=["extra", "sane_lists"])
    return info


def parse_templates():
    src = open(os.path.join(ROOT, "assets", "templates.js"), encoding="utf-8").read()
    return [(s, t) for s, t in re.findall(
        r'\{\s*slug:\s*"([^"]+)",\s*title:\s*"([^"]+)"', src)]


def main():
    files = sorted(f for f in os.listdir(POSTS_DIR) if f.endswith(".md"))
    if not files:
        sys.exit("!! no posts in blog/posts/")

    os.makedirs(os.path.join(ROOT, "blog"), exist_ok=True)
    posts = [parse_post(os.path.join(POSTS_DIR, f)) for f in files]
    posts.sort(key=lambda p: p["date"], reverse=True)
    tpl_slugs = {s for s, _ in parse_templates()}

    for p in posts:
        # check internal template links point at real pages
        for linked in re.findall(r'href="%s/templates/([^/"]+)/"' % SITE, p["html"]):
            if linked not in tpl_slugs:
                print("  WARN: %s links to unknown template '%s'" % (p["slug"], linked))

        minutes = max(2, len(re.findall(r"\w+", p["html"])) // 200)
        image = p.get("image", SITE + "/assets/favicon.svg")
        html = POST_PAGE.format(
            title=p["title"], desc=p["description"], slug=p["slug"],
            site=SITE, date=p["date"], minutes=minutes, image=image,
            content=p["html"], header=HEADER, footer=FOOTER)
        d = os.path.join(ROOT, "blog", p["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
        print("  post  %-45s %s" % (p["slug"], p["date"]))

    cards = []
    for p in posts:
        img = p.get("image")
        thumb = ('<a class="blog-row-thumb" href="/blog/%s/" aria-hidden="true"><img src="%s" alt="" loading="lazy" /></a>'
                 % (p["slug"], img)) if img else '<div class="blog-row-thumb blog-row-fallback"></div>'
        cards.append(
            '<article class="blog-row">' + thumb +
            '<div class="blog-row-body">'
            '<time class="blog-date" datetime="%s">%s</time>'
            '<h3><a href="/blog/%s/">%s</a></h3>'
            '<p>%s</p>'
            '<span class="blog-more">Read the guide &rarr;</span>'
            '</div></article>' % (p["date"], p["date"], p["slug"], p["title"], p["description"]))
    open(os.path.join(ROOT, "blog", "index.html"), "w", encoding="utf-8").write(
        INDEX_PAGE.format(site=SITE, header=HEADER, footer=FOOTER,
                          cards="\n".join(cards)))
    print("  index blog/index.html (%d posts)" % len(posts))

    # ---- rebuild full sitemap (templates + blog + static) ----
    urls = [("/", "1.0", "weekly"), ("/blog/", "0.8", "weekly"),
            ("/about/", "0.4", "yearly"), ("/contact/", "0.4", "yearly"),
            ("/tools/merge-ppt/", "0.8", "monthly"), ("/tools/compress-ppt/", "0.8", "monthly"), ("/tools/split-ppt/", "0.8", "monthly"), ("/privacy/", "0.3", "yearly")]
    urls += [("/templates/%s/" % s, "0.8", "monthly") for s, _ in parse_templates()]
    urls += [("/blog/%s/" % p["slug"], "0.7", "monthly") for p in posts]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pri, freq in urls:
        sm.append("  <url><loc>%s%s</loc><changefreq>%s</changefreq><priority>%s</priority></url>"
                  % (SITE, u, freq, pri))
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")
    print("  sitemap rebuilt: %d urls" % len(urls))


if __name__ == "__main__":
    main()
