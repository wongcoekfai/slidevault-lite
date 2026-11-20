#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply site_config.json to every shipped HTML page. Idempotent.

    python3 tools/apply_config.py            # apply to all HTML files
    python3 tools/apply_config.py --check    # CI / pre-deploy gate, exit 1 on problems

Why this exists: the page generators keep placeholders in their templates.
This script is the single place where real affiliate URLs, the analytics
token and the GSC meta enter the shipped HTML, so regenerating pages can
never silently reintroduce a broken `YOUR_...` link.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "site_config.json")

CANVA_FALLBACK = "https://www.canva.com/"
ENVATO_FALLBACK = "https://elements.envato.com/"
A_START = "<!-- CF_ANALYTICS_START -->"
A_END = "<!-- CF_ANALYTICS_END -->"
G_START = "<!-- GSC_VERIFICATION_START -->"
G_END = "<!-- GSC_VERIFICATION_END -->"
AFF_NOTE = "<!-- affiliate:not-configured -->"
HINT_AFF = "As an affiliate we may earn a commission at no extra cost to you."
HINT_PLAIN = "These are optional third-party tools. We do not earn a commission from these links."

CANVA_RE = re.compile(
    r'(<a class="aff-btn" href=")[^"]*(" target="_blank" rel=")[^"]*(">Try Canva Pro)')
ENVATO_RE = re.compile(
    r'(<a class="aff-btn alt" href=")[^"]*(" target="_blank" rel=")[^"]*(">Millions of assets on Envato)')
ANALYTICS_BLOCK_RE = re.compile(
    r'[ \t]*' + re.escape(A_START) + r'.*?' + re.escape(A_END) + r'\n?', re.S)
GSC_BLOCK_RE = re.compile(
    r'[ \t]*' + re.escape(G_START) + r'.*?' + re.escape(G_END) + r'\n?', re.S)
AFF_NOTE_LINE_RE = re.compile(
    r'^[ \t]*' + re.escape(AFF_NOTE) + r'[ \t]*\n', re.M)
LD_RE = re.compile(
    r'<script type="application/ld\+json" id="tpl-list">(.*?)</script>', re.S)

DRAIN_PLAIN = '<a href="https://tools.slidevaulte.com/">Drainage Calculators</a>'
DRAIN_NOFOLLOW = '<a href="https://tools.slidevaulte.com/" rel="nofollow">Drainage Calculators</a>'


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def html_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
        for fn in files:
            if fn.endswith(".html"):
                yield os.path.join(base, fn)


def apply_one(path, cfg):
    src = open(path, encoding="utf-8").read()
    s = src

    aff = cfg.get("affiliate", {})
    ana = cfg.get("analytics", {})
    canva_cfg = (aff.get("canva_url") or "").strip()
    envato_cfg = (aff.get("envato_url") or "").strip()
    token = (ana.get("cloudflare_web_analytics_token") or "").strip()
    gsc = (ana.get("google_site_verification") or "").strip()

    # 1. Affiliate links: real tracking URL when configured, otherwise a
    #    working official link with no `sponsored` (it is not a paid link).
    s = CANVA_RE.sub(
        lambda m: m.group(1) + (canva_cfg or CANVA_FALLBACK)
                  + m.group(2) + ("sponsored noopener" if canva_cfg else "noopener")
                  + m.group(3), s)
    s = ENVATO_RE.sub(
        lambda m: m.group(1) + (envato_cfg or ENVATO_FALLBACK)
                  + m.group(2) + ("sponsored noopener" if envato_cfg else "noopener")
                  + m.group(3), s)
    hint = HINT_AFF if (canva_cfg or envato_cfg) else HINT_PLAIN
    s = s.replace(HINT_AFF, hint).replace(HINT_PLAIN, hint)
    s = AFF_NOTE_LINE_RE.sub("", s)
    if not (canva_cfg and envato_cfg) and '<section class="affiliate-box">' in s:
        s = s.replace('<section class="affiliate-box">',
                      AFF_NOTE + "\n  <section class=\"affiliate-box\">", 1)

    # 2. Cloudflare Web Analytics beacon (only when a token exists).
    s = ANALYTICS_BLOCK_RE.sub("", s)
    if token and "</head>" in s:
        block = (A_START + '<script defer '
                 'src="https://static.cloudflareinsights.com/beacon.min.js" '
                 "data-cf-beacon='{\"token\": \"%s\"}'></script>" % token
                 + A_END + "\n")
        s = s.replace("</head>", block + "</head>", 1)

    # 3. Optional GSC HTML-tag verification.
    s = GSC_BLOCK_RE.sub("", s)
    if gsc and "</head>" in s:
        block = (G_START + '<meta name="google-site-verification" content="%s" />'
                 % gsc + G_END + "\n")
        s = s.replace("</head>", block + "</head>", 1)

    # 4. Unrelated cross-project footer link: do not pass signals sitewide.
    s = s.replace(DRAIN_NOFOLLOW, DRAIN_PLAIN)
    s = s.replace(DRAIN_PLAIN, DRAIN_NOFOLLOW)

    if s != src:
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
        return True
    return False


def check(cfg):
    problems = []
    for path in html_files():
        s = open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, ROOT)
        if "YOUR_" in s:
            problems.append("%s: 残留 YOUR_ 占位符" % rel)
        if DRAIN_PLAIN in s:
            problems.append("%s: 页脚跨项目链接缺 nofollow" % rel)
        if "https://1.envato.market/YOUR" in s or "www.canva.com/?YOUR" in s:
            problems.append("%s: 无效联盟链接" % rel)

    home = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = LD_RE.search(home)
    if not m:
        problems.append("index.html: 找不到 id=tpl-list 的 JSON-LD")
    else:
        try:
            d = json.loads(m.group(1))
            elems = d.get("itemListElement", [])
            if any(isinstance(x, list) for x in elems):
                problems.append("index.html: tpl-list itemListElement 是嵌套数组（非法）")
            if len(elems) < 60:
                problems.append("index.html: tpl-list 只列了 %d 项" % len(elems))
        except Exception as exc:
            problems.append("index.html: tpl-list JSON 解析失败: %s" % exc)
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report problems only, exit 1 on any")
    args = ap.parse_args()
    cfg = load_config()

    if args.check:
        problems = check(cfg)
        if problems:
            for p in problems:
                print("FAIL " + p)
            print("\n%d 个问题" % len(problems))
            sys.exit(1)
        print("OK: 无占位符残留 / 页脚 nofollow 齐全 / 首页 ItemList 合法")
        return

    changed = [p for p in html_files() if apply_one(p, cfg)]
    print("已更新 %d 个 HTML 文件" % len(changed))

    aff = cfg.get("affiliate", {})
    ana = cfg.get("analytics", {})
    print("联盟链接: %s" % ("已配置" if (aff.get("canva_url") or aff.get("envato_url"))
                            else "未配置 → 使用官方普通链接（无坏链，暂无佣金）"))
    print("访问统计: %s" % ("已注入 beacon" if ana.get("cloudflare_web_analytics_token")
                            else "未配置 → 不加载脚本（填 site_config.json 后重跑）"))


if __name__ == "__main__":
    main()
