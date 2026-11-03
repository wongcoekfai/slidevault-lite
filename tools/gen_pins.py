#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a Pinterest kit: 42 vertical pins (1000x1500) + a CSV of titles,
descriptions and links.

Pinterest works as a search engine of its own, so it sends traffic long before
a new domain ranks in Google. Upload the images from marketing/pins/ and paste
the matching row from marketing/pinterest.csv.

  python3 tools/gen_pins.py
"""
import csv
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "marketing", "pins")
SITE = "https://slidevaulte.com"

W, H = 1000, 1500
BG = (11, 16, 32)
SURFACE = (19, 26, 46)
TEXT = (232, 236, 245)
MUTED = (154, 166, 194)
ACCENT = (59, 130, 246)
ACCENT2 = (34, 211, 238)

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"

BOARD = {
    "business": "Business Presentation Templates",
    "marketing": "Marketing & Brand Decks",
    "startup": "Startup Pitch Decks",
    "sales": "Sales & Proposal Decks",
}

TAGS = {
    "business": "#powerpoint #presentationtemplate #businesstemplate #corporatedeck #slides",
    "marketing": "#powerpoint #marketingtemplate #branding #campaignplanning #slides",
    "startup": "#pitchdeck #startup #fundraising #investordeck #powerpoint",
    "sales": "#salesdeck #proposal #b2bsales #powerpoint #presentationtemplate",
}


def parse_catalog():
    src = open(os.path.join(ROOT, "assets", "templates.js"), encoding="utf-8").read()
    items = []
    for m in re.finditer(
            r'slug:\s*"([^"]+)",\s*title:\s*"([^"]+)",\s*seo:\s*"([^"]*)",\s*'
            r'tag:\s*"([^"]*)",\s*cat:\s*"([^"]*)",\s*desc:\s*"([^"]*)",\s*'
            r'body:\s*"([^"]*)",\s*img:\s*"([^"]*)",\s*file:\s*"([^"]*)"', src):
        items.append(dict(zip(("slug", "title", "seo", "tag", "cat", "desc",
                               "body", "img", "file"), m.groups())))
    if not items:
        sys.exit("!! could not parse assets/templates.js")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gen_pages import slide_outline
    for it in items:
        it["slides_n"], it["outline"] = slide_outline(
            os.path.join(ROOT, "files", it["file"]))
    return items


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def pill(d, x, y, text, fnt, fg, bg, pad_x=22, pad_y=12):
    tw = d.textlength(text, font=fnt)
    th = fnt.size
    d.rounded_rectangle([x, y, x + tw + pad_x * 2, y + th + pad_y * 2],
                        radius=(th + pad_y * 2) // 2, fill=bg)
    d.text((x + pad_x, y + pad_y), text, font=fnt, fill=fg)
    return tw + pad_x * 2


def build_pin(item, cover_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # soft vertical gradient so the flat navy does not look like a placeholder
    for y in range(0, H, 4):
        t = y / H
        r = int(BG[0] + (26 - BG[0]) * t * 0.55)
        g = int(BG[1] + (36 - BG[1]) * t * 0.55)
        b = int(BG[2] + (64 - BG[2]) * t * 0.55)
        d.rectangle([0, y, W, y + 4], fill=(r, g, b))

    # full-bleed 16:9 preview at the top
    img_h = int(W * 9 / 16)
    try:
        shot = Image.open(cover_path).convert("RGB")
        shot = shot.resize((W, img_h), Image.LANCZOS)
        img.paste(shot, (0, 0))
    except Exception:
        d.rectangle([0, 0, W, img_h], fill=SURFACE)
    d.rectangle([0, img_h - 3, W, img_h], fill=(255, 255, 255, 40))

    # floating "FREE" badge over the preview
    f_badge = font(FONT_BLACK, 30)
    bw = pill(d, 48, 44, "FREE .PPTX", f_badge, (4, 18, 43), ACCENT2, pad_x=26, pad_y=14)

    pad = 64
    f_cat = font(FONT_BOLD, 26)
    cat = "%s TEMPLATE" % item["cat"].upper()
    d.text((pad, img_h + 42), cat, font=f_cat, fill=ACCENT2)

    # title, shrinking until it fits three lines
    y = img_h + 88
    size = 72
    while size > 40:
        f_title = font(FONT_BOLD, size)
        lines = wrap(d, item["title"], f_title, W - pad * 2)
        if len(lines) <= 3:
            break
        size -= 4
    for line in lines:
        d.text((pad, y), line, font=f_title, fill=TEXT)
        y += int(size * 1.2)

    # description snippet (shorter when the title already took three lines)
    y += 18
    f_desc = font(FONT_REG, 29)
    desc_lines = wrap(d, item["desc"], f_desc, W - pad * 2)[:2 if len(lines) >= 3 else 3]
    for line in desc_lines:
        d.text((pad, y), line, font=f_desc, fill=MUTED)
        y += 42

    # keyword chips, kept together right above the footer
    chips = [item["tag"], "PowerPoint + Google Slides", "Free for commercial use"]
    f_chip = font(FONT_BOLD, 27)
    footer_top = H - 150
    chip_h = 27 + 24
    rows = [chips[:2], chips[2:]]
    chips_top = footer_top - 60 - chip_h * 2 - 18

    # real slide outline from the .pptx — unique per template, fills the middle.
    # hard-clamped so it can never run into the chips/footer zone
    outline = item.get("outline") or []
    limit = chips_top - 40
    if outline and y + 44 + 38 <= limit:
        y += 26
        f_out = font(FONT_BOLD, 25)
        d.text((pad, y), "SLIDES INCLUDE", font=f_out, fill=ACCENT)
        y += 44
        f_out2 = font(FONT_REG, 26)
        text = "  ·  ".join(outline[:6])
        for line in wrap(d, text, f_out2, W - pad * 2):
            if y + 38 > limit:
                break
            d.text((pad, y), line, font=f_out2, fill=MUTED)
            y += 38

    chip_y = chips_top
    for row in rows:
        x = pad
        for c in row:
            x += pill(d, x, chip_y, c, f_chip, TEXT, (27, 36, 64)) + 16
        chip_y += chip_h + 18

    # footer
    d.rectangle([0, footer_top - 34, W, footer_top - 33], fill=(255, 255, 255, 18))
    d.text((pad, footer_top), "Slide Vault", font=font(FONT_BOLD, 36), fill=TEXT)
    d.text((pad, footer_top + 52), "slidevaulte.com  ·  no signup  ·  no watermark",
           font=font(FONT_REG, 24), fill=MUTED)
    d.text((W - pad - 130, footer_top + 8), "PPT", font=font(FONT_BLACK, 42), fill=ACCENT)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    items = parse_catalog()
    rows = []
    for it in items:
        cover = os.path.join(ROOT, "assets", "img", "gallery", it["slug"], "01.jpg")
        if not os.path.exists(cover):
            cover = os.path.join(ROOT, "assets", "img", it["slug"] + ".jpg")
        pin = build_pin(it, cover)
        fname = "pin-%s.jpg" % it["slug"]
        pin.save(os.path.join(OUT, fname), "JPEG", quality=88, optimize=True)

        title = ("%s — Free PowerPoint Template" % it["title"])[:95]
        desc = ("%s. Free, fully editable .pptx that opens in PowerPoint and Google Slides — "
                "no signup, no watermark, free for commercial use. %s"
                % (it["desc"], TAGS[it["cat"]]))[:480]
        rows.append({
            "image": fname,
            "title": title,
            "description": desc,
            "link": "%s/templates/%s/" % (SITE, it["slug"]),
            "board": BOARD[it["cat"]],
        })
        print("  pin %-56s %s" % (it["slug"], fname))

    csv_path = os.path.join(ROOT, "marketing", "pinterest.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["image", "title", "description", "link", "board"])
        w.writeheader()
        w.writerows(rows)
    print("\ndone: %d pins -> marketing/pins/ | captions -> marketing/pinterest.csv" % len(rows))


if __name__ == "__main__":
    main()
