#!/usr/bin/env node
// Offline test for the subscribe → welcome-email → unsubscribe chain.
//
// Copies functions/*.js to a temp dir as .mjs (Node needs ESM extensions),
// mocks D1, intercepts the Brevo API call, and exercises every branch:
// new subscriber, duplicate, missing API key, failed send, honeypot bot,
// unsubscribe (valid token / forged token / one-click POST).
//
//   node tools/test-welcome-email.mjs

import { cpSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DIR = join(tmpdir(), `svtest-${process.pid}`);

rmSync(DIR, { recursive: true, force: true });
mkdirSync(join(DIR, "_lib"), { recursive: true });
cpSync(join(ROOT, "functions", "_lib", "welcome.js"), join(DIR, "_lib", "welcome.mjs"));
for (const name of ["subscribe.js", "unsubscribe.js"]) {
  const src = await import("node:fs").then((fs) => fs.readFileSync(join(ROOT, "functions", name), "utf8"));
  await import("node:fs").then((fs) =>
    fs.writeFileSync(join(DIR, name.replace(/\.js$/, ".mjs")), src.replace('"./_lib/welcome.js"', '"./_lib/welcome.mjs"')));
}

const calls = [];
let pending = [];
const collect = (p) => pending.push(p);
const settle = async () => {
  await Promise.all(pending.map((p) => Promise.resolve(p).catch(() => {})));
  pending = [];
};

globalThis.fetch = async (url, init) => {
  calls.push({ url: String(url), init });
  return new Response(JSON.stringify({ messageId: "<test@brevo>" }), { status: 201 });
};

const { onRequestPost } = await import(join(DIR, "subscribe.mjs"));
const unsub = await import(join(DIR, "unsubscribe.mjs"));

function fakeDB(changes) {
  const log = [];
  return {
    log,
    prepare(sql) {
      return {
        bind(...args) {
          return { async run() { log.push({ sql, args }); return { meta: { changes } }; } };
        },
      };
    },
  };
}

const post = (body) =>
  new Request("https://slidevaulte.com/subscribe", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(body).toString(),
  });

let failures = 0;
const check = (cond, msg) => { console.log((cond ? "  ✓ " : "  ✗ ") + msg); if (!cond) failures++; };

// 1. new subscriber, key configured → mail sent, success page promises inbox
{
  const env = { BREVO_API_KEY: "xkeysib-test", DB: fakeDB(1) };
  const res = await onRequestPost({ env, request: post({ email: "Ada@Example.com ", want: "pro-tools", source: "bundle_home" }), waitUntil: collect });
  await settle();
  const body = await res.text();
  check(res.status === 200, "status 200");
  check(body.includes("Check your inbox"), "success page mentions the inbox");
  check(body.includes("/#templates") && body.includes("/tools/"), "success page offers next steps");
  check(calls.length === 1 && calls[0].url.includes("api.brevo.com/v3/smtp/email"), "one Brevo call to smtp/email");
  const payload = JSON.parse(calls[0].init.body);
  check(payload.to[0].email === "ada@example.com", "email lowercased + trimmed");
  check(payload.sender.email === "hello@slidevaulte.com", "sender defaults to hello@slidevaulte.com");
  check(/welcome|templates/i.test(payload.subject), "subject mentions templates");
  check(payload.htmlContent.includes("/unsubscribe?e="), "html contains unsubscribe link");
  check(payload.textContent.includes("Unsubscribe:"), "plain-text part present");
  check(Boolean(payload.headers["List-Unsubscribe"]), "List-Unsubscribe header set");
  check(calls[0].init.headers["api-key"] === "xkeysib-test", "api-key header uses the secret");
  check(!JSON.parse(calls[0].init.body).htmlContent.includes("Slide Vault, 12 "), "no postal address in footer when ORG_ADDRESS unset");
}

