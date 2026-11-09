#!/usr/bin/env python3
"""Generate card cover images (assets/img/<Name>.jpg) in the site's house style.
Reusable: add a (file_key, title, slides, sections) tuple per new deck and rerun.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1600, 1000
BG = (15, 22, 38)
BAR = (37, 99, 235)
ACCENT = (34, 211, 238)
TEXT = (237, 242, 247)
MUTED = (148, 163, 184)
LINK = (59, 130, 246)

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"

DECKS = [
    # (cover file stem, title upper, slides, section labels)
    ("Sales-QBR-Template", "SALES QBR TEMPLATE", 12, ["Usage", "Adoption", "Value", "Risks"]),
    ("Pricing-Proposal-Template", "PRICING PROPOSAL TEMPLATE", 12, ["Tiers", "Scope", "Timeline", "Terms"]),
    ("Channel-Partnership-Template", "CHANNEL PARTNERSHIP TEMPLATE", 12, ["Earnings", "Enablement", "Co-Marketing", "Tiers"]),
    ("Seed-Pitch-Deck-Template", "SEED PITCH DECK TEMPLATE", 12, ["Problem", "Product", "Traction", "Ask"]),
    ("Demo-Day-Pitch-Deck-Template", "DEMO DAY PITCH TEMPLATE", 12, ["Problem", "Product", "Traction", "Raise"]),
    ("Product-Pitch-Deck-Template", "PRODUCT PITCH TEMPLATE", 12, ["Vision", "Proposal", "Impact", "Ask"]),
    ("Clinical-Research-Template", "CLINICAL RESEARCH TEMPLATE", 12, ["Design", "Endpoints", "Safety", "Next Steps"]),
    ("Hospital-Annual-Report-Template", "HOSPITAL ANNUAL REPORT", 12, ["Activity", "Outcomes", "Staff", "Finance"]),
    ("Pharma-Launch-Template", "PHARMA LAUNCH TEMPLATE", 12, ["Product", "Market", "Access", "Launch Plan"]),
]


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build(stem, title, slides, sections):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # left accent bar + top-right block
    d.rectangle([0, 0, 14, H], fill=BAR)
    d.rectangle([W - 220, 0, W, 26], fill=ACCENT)
    pad = 100
    # title, shrink to fit two lines
    size = 96
    while size > 56:
        f = font(FONT_BOLD, size)
        lines = wrap(d, title, f, W - pad - 120)
        if len(lines) <= 2:
            break
        size -= 6
    y = 170
    for line in lines:
        d.text((pad, y), line, font=f, fill=TEXT)
        y += int(size * 1.18)
    # subtitle
    sub = "%d slides  ·  " % slides + "  ".join(sections[:3])
    d.text((pad, y + 26), sub, font=font(FONT_REG, 40), fill=MUTED)
    # placeholder pills
    py = 560
    f_pill = font(FONT_REG, 34)
    x = pad
    for s in sections:
        label = "{{%s}}" % s
        tw = d.textlength(label, font=f_pill)
        d.rounded_rectangle([x, py, x + tw + 48, py + 84], radius=16, outline=(59, 130, 246), width=3)
        d.text((x + 24, py + 22), label, font=f_pill, fill=ACCENT)
        x += tw + 48 + 28
        if x > W - 400:
            break
    # footer
    d.text((pad, 820), "Free for personal & commercial use · PowerPoint & Google Slides",
           font=font(FONT_REG, 40), fill=MUTED)
    d.text((pad, 884), "SLIDEVAULTE.COM", font=font(FONT_BOLD, 36), fill=LINK)
    img.save(os.path.join(ROOT, "assets", "img", "%s.jpg" % stem), quality=88)
    print("cover", stem)


if __name__ == "__main__":
    for row in DECKS:
        build(*row)
