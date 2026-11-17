#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check which sitemap URLs are NOT indexed by Google.

Two modes:

1. API mode (recommended, fully automatic once authorised):
     python3 tools/index_status.py
   Uses the official GSC URL Inspection API (quota 2000/day, sitemap is ~106
   URLs). Needs a one-time OAuth consent:
     * create an OAuth client (type: Desktop app) in Google Cloud Console,
       enable the Search Console API, download the JSON as
       ~/Downloads/gsc-client-secret.json
   First run opens a browser for consent; the refresh token is stored at
   marketing/gsc-token.json and every later run is fully unattended.

2. CSV mode (no credentials, semi-automatic):
     python3 tools/index_status.py --from-csv ~/Downloads/pages-export.csv
   GSC "Pages" report reason tables export up to ~1000 example URLs per
   reason. Any CSV whose rows contain URLs works: URLs present in the export
   are treated as "known/not indexed" or "indexed" depending on which table
   you exported; the report highlights sitemap URLs missing from the export.

Output:
  marketing/not-indexed.json  machine-readable
  marketing/not-indexed.html  human-readable report with GSC inspect links
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://slidevaulte.com"
SITE_URL = "sc-domain:slidevaulte.com"
SITEMAP = os.path.join(ROOT, "sitemap.xml")
OUT_DIR = os.path.join(ROOT, "marketing")
OUT_JSON = os.path.join(OUT_DIR, "not-indexed.json")
OUT_HTML = os.path.join(OUT_DIR, "not-indexed.html")
CLIENT_SECRET = os.path.expanduser(
    os.environ.get("GSC_CLIENT_SECRET", "~/Downloads/gsc-client-secret.json"))
TOKEN_FILE = os.path.join(OUT_DIR, "gsc-token.json")
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
REDIRECT_PORT = 8791
GSC_INSPECT = ("https://search.google.com/search-console/inspect"
               "?resource_id=sc-domain%3Aslidevaulte.com&id=")

URL_RE = re.compile(r"https?://[^\s\"',<>\\]+")


def sitemap_urls():
    xml = open(SITEMAP, encoding="utf-8").read()
    return re.findall(r"<loc>(.*?)</loc>", xml)


# ---------------------------------------------------------------- OAuth ----

def load_client_secret():
    if not os.path.isfile(CLIENT_SECRET):
        return None
    d = json.load(open(CLIENT_SECRET, encoding="utf-8"))
    d = d.get("installed") or d.get("web") or d
    return d


