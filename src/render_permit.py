"""Write plan/permit/site_plan_A1.png and .pdf: a gridded 11x17 permit sheet (site plan, pergola elevation,
pier detail, notes, title block) from geometry.py. Needs Pillow. Contains no address; fill it in by hand.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import geometry as g
from export_psd import flatten

OUT_DIR = Path(__file__).resolve().parent.parent / "plan" / "permit"
FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
DPI = 200
W, H = 11 * DPI, 17 * DPI
INK = (20, 54, 93)          # dark blueprint navy
LIGHT = (110, 130, 155)
GRID_MINOR = (214, 230, 245)
GRID_MAJOR = (150, 186, 222)
RED = (176, 40, 40)

PLAN_S = DPI * (3 / 16) / 12        # px per real inch at 3/16" = 1'-0"
OX, OY = 300, 330                   # sheet px of real (0, 0)
ELEV_S = DPI * (1 / 8) / 12         # 1/8" = 1'-0"


def font(px, bold=False):
    return ImageFont.truetype(FONT_PATH, round(px), index=1 if bold else 0)


def ftin(inches):
    inches = round(inches * 2) / 2
    ft, rem = divmod(inches, 12)
    rem_s = f"{int(rem)}" if rem == int(rem) else f"{int(rem)}½"
    return f"{int(ft)}'-{rem_s}\""


def P(x, y):
    return OX + x * PLAN_S, OY + y * PLAN_S


class Sheet:
    def __init__(self):
        self.img = Image.new("RGB", (W, H), "white")
        self.d = ImageDraw.Draw(self.img)

    def text(self, xy, s, px=26, bold=False, fill=INK, anchor="la", angle=0, bg=False):
        f = font(px, bold)
        if not angle:
            if bg:
                l, t, r, b = self.d.textbbox(xy, s, font=f, anchor=anchor)
                self.d.rectangle([l - 6, t - 4, r + 6, b + 4], fill="white")
            self.d.text(xy, s, font=f, fill=fill, anchor=anchor)
            return
        l, t, r, b = f.getbbox(s)
        tile = Image.new("RGBA", (r - l + 8, b - t + 8), (255, 255, 255, 0))
        ImageDraw.Draw(tile).text((4 - l, 4 - t), s, font=f, fill=fill + (255,))
        tile = tile.rotate(angle, resample=Image.BICUBIC, expand=True)
        self.img.paste(tile, (round(xy[0] - tile.width / 2), round(xy[1] - tile.height / 2)), tile)

    def line(self, pts, fill=INK, w=2, dash=None):
        if not dash:
            self.d.line(pts, fill=fill, width=w, joint="curve")
            return
        on, off = dash
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            L = math.hypot(x2 - x1, y2 - y1)
            if L == 0:
                continue
            ux, uy = (x2 - x1) / L, (y2 - y1) / L
            s = 0.0
            while s < L:
                e = min(s + on, L)
                self.d.line([(x1 + ux * s, y1 + uy * s), (x1 + ux * e, y1 + uy * e)], fill=fill, width=w)
                s = e + off

    def dim(self, a, b, label, off=0, px=24, fill=INK):
        """Dimension between sheet points a and b, offset perpendicular by off px, with ticks and centered text."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        a2 = (a[0] + nx * off, a[1] + ny * off)
        b2 = (b[0] + nx * off, b[1] + ny * off)
        if off:
            sgn = 1 if off > 0 else -1
            for p, q in ((a, a2), (b, b2)):
                self.d.line([p, (q[0] + nx * 8 * sgn, q[1] + ny * 8 * sgn)], fill=fill, width=1)
        self.d.line([a2, b2], fill=fill, width=2)
        for q in (a2, b2):
            self.d.line([(q[0] - (ux + nx) * 9, q[1] - (uy + ny) * 9), (q[0] + (ux + nx) * 9, q[1] + (uy + ny) * 9)],
                        fill=fill, width=3)
        mx, my = (a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2
        ang = -math.degrees(math.atan2(dy, dx))
        if ang <= -90 or ang > 90:
            ang += 180
        f = font(px)
        l, t, r, bb = f.getbbox(label)
        tile = Image.new("RGBA", (r - l + 12, bb - t + 8), (255, 255, 255, 255))
        ImageDraw.Draw(tile).text((6 - l, 4 - t), label, font=f, fill=fill + (255,))
        tile = tile.rotate(ang, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255, 0))
        self.img.paste(tile, (round(mx - tile.width / 2), round(my - tile.height / 2)), tile)


