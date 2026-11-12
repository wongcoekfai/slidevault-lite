// Per-download event log for Cloudflare D1.
//
// One row per /download request. This is diagnostics data, not billing data:
// the authoritative lifetime counter is still `downloads`, and the UTC daily
// rollup is still `download_daily`. Nothing here may ever block a 302.
//
// VISITOR DISTINCTION (the point of this log):
//   user_id  - a random first-party cookie (sv_vid, 32 hex chars, no personal
//              data). Stable across days and downloads, so we can tell one
//              browser from another, spot repeat downloads and returning
//              visitors. Clearing site cookies resets it.
//   visitor  - a stable, one-way HMAC fingerprint of the *masked* IP network
//              prefix + user agent + network operator. Fallback for requests
//              without a cookie (curl, crawlers, cookie blockers). It is NOT
//              a user id: everyone behind the same NAT may share it.
//
// PRIVACY: by default we DO NOT write the full IP address. Both identifiers
// are pseudonymous, neither contains the full address, and neither is used
// for advertising or profiling. Set DOWNLOAD_LOG_FULL_IP=1 to store the full
// address instead — only after updating the public privacy policy to say so.
//
// Rows are pruned lazily after DOWNLOAD_EVENT_RETENTION_DAYS (default 90).

const RETENTION_DEFAULT = 90;

export const VISITOR_COOKIE = "sv_vid";
export const VISITOR_COOKIE_MAX_AGE = 180 * 24 * 60 * 60; // 180 days

const COLUMNS = [
  "ts", "day", "file",
  "ip", "user_id", "visitor", "country", "city", "asn", "as_org", "colo",
  "ua", "referer", "ray",
];

const DDL = [
  "CREATE TABLE IF NOT EXISTS download_events (" +
    "id INTEGER PRIMARY KEY AUTOINCREMENT," +
    "ts TEXT NOT NULL," +
    "day TEXT NOT NULL," +
    "file TEXT NOT NULL," +
    "ip TEXT," +
    "user_id TEXT," +
    "visitor TEXT," +
    "country TEXT," +
    "city TEXT," +
    "asn TEXT," +
    "as_org TEXT," +
    "colo TEXT," +
    "ua TEXT," +
    "referer TEXT," +
    "ray TEXT" +
  ")",
  "CREATE INDEX IF NOT EXISTS idx_download_events_ts ON download_events(ts)",
  "CREATE INDEX IF NOT EXISTS idx_download_events_day_file ON download_events(day, file)",
];

// Module-level caches. Workers isolates are long-lived but may be recycled,
// so all DDL is IF NOT EXISTS and the prune DELETE is idempotent.
let schemaReady = false;
let lastPruneDay = null;

// ---------------------------------------------------------------- helpers

function clip(value, max) {
  const s = String(value == null ? "" : value);
  return s.length > max ? s.slice(0, max) : s;
}

// 1.2.3.4 -> 1.2.3.0/24 ; 2001:db8:abcd:... -> 2001:db8:abcd::/48
function maskIp(ip) {
  const s = String(ip || "").trim();
  if (!s) return "unknown";
  if (s.includes(":")) {
    const parts = s.split(":").filter(Boolean);
    return (parts.slice(0, 3).join(":") || "unknown") + "::/48";
  }
  const v4 = s.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (v4) return v4[1] + "." + v4[2] + "." + v4[3] + ".0/24";
  return "redacted";
}

