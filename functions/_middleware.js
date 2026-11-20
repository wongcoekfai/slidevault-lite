// Canonicalise www -> apex.
//
// Cloudflare Pages `_redirects` matches paths only, it cannot match a
// hostname, so the www redirect has to be a Pages Function.
// If www.slidevaulte.com is not routed to this Pages project, also add a
// zone-level Redirect Rule in the Cloudflare dashboard:
//   when hostname equals "www.slidevaulte.com" -> 301 to
//   concat("https://slidevaulte.com", http.request.uri.path)
export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.hostname.toLowerCase().startsWith("www.")) {
    const target = new URL(url.toString());
    target.hostname = url.hostname.slice(4);
    return Response.redirect(target.toString(), 301);
  }
  return next();
}
