// Pages Function: handles POST /subscribe, stores email in Cloudflare D1.
// No third party ever sees the address — it lives only in your Cloudflare account.
// Uses URLSearchParams (no request.formData) to avoid the node:stream dependency.

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Pay-interest poll answers (optional radio in subscribe forms).
// Whitelist — anything else is dropped, so the column can never hold junk.
const WANTS = new Set(["premium-templates", "pro-tools", "membership", "nothing"]);

export async function onRequestPost(context) {
  const { env, request } = context;

  let params;
  try {
    params = new URLSearchParams(await request.text());
  } catch {
    return htmlResponse(400, "Bad request.");
  }

  // Basic bot trap: a hidden field real users never fill.
  if (params.get("website")) {
    // Pretend success to the bot, store nothing.
    return htmlResponse(200, "Thanks for subscribing!");
  }

  const email = (params.get("email") || "").trim().toLowerCase();
  if (!EMAIL_RE.test(email)) {
    return htmlResponse(400, "Please enter a valid email address.");
  }

  const source = (params.get("source") || "newsletter").slice(0, 32);

  const rawWant = (params.get("want") || "").trim();
  const want = WANTS.has(rawWant) ? rawWant : "";

  // Storage strategy, most specific first:
  //  1. email + created_at + source + want   (after "ALTER TABLE subscribers ADD COLUMN want TEXT")
  //  2. no want column yet — fold the answer into source ("bundle_home__pro-tools") so the
  //     poll data is still captured with zero migration
  //  3. original insert — subscribe never breaks
  try {
    await env.DB.prepare(
      "INSERT OR IGNORE INTO subscribers (email, created_at, source, want) VALUES (?, ?, ?, ?)"
    ).bind(email, Date.now(), source, want || null).run();
  } catch (e) {
    try {
      const source2 = want ? `${source}__${want}` : source;
      await env.DB.prepare(
        "INSERT OR IGNORE INTO subscribers (email, created_at, source) VALUES (?, ?, ?)"
      ).bind(email, Date.now(), source2).run();
    } catch (e2) {
      try {
        await env.DB.prepare(
          "INSERT OR IGNORE INTO subscribers (email, created_at) VALUES (?, ?)"
        ).bind(email, Date.now()).run();
      } catch (e3) {
        return htmlResponse(500, "Something went wrong. Please try again later.");
      }
    }
  }

  return htmlResponse(200, "You're subscribed! We'll email you when new decks drop.");
}

function htmlResponse(status, message) {
  const body = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slide Vault</title>
<style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0b1020;color:#e6edf6;
       display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0}
  .card{background:#11182e;border:1px solid #ffffff14;border-radius:16px;padding:32px 40px;text-align:center;max-width:420px}
  h1{font-size:1.4rem;margin:0 0 8px}
  p{color:#9fb0c8;margin:0 0 20px}
  a{color:#22d3ee;text-decoration:none;font-weight:600}
</style></head>
<body><div class="card">
  <h1>${status < 400 ? "✅ Subscribed" : "⚠️ Notice"}</h1>
  <p>${message}</p>
  <a href="/">← Back to Slide Vault</a>
</div></body></html>`;
  return new Response(body, {
    status,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}
