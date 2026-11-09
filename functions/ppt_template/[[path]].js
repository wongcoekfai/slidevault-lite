// 301 legacy WordPress template URLs to the static detail pages.
// WP-era slugs were Capitalized ("Business-Plan-Template") while the static
// pages are lowercase — and CF Pages _redirects :splat preserves case, which
// sent those redirects to 404s (GSC "Redirect error / Not found").
// This catch-all lowercases the slug before redirecting.
export async function onRequestGet({ request }) {
  const url = new URL(request.url);
  const rest = decodeURIComponent(url.pathname.replace(/^\/ppt_template\/?/, ""));
  const slug = rest.toLowerCase().replace(/^\/+|\/+$/g, "");
  const target = slug ? `/templates/${slug}/` : "/#templates";
  return Response.redirect(new URL(target, url.origin).toString(), 301);
}