// 1b. ORG_ADDRESS set → footer carries the physical postal address
{
  calls.length = 0;
  const env = { BREVO_API_KEY: "xkeysib-test", ORG_ADDRESS: "12 Futian Rd, Shenzhen 518000, China", DB: fakeDB(1) };
  await onRequestPost({ env, request: post({ email: "org@example.com" }), waitUntil: collect });
  await settle();
  const payload = JSON.parse(calls[0].init.body);
  check(payload.htmlContent.includes("Slide Vault, 12 Futian Rd"), "html footer carries the postal address");
  check(payload.textContent.includes("Slide Vault, 12 Futian Rd"), "text footer carries the postal address");
}

// 2. duplicate address → no email
{
  calls.length = 0;
  const env = { BREVO_API_KEY: "xkeysib-test", DB: fakeDB(0) };
  const res = await onRequestPost({ env, request: post({ email: "ada@example.com" }), waitUntil: collect });
  await settle();
  await res.text();
  check(calls.length === 0, "duplicate does not trigger a second email");
}

// 3. no API key → signup still works, no call, honest copy
{
  calls.length = 0;
  const env = { DB: fakeDB(1) };
  const res = await onRequestPost({ env, request: post({ email: "bob@example.com" }), waitUntil: collect });
  await settle();
  const body = await res.text();
  check(res.status === 200, "status 200 without a key");
  check(calls.length === 0, "no Brevo call without a key");
  check(!body.includes("Check your inbox"), "does not promise an email it cannot send");
}

// 4. Brevo rejects (403) → signup still succeeds
{
  globalThis.fetch = async () => new Response("denied", { status: 403 });
  const env = { BREVO_API_KEY: "bad", DB: fakeDB(1) };
  const res = await onRequestPost({ env, request: post({ email: "cy@example.com" }), waitUntil: collect });
  await settle();
  check(res.status === 200, "signup survives a failed send");
  await res.text();
  globalThis.fetch = async (url, init) => { calls.push({ url: String(url), init }); return new Response("{}", { status: 201 }); };
}

// 5. honeypot still blocks bots
{
  calls.length = 0;
  const env = { BREVO_API_KEY: "xkeysib-test", DB: fakeDB(1) };
  const res = await onRequestPost({ env, request: post({ email: "bot@example.com", website: "http://spam" }), waitUntil: collect });
  await settle();
  check(res.status === 200, "honeypot returns fake success");
  check(calls.length === 0, "honeypot sends nothing");
  await res.text();
}

// 6. unsubscribe round-trip
{
  const { unsubToken, unsubUrl } = await import(join(DIR, "_lib", "welcome.mjs"));
  const env = { BREVO_API_KEY: "xkeysib-test", DB: fakeDB(1) };
  const token = await unsubToken(env.BREVO_API_KEY, "ada@example.com");
  const link = unsubUrl("ada@example.com", token);
  check(link.startsWith("https://slidevaulte.com/unsubscribe?e="), "unsubscribe link shape ok");

  const okRes = await unsub.onRequestGet({ env, request: new Request(link) });
  const okBody = await okRes.text();
  check(okRes.status === 200 && okBody.includes("off the list"), "valid token deletes the address");
  check(env.DB.log.at(-1).sql.startsWith("DELETE FROM subscribers"), "DELETE issued");

  const badRes = await unsub.onRequestGet({ env, request: new Request(link.replace(/t=../, "t=ff")) });
  check(badRes.status === 400, "forged token rejected");
  await badRes.text();

  const postRes = await unsub.onRequestPost({ env, request: new Request(link, { method: "POST" }) });
  check(postRes.status === 200, "POST (one-click) accepted");
  await postRes.text();
}

// 7. rendered email size sanity (Gmail clips messages over ~102 KB)
{
  const { welcomeHtml } = await import(join(DIR, "_lib", "welcome.mjs"));
  const kb = welcomeHtml("https://slidevaulte.com/unsubscribe?e=a&t=b").length / 1024;
  check(kb < 60, `email html stays small for inboxes (${kb.toFixed(1)} KB)`);
}

rmSync(DIR, { recursive: true, force: true });
console.log(failures === 0 ? "\nALL PASS" : `\n${failures} FAILURE(S)`);
process.exit(failures === 0 ? 0 : 1);
