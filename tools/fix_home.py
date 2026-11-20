#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rebuild the homepage ItemList JSON-LD and the static crawl-path index
from assets/templates.js. Idempotent — safe to run on every deploy.

    python3 tools/fix_home.py

Fixes:
  - itemListElement was a nested array (invalid schema.org), now flat
  - it only listed 13 templates, now all of them
  - adds a crawlable A-Z index so the 62 detail pages are reachable from
    the homepage without executing app.js
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.join(ROOT, "index.html")
CATALOG = os.path.join(ROOT, "assets", "templates.js")
SITE = "https://slidevaulte.com"

START = "<!-- ALL_TEMPLATES_INDEX_START -->"
END = "<!-- ALL_TEMPLATES_INDEX_END -->"
GRID = '<div class="grid" id="template-grid"><!-- rendered by app.js --></div>'
ITEM_RE = re.compile(r'\{\s*slug:\s*"([^"]+)",\s*title:\s*"([^"]+)"', re.S)
LD_RE = re.compile(
    r'(<script type="application/ld\+json" id="tpl-list">\s*)(.*?)(\s*</script>)', re.S)
BLOCK_RE = re.compile(
    r'(' + re.escape(START) + r')(.*?)(' + re.escape(END) + r')', re.S)


def catalog():
    src = open(CATALOG, encoding="utf-8").read()
    pairs = ITEM_RE.findall(src)
    if not pairs:
        raise SystemExit("无法从 assets/templates.js 解析模板目录")
    return pairs


def main():
    pairs = catalog()
    src = open(HOME, encoding="utf-8").read()
    s = src

    elems = [{"@type": "ListItem", "position": i + 1,
              "name": title, "url": "%s/templates/%s/" % (SITE, slug)}
             for i, (slug, title) in enumerate(pairs)]
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": "Free PPT Templates", "numberOfItems": len(elems),
          "itemListElement": elems}
    if not LD_RE.search(s):
        raise SystemExit("index.html 中找不到 id=tpl-list 的 JSON-LD 块")
    s = LD_RE.sub(lambda m: m.group(1) + json.dumps(ld, ensure_ascii=False) + m.group(3),
                  s, count=1)

    links = sorted(((html.escape(title), slug) for slug, title in pairs),
                   key=lambda x: x[0].lower())
    joined = " &middot;\n          ".join(
        '<a href="/templates/%s/">%s</a>' % (slug, title) for title, slug in links)
    content = ('\n      <details class="all-tpl-index" id="all-templates-index">\n'
               '        <summary>All %d free templates (A&ndash;Z)</summary>\n'
               '        <p class="cat-links">%s</p>\n'
               '      </details>\n      '
               '<noscript><p class="cat-links">%s</p></noscript>\n      '
               % (len(links), joined, joined))

    if GRID not in s:
        raise SystemExit("index.html 中找不到 template-grid 容器")
    if BLOCK_RE.search(s):
        s = BLOCK_RE.sub(lambda m: m.group(1) + content + m.group(3), s, count=1)
    else:
        s = s.replace(GRID, GRID + "\n      " + START + content + END, 1)

    if s != src:
        with open(HOME, "w", encoding="utf-8") as f:
            f.write(s)
    print("首页已重建：ItemList 扁平化并列出 %d 个模板；静态索引已注入" % len(elems))


if __name__ == "__main__":
    main()
