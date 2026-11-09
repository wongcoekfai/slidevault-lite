#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single source of truth for sitemap.xml.

Google ignores <changefreq> and <priority> entirely, but it DOES use
<lastmod> as a crawl-scheduling signal (developers.google.com, 2023-06).
So every URL gets a real lastmod derived from git history -- never from the
clock at generation time, which would make all 85 pages look "modified today"
on every rebuild and eventually get ignored.

  python3 tools/sitemap.py          # refresh lastmod against current sitemap
  from sitemap import write_sitemap # called by gen_pages.py / gen_blog.py

rows are (path, priority, changefreq) tuples, e.g. ("/blog/", "0.8", "weekly").
"""
import datetime
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://slidevaulte.com"
SITEMAP = os.path.join(ROOT, "sitemap.xml")

# Aggregated pages also change when the catalog changes, even if the HTML
# template itself did not. Track those dependencies for an honest lastmod.
EXTRA_DEPS = {
    "": ["assets/templates.js", "assets/app.js"],
    "blog": ["assets/templates.js"],
    "tools": ["assets/templates.js"],
}


def git_file_times():
    """Map repo-relative path -> timestamp of its most recent commit."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--format=@@%ct", "--name-only", "--no-renames"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return {}
    stamp, times = None, {}
    for line in out.splitlines():
        if line.startswith("@@"):
            stamp = int(line[2:])
        elif stamp and line.strip():
            path = line.strip()
            # git log is newest-first, so the first sighting is the latest change
            times.setdefault(path, stamp)
    return times


def lastmod(path, times):
    """Last significant modification of a URL, as YYYY-MM-DD (or None)."""
    rel = path.strip("/")
    candidates = [os.path.join(rel, "index.html") if rel else "index.html"]
    candidates += EXTRA_DEPS.get(rel, [])
    best = 0
    for relp in candidates:
        ts = times.get(relp)
        if ts is None:
            full = os.path.join(ROOT, relp)
            if os.path.isfile(full):
                ts = int(os.path.getmtime(full))
        if ts:
            best = max(best, ts)
    if not best:
        return None
    return datetime.datetime.fromtimestamp(best).strftime("%Y-%m-%d")


def write_sitemap(rows):
    """Write sitemap.xml for rows; returns number of URLs written."""
    times = git_file_times()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    seen = set()
    count = 0
    for path, priority, freq in rows:
        if path in seen:
            continue
        seen.add(path)
        lm = lastmod(path, times)
        lm_xml = "<lastmod>%s</lastmod>" % lm if lm else ""
        lines.append("  <url><loc>%s%s</loc>%s<changefreq>%s</changefreq>"
                     "<priority>%s</priority></url>"
                     % (SITE, path, lm_xml, freq, priority))
        count += 1
    lines.append("</urlset>")
    with open(SITEMAP, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return count


def main():
    """Refresh lastmod in place without regenerating any HTML pages."""
    xml = open(SITEMAP, encoding="utf-8").read()
    rows = []
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>.*?slidevaulte\.com(/[^<]*)</loc>", block, re.S)
        if not loc:
            continue
        freq = re.search(r"<changefreq>(.*?)</changefreq>", block)
        pri = re.search(r"<priority>(.*?)</priority>", block)
        rows.append((loc.group(1), pri.group(1) if pri else "0.8",
                     freq.group(1) if freq else "weekly"))
    n = write_sitemap(rows)
    dated = len(re.findall(r"<lastmod>", open(SITEMAP, encoding="utf-8").read()))
    print("sitemap.xml: %d urls, %d with lastmod" % (n, dated))


if __name__ == "__main__":
    main()
