#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Submit every URL in sitemap.xml to IndexNow (Bing, Yandex, Seznam, Naver).

IndexNow is the fastest way to get a new page crawled outside Google: Bing
usually picks URLs up within hours instead of weeks. The key file must already
be live at https://<host>/<key>.txt, so run this AFTER the Cloudflare Pages
deploy finishes.

  python3 tools/indexnow.py              # submit all sitemap URLs
  python3 tools/indexnow.py <url> [...]  # submit specific URLs
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://slidevaulte.com"
HOST = "slidevaulte.com"
KEY = "158171d905a750c97cbc1b2b09f6957b"   # filename must match: <key>.txt at site root
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls():
    xml = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    return re.findall(r"<loc>(.*?)</loc>", xml)


def submit(urls):
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": "%s/%s.txt" % (SITE, KEY),
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=data,
        headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", "ignore")


def main():
    urls = sys.argv[1:] or sitemap_urls()
    print("submitting %d urls to IndexNow (host %s)" % (len(urls), HOST))
    for i in range(0, len(urls), 100):        # API accepts up to 10k per call
        chunk = urls[i:i + 100]
        code, body = submit(chunk)
        print("  batch %d: HTTP %s %s" % (i // 100 + 1, code, body.strip()[:120]))
    print("done. 200/202 = accepted; 403 = key file not reachable yet.")


if __name__ == "__main__":
    main()
