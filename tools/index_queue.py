#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Automate everything about indexing except the one click Google won't expose.

Google has no API to "Request indexing" for ordinary pages: the Indexing API
only accepts JobPosting / BroadcastEvent pages, the URL Inspection API is
read-only, and the sitemap ping endpoint was retired in 2023. What CAN be
automated:

  * detect newly added URLs since the last deployment baseline
  * push them to IndexNow (Bing / Yandex / Seznam / Naver) in one request
  * build a one-click GSC queue page: open URL Inspection pre-filled, click
    "Request indexing", tick the box, progress is saved locally

Usage:
  python3 tools/index_queue.py             # build marketing/index-queue.html
  python3 tools/index_queue.py --push      # also submit new URLs to IndexNow
  python3 tools/index_queue.py --mark-all  # clear the queue after GSC is done
  python3 tools/index_queue.py --all       # list all sitemap URLs, not just new
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://slidevaulte.com"
SITEMAP = os.path.join(ROOT, "sitemap.xml")
STATE = os.path.join(ROOT, "marketing", "index-queue.json")
PANEL = os.path.join(ROOT, "marketing", "index-queue.html")
BASELINE = "b6da1e8"        # last commit before this round of new pages
GSC = ("https://search.google.com/search-console/inspect"
       "?resource_id=sc-domain%3Aslidevaulte.com&id=")
GSC_SITEMAPS = ("https://search.google.com/search-console/sitemaps"
                "?resource_id=sc-domain%3Aslidevaulte.com")


def urls_from(xml_text):
    return re.findall(r"<loc>(.*?)</loc>", xml_text)


def load_state():
    if os.path.isfile(STATE):
        try:
            return json.load(open(STATE, encoding="utf-8"))
        except Exception:
            pass
    return {"baseline_commit": BASELINE, "submitted": []}


