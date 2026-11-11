---
title: How to Import a PPTX Into Google Slides Without Breaking the Layout
description: Fonts get swapped, charts lose their data connection, SmartArt falls apart. Here is the import order that keeps a PowerPoint template looking right in Google Slides — and what to fix in the first two minutes.
date: 2026-11-11
image: https://slidevaulte.com/assets/img/Academic-Defense-Template.jpg
---

The promise is one click: drop a .pptx into Google Drive, double-click, keep working. Ten minutes later the headline is in the wrong font, a chart turned into a picture, and the timeline slide has text boxes floating where arrows used to be.

None of that is random. Google Slides is a browser app with its own font library and a simpler animation engine, and the import step is where every difference surfaces at once. Import in the right order and review four specific things, and a well-built template survives the trip almost untouched.

## The import order that works

1. **Upload the .pptx to Google Drive** — drag it into any folder and wait for the upload to finish.
2. **Right-click the file → Open with → Google Slides.** You are now in compatibility mode; the filename shows a `.pptx` badge. Preview works fine here, but treat it as read-only.
3. **File → Save as Google Slides.** This is the step most people skip. It creates a native copy that fully supports editing, theme colors and Sheets-linked charts. Work in the native copy from now on.
4. **Do a two-minute fidelity check** on the four things below before you add real content.

Never work in compatibility mode for longer than it takes to press Save as. Edits made there can bake the substitutions in permanently.

## Fix 1: fonts (the number one culprit)

Google Slides can only render fonts from its own library. Anything else is silently replaced — Calibri with Carlito, unknown fonts with Arial. Because different fonts have different character widths, the swap can push text out of boxes and change line breaks.

- **Check which fonts the deck uses first.** If the template ships with common faces — Arial, Georgia, Trebuchet MS, Verdana, or Calibri — you are already safe: the first three are native to Slides, and Calibri maps to Carlito, which shares Calibri's exact character widths so the layout holds.
- **If a headline still looks wrong**, select it and pick the closest Google font from the toolbar. Fix the font on the slide layouts, not slide by slide: **Slide → Edit theme**, then change the font there once — every slide inheriting that layout updates with it.
- Our templates are deliberately built on Calibri and Arial for this reason. See the full <a href="/blog/powerpoint-template-fonts-not-working/">font troubleshooting guide</a> for what breaks on desktop PowerPoint too.

## Fix 2: charts

Charts built in PowerPoint usually survive the import as images of themselves: right shape, right colors, but **no editable data behind them**. Google Slides charts are fed by Google Sheets.

1. Click the chart. If Slides shows a **link icon**, the chart is still native — click it to open the data in Google Sheets and edit there.
2. If it is a static picture, the cheapest fix is usually to rebuild that one chart: **Insert → Chart** in Slides, pick the type, edit the linked Sheet, then copy the colors from the original.

Templates from Slide Vault flag their sample data with a small caption — "edit the chart to replace it" — so you know exactly which numbers are placeholders. The faster path for one-off edits: right-click → **Edit Data** in PowerPoint first, then import.

## Fix 3: SmartArt and complex diagrams

SmartArt does not transfer — it becomes a flat picture, or a pile of disconnected shapes. Two options, in order of preference:

- **Rebuild it with native shapes.** Slides' shape library plus Insert → Line → Arrow covers org charts, process flows and pyramids in a few minutes, and the result stays editable forever.
- Or export that one slide from PowerPoint as a high-resolution image and place it. Crisp on screen, but frozen.

## Fix 4: animations and embedded media

Expect losses. Morph transitions, motion paths and multi-step sequences are downgraded to simple fades or dropped. Locally embedded video does not travel; re-add it with **Insert → Video** (YouTube or Drive links work best). If a deck's message depends on a specific animation, keep that version in PowerPoint and present from there — Slides is the better collaboration surface, PowerPoint the better presentation engine.

## When to just stay in PowerPoint

Collaboration, comments and anywhere-anywhere access: Slides wins. Pixel-level layout control, embedded fonts and animation: PowerPoint wins. Our <a href="/blog/google-slides-vs-powerpoint/">PowerPoint vs Google Slides comparison</a> breaks the decision down by scenario — and every <a href="/#templates">free template on Slide Vault</a> is built to open cleanly in both, so the choice stays yours after you download.
