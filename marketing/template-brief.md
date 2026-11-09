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
