// GET /download?file=Name.pptx
// Counts the download (lifetime + UTC daily rollup + one detail event),
// then 302-redirects to the real file.
// CANONICAL_FILES is generated from assets/templates.js by tools/gen_pages.py,
// so a request for a file we do not ship is rejected before anything is counted
// (previously those requests counted once and then redirected to a 404).
import { CANONICAL_FILES } from "./_lib/files.js";
import { recordDownload, resolveVisitor } from "./_lib/download_events.js";

// The daily rollup table is created lazily: wrangler migrations are not always
// available from the deploy environment, and a DDL must never block a download.
let dailyReady = false;

async function ensureDailyTable(env) {
  if (dailyReady) return true;
  try {
    await env.DB.prepare(
      "CREATE TABLE IF NOT EXISTS download_daily (" +
      "day TEXT NOT NULL, file TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0, " +
      "PRIMARY KEY (day, file))"
    ).run();
    dailyReady = true;
    return true;
  } catch (e) {
    return false;
  }
}

export async function onRequestGet(context) {
  const { env, request } = context;
  const url = new URL(request.url);
  const raw = url.searchParams.get("file") || "";

  // Allowlist: plain .pptx filenames only, no paths, no traversal.
  if (!/^[A-Za-z0-9._-]+\.pptx$/.test(raw)) {
    return new Response("Not found", { status: 404 });
  }

  // Fold case variants onto the exact filename that ships in /files/.
  const file = CANONICAL_FILES[raw.toLowerCase()];
  if (!file) {
    return new Response("Not found", { status: 404 });
  }

  try {
    await env.DB.prepare(
      "INSERT INTO downloads (file, count) VALUES (?, 1) " +
      "ON CONFLICT(file) DO UPDATE SET count = count + 1"
    ).bind(file).run();
  } catch (e) {
    // Counting must never block a download.
  }

  // Daily rollup answers "is the site growing?" — best effort only.
  try {
    if (await ensureDailyTable(env)) {
      const day = new Date().toISOString().slice(0, 10); // UTC
      await env.DB.prepare(
        "INSERT INTO download_daily (day, file, count) VALUES (?, ?, 1) " +
        "ON CONFLICT(day, file) DO UPDATE SET count = count + 1"
      ).bind(day, file).run();
    }
  } catch (e) {
    // Rollup is observational; the lifetime counter above is authoritative.
  }

  // A random first-party id lets the event log distinguish one browser from
  // another across days. resolveVisitor is sync so Set-Cookie can go on the
  // 302; the D1 write itself stays off the critical path via waitUntil.
  const { userId, setCookie } = resolveVisitor(request);
  const event = recordDownload(env, request, file, new Date(), userId);
  if (typeof context.waitUntil === "function") {
    context.waitUntil(event);
  } else {
    // Local test harnesses / runtimes without waitUntil.
    await event;
  }

  const headers = new Headers({
    Location: new URL("/files/" + file, url.origin).toString(),
    // This response may carry Set-Cookie: never let a shared cache serve it
    // to a different visitor (or skip the counting Function entirely).
    "Cache-Control": "private, no-store",
  });
  if (setCookie) headers.append("Set-Cookie", setCookie);
  return new Response(null, { status: 302, headers });
}
