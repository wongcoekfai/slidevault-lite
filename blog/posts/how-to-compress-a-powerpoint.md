---
title: How to Compress a PowerPoint File (Get Under 10 MB Without Ruining It)
description: Why .pptx files balloon to 100+ MB and seven ways to shrink them — PowerPoint's built-in options, the causes most people miss, and a free one-click compressor.
date: 2026-10-30
image: https://slidevaulte.com/assets/img/Digital-Marketing-Advertising-Agency-Premium-Template.jpg
---

You attach the deck. Outlook rejects it. Gmail converts it to a Google Drive link and half the recipients never open it. A 150 MB presentation is almost always one thing: images that were never prepared for slides. The good news is that most decks can shrink by half or more with zero visible difference — if you attack the actual cause instead of the symptoms.

## First, find out what is actually heavy

A .pptx is a ZIP archive. Rename a copy to `.zip`, open it, and look at the `ppt/media/` folder — sort by size. In ninety percent of bloated decks you will find a handful of 5–15 MB photos straight from a phone camera (4000×3000 pixels, displayed at a quarter of that), plus maybe an unused video someone embedded and forgot.

This one-minute diagnosis tells you where to aim. If `ppt/media/` is small, your problem is something else entirely — usually an embedded Excel workbook or a video.

## The built-in fixes (in the order to try them)

**1. Compress pictures.** Select any picture → **Picture Format → Compress Pictures** → untick *Apply only to this picture* → choose *Email (96 ppi)*... actually, don't. 96 ppi is aggressive and visibly degrades full-screen photos. Pick *HD (150 ppi)* for screen presentations, *Print (220 ppi)* only if the deck will actually be printed. **Also untick "Delete cropped areas" only if you plan to uncrop later** — otherwise leave it ticked; cropped-out pixels are pure dead weight.

**2. Re-save as .pptx.** Files edited across years of PowerPoint versions accumulate garbage. **File → Save As → .pptx** repacks the whole archive cleanly. Costs nothing, occasionally saves tens of megabytes.

**3. Evict embedded objects.** Double-click suspected embedded Excel tables. If someone pasted a full workbook, replace it with a Paste Special → picture or a linked value set. Embedded spreadsheets are invisible bloat.

**4. Check for orphaned video and audio.** Slide transitions and animations can reference media that is easy to miss on a flip-through. Slide Show from start and listen.

## The causes most people miss

- **The file was never the problem — the source images were.** A phone photo is 10× larger than a slide can display. Compress Pictures fixes existing decks; pasting from "web-sized" sources prevents the next one.
- **Screenshots pasted at retina resolution.** A Mac Retina screenshot is 2× the pixels you need. These look identical compressed.
- **Corporate template bloat.** Some company masters carry a dozen full-resolution background images used by layouts your deck never touches. If every deck from your team is 80 MB, the template is the patient.

## When manual isn't enough

The built-in tools have real limits: Compress Pictures re-encodes *every* image at the same setting (one size fits all), it skips SVG and EMF vector files entirely, and it offers no "make this deck under 10 MB" target.

Our free [Compress PPT tool](https://slidevaulte.com/tools/compress-ppt/) works differently: it analyzes each image inside the deck, re-encodes only the oversized ones (downscaling to what a slide can actually display), leaves already-small and transparent images untouched — and if any single image would get bigger, it keeps the original. Everything runs in your browser; the deck never leaves your device. Real decks typically drop 40–90% with no visible change, and you get a before/after comparison.

Typical results on template decks: a 34 MB photo-heavy deck down to 5 MB; a 4 MB text deck stays 3.8 MB because there was nothing to save — which is exactly what you want a compressor to decide.

## A workflow that keeps decks small

1. **Prepare images before pasting** — resize screenshots, use web-sized exports of photos.
2. **Compress at the end, not the beginning.** Compressing mid-edit means new images arrive after the cleanup.
3. **One compression pass before sending.** Make it part of the send ritual, like spell-check.
4. **If the deck is huge *and* needs to travel in parts**, [Split PPT](https://slidevaulte.com/tools/split-ppt/) divides it after compression, and [Merge PPT](https://slidevaulte.com/tools/merge-ppt/) reassembles received parts into one file.

None of this requires design talent — just the habit of checking what is inside the file before you ship it. Starting fresh? Our [free PowerPoint templates](https://slidevaulte.com/#templates) are optimized to stay lean even after you add your own images.