def plan_view(s):
    d = s.d
    x_max, y_max = 312, 816
    # grid: 1' minor, 5' major, labeled in feet from the lot corner
    for i in range(0, x_max + 1, 12):
        major = i % 60 == 0
        d.line([P(i, 0), P(i, y_max)], fill=GRID_MAJOR if major else GRID_MINOR, width=2 if major else 1)
        if major:
            s.text((P(i, 0)[0], P(0, y_max)[1] + 24), f"{i // 12}'", 20, fill=LIGHT, anchor="mm")
    for j in range(0, y_max + 1, 12):
        major = j % 60 == 0
        d.line([P(0, j), P(x_max, j)], fill=GRID_MAJOR if major else GRID_MINOR, width=2 if major else 1)
        if major:
            s.text((OX - 28, P(0, j)[1]), f"{j // 12}'", 20, fill=LIGHT, anchor="mm")

    # existing conditions
    for pts in g.BASE_LINES:
        s.line([P(*p) for p in pts], INK, 3)
    for path in (g.GRASS_PATH, g.CONCRETE_PATH):
        s.line([P(*p) for p in flatten(path)], INK, 3)
    for x, y, w, h in g.BASE_RECTS:
        d.rectangle([P(x, y), P(x + w, y + h)], outline=INK, width=3)
    for cx, cy, r in g.BASE_CIRCLES:
        d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], outline=INK, width=2)

    # property lines (approximate)
    for x in (0, g.PAD_W):
        s.line([P(x, -16), P(x, y_max)], RED, 3, dash=(36, 10))
    s.line([P(-8, 0), P(g.PAD_W + 8, 0)], RED, 3, dash=(36, 10))

    # proposed minor items (light)
    for x, y, w, h in g.PLANTERS:
        d.rectangle([P(x, y), P(x + w, y + h)], outline=LIGHT, width=2)
    for cx, cy, r in g.SHRUBS:
        d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], outline=LIGHT, width=2)
    cx, cy, r = g.TREE
    d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], outline=LIGHT, width=2)
    x, y, w, h = g.COMPOSTER
    d.rectangle([P(x, y), P(x + w, y + h)], outline=LIGHT, width=2)
    s.line([P(*p) for p in g.SAIL + [g.SAIL[0]]], LIGHT, 2, dash=(14, 8))

    # pergola (the permitted structure): heavy outline, beams, posts, piers, braces
    px, py, pw, ph = g.PERGOLA
    for bx, by, bw, bh in g.PERGOLA_BEAMS:
        d.rectangle([P(bx, by), P(bx + bw, by + bh)], outline=INK, width=2)
    d.rectangle([P(px, py), P(px + pw, py + ph)], outline=INK, width=6)
    for (sx, sy, sw, sh) in g.PERGOLA_SLATS[::2]:
        d.line([P(sx, sy + sh / 2), P(sx + sw, sy + sh / 2)], fill=LIGHT, width=1)
    for (x0, y0), (x1, y1) in g.PERGOLA_BRACES:
        d.line([P(x0, y0), P(x1, y1)], fill=INK, width=4)
    for cx, cy, r in g.PERGOLA_PIERS:
        a, b = P(cx - r, cy - r), P(cx + r, cy + r)
        for k in range(0, 360, 30):
            d.arc([a, b], k, k + 18, fill=INK, width=3)
    for x, y, w, h in g.PERGOLA_POSTS:
        d.rectangle([P(x, y), P(x + w, y + h)], fill=INK)
    for x, y, w, h in g.PERGOLA_SLAB_POSTS:
        cxp, cyp = P(x + w / 2, y + h / 2)
        d.line([(cxp - 14, cyp - 14), (cxp + 14, cyp + 14)], fill=RED, width=3)
        d.line([(cxp - 14, cyp + 14), (cxp + 14, cyp - 14)], fill=RED, width=3)

    # labels
    lab = [
        ((154, -50), "ALLEY (SE)", 26, True),
        ((130, 110), "EXISTING CONCRETE PARKING PAD", 22, True),
        ((20, 420), "SIDEWALK", 20, False),
        ((160, 470), "LAWN", 22, True),
        ((289, 520), "MULCH", 18, False),
        ((104, 765), "EXISTING HOUSE", 26, True),
        ((255, 745), "PATIO", 18, False),
        ((258, 791), "SHED", 16, False),
        ((207, 744), "A/C", 16, False),
        ((49, 95), "HALF\nWALL", 16, False),
    ]
    for (x, y), t, pxs, bold in lab:
        s.d.multiline_text(P(x, y), t, font=font(pxs, bold), fill=INK, anchor="mm", align="center")
    s.text(P(177, py + 18), "PROPOSED FREE-STANDING PERGOLA", 22, True, anchor="mm", bg=True)
    s.text(P(177, py + 36), "20'-0\" × 12'-0\" (240 SF), H = 8'-5½\"", 20, anchor="mm", bg=True)
    s.text((P(0, 0)[0] + 22, P(0, 250)[1]), "PROPERTY LINE (APPROX.)", 18, fill=RED, angle=90)
    s.text((P(g.PAD_W, 0)[0] + 26, P(0, 130)[1]), "PROPERTY LINE (APPROX.)", 18, fill=RED, angle=90)

    # dimensions (sheet px)
    s.dim(P(0, 0), P(g.PAD_W, 0), f"{ftin(g.PAD_W)} MEASURED (CITY GIS 25'-0\")", off=-55, px=20)
    s.dim(P(px, py), P(px + pw, py), ftin(pw), off=-34, px=22)
    s.dim(P(px + pw, py), P(px + pw, py + ph), ftin(ph), off=-48, px=22)
    s.dim(P(0, py + 30), P(px, py + 30), ftin(px), off=0, px=18)
    s.dim(P(px + pw, py - 40), P(g.PAD_W, py - 40), ftin(g.PAD_W - px - pw), off=0, px=18)
    s.dim(P(-50, 0), P(-50, py), f"{ftin(py)} REAR LOT LINE TO PERGOLA", off=0, px=20)

    # north arrow: up = SE, right = SW, so north points down-left
    ncx, ncy = P(255, 160)
    d.ellipse([ncx - 46, ncy - 46, ncx + 46, ncy + 46], outline=INK, width=3)
    ux, uy = -1 / math.sqrt(2), 1 / math.sqrt(2)
    tip = (ncx + ux * 40, ncy + uy * 40)
    tail = (ncx - ux * 40, ncy - uy * 40)
    d.line([tail, tip], fill=INK, width=4)
    d.polygon([tip, (tip[0] - ux * 22 + uy * 10, tip[1] - uy * 22 - ux * 10),
               (tip[0] - ux * 22 - uy * 10, tip[1] - uy * 22 + ux * 10)], fill=INK)
    s.text((tip[0] + ux * 26, tip[1] + uy * 26), "N", 28, True, anchor="mm")


