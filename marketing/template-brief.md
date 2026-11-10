# Template Sourcing Brief — 9 decks to add (Nov 2026)

Priority is set by real D1 download data (488 downloads / 42 templates since launch):

- **sales** — 3 templates, but Sales Proposal is tied #1 site-wide (17). Demand > supply.
- **startup** — highest per-template average (14.2); pitch decks hold 3 of the top 5 slots.
- **healthcare** — 2 existing decks (NOVA 17 + Healthcare 13, avg 15 = site best). 3 more unlocks the category hub.

Workflow per deck: download .pptx → drop into `files/` → add entry to `assets/templates.js` → run `python3 tools/gen_pages.py && python3 tools/gen_blog.py` → commit & push. Gallery preview images are auto-extracted.

---

## Sales (+3)

| # | File name (target) | Positioning | Search terms to cover |
|---|---|---|---|
| 1 | `QBR-Template.pptx` | Quarterly Business Review for account teams: account health, renewal risk, upsell, next quarter plan | quarterly business review template, QBR powerpoint template |
| 2 | `Pricing-Proposal-Template.pptx` | Quote/proposal with 3-tier pricing table, scope comparison, ROI block | pricing proposal template, quote presentation template |
| 3 | `Channel-Partner-Proposal-Template.pptx` | Partner/reseller pitch: margin structure, co-marketing, enablement, requirements | partner proposal template, channel partner presentation |

## Startup (+3)

| # | File name (target) | Positioning | Search terms to cover |
|---|---|---|---|
| 4 | `Seed-Pitch-Deck-Template.pptx` | Lean seed-round deck, 10–12 slides, one idea per slide | seed pitch deck template, seed round presentation |
| 5 | `Demo-Day-Pitch-Deck-Template.pptx` | 3–5 minute stage deck: big headlines, one metric per slide, minimal text | demo day pitch template, 5 minute pitch deck |
| 6 | `Product-Pitch-Deck-Template.pptx` | Product launch / internal project pitch (also serves product managers) | product pitch deck template, product launch presentation |

## Healthcare (+3 — then flip category)

| # | File name (target) | Positioning | Search terms to cover |
|---|---|---|---|
| 7 | `Clinical-Research-Template.pptx` | Clinical trial / study report: endpoints, cohort, safety data | clinical trial presentation template, medical research ppt |
| 8 | `Hospital-Annual-Report-Template.pptx` | Hospital/department yearly review: volumes, quality indicators, finance | hospital presentation template, healthcare annual report |
| 9 | `Pharma-Launch-Template.pptx` | Drug/device launch brief: market access, positioning, field plan | pharmaceutical presentation template, medical device pitch |

### When #7–9 are live

Flip these five slugs from `business` → `healthcare` in `assets/templates.js`:

```
nova-medical-healthcare-template
healthcare-presentation-template
clinical-research-template
hospital-annual-report-template
pharma-launch-template
```

Then add a `healthcare` entry to `CATS` + `CAT_COPY` + `READING` in `tools/gen_pages.py` (copy the education block as the pattern) and regenerate. The hub auto-publishes and the sitemap picks it up.

## Do NOT add

- More generic corporate/business decks — 21 already, newest generic ones (competitive analysis, UX research, PRD) rank at the bottom of downloads.
- More marketing decks until the 9 above ship — marketing avg (11.1) is the lowest.

---

# Retention brief — what to add so visitors come back (2026-11-10)

## Diagnosis first

51 decks, 6 categories. D1 data (488 downloads / 42 decks, mean 11.6, range 6–18)
is **flat**: no breakout hit and, more importantly, no reason for anyone to return
a second time. Visitors browse the catalogue, take one or two decks, leave.
Adding more of the same only increases the denominator and the indexing backlog
(6 of the last 9 pages are still not indexed). So the goal is not quantity — it is
**building return triggers and series**.

Three mechanisms actually retain:

1. **Recurring calendar decks** — something the user must redo weekly / monthly /
   quarterly. The calendar itself brings them back.
2. **Kits / series** — one job needs 3–5 decks. More pages and downloads per
   session, and every page links to its siblings.
3. **Tool hooks** — decks that are large, image-heavy or contain notes/metadata
   naturally send visitors to the 7 browser tools, keeping them on-site.

## Tier 1 — recurring decks (ship these 6 first)

