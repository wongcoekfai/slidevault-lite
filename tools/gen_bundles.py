#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the kit Bundle ZIPs and the homepage kit data.

    python3 tools/gen_bundles.py

Reads tools/kits.py (the single source of truth) + assets/templates.js, then:
  * writes files/bundles/<kit-id>-kit.zip  (all member .pptx + a README)
  * writes assets/kits.js                 (window.KITS for the homepage)
  * writes functions/_lib/kits.js         (KITS map for the subscribe Function)

Builds are deterministic: ZIP member order, timestamps and compression are
fixed, so re-running the script produces byte-identical files and no git noise.
No new HTML pages and no new sitemap URLs are created.
"""
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kits import KITS, bundle_url  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://slidevaulte.com"
CATALOG = os.path.join(ROOT, "assets", "templates.js")
BUNDLE_DIR = os.path.join(ROOT, "files", "bundles")
KITS_JS = os.path.join(ROOT, "assets", "kits.js")
FN_KITS_JS = os.path.join(ROOT, "functions", "_lib", "kits.js")
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def read_catalog():
    src = open(CATALOG, encoding="utf-8").read()
    out = {}
    for m in re.finditer(
            r'\{\s*slug:\s*"([^"]+)",\s*title:\s*"([^"]+)".*?file:\s*"([^"]+)"', src):
        slug, title, fname = m.groups()
        out[slug] = dict(slug=slug, title=title, file=fname)
    if not out:
        sys.exit("!! could not parse assets/templates.js")
    return out


def write_if_changed(path, data):
    if os.path.isfile(path):
        with open(path, "rb") as fh:
            if fh.read() == data:
                return False
    with open(path, "wb") as fh:
        fh.write(data)
    return True


def bundle_readme(kit, members):
    lines = [
        kit["name"].upper() + " — Slide Vault",
        "=" * 46,
        "",
        "%d editable PowerPoint templates, free for personal and commercial use." % len(members),
        "No signup, no watermark, no attribution required.",
        "",
        "IN THIS BUNDLE (suggested order)",
    ]
    for i, t in enumerate(members, 1):
        lines.append("  %d. %-52s  %s" % (i, t["title"], t["file"]))
        lines.append("     %s/templates/%s/" % (SITE, t["slug"]))
    lines += [
        "",
        "EDITING",
        "  Every file is a plain .pptx built from standard shapes and text boxes.",
        "  Opens in PowerPoint, Google Slides and Keynote. Change colours through",
        "  Design > Variants > Colors; replace images with right-click > Change Picture.",
        "",
        "BEFORE YOU SHARE",
        "  These layouts ship with speaker notes and document properties. Strip them",
        "  with the free browser tools at %s/tools/ (nothing is uploaded)." % SITE,
        "",
        "MORE FREE DECKS",
        "  %s/#templates" % SITE,
        "",
        "Slide Vault · https://slidevaulte.com",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_zip(kit, members, catalog):
    buf_path = os.path.join(BUNDLE_DIR, kit["id"] + "-kit.zip")
    # Build in memory first so a failed run never leaves a half-written ZIP.
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        info = zipfile.ZipInfo("README.txt", FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = 0o644 << 16
        zf.writestr(info, bundle_readme(kit, members))
        for t in members:
            src = os.path.join(ROOT, "files", t["file"])
            if not os.path.isfile(src):
                sys.exit("!! missing pptx for %s: %s" % (t["slug"], t["file"]))
            with open(src, "rb") as fh:
                data = fh.read()
            info = zipfile.ZipInfo(t["file"], FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    return buf_path, buf.getvalue()


def main():
    catalog = read_catalog()
    os.makedirs(BUNDLE_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(FN_KITS_JS), exist_ok=True)
    js_kits = []
    fn_map = {}

    for kit in KITS:
        missing = [s for s in kit["slugs"] if s not in catalog]
        if missing:
            sys.exit("!! kit %s references unknown slugs: %s" % (kit["id"], ", ".join(missing)))
        members = [catalog[s] for s in kit["slugs"]]
        path, data = build_zip(kit, members, catalog)
        changed = write_if_changed(path, data)
        print("  %-22s %2d decks  %6.2f MB  %s" % (
            kit["id"], len(members), len(data) / 1048576.0,
            "written" if changed else "unchanged"))
        js_kits.append(dict(
            id=kit["id"], name=kit["name"], eyebrow=kit["eyebrow"],
            desc=kit["desc"], zip=bundle_url(kit["id"]),
            decks=[dict(slug=t["slug"], title=t["title"],
                        url="/templates/%s/" % t["slug"]) for t in members],
        ))
        fn_map[kit["id"]] = dict(name=kit["name"], zip=bundle_url(kit["id"]),
                                 decks=len(members))

    js = ("// Generated by tools/gen_bundles.py — edit tools/kits.py instead.\n"
          "window.KITS = " + json.dumps(js_kits, ensure_ascii=False, indent=2) + ";\n")
    changed = write_if_changed(KITS_JS, js.encode("utf-8"))
    fn_js = ("// Generated by tools/gen_bundles.py — edit tools/kits.py instead.\n"
             "// Whitelist shared with the subscribe Function; keys are safe to use in URLs.\n"
             "export const KITS = " + json.dumps(fn_map, ensure_ascii=False, indent=2) + ";\n")
    fn_changed = write_if_changed(FN_KITS_JS, fn_js.encode("utf-8"))
    print("\ndone: %d kits | assets/kits.js %s | functions/_lib/kits.js %s"
          % (len(KITS), "written" if changed else "unchanged",
             "written" if fn_changed else "unchanged"))


if __name__ == "__main__":
    main()