def plan_title(s, x0, y0):
    d = s.d
    s.text((x0, y0), "SITE PLAN (REAR YARD)", 34, True)
    s.text((x0, y0 + 46), "SCALE: 3/16\" = 1'-0\"   GRID: 1'-0\" SQUARES, HEAVY EVERY 5'-0\"", 18)
    s.text((x0, y0 + 72), "GRID ORIGIN: REAR (NE) LOT CORNER. UP = SE (ALLEY).", 18)
    bar_y = y0 + 112
    for ft in (0, 5, 10):
        s.text((x0 + ft * 12 * PLAN_S, bar_y + 30), f"{ft}'", 18, anchor="mm")
    for a, b, fill in ((0, 5, INK), (5, 10, "white")):
        d.rectangle([x0 + a * 12 * PLAN_S, bar_y, x0 + b * 12 * PLAN_S, bar_y + 12], fill=fill, outline=INK, width=2)


def elevation(s, x0, y0):
    """Front elevation of the pergola (looking at the house from the yard). x0, y0 = sheet px of left post base."""
    d = s.d
    E = ELEV_S
    T, post_h, beam = g.TIMBER, 96, g.TIMBER
    pier_up = 4
    grade = y0 + pier_up * E
    s.text((x0, y0 - (post_h + beam) * E - 110), "FRONT ELEVATION (FROM YARD)", 30, True)
    s.text((x0, y0 - (post_h + beam) * E - 72), "SCALE: 1/8\" = 1'-0\"", 20)
    d.line([(x0 - 40, grade), (x0 + 240 * E + 40, grade)], fill=INK, width=3)
    for k in range(0, int(240 * E) + 80, 18):
        d.line([(x0 - 40 + k, grade), (x0 - 52 + k, grade + 12)], fill=LIGHT, width=1)
    cols = [0, (240 - T) / 2, 240 - T]
    for c in cols:
        d.rectangle([x0 + c * E, y0 - post_h * E, x0 + (c + T) * E, y0], outline=INK, width=2)
        cx = x0 + (c + T / 2) * E
        s.line([(cx - 6 * E, y0), (cx - 6 * E, grade + 44 * E), (cx + 6 * E, grade + 44 * E), (cx + 6 * E, y0)],
               INK, 2, dash=(8, 6))
    d.rectangle([x0, y0 - (post_h + beam) * E, x0 + 240 * E, y0 - post_h * E], outline=INK, width=2)
    bp = g.BRACE_PLAN
    for c, sgn in ((T, 1), (240 - T, -1)):
        d.line([(x0 + c * E, y0 - (post_h - bp) * E), (x0 + (c + sgn * bp) * E, y0 - post_h * E)], fill=INK, width=4)
    s.dim((x0, y0 - (post_h + beam) * E), (x0 + 240 * E, y0 - (post_h + beam) * E), "20'-0\"", off=-26, px=18)
    s.dim((x0 + 240 * E, y0 - (post_h + beam) * E), (x0 + 240 * E, y0), "8'-5½\"", off=-40, px=18)
    s.dim((x0, y0 + 0), (x0, grade + 44 * E), "≥ 3'-8\" BELOW GRADE", off=60, px=16)
    s.text((x0 + 120 * E, grade + 60 * E), "12\" DIA. CONCRETE PIERS (DASHED); 2 REAR POSTS ON EXISTING SLAB", 16,
           anchor="mm")
    s.text((x0 + 120 * E, grade + 60 * E + 26), "2x6 ROOF SLATS @ ±11\" O.C. AT 45° SIT BETWEEN BEAMS (NOT SHOWN)", 16,
           anchor="mm")