function randomId() {
  const bytes = new Uint8Array(16);
  if (globalThis.crypto && globalThis.crypto.getRandomValues) {
    globalThis.crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
  }
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

// Synchronous so the 302 can carry Set-Cookie; the async D1 write happens
// later inside waitUntil. Strict validation prevents forged/injected values.
export function resolveVisitor(request) {
  const raw = (request && request.headers && request.headers.get("cookie")) || "";
  for (const part of raw.split(";")) {
    const idx = part.indexOf("=");
    if (idx < 0) continue;
    const name = part.slice(0, idx).trim();
    const value = part.slice(idx + 1).trim();
    if (name === VISITOR_COOKIE && /^[0-9a-f]{32}$/.test(value)) {
      return { userId: value, setCookie: null };
    }
  }
  const userId = randomId();
  return {
    userId,
    setCookie: VISITOR_COOKIE + "=" + userId +
      "; Path=/; Max-Age=" + VISITOR_COOKIE_MAX_AGE +
      "; SameSite=Lax; Secure; HttpOnly",
  };
}

// 16 hex chars of HMAC-SHA256. Falls back to a salted non-crypto mix only in
// runtimes without WebCrypto (Workers and Node 22 always have it).
async function hmac16(secret, msg) {
  const subtle = globalThis.crypto && globalThis.crypto.subtle;
  if (subtle) {
    const enc = new TextEncoder();
    const key = await subtle.importKey(
      "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
    );
    const sig = new Uint8Array(await subtle.sign("HMAC", key, enc.encode(msg)));
    return Array.from(sig.slice(0, 8))
      .map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  let h1 = 0x811c9dc5, h2 = 0x01000193;
  for (let i = 0; i < msg.length; i++) {
    h1 = Math.imul(h1 ^ msg.charCodeAt(i), 16777619) >>> 0;
    h2 = Math.imul(h2 + msg.charCodeAt(i), 2246822519) >>> 0;
  }
  return h1.toString(16).padStart(8, "0") + h2.toString(16).padStart(8, "0");
}

// Keep only origin + path; query strings can carry unrelated tracking params.
function cleanReferer(value) {
  if (!value) return "";
  try {
    const u = new URL(value);
    return clip(u.origin + u.pathname, 300);
  } catch {
    return clip(String(value).split("?")[0], 300);
  }
}

function cfInfo(request) {
  const cf = (request && request.cf) || {};
  const h = request.headers;
  return {
    ip: h.get("cf-connecting-ip") || (h.get("x-forwarded-for") || "").split(",")[0].trim() || "",
    country: clip(cf.country || h.get("cf-ipcountry") || "", 8),
    city: clip(cf.city || "", 80),
    asn: clip(cf.asn == null ? "" : cf.asn, 16),
    as_org: clip(cf.asOrganization || "", 120),
    colo: clip(cf.colo || "", 8),
    ray: clip(h.get("cf-ray") || "", 40),
    ua: clip(h.get("user-agent") || "", 300),
    referer: cleanReferer(h.get("referer")),
  };
}

function retentionDays(env) {
  const n = parseInt(env && env.DOWNLOAD_EVENT_RETENTION_DAYS, 10);
  return Number.isFinite(n) && n >= 1 ? Math.min(n, 3650) : RETENTION_DEFAULT;
}

async function ensureSchema(env) {
  if (schemaReady) return;
  for (const sql of DDL) await env.DB.prepare(sql).run();
  // Deployments that already had download_events before user_id existed.
  // "duplicate column name" is expected on fresh tables and is ignored.
  try {
    await env.DB.prepare("ALTER TABLE download_events ADD COLUMN user_id TEXT").run();
  } catch (e) {
    // "duplicate column name" on fresh tables; expected and ignored.
  }
  // Must come AFTER the ALTER: on upgraded tables the column did not exist
  // when the other two indexes were created.
  await env.DB.prepare(
    "CREATE INDEX IF NOT EXISTS idx_download_events_user ON download_events(user_id)"
  ).run();
  schemaReady = true;
}

// ---------------------------------------------------------------- write

export async function recordDownload(env, request, file, when = new Date(), userId = "") {
  try {
    const ts = when.toISOString();
    const day = ts.slice(0, 10); // UTC
    const info = cfInfo(request);

    const fullIp = env && (env.DOWNLOAD_LOG_FULL_IP === "1" ||
      String(env.DOWNLOAD_LOG_FULL_IP).toLowerCase() === "true");
    const storedIp = fullIp ? (info.ip || "unknown") : maskIp(info.ip);

    const secret = (env && (env.DOWNLOAD_HASH_SECRET || env.UNSUB_SECRET)) ||
      "slidevault-download-events-v1";
    const fingerprint = await hmac16(secret,
      [secret, maskIp(info.ip), info.ua, info.asn, info.as_org].join("|"));
    const user = /^[0-9a-f]{32}$/.test(userId) ? userId : "";

    await ensureSchema(env);

    await env.DB.prepare(
      "INSERT INTO download_events (" + COLUMNS.join(", ") + ") " +
      "VALUES (" + COLUMNS.map(() => "?").join(", ") + ")"
    ).bind(
      ts, day, file,
      storedIp, user, fingerprint, info.country, info.city, info.asn, info.as_org,
      info.colo, info.ua, info.referer, info.ray
    ).run();

    // Cheap, idempotent retention: once per UTC day per isolate.
    if (lastPruneDay !== day) {
      lastPruneDay = day;
      const cutoff = new Date(when.getTime() - retentionDays(env) * 86400000)
        .toISOString().slice(0, 10);
      await env.DB.prepare("DELETE FROM download_events WHERE day < ?").bind(cutoff).run();
    }
  } catch (e) {
    // Diagnostics must never affect the download, the lifetime counter or
    // the daily rollup. Swallow everything.
  }
}

// ---------------------------------------------------------------- read

export async function queryEvents(env, opts) {
  const days = Math.min(Math.max(parseInt(opts.days, 10) || 7, 1), 90);
  const limit = Math.min(Math.max(parseInt(opts.limit, 10) || 100, 1), 500);
  const from = new Date(Date.now() - (days - 1) * 86400000).toISOString().slice(0, 10);

  let sql = "SELECT " + COLUMNS.join(", ") + " FROM download_events WHERE day >= ?";
  const args = [from];
  if (opts.file) {
    sql += " AND lower(file) = lower(?)";
    args.push(opts.file);
  }
  if (opts.user) {
    sql += " AND user_id = ?";
    args.push(opts.user);
  }
  sql += " ORDER BY ts DESC LIMIT ?";
  args.push(limit);

  const res = await env.DB.prepare(sql).bind(...args).all();
  return {
    days,
    from,
    retention_days: retentionDays(env),
    limit,
    count: (res.results || []).length,
    rows: res.results || [],
  };
}
