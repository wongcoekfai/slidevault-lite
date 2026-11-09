---
title: How to Remove Your Name and Metadata From a PowerPoint File
description: Every .pptx carries an author, a company, a "last saved by" and often custom properties from the template it started life in. Here is where that data lives and four ways to strip it.
date: 2026-11-09
image: https://slidevaulte.com/assets/img/AETHER-Financial-Consulting-Template.jpg
---

You built the deck on your old employer's template. It looks clean — your logo, your colours, your content. Then someone opens **File → Info** and reads *Company: the company you left two years ago*, next to a **Last Modified By** with a name that is not yours.

That panel is not decoration. Every PowerPoint file carries a document-properties block, and most of it was written by the template before you typed a word.

## Where the paper trail lives

Right-click the file, choose **Properties → Details** without opening it, and you can already see the trail. Inside the `.pptx` package it sits in three small XML parts:

- `docProps/core.xml` — author (`dc:creator`), last modified by (`cp:lastModifiedBy`), revision, created and modified timestamps
- `docProps/app.xml` — company, manager, template name, slide count, total editing time
- `docProps/custom.xml` — anything the template's author added: client names, project codes, an internal classification tag

None of it appears on a slide. All of it is readable by anyone who receives the file, and searchable by the tools that index shared drives and applicant tracking systems.

## What actually matters

| Field | Why it bites |
| --- | --- |
| Author | Your name, or the name of whoever created the original template |
| Last saved by | Whoever touched the file last — often rewritten silently on save |
| Company / Manager | Reveals your employer, or a client you are not allowed to name |
| Revision, editing time | Says how many drafts exist and how long you spent. Oddly revealing in a submission |
| Custom properties | Free-text fields, rarely audited, frequently left over from someone else's project |

## Method 1: Clear the fields in the Info panel

**File → Info** shows the properties on the right. Click a value and you can usually overwrite it; **Properties → Advanced Properties** exposes the full dialog.

The catch: `lastModifiedBy` is rewritten the moment you save, using whichever Microsoft account PowerPoint is signed into. You clear it, save, and it comes back with your name. For a file you are about to hand to a stranger, this method is more effort than it is worth.

## Method 2: Document Inspector (desktop PowerPoint)

1. **File → Info → Check for Issues → Inspect Document**
2. Tick **Document Properties and Personal Information**
3. **Inspect**, then **Remove All**
4. Save

This is the official route and it works — it empties author, last-saved-by, company and custom properties in one pass. It also requires the desktop app, and it edits the file you have open, so run it on a copy. While you are in there, tick **Comments and Revisions** and **Presentation Notes** too: they are a different kind of leak with the same cause (see [removing speaker notes](https://slidevaulte.com/blog/how-to-remove-speaker-notes-from-powerpoint/)).

## Method 3: Make it automatic in the Trust Center

**File → Options → Trust Center → Trust Center Settings → Privacy Options**, then tick **Remove personal information from file properties on save**.

From then on, every file you save on that machine is scrubbed without asking. It is the right setting for anyone who sends decks to clients regularly. Two limits: it only applies to that machine and that Office profile, and it does nothing for the deck you already sent from your laptop last month.

## Method 4: Edit the properties block directly

Unzip the `.pptx`, edit the three `docProps/*.xml` files in a text editor, rezip. Precise, scriptable, and easy to corrupt: OOXML is strict about element order and content types, and a malformed `core.xml` gets you a "PowerPoint found a problem with content" dialog on the recipient's machine.

Worth it only if you are automating a pipeline. For a one-off deck, use Method 2 or 5.

## Method 5: Clean it in the browser, including batches

Our free [Clean Metadata tool](https://slidevaulte.com/tools/clean-metadata/) is the batch version. Drop in one file or forty, press the button, and it rewrites `docProps` inside your browser: author, last-saved-by, company, manager and custom properties are removed, and you get a report of every value it stripped so you can verify before sending.

Multiple files come back as a ZIP. Nothing is uploaded — the deck is unpacked in browser memory and rewritten there. Slide content, design, fonts and dates inside the slides are untouched; the file keeps a valid structure and opens in PowerPoint, Google Slides and Keynote without a warning.

## When this is not optional

- **Job applications.** Applicant tracking systems index document properties. A deck built on your current employer's template, submitted for a role elsewhere, has their name in it.
- **Template resale and licensing.** Stock marketplaces reject submissions that still carry the original designer's author and company fields.
- **Client work under NDA.** The custom properties field is where agencies leave the internal project code.
- **Anonymous review and blind submissions.** Conference and grant systems often strip the first page and nothing else.
- **Anything going to a competitor.** Template name and editing time tell them how the deck was made and how long you spent.

## One honest caveat

Cleaning metadata does not make a deck anonymous in any deeper sense. Fonts, image sources, phrasing quirks and the file's creation date are all still there, and the timestamp on the original build stays in the slide XML. If identity genuinely cannot leak, start from a blank file created on the machine you are sending from — and clean that one too.

Otherwise, spend the thirty seconds. The properties block is the part of the deck you never look at, which is exactly why it is worth a look before someone else does.