def pier_detail(s, x0, y0):
    d = s.d
    s.text((x0, y0), "PIER DETAIL (N.T.S.)", 30, True)
    gx, gy = x0 + 40, y0 + 270
    d.line([(gx - 30, gy), (gx + 330, gy)], fill=INK, width=3)
    for k in range(0, 360, 16):
        d.line([(gx - 30 + k, gy), (gx - 42 + k, gy + 12)], fill=LIGHT, width=1)
    tx0, tx1 = gx + 90, gx + 190
    d.rectangle([tx0, gy - 40, tx1, gy + 420], outline=INK, width=3)
    d.rectangle([tx0 - 10, gy + 420, tx1 + 10, gy + 460], outline=INK, width=2)
    for k in range(6):
        d.ellipse([tx0 + 8 + k * 16, gy + 430, tx0 + 18 + k * 16, gy + 440], outline=LIGHT, width=2)
    d.rectangle([tx0 + 15, gy - 60, tx1 - 15, gy - 40], fill=INK)
    d.rectangle([tx0 + 30, gy - 200, tx1 - 30, gy - 60], outline=INK, width=3)
    for ax in (tx0 + 22, tx1 - 22):
        d.line([(ax, gy - 50), (ax, gy + 10)], fill=RED, width=3)
    notes = [
        (gy - 150, "6x6 DOUGLAS FIR POST"),
        (gy - 55, "ZEN 6x6 STEEL BASE BRACKET"),
        (gy - 15, "SIMPSON TITEN HD 3/8\" × 4\" (MECH. GALV.)"),
        (gy + 60, "TOP OF PIER +4\" ABOVE GRADE"),
        (gy + 180, "12\" DIA. QUIK-TUBE, CONCRETE FILL"),
        (gy + 300, "BOTTOM ≥ 44\" BELOW GRADE (FROST 36\")"),
        (gy + 440, "4\" GRAVEL BASE"),
    ]
    for yy, t in notes:
        d.line([(tx1 + 12, yy), (tx1 + 50, yy)], fill=INK, width=1)
        s.text((tx1 + 56, yy), t, 17, anchor="lm")


