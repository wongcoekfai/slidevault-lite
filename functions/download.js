// GET /download?file=Name.pptx
// Increments the download counter in D1, then 302-redirects to the real file.
export async function onRequestGet(context) {
  const { env, request } = context;
  const url = new URL(request.url);
  const file = url.searchParams.get("file") || "";

  // Allowlist: plain .pptx filenames only, no paths, no traversal.
  if (!/^[A-Za-z0-9._-]+\.pptx$/.test(file)) {
    return new Response("Not found", { status: 404 });
  }

  try {
    await env.DB.prepare(
      "INSERT INTO downloads (file, count) VALUES (?, 1) " +
      "ON CONFLICT(file) DO UPDATE SET count = count + 1"
    ).bind(file).run();
  } catch (e) {
    // Counting must never block a download.
  }

  return Response.redirect(new URL("/files/" + file, url.origin).toString(), 302);
}
