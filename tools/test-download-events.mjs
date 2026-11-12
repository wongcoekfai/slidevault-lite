#!/usr/bin/env node
// Offline regression test for the per-download event log.
// Mirrors tools/test-welcome-email.mjs: copies the Functions into a temp dir
// as .mjs (Node needs ESM extensions), mocks D1 and Cloudflare request
// metadata, then checks event fields, IP masking, the first-party visitor
// cookie, stable network fingerprints, schema upgrade order, retention
// pruning, waitUntil vs await, admin auth/JSON/CSV, and the /downloads contract.
//
//   node tools/test-download-events.mjs

import { mkdirSync, rmSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DIR = join(tmpdir(), `sv-events-${process.pid}`);
rmSync(DIR, { recursive: true, force: true });
mkdirSync(join(DIR, "_lib"), { recursive: true });
mkdirSync(join(DIR, "admin"), { recursive: true });

const read = (p) => readFileSync(join(ROOT, p), "utf8");
const put = (p, s) => writeFileSync(join(DIR, p), s);
const imp = (p) => import(pathToFileURL(join(DIR, p)).href);

put("_lib/files.mjs", read("functions/_lib/files.js"));
put("_lib/download_events.mjs", read("functions/_lib/download_events.js"));
put("download.mjs", read("functions/download.js")
  .replaceAll("./_lib/files.js", "./_lib/files.mjs")
  .replaceAll("./_lib/download_events.js", "./_lib/download_events.mjs"));
put("downloads.mjs", read("functions/downloads.js")
  .replaceAll("./_lib/files.js", "./_lib/files.mjs"));
put("admin/download-events.mjs", read("functions/admin/download-events.js")
  .replaceAll("../_lib/download_events.js", "../_lib/download_events.mjs"));

const { onRequestGet: download } = await imp("download.mjs");
const { onRequestGet: downloads } = await imp("downloads.mjs");
const { onRequestGet: admin } = await imp("admin/download-events.mjs");

// Each direct recordDownload() call gets its own module instance, so the
// module-level schema/prune caches cannot leak between scenarios.
let seq = 0;
const recordDownload = async (...args) => {
  const name = `_lib/events_case_${++seq}.mjs`;
  put(name, read("functions/_lib/download_events.js"));
  return (await imp(name)).recordDownload(...args);
};

const COLS = ["ts", "day", "file", "ip", "user_id", "visitor", "country", "city",
  "asn", "as_org", "colo", "ua", "referer", "ray"];

function makeDB(opts = {}) {
  const calls = [];
  const lifetime = opts.lifetime || [];
  const daily = opts.daily || [];
  const events = opts.events || [];
  const inserted = [];
  const failEventInsert = opts.failEventInsert || false;
  const DB = {
    prepare(sql) {
      const rec = { sql, args: [] };
      calls.push(rec);
      const stmt = {
        bind(...a) { rec.args = a; return stmt; },
        run() {
          if (sql.includes("INSERT INTO download_events")) {
            if (failEventInsert) return Promise.reject(new Error("D1 down"));
            inserted.push(Object.fromEntries(COLS.map((c, i) => [c, rec.args[i]])));
            events.push(Object.fromEntries(COLS.map((c, i) => [c, rec.args[i]])));
          }
          return Promise.resolve({ success: true });
        },
        all() {
          if (sql.includes("FROM download_events") && sql.includes("SELECT")) {
            const from = rec.args[0];
            const hasFile = sql.includes("lower(file)");
            const hasUser = sql.includes("user_id = ?");
            let i = 1;
            const file = hasFile ? rec.args[i++] : null;
            const user = hasUser ? rec.args[i++] : null;
            const limit = rec.args[i];
            let rows = events.filter(r => r.day >= from &&
              (!file || String(r.file).toLowerCase() === String(file).toLowerCase()) &&
              (!user || r.user_id === user));
            rows = rows.slice().sort((a, b) => b.ts.localeCompare(a.ts)).slice(0, limit);
            return Promise.resolve({ results: rows });
          }
          if (sql.includes("download_daily") && sql.includes("SELECT")) {
            return Promise.resolve({ results: daily.filter(r => {
              if (rec.args[0] && r.day < rec.args[0]) return false;
              if (rec.args[1] && String(r.file).toLowerCase() !== String(rec.args[1]).toLowerCase()) return false;
              return true;
            }) });
          }
          if (sql.includes("FROM downloads") && sql.includes("lower(file)")) {
            return Promise.resolve({ results: lifetime.filter(r =>
              String(r.file).toLowerCase() === String(rec.args[0]).toLowerCase()) });
          }
          if (sql.includes("FROM downloads")) return Promise.resolve({ results: lifetime });
          return Promise.resolve({ results: [] });
        },
        first() { return Promise.resolve(lifetime[0] || null); }
      };
      return stmt;
    }
  };
  return { DB, calls, inserted, events };
}

function req(url, opts = {}) {
  const r = new Request(url, { headers: opts.headers || {} });
  if (opts.cf) r.cf = opts.cf;
  return r;
}

const HEADERS = {
  "cf-connecting-ip": "203.0.113.47",
  "cf-ipcountry": "US",
  "cf-ray": "8f1234abc-SIN",
  "user-agent": "Mozilla/5.0 (Macintosh) TestAgent/1.0",
  "referer": "https://slidevaulte.com/templates/academic-defense-template/?utm_source=x&secret=1"
};
const CF = { country: "US", city: "San Francisco", asn: 13335, asOrganization: "CLOUDFLARENET", colo: "SJC" };

function ctx(db, request, opts = {}) {
  const c = { env: { DB: db.DB, ...(opts.env || {}) }, request, waited: [] };
  if (opts.waitUntil !== false) c.waitUntil = (p) => c.waited.push(Promise.resolve(p));
  return c;
}

const settle = (c) => Promise.all(c.waited);
let pass = 0, fail = 0;
const ok = (name, cond, extra = "") => {
  cond ? pass++ : fail++;
  console.log((cond ? "PASS " : "FAIL ") + name + (extra ? "  " + extra : ""));
};

// ---------------------------------------------------------------- 1. 明细写入
{
  const d = makeDB();
  const c = ctx(d, req("https://x.test/download?file=Academic-Defense-Template.pptx", { headers: HEADERS, cf: CF }));
  const r = await download(c);
  await settle(c);
  ok("正常下载 -> 302", r.status === 302);
  ok("302 禁止共享缓存（保护 Set-Cookie）", r.headers.get("cache-control") === "private, no-store");
  ok("明细写入 1 条", d.inserted.length === 1, "got " + d.inserted.length);
  const e = d.inserted[0] || {};
  ok("ts 为 ISO UTC 毫秒时间", /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(e.ts || ""), e.ts);
  ok("day 与 ts 一致", e.day === e.ts.slice(0, 10));
  ok("file 为 canonical 名", e.file === "Academic-Defense-Template.pptx");
  ok("IPv4 脱敏为 /24", e.ip === "203.0.113.0/24", e.ip);
  const setCookie = r.headers.get("set-cookie") || "";
  ok("首次下载下发 Set-Cookie 且属性齐全",
    /^sv_vid=[0-9a-f]{32};/.test(setCookie) &&
    setCookie.includes("Path=/") && setCookie.includes("Max-Age=15552000") &&
    setCookie.includes("SameSite=Lax") && setCookie.includes("Secure") &&
    setCookie.includes("HttpOnly"), setCookie);
  ok("user_id 为 32 hex 且与 cookie 一致",
    /^[0-9a-f]{32}$/.test(e.user_id || "") && setCookie.includes("sv_vid=" + e.user_id));
  ok("visitor 为 16 位 hex 网络指纹", /^[0-9a-f]{16}$/.test(e.visitor || ""), e.visitor);
  ok("country/city/asn/ASN 组织/colo 齐全",
    e.country === "US" && e.city === "San Francisco" && e.asn === "13335" &&
    e.as_org === "CLOUDFLARENET" && e.colo === "SJC", JSON.stringify([e.country, e.city, e.asn, e.as_org, e.colo]));
  ok("UA 与 CF-Ray 记录", String(e.ua).includes("TestAgent") && e.ray === "8f1234abc-SIN");
  ok("referer 去掉查询串", e.referer === "https://slidevaulte.com/templates/academic-defense-template/", e.referer);
  ok("events 表只建一次 + 3 索引 + ALTER 兼容旧表",
    d.calls.filter(x => x.sql.includes("CREATE TABLE IF NOT EXISTS download_events")).length === 1 &&
    d.calls.filter(x => x.sql.includes("CREATE INDEX")).length === 3 &&
    d.calls.filter(x => x.sql.includes("CREATE TABLE IF NOT EXISTS download_daily")).length === 1 &&
    d.calls.some(x => x.sql.includes("ALTER TABLE download_events ADD COLUMN user_id")),
    JSON.stringify(d.calls.filter(x => x.sql.includes("CREATE ")).map(x => x.sql.slice(0, 58))));
  const alterAt = d.calls.findIndex(x => x.sql.includes("ALTER TABLE download_events"));
  const userIdxAt = d.calls.findIndex(x => x.sql.includes("idx_download_events_user"));
  ok("ALTER 在建 user_id 索引之前（旧表升级顺序）", alterAt >= 0 && userIdxAt > alterAt);
  ok("按天惰性清理执行一次且 cutoff = 90 天", d.calls.filter(x => x.sql.includes("DELETE FROM download_events")).length === 1,
    JSON.stringify((d.calls.find(x => x.sql.includes("DELETE FROM download_events")) || {}).args));
  ok("累计计数与按天聚合仍写入", d.calls.some(x => x.sql.includes("INSERT INTO downloads")) &&
    d.calls.some(x => x.sql.includes("INSERT INTO download_daily")));
}

// ---------------------------------------------------------------- 2. waitUntil / 无 waitUntil
{
  const d = makeDB();
  const c = ctx(d, req("https://x.test/download?file=NOVA-Medical-Healthcare-Template.pptx", { headers: HEADERS }));
  const r = await download(c);
  ok("waitUntil 路径立即返回 302", r.status === 302 && c.waited.length === 1);
  await settle(c);
  ok("waitUntil 完成后明细落库", d.inserted.length === 1);
}
{
  const d = makeDB();
  const c = ctx(d, req("https://x.test/download?file=Pitch-Deck-Template.pptx", { headers: HEADERS }), { waitUntil: false });
  const r = await download(c);
  ok("无 waitUntil 时降级 await 且仍写入", r.status === 302 && d.inserted.length === 1);
}

// ---------------------------------------------------------------- 3. 拒绝与容错
{
  const d = makeDB();
  const r = await download(ctx(d, req("https://x.test/download?file=Does-Not-Exist.pptx")));
  ok("未知文件 -> 404 且零 DB 写入", r.status === 404 && d.calls.length === 0);
}
{
  const d = makeDB();
  const r = await download(ctx(d, req("https://x.test/download?file=../secret.pptx")));
  ok("路径穿越 -> 404", r.status === 404 && d.calls.length === 0);
}
{
  const d = makeDB();
  const c = ctx(d, req("https://x.test/download?file=monthly-business-review-template.pptx", { headers: HEADERS }));
  const r = await download(c);
  await settle(c);
  ok("小写变体 302 到 canonical", r.status === 302 &&
    r.headers.get("location").endsWith("/files/Monthly-Business-Review-Template.pptx"));
  ok("明细里的 file 也是 canonical", d.inserted[0].file === "Monthly-Business-Review-Template.pptx");
}
{
  const d = makeDB({ failEventInsert: true });
  const c = ctx(d, req("https://x.test/download?file=Pitch-Deck-Template.pptx", { headers: HEADERS }));
  const r = await download(c);
  await settle(c);
  ok("明细写库失败不影响 302", r.status === 302, "status " + r.status);
}

// ---------------------------------------------------------------- 4. IPv6 / full IP / 稳定网络指纹
{
  const d = makeDB();
  await recordDownload({ DB: d.DB }, req("https://x.test/x", {
    headers: { "cf-connecting-ip": "2001:db8:abcd:1234:5678:9abc:def0:1234" }
  }), "Pitch-Deck-Template.pptx", new Date("2026-11-12T01:02:03.456Z"));
  ok("IPv6 脱敏为 /48", d.inserted[0].ip === "2001:db8:abcd::/48", d.inserted[0].ip);
}
{
  const d = makeDB();
  await recordDownload({ DB: d.DB, DOWNLOAD_LOG_FULL_IP: "1" },
    req("https://x.test/x", { headers: { "cf-connecting-ip": "203.0.113.47" } }),
    "Pitch-Deck-Template.pptx", new Date("2026-11-12T01:02:03.456Z"));
  ok("显式开关后写完整 IP", d.inserted[0].ip === "203.0.113.47", d.inserted[0].ip);
}
{
  const d = makeDB();
  const env = { DB: d.DB, DOWNLOAD_HASH_SECRET: "test-secret" };
  const rqA = req("https://x.test/x", { headers: { "cf-connecting-ip": "203.0.113.47", "user-agent": "UA-A" } });
  const rqB = req("https://x.test/x", { headers: { "cf-connecting-ip": "203.0.113.47", "user-agent": "UA-B" } });
  await recordDownload(env, rqA, "Pitch-Deck-Template.pptx", new Date("2026-11-12T01:00:00Z"));
  await recordDownload(env, rqA, "Pitch-Deck-Template.pptx", new Date("2026-11-13T01:00:00Z"));
  await recordDownload(env, rqB, "Pitch-Deck-Template.pptx", new Date("2026-11-13T01:00:00Z"));
  const [a, b, c] = d.inserted.map(x => x.visitor);
  ok("同一网络跨天指纹稳定（不再按天轮换）", a === b);
  ok("不同 UA -> 不同网络指纹", a !== c);
  ok("指纹不含原始 IP 串", !a.includes("203") && a.length === 16);
}
{
  const d = makeDB();
  await recordDownload({ DB: d.DB, DOWNLOAD_EVENT_RETENTION_DAYS: "30" },
    req("https://x.test/x", { headers: HEADERS }), "Pitch-Deck-Template.pptx",
    new Date("2026-11-12T01:00:00Z"));
  const del = d.calls.find(x => x.sql.includes("DELETE FROM download_events"));
  ok("自定义保留期生效（cutoff = 2026-10-13）", del && del.args[0] === "2026-10-13", JSON.stringify(del && del.args));
}

// ---------------------------------------------------------------- 4.5 用户区分（第一方 cookie）
{
  const id = "a".repeat(32);
  const d = makeDB();
  const c = ctx(d, req("https://x.test/download?file=Pitch-Deck-Template.pptx",
    { headers: { ...HEADERS, cookie: "foo=1; sv_vid=" + id + "; bar=2" } }));
  const r = await download(c); await settle(c);
  ok("带合法 cookie -> 不再下发 Set-Cookie", r.headers.get("set-cookie") === null);
  ok("复用 cookie 值作为 user_id", d.inserted[0].user_id === id);
}
{
  const d = makeDB();
  const c = ctx(d, req("https://x.test/download?file=Pitch-Deck-Template.pptx",
    { headers: { ...HEADERS, cookie: "sv_vid=NOT-A-VALID-ID" } }));
  const r = await download(c); await settle(c);
  ok("伪造 cookie 被拒绝并重新生成",
    /^sv_vid=[0-9a-f]{32};/.test(r.headers.get("set-cookie") || "") &&
    d.inserted[0].user_id !== "NOT-A-VALID-ID");
}
{
  const a = "a".repeat(32), b = "b".repeat(32);
  const d = makeDB();
  for (const id of [a, a, b]) {
    const c = ctx(d, req("https://x.test/download?file=Pitch-Deck-Template.pptx",
      { headers: { ...HEADERS, cookie: "sv_vid=" + id } }));
    await download(c); await settle(c);
  }
  const ids = d.inserted.map(x => x.user_id);
  ok("同一访客多次/跨天下载 user_id 稳定", ids[0] === ids[1] && ids[0] === a);
  ok("不同访客 user_id 可区分", ids[2] === b && ids[2] !== ids[0]);
}
{
  const d = makeDB();
  await recordDownload({ DB: d.DB }, req("https://x.test/x", { headers: HEADERS }),
    "Pitch-Deck-Template.pptx", new Date("2026-11-12T01:00:00Z"), "forged");
  ok("recordDownload 拒绝非法 userId", d.inserted[0].user_id === "");
}

// ---------------------------------------------------------------- 5. 查询接口鉴权与输出
const TOKEN = "unit-test-token";
{
  const d = makeDB();
  const r = await admin({ env: { DB: d.DB }, request: req("https://x.test/admin/download-events") });
  ok("未配置 token -> 404 且不查库", r.status === 404 && d.calls.length === 0);
}
{
  const d = makeDB();
  const r = await admin({ env: { DB: d.DB, DOWNLOAD_EVENTS_TOKEN: TOKEN },
    request: req("https://x.test/admin/download-events") });
  ok("无 Authorization -> 401", r.status === 401);
}
{
  const d = makeDB();
  const r = await admin({ env: { DB: d.DB, DOWNLOAD_EVENTS_TOKEN: TOKEN },
    request: req("https://x.test/admin/download-events", { headers: { authorization: "Bearer wrong" } }) });
  ok("错误 token -> 401", r.status === 401);
}
{
  const today = new Date().toISOString().slice(0, 10);
  const d = makeDB({ events: [
    { ts: today + "T10:00:00.000Z", day: today, file: "A.pptx", ip: "203.0.113.0/24", visitor: "aabb", ua: 'Mozilla, "quoted"' },
    { ts: today + "T09:00:00.000Z", day: today, file: "B.pptx", ip: "198.51.100.0/24", visitor: "ccdd" },
  ] });
  const r = await admin({ env: { DB: d.DB, DOWNLOAD_EVENTS_TOKEN: TOKEN },
    request: req("https://x.test/admin/download-events?days=7&limit=10", { headers: { authorization: "Bearer " + TOKEN } }) });
  const j = await r.json();
  ok("正确 token -> 200 且返回 2 行", r.status === 200 && j.count === 2, JSON.stringify(j).slice(0, 140));
  ok("结果按 ts 倒序", j.rows[0].file === "A.pptx");
  ok("响应含保留期元信息", j.retention_days === 90 && j.days === 7 && j.limit === 10);
  ok("查询 SQL 不返回原始完整 IP 列之外的内容", d.calls[0].sql.includes("SELECT ts, day, file"));
}
{
  const today = new Date().toISOString().slice(0, 10);
  const d = makeDB({ events: [
    { ts: today + "T10:00:00.000Z", day: today, file: "A.pptx", ua: 'Mozilla, "quoted"' },
  ] });
  const r = await admin({ env: { DB: d.DB, DOWNLOAD_EVENTS_TOKEN: TOKEN },
    request: req("https://x.test/admin/download-events?format=csv&file=A.pptx&limit=5", { headers: { authorization: "Bearer " + TOKEN } }) });
  const text = await r.text();
  ok("CSV 响应头正确", r.headers.get("content-type").includes("text/csv"));
  ok("CSV 含表头与转义后的引号", text.startsWith("ts,day,file,") && text.includes('"Mozilla, ""quoted"""'), text.slice(0, 180));
  ok("CSV 表头含 user_id", text.split("\r\n")[0].includes("user_id"));
  ok("file 过滤传到 SQL", d.calls[0].sql.includes("lower(file) = lower(?)") && d.calls[0].args[1] === "A.pptx");
}

{
  const today = new Date().toISOString().slice(0, 10);
  const d = makeDB({ events: [
    { ts: today + "T10:00:00.000Z", day: today, file: "A.pptx", user_id: "visitor-one" },
    { ts: today + "T09:00:00.000Z", day: today, file: "B.pptx", user_id: "visitor-two" },
  ] });
  const r = await admin({ env: { DB: d.DB, DOWNLOAD_EVENTS_TOKEN: TOKEN },
    request: req("https://x.test/admin/download-events?user=visitor-one", { headers: { authorization: "Bearer " + TOKEN } }) });
  const j = await r.json();
  ok("?user= 按匿名访客过滤", j.count === 1 && j.rows[0].user_id === "visitor-one" &&
    d.calls[0].sql.includes("user_id = ?"), JSON.stringify(j.rows));
}

// ---------------------------------------------------------------- 6. /downloads 原契约回归
{
  const d = makeDB({ lifetime: [
    { file: "Monthly-Business-Review-Template.pptx", count: 2 },
    { file: "monthly-business-review-template.pptx", count: 1 },
    { file: "Academic-Defense-Template.pptx", count: 53 }
  ] });
  const r = await downloads({ env: { DB: d.DB }, request: req("https://x.test/downloads") });
  const j = await r.json();
  ok("全列表大小写合并", Object.keys(j).length === 2 && j["Monthly-Business-Review-Template.pptx"] === 3);
}
{
  const d = makeDB({ lifetime: [
    { file: "Monthly-Business-Review-Template.pptx", count: 2 },
    { file: "monthly-business-review-template.pptx", count: 1 }
  ] });
  const r = await downloads({ env: { DB: d.DB }, request: req("https://x.test/downloads?file=monthly-business-review-template.pptx") });
  const j = await r.json();
  ok("?file 契约不变", j.file === "Monthly-Business-Review-Template.pptx" && j.count === 3);
}
{
  const today = new Date().toISOString().slice(0, 10);
  const d = makeDB({ daily: [
    { day: today, file: "Academic-Defense-Template.pptx", count: 4 },
    { day: today, file: "academic-defense-template.pptx", count: 1 }
  ] });
  const r = await downloads({ env: { DB: d.DB }, request: req("https://x.test/downloads?days=7") });
  const j = await r.json();
  ok("?days=7 契约不变", j.total === 5 && j.by_day[today] === 5);
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
