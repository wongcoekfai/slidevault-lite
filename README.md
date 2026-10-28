# Slide Vault — Static Migration (WordPress → Cloudflare Pages)

A lightweight, zero-build static replacement for the WordPress site **slidevaulte.com**.
All 13 templates, their `.pptx` files, and preview images were pulled from the live
site. Frontend is plain HTML/CSS/JS — commit to GitHub, deploy to Cloudflare Pages.

## Project structure
```
slidevault-lite/
├── index.html              # home + grid + category filter + FAQ + subscribe
├── 404.html                # real 404 (stops Cloudflare's soft-404 fallback)
├── _redirects              # 301s from old WordPress URLs
├── robots.txt  sitemap.xml
├── assets/
│   ├── style.css           # dark theme, grid, galleries, lightbox
│   ├── templates.js        # TEMPLATE CATALOG (metadata + gallery[], auto-updated)
│   ├── app.js              # renders the homepage grid + filters
│   ├── gallery.js          # multi-page preview viewer / lightbox
│   ├── img/                # cover thumbnails
│   └── img/gallery/<slug>/ # per-template slide previews (you supply these)
├── files/                  # 13 .pptx templates
├── templates/<slug>/index.html   # 13 generated detail pages
├── functions/
│   ├── subscribe.js        # POST /subscribe → D1  (no third party sees emails)
│   ├── download.js         # GET /download  → counts, then 302 to the file
│   └── downloads.js        # GET /downloads → JSON counts
├── wrangler.toml           # D1 binding + nodejs_compat
└── tools/gen_pages.py      # rebuilds detail pages + sitemap from templates.js
```

## Local preview
```bash
cd slidevault-lite
python3 -m http.server 8080
# open http://localhost:8080
```

## Deploy to Cloudflare Pages
Already wired up: repo `wongcoekfai/slidevault-lite` → Pages project `slidevault-lite` → `https://slidevaulte.com`.

Manual deploy from this folder:
```bash
export CLOUDFLARE_API_TOKEN=<token> CLOUDFLARE_ACCOUNT_ID=9696ba91cd615d382166b699ae0bf17b
npx wrangler pages deploy . --project-name slidevault-lite --branch main
```

Original setup (already done, for reference):
1. Push this folder to a GitHub repo.
1. Push this folder to a GitHub repo.
2. Cloudflare Dashboard → **Pages** → **Create via GitHub**.
3. Build settings: **Framework = None**, **Build command = (empty)**, **Output directory = `/` (root)**.
4. Deploy → you get a `*.pages.dev` URL for free.

## Keep the Spaceship domain
- Spaceship stays the **registrar** (no transfer needed).
- Cloudflare Pages → **Custom domains** → add `slidevaulte.com`.
- Cloudflare gives you CNAME / A records; paste them into **Spaceship DNS**.
- (Optional) While cutover propagates, keep the old WordPress site live and add 301
  redirects from old `/ppt_template/<slug>/` URLs to `/#templates` to preserve any links.

## Adding / editing a template (the new "CMS" workflow)
1. Drop the `.pptx` into `files/` and a cover image into `assets/img/`.
2. Add one object to `window.TEMPLATES` in `assets/templates.js`.
3. Run `python3 tools/gen_pages.py` to (re)build the detail page + sitemap.
4. `git commit && git push`, then redeploy.

## Multi-page preview galleries
Each template detail page shows a **slide gallery** (big image + thumbnail strip +
keyboard/swipe navigation + click-to-zoom lightbox).

To add photos for a template, drop them here:

```
assets/img/gallery/<slug>/01.jpg
assets/img/gallery/<slug>/02.jpg
assets/img/gallery/<slug>/03.jpg
...
```

- Folder name = the template's `slug` in `assets/templates.js`.
- Name files `01 / 02 / 03 ...` to control slide order (natural sort).
- Accepted formats: `.jpg .jpeg .png .webp`.
- Then run the generator — it picks them up automatically and writes them into
  `templates.js` as `gallery: [...]`:

```bash
python3 tools/gen_pages.py            # regenerate detail pages + sitemap
python3 tools/gen_pages.py --resize   # also downscale photos wider than 1600px
```

Graceful degradation: **0 photos** → "Preview coming soon" placeholder;
**1 photo** → plain image, no nav controls; **2+ photos** → full gallery with
a `N slides` badge.

> Note: `tools/gen_pages.py` rewrites `assets/templates.js`, but only the
> `gallery: [...]` field is machine-generated — your `title / tag / cat / desc /
> img / file` edits are preserved.

## Notes
- **Large binaries**: the 13 `.pptx` total ~30 MB. Fine for Cloudflare Pages, but if the
  library grows, move files to **Cloudflare R2** (private) and point `download` at signed URLs.
- **Subscribe form**: posts to `/subscribe` (Pages Function) → stored in D1 database
  `slidevault_subs`, table `subscribers`. Emails never touch a third party. Query them in
  Cloudflare Dashboard → D1 → Console, or ask me to export a CSV.
- **Download stats**: all download buttons go through `/download?file=...`, which increments
  the `downloads` table then 302s to the real `.pptx`. `GET /downloads` returns JSON.
- **Images must be root-absolute** (`/assets/...`). Detail pages live at
  `/templates/<slug>/`, so relative paths would resolve to the wrong directory.
- **Paid tier** (future): add a `price` + `buy` field and a Stripe Payment Link / Lemon Squeezy URL.
- **Search**: if templates exceed ~50, add Pagefind for static search.
