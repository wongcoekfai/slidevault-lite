// GET /admin/download-events
//
// Private, token-protected view of the per-download event log. The endpoint
// stays dark (404) until DOWNLOAD_EVENTS_TOKEN is configured in Cloudflare
// Pages > Settings > Variables and Secrets, so deploying this file alone can
// never expose diagnostics data.
//
//   curl -H "Authorization: Bearer $TOKEN" \
//     "https://slidevaulte.com/admin/download-events?days=7&limit=200"
//   ...&format=csv   -> downloadable CSV for spreadsheets
//   ...&file=Academic-Defense-Template.pptx -> one template
//   ...&user=<sv_vid> -> every download from one anonymous visitor id
//
import { queryEvents } from "../_lib/download_events.js";

function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) {
    return false;
  }
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}

function csvCell(v) {
  const s = String(v == null ? "" : v);
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function toCsv(rows, columns) {
  const lines = [columns.join(",")];
  for (const r of rows) lines.push(columns.map((c) => csvCell(r[c])).join(","));
  return lines.join("\r\n") + "\r\n";
}

export async function onRequestGet(context) {
  const { env, request } = context;
  const token = env && env.DOWNLOAD_EVENTS_TOKEN;

  // No token configured -> endpoint does not exist as far as the world knows.
  if (!token) return json({ error: "not found" }, 404);

  const auth = request.headers.get("authorization") || "";
  if (!safeEqual(auth, "Bearer " + token)) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = new URL(request.url);
  try {
    const out = await queryEvents(env, {
      days: url.searchParams.get("days"),
      limit: url.searchParams.get("limit"),
      file: url.searchParams.get("file"),
      user: url.searchParams.get("user"),
    });
    if (url.searchParams.get("format") === "csv") {
      const columns = [
        "ts", "day", "file", "ip", "user_id", "visitor", "country", "city",
        "asn", "as_org", "colo", "ua", "referer", "ray",
      ];
      return new Response(toCsv(out.rows, columns), {
        headers: {
          "content-type": "text/csv; charset=utf-8",
          "content-disposition": 'attachment; filename="download-events.csv"',
          "cache-control": "no-store",
        },
      });
    }
    return json(out);
  } catch (e) {
    return json({ error: "unavailable" }, 500);
  }
}