def notes_block(s, x0, y0, width):
    s.text((x0, y0), "GENERAL NOTES", 30, True)
    notes = [
        "Free-standing pergola, 20'-0\" × 12'-0\" (240 SF). Kit: Zen Pergolas 6x6, 2-block, free-standing.",
        "Posts & beams: 6x6 #1 Douglas fir (5½\" × 5½\"), FOHC, factory stained. Posts 96\"; beams on top.",
        "Roof: open 2x6 slats at 45°, ±11\" o.c., 11 per opening. Bracing: eight 6x6 knee braces, 30\".",
        "Height: 8'-5½\" from post base to top of beam.",
        "Footings: four 12\" dia. concrete piers, bottom ≥ 44\" below grade (frost depth 36\"). Two rear posts "
        "anchored to existing concrete patio (min. ±5\" slab, verify) with Titen HD 3/8\" × 4\" MG anchors.",
        "Property lines shown are approximate (owner measurements and City GIS). Boundary survey pending; "
        "setbacks to be confirmed before construction.",
        "Private sewer lateral to be located and marked by a plumber before any excavation.",
        "Zone district U-RH-2.5. Historic district: Landmark Preservation approval required.",
    ]
    f = font(18)
    y = y0 + 50
    for i, n in enumerate(notes, 1):
        words, lines, cur = n.split(), [], ""
        for w_ in words:
            trial = f"{cur} {w_}".strip()
            if f.getlength(trial) > width - 40:
                lines.append(cur)
                cur = w_
            else:
                cur = trial
        lines.append(cur)
        s.text((x0, y), f"{i}.", 18, True)
        for ln in lines:
            s.text((x0 + 34, y), ln, 18)
            y += 26
        y += 8
    y += 14
    s.text((x0, y), "LEGEND", 26, True)
    y += 42
    items = [
        ("prop", "PROPERTY LINE (APPROX.)"),
        ("heavy", "PROPOSED PERGOLA (POSTS SOLID)"),
        ("pier", "NEW 12\" CONCRETE PIER"),
        ("x", "POST ANCHORED TO EXISTING SLAB"),
        ("light", "OTHER LANDSCAPE ITEMS (NOT PART OF PERMIT)"),
    ]
    d = s.d
    for kind, t in items:
        if kind == "prop":
            s.line([(x0, y), (x0 + 70, y)], RED, 3, dash=(24, 8))
        elif kind == "heavy":
            d.line([(x0, y), (x0 + 70, y)], fill=INK, width=6)
        elif kind == "pier":
            for k in range(0, 360, 30):
                d.arc([x0 + 20, y - 15, x0 + 50, y + 15], k, k + 18, fill=INK, width=3)
        elif kind == "x":
            d.line([(x0 + 22, y - 12), (x0 + 46, y + 12)], fill=RED, width=3)
            d.line([(x0 + 22, y + 12), (x0 + 46, y - 12)], fill=RED, width=3)
        else:
            d.line([(x0, y), (x0 + 70, y)], fill=LIGHT, width=2)
        s.text((x0 + 90, y), t, 17, anchor="lm")
        y += 36


def title_block(s, x0, y0, x1, y1):
    d = s.d
    d.rectangle([x0, y0, x1, y1], outline=INK, width=4)
    rows = [
        ("PROJECT", "REAR YARD PERGOLA — DENVER PROPERTY", 30, True),
        ("ADDRESS", "______________________________________", 24, False),
        ("OWNER", "______________________________________", 24, False),
        ("SHEET", "A-1  SITE PLAN, PERGOLA ELEVATION & PIER DETAIL", 22, True),
        ("SCALES", "PLAN 3/16\" = 1'-0\"   ELEVATION 1/8\" = 1'-0\"   DETAIL N.T.S.", 20, False),
        ("DATE", "2026-10-18   PREPARED BY OWNER   SHEET 1 OF 1", 20, False),
    ]
    rh = (y1 - y0) / len(rows)
    for i, (k, v, px, bold) in enumerate(rows):
        yy = y0 + i * rh
        if i:
            d.line([(x0, yy), (x1, yy)], fill=INK, width=2)
        s.text((x0 + 16, yy + rh / 2), k, 16, True, fill=LIGHT, anchor="lm")
        s.text((x0 + 150, yy + rh / 2), v, px, bold, anchor="lm")
    d.line([(x0 + 135, y0), (x0 + 135, y1)], fill=INK, width=2)


def main():
    s = Sheet()
    m = int(0.4 * DPI)
    s.d.rectangle([m, m, W - m, H - m], outline=INK, width=6)
    s.d.rectangle([m + 12, m + 12, W - m - 12, H - m - 12], outline=INK, width=2)
    plan_view(s)
    rx = 1420
    s.d.line([(rx - 40, m + 12), (rx - 40, 2980)], fill=INK, width=2)
    plan_title(s, rx, 110)
    elevation(s, rx + 60, 640)
    pier_detail(s, rx, 880)
    notes_block(s, rx, 1700, W - m - 30 - rx)
    title_block(s, m + 12, 2980, W - m - 12, H - m - 12)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png, pdf = OUT_DIR / "site_plan_A1.png", OUT_DIR / "site_plan_A1.pdf"
    s.img.save(png, optimize=True)
    s.img.save(pdf, resolution=DPI)
    print(f"wrote {png.relative_to(OUT_DIR.parents[1])} and .pdf (11x17 in)")


if __name__ == "__main__":
    main()
