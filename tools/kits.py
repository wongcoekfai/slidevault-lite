#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single source of truth for template kits / bundles.

A kit groups 4-5 existing decks that belong to one real job. It powers:
  * `Part of the ... Kit` navigation on detail pages (gen_pages.py)
  * the `Complete a kit` section on the homepage (assets/kits.js -> app.js)
  * the downloadable Bundle ZIP behind /subscribe (gen_bundles.py, subscribe.js)

Kits add NO new URLs: every member is an existing template page, and the
bundle is a static file under /files/bundles/. Adding a template to a kit
only requires editing `slugs` here and re-running the generators.
"""

# id, display name, short pitch, ordered member slugs (order = suggested workflow)
KITS = [
    dict(
        id="fundraising",
        name="Fundraising Kit",
        eyebrow="Startup / investors",
        desc="From the first seed conversation to the monthly investor update — one "
             "consistent story, five editable decks.",
        slugs=[
            "seed-pitch-deck-template",
            "saas-startup-pitch-deck-template",
            "demo-day-pitch-deck-template",
            "product-pitch-deck-template",
            "investor-update-template",
        ],
    ),
    dict(
        id="client-lifecycle",
        name="Client Lifecycle Kit",
        eyebrow="Sales / accounts",
        desc="Win the deal, agree the price, scope the work, then run the quarterly "
             "review. The full client timeline in one place.",
        slugs=[
            "sales-proposal-template",
            "pricing-proposal-template",
            "project-proposal-template",
            "sales-qbr-template",
            "channel-partnership-template",
        ],
    ),
    dict(
        id="reporting",
        name="Reporting Kit",
        eyebrow="Business / leadership",
        desc="Weekly all-hands, quarterly OKR check-in, monthly marketing numbers "
             "and the annual report — all in the same visual language.",
        slugs=[
            "all-hands-template",
            "sales-performance-template",
            "professional-marketing-report-template",
            "okr-planning-template",
            "annual-report-template",
        ],
    ),
    dict(
        id="clinical",
        name="Clinical & Hospital Kit",
        eyebrow="Healthcare",
        desc="Study readouts, department reviews and launch briefs, built for "
             "teams that present evidence to both specialists and non-specialists.",
        slugs=[
            "clinical-research-template",
            "hospital-annual-report-template",
            "pharma-launch-template",
            "nova-medical-healthcare-template",
            "healthcare-presentation-template",
        ],
    ),
    dict(
        id="teaching",
        name="Teaching Kit",
        eyebrow="Education / training",
        desc="Plan the lesson, run the workshop, deliver the training course and "
             "defend the thesis — the four decks teachers rebuild every term.",
        slugs=[
            "lesson-plan-template",
            "workshop-presentation-template",
            "training-course-template",
            "academic-defense-template",
        ],
    ),
]

KIT_IDS = tuple(k["id"] for k in KITS)

# Default preselection on category hubs and the homepage.
KIT_BY_CAT = {
    "startup": "fundraising",
    "sales": "client-lifecycle",
    "business": "reporting",
    "marketing": "reporting",
    "healthcare": "clinical",
    "education": "teaching",
}


def kit_by_id(kit_id):
    for k in KITS:
        if k["id"] == kit_id:
            return k
    return None


def kits_for_slug(slug):
    """A deck can belong to more than one kit; the first one is the primary."""
    return [k for k in KITS if slug in k["slugs"]]


def primary_kit(slug):
    ks = kits_for_slug(slug)
    return ks[0] if ks else None


def bundle_url(kit_id):
    return "/files/bundles/%s-kit.zip" % kit_id