def baseline_urls(state):
    urls = state.get("baseline_urls")
    if urls:
        return urls
    try:
        xml = subprocess.check_output(
            ["git", "show", "%s:sitemap.xml" % state.get("baseline_commit", BASELINE)],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        urls = urls_from(xml)
    except Exception:
        urls = []
    state["baseline_urls"] = urls
    return urls


def kind(url):
    path = url.replace(SITE, "").strip("/")
    if path.startswith("tools/"):
        return "工具页"
    if path.startswith("blog/"):
        return "文章"
    if path.startswith("templates/"):
        rest = path[len("templates/"):].strip("/")
        if rest in ("business", "startup", "marketing", "sales",
                    "education", "healthcare"):
            return "分类页"
        return "模板页"
    return "站点页"


def gsc_link(url):
    return GSC + urllib.parse.quote(url, safe="")


def build_panel(pending, all_urls):
    rows = []
    for i, url in enumerate(pending, 1):
        safe = html.escape(url, quote=True)
        rows.append("""
<tr data-url="{safe}">
  <td class="num">{i}</td>
  <td><a class="u" href="{safe}" target="_blank" rel="noopener">{u}</a>
      <span class="kind">{kind}</span></td>
  <td class="ops">
    <button class="btn copy" data-url="{safe}">复制</button>
    <a class="btn primary" href="{gsc}" target="_blank" rel="noopener">打开 GSC</a>
    <label class="done"><input type="checkbox" data-url="{safe}"> 已提交</label>
  </td>
</tr>""".format(i=i, safe=safe, u=html.escape(url), kind=kind(url),
                gsc=html.escape(gsc_link(url), quote=True)))
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SlideVault · 待收录队列</title>
<style>
:root{{color-scheme:light}}
*{{box-sizing:border-box}}
body{{margin:0;padding:32px 20px 64px;background:#f6f7f9;color:#1c2230;
 font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif}}
.wrap{{max-width:980px;margin:0 auto}}
h1{{font-size:24px;margin:0 0 6px}}
.sub{{color:#5b6475;margin:0 0 22px}}
.card{{background:#fff;border:1px solid #e3e6ec;border-radius:14px;padding:20px 22px;
 margin-bottom:18px;box-shadow:0 1px 3px rgba(20,30,60,.04)}}
.bar{{height:9px;background:#e9ecf2;border-radius:9px;overflow:hidden;margin:12px 0 8px}}
.bar > i{{display:block;height:100%;width:0;background:#2563eb;border-radius:9px;
 transition:width .25s}}
.note{{color:#5b6475;font-size:13px}}
table{{width:100%;border-collapse:collapse}}
td{{padding:11px 8px;border-top:1px solid #eef0f4;vertical-align:middle}}
td.num{{width:34px;color:#9aa3b2;font-variant-numeric:tabular-nums}}
.u{{color:#1c4fd8;text-decoration:none;word-break:break-all;font-size:13px}}
.u:hover{{text-decoration:underline}}
.kind{{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:20px;
 background:#eef2ff;color:#4353a8;font-size:11px;white-space:nowrap}}
.ops{{text-align:right;white-space:nowrap;width:280px}}
.btn{{display:inline-block;padding:6px 11px;margin-left:6px;border:1px solid #d7dce5;
 border-radius:8px;background:#fff;color:#33405a;font-size:12px;cursor:pointer;
 text-decoration:none}}
.btn:hover{{border-color:#2563eb;color:#2563eb}}
.btn.primary{{background:#2563eb;border-color:#2563eb;color:#fff}}
.btn.primary:hover{{background:#1d4ed8;color:#fff}}
.done{{margin-left:10px;font-size:12px;color:#5b6475;white-space:nowrap;cursor:pointer}}
.done input{{vertical-align:-2px;margin-right:3px}}
tr.ok{{opacity:.5}} tr.ok .u{{text-decoration:line-through}}
code{{background:#eef1f6;padding:2px 6px;border-radius:5px;font-size:12px}}
a.ext{{color:#2563eb}}
ol{{margin:8px 0 0 20px;padding:0}} li{{margin:6px 0}}
</style></head><body><div class="wrap">
<h1>待收录队列 · slidevaulte.com</h1>
<p class="sub">共 {pending} 条新页面待在 Google 提交；全站 sitemap 现有 {total} 条 URL。</p>

<div class="card">
  <strong>Google 侧进度</strong>
  <div class="bar"><i id="bar"></i></div>
  <div class="note"><span id="count">0 / {pending}</span> 已提交 · 勾选状态保存在本机浏览器</div>
</div>

<div class="card">
  <strong>怎么操作（每条约 10 秒）</strong>
  <ol>
    <li>点「打开 GSC」→ 网址检查页会带上该 URL；若未自动填入，点「复制」后粘贴到检查框。</li>
    <li>检查通过后点 <code>Request indexing / 请求编入索引</code>。</li>
    <li>回到本页勾选「已提交」。有日配额，提交完当天剩下的次日再点，重复提交不会加快。</li>
  </ol>
  <p class="note" style="margin-bottom:0">
    Bing / Yandex / Seznam / Naver 无需手工：<code>python3 tools/index_queue.py --push</code> 已通过 IndexNow 推送。
    另外可 <a class="ext" href="{gsc_sitemaps}" target="_blank" rel="noopener">在 GSC 重新提交 sitemap.xml</a>（只需一次，之后 Google 会自动重读）。
  </p>
</div>

<div class="card" style="padding:8px 12px">
<table><tbody>{rows}</tbody></table>
</div>
<p class="note">队列来自 sitemap.xml 与基线提交的差量；全部提交完可运行
<code>python3 tools/index_queue.py --mark-all</code> 清空待办。</p>
</div>
<script>
(function(){{
  var KEY='sv_index_queue_v2', state={{}};
  try{{state=JSON.parse(localStorage.getItem(KEY)||'{{}}')}}catch(e){{}}
  var boxes=[].slice.call(document.querySelectorAll('.done input'));
  function sync(){{
    var done=boxes.filter(function(b){{return b.checked}}).length;
    document.getElementById('count').textContent=done+' / '+boxes.length;
    document.getElementById('bar').style.width=(boxes.length?done*100/boxes.length:0)+'%';
  }}
  boxes.forEach(function(b){{
    b.checked=!!state[b.dataset.url];
    b.closest('tr').classList.toggle('ok',b.checked);
    b.addEventListener('change',function(){{
      state[b.dataset.url]=b.checked;
      try{{localStorage.setItem(KEY,JSON.stringify(state))}}catch(e){{}}
      b.closest('tr').classList.toggle('ok',b.checked);
      sync();
    }});
  }});
  [].slice.call(document.querySelectorAll('.copy')).forEach(function(btn){{
    btn.addEventListener('click',function(){{
      var t=document.createElement('textarea');t.value=btn.dataset.url;
      document.body.appendChild(t);t.select();
      try{{document.execCommand('copy');btn.textContent='已复制'}}catch(e){{btn.textContent='复制失败'}}
      document.body.removeChild(t);
      setTimeout(function(){{btn.textContent='复制'}},1400);
    }});
  }});
  sync();
}})();
</script></body></html>
""".format(pending=len(pending), total=len(all_urls), rows="".join(rows),
           gsc_sitemaps=html.escape(GSC_SITEMAPS, quote=True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true", help="submit new URLs to IndexNow")
    ap.add_argument("--mark-all", action="store_true", help="mark every pending URL as done")
    ap.add_argument("--all", action="store_true", help="list every sitemap URL")
    args = ap.parse_args()

    current = urls_from(open(SITEMAP, encoding="utf-8").read())
    state = load_state()
    base = baseline_urls(state)
    new_urls = [u for u in current if u not in set(base)]
    submitted = set(state.get("submitted", []))
    pending = current if args.all else [u for u in new_urls if u not in submitted]

    if args.mark_all:
        submitted.update(new_urls)
        state["submitted"] = sorted(submitted)
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump(state, open(STATE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("marked %d URLs as submitted; %d total in state" %
              (len(new_urls), len(submitted)))
        return

    if args.push and pending:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import indexnow
        print("pushing %d new URLs to IndexNow..." % len(pending))
        for i in range(0, len(pending), 100):
            code, body = indexnow.submit(pending[i:i + 100])
            print("  HTTP %s %s" % (code, body.strip()[:120]))

    os.makedirs(os.path.dirname(PANEL), exist_ok=True)
    open(PANEL, "w", encoding="utf-8").write(build_panel(pending, current))
    if not state.get("baseline_urls_saved"):
        state["baseline_urls_saved"] = True
        json.dump(state, open(STATE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    print("queue: %d new URLs since baseline, %d pending" % (len(new_urls), len(pending)))
    print("panel: %s" % PANEL)


if __name__ == "__main__":
    main()