| # | Target file | Cat | Cycle | Return trigger / internal links | Search terms |
|---|---|---|---|---|---|
| 1 | `Monthly-Business-Review-Template.pptx` | business | monthly | Completes the month → quarter → year ladder with Sales QBR + Annual Report | monthly business review template, monthly report ppt |
| 2 | `Weekly-Status-Update-Template.pptx` | business | weekly | Highest-frequency deck on the site; best subscription/bundle hook | weekly status report powerpoint, team update template |
| 3 | `OKR-Quarterly-Review-Template.pptx` | business | quarterly | Pairs with existing OKR Planning: plan → review loop | okr review presentation, quarterly goals review |
| 4 | `Board-Meeting-Pack-Template.pptx` | startup | quarterly | High-value B2B; ships with speaker notes + author metadata → links to Remove Notes / Clean Metadata | board meeting deck template, board pack ppt |
| 5 | `Client-Onboarding-Deck-Template.pptx` | sales | per new client | Client lifecycle: Pricing Proposal → QBR → Onboarding | client onboarding presentation, kickoff deck template |
| 6 | `Department-Monthly-Report-Template.pptx` | healthcare | monthly | Healthcare has only 5 decks; adds the one recurring hospital need | hospital monthly report ppt, department review template |

## Tier 2 — complete the kits (one job, several downloads)

| # | Target file | Cat | Kit | Links to |
|---|---|---|---|---|
| 7 | `Investor-One-Pager-Template.pptx` | startup | Fundraising Kit | Seed Pitch, Demo Day, Product Pitch, Investor Update |
| 8 | `Financial-Model-Slides-Template.pptx` | startup | Fundraising Kit | Seed Pitch, Investor One-Pager |
| 9 | `Renewal-Proposal-Template.pptx` | sales | Client Lifecycle Kit | Sales Proposal, Pricing Proposal, Sales QBR |
| 10 | `Case-Study-One-Pager-Template.pptx` | sales | Client Lifecycle Kit | Renewal Proposal, Professional Agency Proposal |

## Tier 3 — new high-frequency audience (only after Tier 1 indexes)

| # | Target file | Cat | Why it retains |
|---|---|---|---|
| 11 | `Student-Project-Presentation-Template.pptx` | education | Semester cycle; students/teachers are the most repeat-heavy audience, strongest Pinterest pool |
| 12 | `Parent-Teacher-Conference-Template.pptx` | education | Twice-yearly recurring need; education has only 4 decks today |
| 13 | `Patient-Education-Template.pptx` | healthcare | Clinics reuse it for every condition/procedure; near-zero competition in the current catalogue |

## Cheaper than adding decks — SHIPPED 2026-11-10

All four are live. Zero new URLs, zero new index requests, zero new templates.

- **Kit navigation** — `tools/kits.py` defines 5 kits covering 24 existing decks.
  `tools/gen_pages.py` renders "Complete the … Kit" with ordered sibling links on
  those 24 detail pages, and their secondary CTA now points at the kit instead
  of the generic catalogue.
- **Bundle ZIP** — `tools/gen_bundles.py` builds deterministic ZIPs into
  `files/bundles/`, plus `assets/kits.js` (homepage) and `functions/_lib/kits.js`
  (subscribe whitelist). The `/subscribe` forms on home, 51 detail pages and 6
  hubs have a kit picker; the success page hands over the ZIP immediately and
  the Brevo welcome mail carries the same link.
- **Tool hooks** — all 51 detail pages show "Before you send this deck"; the 7
  heavy decks (>1 MB or >=30 slides) get compress / split / extract variants.
- **Homepage** — "Complete a kit, not just a slide" with 5 cards and 24 internal
  deck links; the subscribe block now promises a kit ZIP rather than a generic
  full-library bundle.

To change a kit: edit `tools/kits.py`, then run `python3 tools/gen_bundles.py`
followed by `python3 tools/gen_pages.py`.

## Still do NOT add

- Generic corporate / business decks (19 already; generic ones rank last).
- Generic marketing decks (lowest per-deck average, 11.1).
- One-off event decks (event plan, brand launch) — used once, never revisited.
- More than 6 new decks in one batch while 6 URLs are still unindexed and AdSense
  is pending: each new page needs its own crawl + index cycle.
