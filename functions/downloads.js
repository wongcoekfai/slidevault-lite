// GET /downloads            -> JSON { file: count, ... } for all files
// GET /downloads?file=X.pptx -> JSON { file: "X.pptx", count: N }
export async function onRequestGet(context) {
  const { env, request } = context;
  const url = new URL(request.url);
  const file = url.searchParams.get("file");

  try {
    if (file) {
      const row = await env.DB.prepare(
        "SELECT file, count FROM downloads WHERE file = ?"
      ).bind(file).first();
      return json({ file, count: row ? row.count : 0 });
    }
    const { results } = await env.DB.prepare(
      "SELECT file, count FROM downloads ORDER BY count DESC"
    ).all();
    const out = {};
    for (const r of results) out[r.file] = r.count;
    return json(out);
  } catch (e) {
    return json({ error: "unavailable" }, 500);
  }
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}
