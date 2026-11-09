// Pages Function: GET|POST /unsubscribe?e=<email>&t=<token>
//
// Removes the address from D1. Reachable from the footer link of every
// welcome email and from the List-Unsubscribe header, which is why it also
// accepts POST (mailbox providers send "List-Unsubscribe=One-Click" that way).
//
// The token is the HMAC issued by functions/subscribe.js, so a stranger cannot
// unsubscribe addresses they merely guess.

import { unsubToken } from "./_lib/welcome.js";

export async function onRequestGet(context) {
  return handle(context);
}

export async function onRequestPost(context) {
  return handle(context);
}

async function handle(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const email = (url.searchParams.get("e") || "").trim().toLowerCase();
  const token = (url.searchParams.get("t") || "").trim();

  if (!email) return page(400, "Missing address", "This unsubscribe link looks incomplete.");

  const secret = env.UNSUB_SECRET || env.BREVO_API_KEY || "";
  const expected = await unsubToken(secret, email);
  if (token && token !== expected) {
    return page(400, "Link expired", "This unsubscribe link is not valid any more. Reply to any of our emails and we will remove you manually.");
  }

  let removed = false;
  try {
    const res = await env.DB.prepare("DELETE FROM subscribers WHERE email = ?").bind(email).run();
    removed = Boolean(res.meta && res.meta.changes);
  } catch (err) {
    return page(500, "Something went wrong", "We could not update our list just now. Please try again in a minute.");
  }

  return page(
    200,
    "You're unsubscribed",
    removed
      ? "That address is off the list. No hard feelings — the templates stay free and ungated."
      : "That address was not on the list, so there is nothing left to remove."
  );
}

function page(status, title, message) {
  const body = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title} — Slide Vault</title>
<style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0b1020;color:#e6edf6;
       display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;padding:24px}
  .card{background:#11182e;border:1px solid #ffffff14;border-radius:16px;padding:32px 40px;text-align:center;max-width:440px}
  h1{font-size:1.35rem;margin:0 0 8px}
  p{color:#9fb0c8;margin:0 0 20px;line-height:1.6}
  a{color:#22d3ee;text-decoration:none;font-weight:600}
</style></head>
<body><div class="card">
  <h1>${title}</h1>
  <p>${message}</p>
  <a href="/">← Back to Slide Vault</a>
</div></body></html>`;
  return new Response(body, {
    status,
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
  });
}
