// GET /downloads                  -> { file: lifetime_count, ... }
// GET /downloads?file=X.pptx      -> { file, count }   (used by detail pages)
// GET /downloads?days=7           -> rolling daily rollup for the whole site
// GET /downloads?days=7&file=X    -> rolling daily rollup for one template
//
// Historical rows written with a different filename case are folded onto the
// canonical name at read time, so the API reports one row per real .pptx file.
import { CANONICAL_FILES } from "./_lib/files.js";

function canonical(name) {
  return CANONICAL_FILES[String(name).toLowerCase()] || name;
}

function clampDays(raw) {
  if (raw === null) return null;
  const n = parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) return 1;
  return Math.min(n, 365);
}

async function dailyReport(env, file, days) {
  const from = new Date(Date.now() - (days - 1) * 86400000).toISOString().slice(0, 10);
  let rows = [];
  let note;
  try {
    let res;
    if (file) {
      const name = canonical(file);
      res = await env.DB.prepare(
        "SELECT day, file, count FROM download_daily " +
        "WHERE day >= ? AND lower(file) = lower(?) ORDER BY day"
      ).bind(from, name).all();
    } else {
      res = await env.DB.prepare(
        "SELECT day, file, count FROM download_daily WHERE day >= ? ORDER BY day"
      ).bind(from).all();
    }
    rows = res.results || [];
  } catch (e) {
    // The table is created on the first counted download after deploy.
    note = "no daily data yet (the rollup table is created on first download)";
  }
  const by_day = {};
  const by_file = {};
  let total = 0;
  for (const r of rows) {
    const name = canonical(r.file);
    by_day[r.day] = (by_day[r.day] || 0) + r.count;
    by_file[name] = (by_file[name] || 0) + r.count;
    total += r.count;
  }
  const out = { days, from, total, by_day, by_file };
  if (file) out.file = canonical(file);
  if (note) out.note = note;
  return json(out);
}

export async function onRequestGet(context) {
  const { env, request } = context;
  const url = new URL(request.url);
  const file = url.searchParams.get("file");
  const days = clampDays(url.searchParams.get("days"));

  try {
    if (days !== null) return await dailyReport(env, file, days);

    if (file) {
      const name = canonical(file);
      const res = await env.DB.prepare(
        "SELECT file, count FROM downloads WHERE lower(file) = lower(?)"
      ).bind(name).all();
      const count = (res.results || []).reduce((sum, r) => sum + (r.count || 0), 0);
      return json({ file: name, count });
    }

    const { results } = await env.DB.prepare(
      "SELECT file, count FROM downloads ORDER BY count DESC"
    ).all();
    const out = {};
    for (const r of results) {
      const name = canonical(r.file);
      out[name] = (out[name] || 0) + r.count;
    }
    return json(out);
  } catch (e) {
    return json({ error: "unavailable" }, 500);
  }
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}