def token_path_auth(client):
    """Installed-app OAuth via localhost loopback; stores refresh token."""
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?client_id=" + client["client_id"] +
        "&redirect_uri=" + urllib.parse.quote(
            "http://localhost:%d" % REDIRECT_PORT) +
        "&response_type=code&scope=" + urllib.parse.quote(SCOPE) +
        "&access_type=offline&prompt=consent")
    captured = {}

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            captured["code"] = (q.get("code") or [None])[0]
            captured["error"] = (q.get("error") or [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>OK - return to the terminal.</h2>")

        def log_message(self, *a):
            pass

    srv = HTTPServer(("localhost", REDIRECT_PORT), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    print("Opening browser for Google consent (one time only)...")
    print(auth_url)
    webbrowser.open(auth_url)
    try:
        while "code" not in captured and "error" not in captured:
            pass  # served by handler thread
    except KeyboardInterrupt:
        pass
    srv.shutdown()
    if captured.get("error") or not captured.get("code"):
        sys.exit("OAuth consent failed: %s" % captured.get("error", "no code"))
    data = urllib.parse.urlencode({
        "code": captured["code"],
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "redirect_uri": "http://localhost:%d" % REDIRECT_PORT,
        "grant_type": "authorization_code",
    }).encode()
    tok = json.load(urllib.request.urlopen(
        urllib.request.Request(
            "https://oauth2.googleapis.com/token", data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"})))
    tok["obtained_at"] = datetime.now(timezone.utc).isoformat()
    json.dump(tok, open(TOKEN_FILE, "w"), indent=1)
    print("Token saved:", TOKEN_FILE)
    return tok


def access_token(client):
    if os.path.isfile(TOKEN_FILE):
        tok = json.load(open(TOKEN_FILE, encoding="utf-8"))
    else:
        tok = token_path_auth(client)
    data = urllib.parse.urlencode({
        "refresh_token": tok["refresh_token"],
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "grant_type": "refresh_token",
    }).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"})))
    return r["access_token"]


# ------------------------------------------------------------- API mode ----

def inspect_all(urls, token):
    results = {}
    req_base = urllib.request.Request
    for i, u in enumerate(urls):
        body = json.dumps({
            "inspectionUrl": u, "siteUrl": SITE_URL,
            "languageCode": "en-US"}).encode()
        r = req_base(
            "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
            data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + token})
        try:
            d = json.load(urllib.request.urlopen(r, timeout=30))
            isr = d.get("inspectionResult", {}).get("indexStatusResult", {})
            results[u] = {
                "verdict": isr.get("verdict", "UNKNOWN"),
                "coverage": isr.get("coverageState", ""),
                "state": isr.get("indexingState", ""),
                "last_crawl": isr.get("lastCrawlTime", ""),
                "canonical": isr.get("googleCanonical", ""),
            }
        except Exception as e:
            results[u] = {"verdict": "ERROR", "coverage": str(e)[:120],
                          "state": "", "last_crawl": "", "canonical": ""}
        print("  %d/%d  %s -> %s" % (i + 1, len(urls), u.split("/")[-1] or "/",
                                     results[u]["verdict"]))
    return results


# ------------------------------------------------------------- CSV mode ----

def csv_urls(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    found = []
    seen = set()
    for line in txt.splitlines():
        m = URL_RE.search(line)
        if m and "slidevaulte.com" in m.group(0):
            u = m.group(0).rstrip(".,)")
            if u not in seen:
                seen.add(u)
                found.append(u)
    return found


# ---------------------------------------------------------------- report ---

def write_report(not_indexed, checked_at, mode, extra=None):
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump({
        "checked_at": checked_at, "mode": mode,
        "not_indexed": not_indexed, "extra": extra or {},
    }, open(OUT_JSON, "w"), indent=1, ensure_ascii=False)

    rows = []
    for item in not_indexed:
        u = item["url"] if isinstance(item, dict) else item
        why = item.get("coverage", "") if isinstance(item, dict) else ""
        last = item.get("last_crawl", "") if isinstance(item, dict) else ""
        rows.append(
            '<tr><td><a href="%s%s">%s</a></td><td>%s</td><td>%s</td></tr>'
            % (GSC_INSPECT, urllib.parse.quote(u, safe=""),
               html.escape(u.replace(SITE, "")) or "/",
               html.escape(why), html.escape(last[:10])))
    doc = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Not-indexed URLs - slidevaulte.com</title>
<style>body{font:15px/1.6 -apple-system,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;color:#1a1a1a}
h1{font-size:1.4rem}table{border-collapse:collapse;width:100%%}
td,th{border:1px solid #ddd;padding:6px 10px;text-align:left;font-size:.92rem}
th{background:#f5f5f5}.meta{color:#666;font-size:.9rem}</style></head>
<body><h1>Not-indexed URLs (%d)</h1>
<p class="meta">checked %s &middot; mode: %s &middot; click a URL to open GSC inspection</p>
<table><tr><th>URL</th><th>Reason / status</th><th>Last crawl</th></tr>
%s</table></body></html>""" % (len(not_indexed), checked_at, mode,
                               "\n".join(rows) or
                               '<tr><td colspan="3">All checked URLs are indexed.</td></tr>')
    open(OUT_HTML, "w", encoding="utf-8").write(doc)
    print("report:", OUT_HTML)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-csv", metavar="CSV")
    ap.add_argument("--limit", type=int, default=2000)
    args = ap.parse_args()
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    urls = sitemap_urls()

    if args.from_csv:
        known = set(csv_urls(args.from_csv))
        missing = [u for u in urls if u not in known]
        write_report(missing, checked_at, "csv:%s" % os.path.basename(args.from_csv),
                     {"csv_urls": len(known), "sitemap_urls": len(urls)})
        print("sitemap %d | export %d | not in export %d" %
              (len(urls), len(known), len(missing)))
        return

    client = load_client_secret()
    if not client:
        sys.exit("""No OAuth client found at %s.

One-time setup (about 3 minutes):
  1. https://console.cloud.google.com -> create/select a project
  2. APIs & Services -> Library -> enable "Search Console API"
  3. APIs & Services -> Credentials -> Create credentials ->
     OAuth client ID -> Application type: Desktop app
  4. Download the JSON and save it as:  %s
  5. Run this script again; a browser window opens for consent.

(No credentials at all? Use --from-csv with a GSC "Pages" report export.)"""
                 % (CLIENT_SECRET, CLIENT_SECRET))
    token = access_token(client)
    results = inspect_all(urls[:args.limit], token)
    not_indexed = [
        {"url": u, "verdict": v["verdict"], "coverage": v["coverage"],
         "last_crawl": v["last_crawl"]}
        for u, v in results.items() if v["verdict"] != "PASS"]
    write_report(not_indexed, checked_at, "api")
    ok = sum(1 for v in results.values() if v["verdict"] == "PASS")
    print("\nindexed %d / %d | NOT indexed %d" %
          (ok, len(results), len(not_indexed)))


if __name__ == "__main__":
    main()
