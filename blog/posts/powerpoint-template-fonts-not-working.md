---
title: PowerPoint Template Fonts Not Working? Why It Happens and How to Fix It
description: Text jumps out of its boxes, the headline changes typeface, Google Slides swaps Calibri for something else. The three causes of font trouble in templates — and the fix for each, including which fonts survive every device.
date: 2026-11-11
image: https://slidevaulte.com/assets/img/Lesson-Plan-Template.jpg
---

You downloaded a template, opened it on the presentation laptop, and the deck now looks slightly wrong: the headline is a different typeface, the body text sits a millimeter off its baseline, one slide's text box overflows. Nothing was edited. The fonts moved.

This is the single most common "the template is broken" complaint, and it is almost never the template. It is one of three font problems, each with a different fix.

## Cause 1: the font is not installed on that machine

PowerPoint does not travel with fonts. A .pptx stores font *names*, not font *files* — unless fonts were embedded at save time. Open the deck on a machine without the exact typeface and PowerPoint silently substitutes whatever looks close, and because every font has different character widths, "close" means text boxes resize, lines wrap differently, and tight layouts breathe in the wrong places.

**The fix, in order of preference:**

1. **Use the same fonts on every machine.** For a company deck, this means installing the brand fonts on the laptops that present. One minute of setup, zero surprises.
2. **Embed fonts into the file:** **File → Options → Save → Embed fonts in the file**. Best choice with **"Embed only the characters used"** for a deck that will not be edited further, or **"Embed all characters"** if colleagues will edit it. Embedding works on Windows PowerPoint; the Mac version still has gaps for some font types.
3. **Convert title art to images.** For a logo wordmark or a stylized headline where the exact typeface matters, a PNG renders identically everywhere. Use it for the few elements where the typeface is the brand, keep everything else as text.
4. **Pick a font that is everywhere already.** This is how our templates are built — see the shortlist below.

If you are not sure which fonts a deck uses, open a slide, click any text, and read the font name in the Home toolbar — or run our <a href="/tools/ppt-stats/">PPT Stats tool</a> on the file for a quick inventory.

## Cause 2: the substitution cascade in Google Slides

Google Slides can only render fonts from its own library. Everything else gets replaced on import — usually with Arial — and, importantly, **the substitution becomes permanent the moment you edit anything**, because Slides saves its own copy of the file.

The practical consequences:

- **Calibri → Carlito.** This one is harmless: Carlito is Google's metric-compatible twin of Calibri, with identical character widths, so line breaks and layouts survive. Most of our templates ship in Calibri for exactly this reason.
- **Arial, Georgia, Trebuchet MS, Verdana, Times New Roman, Courier New, Impact** are native to Slides — they never move.
- **Anything else** gets swapped for Arial, and text starts reflowing. If a deck uses a display font in the headlines, fix it on the slide layouts (**Slide → Edit theme**) rather than slide by slide, or the fix will not propagate.

The import sequence that minimizes all of this — upload, open with Slides, immediately **File → Save as Google Slides**, then audit four specific things — is in <a href="/blog/how-to-import-pptx-into-google-slides/">the import guide</a>.

## Cause 3: the file uses a font you do not have a license for

Rarer, but it bites in corporate settings: some premium fonts are licensed per machine, and a deck built on one legally requires the same license everywhere it renders. This is a reason to keep presentation decks on system fonts even when a prettier typeface exists.

Our templates never have this problem — everything ships in faces that ship with Office or sit in Google's library. If you swap in your own brand font, its license governs your file; the <a href="/license/">template license</a> covers the template, not third-party fonts you add.

## The safe font shortlist

If you are choosing a typeface for a deck that must survive laptops, conference PCs, Google Slides and PDF export, these are the reliable ones:

| Font | Windows | Mac | Google Slides | Use for |
|---|---|---|---|---|
| Calibri | ✓ (Office) | ✓ (Office) | Carlito (same widths) | body text |
| Arial | ✓ | ✓ | ✓ | everything |
| Georgia | ✓ | ✓ | ✓ | editorial serif |
| Trebuchet MS | ✓ | ✓ | ✓ | friendly headings |
| Verdana | ✓ | ✓ | ✓ | dense data labels |

Pick one for headings and one for body, and resist the urge to add a third. Two typefaces with a clear size hierarchy read as more professional than five chosen individually — and they are the reason a deck that starts here still looks like itself on whichever machine opens it.

## Quick diagnosis

- **Looks wrong only on one machine** → font not installed; embed or install.
- **Looks wrong only in Google Slides** → substitution; use the import order, fix on the theme.
- **Looks wrong everywhere after editing** → the edit baked a substitution in; restore from the original download and apply fixes on the layouts, not the slides.
- **Not sure which fonts are in the file** → <a href="/tools/ppt-stats/">PPT Stats</a> tells you in one drop, right in the browser.
