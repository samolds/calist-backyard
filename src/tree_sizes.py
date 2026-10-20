"""Write plan/images/trees/size_comparison.png: every tree option drawn to one scale next to a 5'10" person
and a typical single-story house.

Sizes are the midpoints of the mature-size ranges in plan/FINAL_PLAN.md (Part A, step A2); keep them in sync.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "plan" / "images" / "trees" / "size_comparison.png"
FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
PX = 9            # pixels per foot
PERSON_FT = 70 / 12
HOUSE_W, HOUSE_EAVE, HOUSE_PEAK = 24, 10, 17   # typical single-story single-family house, not a measurement
GAP_FT = 5
MIN_SLOT_FT = 26  # room for the two-line label under narrow trees

# (label line 1, label line 2, size text, height ft, spread ft, shape)
ROWS = [
    ("A2.1 Shade trees (25–35' canopy)", "#5b9a45", [
        ("American", "hophornbeam", "30–50' × 25–30'", 40, 28, "oval"),
        ("State Street", "maple", "50' × 30'", 50, 30, "oval"),
        ("Norwegian Sunset", "maple", "35' × 25'", 35, 25, "oval"),
        ("Chinkapin", "oak", "40–50' × 35–45'", 45, 40, "round"),
        ("Kentucky coffeetree", "'Espresso'", "50' × 35'", 50, 35, "oval"),
        ("Common", "hackberry", "50–70' × 40–50'", 60, 45, "oval"),
    ]),
    ("A2.2 Smaller trees (canopy 25' or less)", "#7cb342", [
        ("Hot Wings", "Tatarian maple", "20–25' × 15–20'", 22.5, 17.5, "round"),
        ("Bigtooth", "maple", "20–25' × 20–25'", 22.5, 22.5, "round"),
        ("Gambel", "oak", "15–25' × 10–20'", 20, 15, "oval"),
        ("Thornless cockspur", "hawthorn", "15–20' × 20–25'", 17.5, 22.5, "flat"),
        ("Japanese tree lilac", "'Ivory Silk'", "20–25' × 15'", 22.5, 15, "oval"),
    ]),
    ("A2.3 Evergreens", "#2e6b3a", [
        ("Piñon", "pine", "20–30' × 15–25'", 25, 20, "broadcone"),
        ("Vanderwolf's Pyramid", "limber pine", "20–30' × 10–15'", 25, 12.5, "cone"),
        ("Rocky Mountain juniper", "'Moonglow'", "15–20' × 6–8'", 17.5, 7, "cone"),
    ]),
]


def font(size, bold=False):
    return ImageFont.truetype(FONT_PATH, size, index=1 if bold else 0)


def draw_tree(d, cx, ground, h, w, shape, color):
    H, W = h * PX, w * PX
    trunk_w = max(0.8, w * 0.04) * PX
    d.rectangle([cx - trunk_w / 2, ground - H * 0.45, cx + trunk_w / 2, ground], fill="#6d4c33")
    top = ground - H
    if shape in ("round", "oval", "flat"):
        base = {"round": 0.35, "oval": 0.3, "flat": 0.4}[shape]
        d.ellipse([cx - W / 2, top, cx + W / 2, ground - H * base], fill=color, outline="#1f3d1a", width=2)
    else:
        base = ground - H * (0.12 if shape == "cone" else 0.18)
        pts = [(cx, top), (cx + W / 2, base), (cx - W / 2, base)]
        if shape == "broadcone":
            pts = [(cx - W * 0.12, top), (cx + W * 0.12, top), (cx + W / 2, base), (cx - W / 2, base)]
        d.polygon(pts, fill=color, outline="#13301a", width=2)


def draw_person(d, x, ground):
    s = PERSON_FT * PX
    head = s * 0.13
    cx = x + s * 0.15
    d.ellipse([cx - head / 2, ground - s, cx + head / 2, ground - s + head], fill="#333")
    d.rounded_rectangle([cx - s * 0.11, ground - s + head * 1.05, cx + s * 0.11, ground - s * 0.47], radius=4, fill="#333")
    d.rectangle([cx - s * 0.10, ground - s * 0.48, cx - s * 0.015, ground], fill="#333")
    d.rectangle([cx + s * 0.015, ground - s * 0.48, cx + s * 0.10, ground], fill="#333")


def draw_house(d, x, ground):
    w, eave, peak = HOUSE_W * PX, ground - HOUSE_EAVE * PX, ground - HOUSE_PEAK * PX
    line = "#6b5b4a"
    d.rectangle([x, eave, x + w, ground], fill="#efe3d3", outline=line, width=2)
    d.polygon([(x - 1 * PX, eave), (x + w / 2, peak), (x + w + 1 * PX, eave)], fill="#b9a48c", outline=line, width=2)
    for fx in (0.12, 0.7):
        wx, wy = x + w * fx, ground - 7 * PX
        d.rectangle([wx, wy, wx + 3.5 * PX, wy + 4 * PX], fill="#cfe0ea", outline=line, width=2)
    d.rectangle([x + w * 0.42, ground - 7 * PX, x + w * 0.42 + 3.5 * PX, ground], fill="#8a6d52", outline=line, width=2)


def main():
    f_title, f_name, f_size, f_small = font(30, True), font(21, True), font(20), font(18)
    house_x_ft = 14
    left_ft = house_x_ft + HOUSE_W + 2 * GAP_FT  # ruler + person + house
    widths = [left_ft + sum(max(t[4], MIN_SLOT_FT) + GAP_FT for t in trees) for _, _, trees in ROWS]
    row_h = [max(max(t[3] for t in trees), HOUSE_PEAK) + 4 for _, _, trees in ROWS]
    label_px, title_px = 70, 50
    W = round(max(widths) * PX) + 40
    H = 150 + sum(round(h * PX) + label_px + title_px for h in row_h)
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((20, 15), "Mature tree sizes, all drawn to the same scale", font=f_title, fill="black")
    bar_y = 75
    d.rectangle([20, bar_y, 20 + 25 * PX, bar_y + 12], fill="#c0392b")
    for i in range(6):
        x = 20 + i * 5 * PX
        d.line([x, bar_y - 6, x, bar_y + 18], fill="#c0392b", width=2)
    d.text((30 + 25 * PX, bar_y - 6), "25' = the width of your lot. Person = 5' 10\". "
           "House = a typical 1-story home. Shapes are simplified.", font=f_size, fill="black")

    y = 120
    for (title, color, trees), rh in zip(ROWS, row_h):
        d.text((20, y), title, font=f_name, fill="black")
        ground = y + title_px + round(rh * PX)
        x0 = 20
        for ft in range(0, int(rh) + 1, 5):
            yy = ground - ft * PX
            d.line([x0 + 40, yy, x0 + 52, yy], fill="#555", width=2)
            if ft % 10 == 0 or ft == 25:
                d.text((x0, yy - 10), f"{ft}'", font=f_small, fill="#555")
        d.line([x0 + 52, ground, x0 + 52, ground - rh * PX], fill="#555", width=2)
        if rh >= 25:
            yy = ground - 25 * PX
            for xx in range(x0 + 60, W - 20, 18):
                d.line([xx, yy, xx + 9, yy], fill="#c0392b", width=2)
        draw_person(d, x0 + 8 * PX, ground)
        d.text((x0 + 8 * PX - 4, ground - PERSON_FT * PX - 24), "5' 10\"", font=f_small, fill="#333")
        hx = x0 + (house_x_ft + GAP_FT) * PX
        draw_house(d, hx, ground)
        for i, (s, f) in enumerate((("Typical 1-story", f_name), ("house", f_name), ("~17' to the peak", f_size))):
            tw = d.textlength(s, font=f)
            d.text((hx + HOUSE_W * PX / 2 - tw / 2, ground + 6 + i * 22), s, font=f, fill="black")
        cx = x0 + left_ft * PX
        for l1, l2, size, h, w, shape in trees:
            slot = max(w, MIN_SLOT_FT) * PX
            mid = cx + slot / 2
            draw_tree(d, mid, ground, h, w, shape, color)
            for i, (s, f) in enumerate(((l1, f_name), (l2, f_name), (size, f_size))):
                tw = d.textlength(s, font=f)
                d.text((mid - tw / 2, ground + 6 + i * 22), s, font=f, fill="black")
            cx += slot + GAP_FT * PX
        d.line([20, ground, W - 20, ground], fill="#4a3b2a", width=3)
        y = ground + label_px + 10

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(OUT.parents[3])}")


if __name__ == "__main__":
    main()
