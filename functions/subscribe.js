// Pages Function: handles POST /subscribe, stores email in Cloudflare D1,
// then fires the welcome email through Brevo (see functions/_lib/welcome.js).
// No third party ever sees the address — it lives only in your Cloudflare account.
// Uses URLSearchParams (no request.formData) to avoid the node:stream dependency.

import { unsubToken, unsubUrl, sendWelcome } from "./_lib/welcome.js";
// Generated from tools/kits.py by tools/gen_bundles.py — a strict whitelist so
// the `kit` form field can never point at an arbitrary file on the site.
import { KITS } from "./_lib/kits.js";

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
  const rawKit = (params.get("kit") || "").trim();
  const kit = Object.prototype.hasOwnProperty.call(KITS, rawKit) ? KITS[rawKit] : null;
  // Record the chosen kit alongside the source so D1 shows which bundle people
  // actually want. Bounded length — the value can only come from the whitelist.
  const storedSource = (source + (kit ? "__kit=" + rawKit : "")).slice(0, 64);

  const rawWant = (params.get("want") || "").trim();
  const want = WANTS.has(rawWant) ? rawWant : "";

  // Storage strategy, most specific first:
  //  1. email + created_at + source + want   (after "ALTER TABLE subscribers ADD COLUMN want TEXT")
  //  2. no want column yet — fold the answer into source ("bundle_home__pro-tools") so the
  //     poll data is still captured with zero migration
  //  3. original insert — subscribe never breaks
  //
  // `isNew` tells us whether this address was actually added (INSERT OR IGNORE
  // reports 0 changes for a duplicate). Only new subscribers get a welcome
  // email, so re-submitting the form never spams anyone.
  let isNew = false;
  try {
    const r = await env.DB.prepare(
      "INSERT OR IGNORE INTO subscribers (email, created_at, source, want) VALUES (?, ?, ?, ?)"
    ).bind(email, Date.now(), storedSource, want || null).run();
    isNew = !r.meta || r.meta.changes !== 0;
  } catch (e) {
    try {
      const source2 = want ? `${storedSource}__${want}` : storedSource;
      const r = await env.DB.prepare(
        "INSERT OR IGNORE INTO subscribers (email, created_at, source) VALUES (?, ?, ?)"
      ).bind(email, Date.now(), source2).run();
      isNew = !r.meta || r.meta.changes !== 0;
    } catch (e2) {
      try {
        const r = await env.DB.prepare(
          "INSERT OR IGNORE INTO subscribers (email, created_at) VALUES (?, ?)"
        ).bind(email, Date.now()).run();
        isNew = !r.meta || r.meta.changes !== 0;
      } catch (e3) {
        return htmlResponse(500, "Something went wrong. Please try again later.");
      }
    }
  }

  // Welcome email — fire and forget. waitUntil keeps the worker alive after the
  // response is sent, and a failure here never affects the signup itself.
  const mailReady = Boolean(env.BREVO_API_KEY);
  if (isNew && mailReady) {
    const secret = env.UNSUB_SECRET || env.BREVO_API_KEY;
    const job = (async () => {
      const token = await unsubToken(secret, email);
      const result = await sendWelcome(env, email, unsubUrl(email, token), kit ? rawKit : "");
      if (!result.sent) console.warn("welcome email not sent:", JSON.stringify(result));
    })().catch((err) => console.warn("welcome email error:", String(err)));

    if (context.waitUntil) context.waitUntil(job);
    else await job;
  }

  return htmlResponse(
    200,
    kit
      ? `Your ${kit.name} is ready. Download the ZIP below — we've also emailed you the link${mailReady ? "" : " (email delivery is being set up)"}.`
      : (mailReady
        ? "Check your inbox — we just sent your free templates and the 7 browser tools. Nothing there in a minute? Look in spam and mark it as not spam."
        : "You're subscribed! We'll email you when new decks drop."),
    kit
  );
}

function safe(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function htmlResponse(status, message, kit) {
  // Success page doubles as a next step: subscribers who never open the email
  // still get the bundle and one-click paths back into the library.
  const bundle = status < 400 && kit
    ? `<div class="bundle">
    <a class="btn" href="${safe(kit.zip)}" download>&#11015; Download ${safe(kit.name)} ZIP</a>
    <p>${kit.decks} editable .pptx decks &middot; no signup &middot; free for commercial use</p>
  </div>`
    : "";
  const actions = status < 400
    ? `<div class="actions">
    <a class="btn" href="/#kits">Browse all kits</a>
    <a class="btn ghost" href="/tools/">Free PPT tools</a>
  </div>`
    : "";
  const body = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slide Vault</title>
<style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0b1020;color:#e6edf6;
       display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;padding:24px}
  .card{background:#11182e;border:1px solid #ffffff14;border-radius:16px;padding:32px 40px;text-align:center;max-width:460px}
  h1{font-size:1.4rem;margin:0 0 8px}
  p{color:#9fb0c8;margin:0 0 20px;line-height:1.6}
  a{color:#22d3ee;text-decoration:none;font-weight:600}
  .actions{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:0 0 18px}
  .btn{background:#3b82f6;color:#fff;border-radius:10px;padding:11px 20px;font-size:.92rem}
  .btn.ghost{background:transparent;color:#9fb0c8;border:1px solid #ffffff2b}
  .bundle{background:#0e1632;border:1px solid #ffffff1f;border-radius:12px;padding:18px;margin:0 0 18px}
  .bundle .btn{display:inline-block;background:linear-gradient(135deg,#3b82f6,#22d3ee);color:#04122b;font-weight:700}
  .bundle p{font-size:.8rem;margin:10px 0 0;color:#9fb0c8}
</style></head>
<body><div class="card">
  <h1>${status < 400 ? "✅ Subscribed" : "⚠️ Notice"}</h1>
  <p>${message}</p>
  ${bundle}
  ${actions}
  <a href="/">← Back to Slide Vault</a>
</div></body></html>`;
  return new Response(body, {
    status,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}
