# Slide Vault — Static Migration (WordPress → Cloudflare Pages)

A lightweight, zero-build static replacement for the WordPress site **slidevaulte.com**.
All 13 templates, their `.pptx` files, and preview images were pulled from the live
site. Frontend is plain HTML/CSS/JS — commit to GitHub, deploy to Cloudflare Pages.

## Project structure
```
slidevault-lite/
├── index.html              # home + template grid + about + subscribe
├── assets/
│   ├── style.css           # dark theme, responsive grid
│   ├── templates.js        # TEMPLATE CATALOG (edit this to add/remove templates)
│   ├── app.js              # renders the grid from templates.js
│   └── img/                # 12 preview thumbnails (pulled from live site)
├── files/                  # 13 downloaded .pptx templates
├── sitemap.xml
└── README.md
```

## Local preview
```bash
cd slidevault-lite
python3 -m http.server 8080
# open http://localhost:8080
```

## Deploy to Cloudflare Pages (recommended — DNS already on Cloudflare)
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
1. Drop the `.pptx` into `files/` and the preview into `assets/img/`.
2. Add one object to `window.TEMPLATES` in `assets/templates.js`.
3. `git commit && git push` → auto-redeploy.

## Notes
- **Large binaries**: the 13 `.pptx` total ~30 MB. Fine for Cloudflare Pages, but if the
  library grows, move files to **Cloudflare R2** (private) and point `download` at signed URLs.
- **Subscribe form**: set the `action` in `index.html` to a Formspree or Cloudflare Forms endpoint.
- **Paid tier** (future): add a `price` + `buy` field and a Stripe Payment Link / Lemon Squeezy URL.
- **Search**: if templates exceed ~50, add Pagefind for static search.
