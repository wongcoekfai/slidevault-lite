// Shared welcome-email builder + sender for the subscribe flow.
//
// Runs inside Cloudflare Pages Functions (no dependencies, no bundler needed).
// The email is sent through Brevo's transactional API with a single secret:
//   BREVO_API_KEY   — required; when missing the flow silently skips sending
//   EMAIL_FROM      — optional, defaults to "Slide Vault <hello@slidevaulte.com>"
//   UNSUB_SECRET    — optional, used to sign unsubscribe links (falls back to the API key)

import { KITS } from "./kits.js";

const encoder = new TextEncoder();

const SITE = "https://slidevaulte.com";

// Only ids from the generated whitelist resolve to a bundle.
function kitFor(id) {
  return id && Object.prototype.hasOwnProperty.call(KITS, id) ? KITS[id] : null;
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
  .replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function hex(buf) {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// Short HMAC so unsubscribe links cannot be forged by guessing addresses alone.
// Note: if no secret is configured at all the link is still signed with a
// constant, which only stops casual tampering — set UNSUB_SECRET in production.
export async function unsubToken(secret, email) {
  const key = await crypto.subtle.importKey(
    "raw", encoder.encode(secret || "slidevault-dev"), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, encoder.encode("unsub:" + email));
  return hex(sig).slice(0, 20);
}

export function unsubUrl(email, token) {
  return SITE + "/unsubscribe?e=" + encodeURIComponent(email) + "&t=" + token;
}

export function welcomeSubject(kitId) {
  const kit = kitFor(kitId);
  return kit
    ? "Your " + kit.name + " is ready (+ 7 browser tools)"
    : "Your free PowerPoint templates (+ 7 browser tools)";
}

export function welcomeText(unsub, orgAddress, kitId) {
  const kit = kitFor(kitId);
  return [
    "YOUR FREE POWERPOINT TEMPLATES ARE READY",
    "=========================================",
    "",
    "Thanks for subscribing!",
    "",
    "Everything on Slide Vault is free to download, fully editable and free for",
    "commercial use -- no signup walls, no watermarks.",
    "",
    "Browse all 51 templates: " + SITE + "/#templates",
    "",
    ...(kit ? [
      "YOUR " + kit.name.toUpperCase() + " IS READY",
      kit.decks + " editable .pptx decks in one ZIP:",
      SITE + kit.zip,
      "",
    ] : []),
    "START WITH THESE",
    "- SaaS Startup Pitch Deck (12 slides, problem to ask):",
    "  " + SITE + "/templates/saas-startup-pitch-deck-template/",
    "- Sales QBR Template (usage, adoption, value, risks):",
    "  " + SITE + "/templates/sales-qbr-template/",
    "- Lesson Plan Template (objectives to assessment):",
    "  " + SITE + "/templates/lesson-plan-template/",
    "",
    "AND 7 TOOLS YOU WILL ACTUALLY USE",
    "Merge, compress, split decks, extract images, strip speaker notes, clean",
    "metadata and count slides & words -- everything runs inside your browser,",
    "so confidential decks never leave your device.",
    "",
    "Open the free PPT tools: " + SITE + "/tools/",
    "",
    "POPULAR GUIDES",
    "- Merge PowerPoint decks without losing the design:",
    "  " + SITE + "/blog/how-to-merge-powerpoint-presentations/",
    "- Compress a PowerPoint without wrecking the images:",
    "  " + SITE + "/blog/how-to-compress-a-powerpoint/",
    "- Remove speaker notes before you send a deck:",
    "  " + SITE + "/blog/how-to-remove-speaker-notes-from-powerpoint/",
    "",
    "---------------------------------------------",
    "You are receiving this because you subscribed at slidevaulte.com.",
    "Unsubscribe: " + unsub,
    "About Slide Vault: " + SITE + "/about/",
    ...(orgAddress ? ["Slide Vault, " + orgAddress] : []),
  ].join("\n");
}

export function welcomeHtml(unsub, orgAddress, kitId) {
  const kit = kitFor(kitId);
  const link = (href, label) =>
    '<a href="' + href + '" style="color:#3b82f6;text-decoration:none;">' + label + "</a>";

  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${welcomeSubject(kitId)}</title></head>
<body style="margin:0;padding:0;background:#eef1f6;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">51 free .pptx templates and 7 privacy-first tools. No signup, no watermark.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f6;padding:24px 0;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:92%;background:#ffffff;border-radius:12px;overflow:hidden;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <tr><td style="background:#0b1020;padding:26px 32px;">
    <span style="color:#e8ecf5;font-size:20px;font-weight:700;">Slide<span style="color:#22d3ee;">Vault</span></span>
    <div style="color:#9aa6c2;font-size:13px;margin-top:4px;">Free PowerPoint &amp; Google Slides templates</div>
  </td></tr>
  <tr><td style="padding:32px;">
    <h1 style="margin:0 0 12px;font-size:22px;line-height:1.3;color:#0b1020;">Thanks for subscribing</h1>
    <p style="margin:0 0 18px;font-size:15px;line-height:1.6;color:#3c4658;">
      Everything on Slide Vault is free to download, fully editable and free for commercial use &mdash;
      no signup walls, no watermarks, no &ldquo;personal use only&rdquo;.
    </p>
    <table role="presentation" cellpadding="0" cellspacing="0"><tr>
      <td style="background:#3b82f6;border-radius:8px;">
        <a href="${SITE}/#templates" style="display:inline-block;padding:13px 26px;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;">Browse all free templates &rarr;</a>
      </td>
    </tr></table>

    ${kit ? `<p style="margin:28px 0 8px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#8a94a8;">Your ${esc(kit.name)} is ready</p>
    <table role="presentation" cellpadding="0" cellspacing="0"><tr>
      <td style="background:#e8f2fe;border-radius:8px;">
        <a href="${SITE}${kit.zip}" style="display:inline-block;padding:13px 26px;color:#2563eb;font-size:15px;font-weight:600;text-decoration:none;">Download ${kit.decks} decks in one ZIP &rarr;</a>
      </td>
    </tr></table>
    <p style="margin:10px 0 0;font-size:13px;line-height:1.6;color:#8a94a8;">Keep this email — the kit link works whenever you need it again.</p>` : ""}

    <p style="margin:28px 0 8px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#8a94a8;">Start with these</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:15px;line-height:1.7;color:#3c4658;">
      <tr><td style="padding:6px 0;border-bottom:1px solid #eef1f6;">${link(SITE + "/templates/saas-startup-pitch-deck-template/", "SaaS Startup Pitch Deck")} &mdash; 12 slides, problem to ask</td></tr>
      <tr><td style="padding:6px 0;border-bottom:1px solid #eef1f6;">${link(SITE + "/templates/sales-qbr-template/", "Sales QBR Template")} &mdash; usage, adoption, value, risks</td></tr>
      <tr><td style="padding:6px 0;">${link(SITE + "/templates/lesson-plan-template/", "Lesson Plan Template")} &mdash; objectives to assessment</td></tr>
    </table>

    <p style="margin:28px 0 8px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#8a94a8;">And 7 tools you will actually use</p>
    <p style="margin:0 0 10px;font-size:15px;line-height:1.6;color:#3c4658;">
      Merge, compress, split decks, extract images, strip speaker notes, clean metadata and count
      slides &amp; words &mdash; everything runs inside your browser, so confidential decks never
      leave your device.
    </p>
    <table role="presentation" cellpadding="0" cellspacing="0"><tr>
      <td style="background:#e8f2fe;border-radius:8px;">
        <a href="${SITE}/tools/" style="display:inline-block;padding:11px 22px;color:#2563eb;font-size:14px;font-weight:600;text-decoration:none;">Open the free PPT tools &rarr;</a>
      </td>
    </tr></table>

    <p style="margin:28px 0 8px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#8a94a8;">Popular guides</p>
    <p style="margin:0;font-size:15px;line-height:1.8;color:#3c4658;">
      ${link(SITE + "/blog/how-to-merge-powerpoint-presentations/", "Merge PowerPoint decks without losing the design")}<br>
      ${link(SITE + "/blog/how-to-compress-a-powerpoint/", "Compress a PowerPoint without wrecking the images")}<br>
      ${link(SITE + "/blog/how-to-remove-speaker-notes-from-powerpoint/", "Remove speaker notes before you send a deck")}
    </p>
  </td></tr>
  <tr><td style="background:#f7f8fb;padding:20px 32px;border-top:1px solid #e6e9ef;">
    <p style="margin:0;font-size:12px;line-height:1.6;color:#8a94a8;">
      You are receiving this because you subscribed at slidevaulte.com.<br>
      <a href="${unsub}" style="color:#8a94a8;">Unsubscribe</a> &nbsp;&middot;&nbsp;
      <a href="${SITE}/about/" style="color:#8a94a8;text-decoration:none;">About Slide Vault</a>
      ${orgAddress ? `<br>Slide Vault, ${orgAddress}` : ""}
    </p>
  </td></tr>
</table>
</td></tr></table>
</body></html>`;
}

// Sends the welcome email. Never throws: a failed send must not break signup.
// Returns { sent, status?, reason? } for logging.
export async function sendWelcome(env, email, unsub, kitId) {
  if (!env || !env.BREVO_API_KEY) return { sent: false, reason: "no-api-key" };

  const fromRaw = env.EMAIL_FROM || "Slide Vault <hello@slidevaulte.com>";
  const m = /^(.*)<([^>]+)>$/.exec(fromRaw.trim());
  const sender = m
    ? { name: (m[1] || "Slide Vault").trim() || "Slide Vault", email: m[2].trim() }
    : { name: "Slide Vault", email: fromRaw.trim() };

  // CAN-SPAM / anti-spam rules: every commercial email must carry a valid
  // physical postal address. Set ORG_ADDRESS once the Brevo organization
  // address is chosen — until then the footer simply omits it.
  const orgAddress = (env.ORG_ADDRESS || "").trim();

  const payload = {
    sender,
    to: [{ email }],
    subject: welcomeSubject(kitId),
    htmlContent: welcomeHtml(unsub, orgAddress, kitId),
    textContent: welcomeText(unsub, orgAddress, kitId),
    headers: {
      "List-Unsubscribe": "<" + unsub + ">",
      "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    },
  };

  try {
    const res = await fetch("https://api.brevo.com/v3/smtp/email", {
      method: "POST",
      headers: {
        "api-key": env.BREVO_API_KEY,
        "content-type": "application/json",
        accept: "application/json",
      },
      body: JSON.stringify(payload),
    });
    return { sent: res.ok, status: res.status };
  } catch (err) {
    return { sent: false, reason: String(err && err.message ? err.message : err) };
  }
}
