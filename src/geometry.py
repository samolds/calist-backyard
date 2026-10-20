"""Single source of truth for the backyard plan geometry.

Units are inches. x = 0 is the left boundary (sidewalk/alley outer edge), y = 0 is the top line
(top of the parking pad); y grows toward the house. Both render_svg.py and export_psd.py read this.
"""

VIEW_BOTTOM = 832          # open-ended lines (left boundary, house wall) stop here

# ---- Site (measured / confirmed) ----
PAD_W = 308                # pad right edge = mulch outer edge = right boundary
PAD_H = 217                # pad depth; also the grass top edge
SIDEWALK_W = 41.5          # grass left edge
NOTCH_X = 126.5            # SIDEWALK_W + 85
NOTCH_BOTTOM = 278         # PAD_H + 61
GRASS_RIGHT = 270          # mulch line
GRASS_BOTTOM = 625
HOUSE_FRONT = 721          # GRASS_BOTTOM + 96
HOUSE_L, HOUSE_R = 23.5, 186
CONCRETE_X = 285           # HOUSE_R + 99
BOTTOM_LINE = 806          # HOUSE_FRONT + 85

HALF_WALL = (36, 6, 27, 179)          # x, y, w, h
STEPS = (72, 670, 69, 51)             # x, y, w, h (bottom edge is the house front)
AC = (191.4, 728, 32, 32)
SHED = (232.5, 775.5, 51, 30.5)
POST = (289, 479.2, 4)                # cx, cy, r
# 84" round table: x centered under the pergola's right 10' half (x 177-297); y centered on the patio, grass to house
TABLE = (237, (GRASS_BOTTOM + HOUSE_FRONT) / 2, 42)

# Paths as (command, points...) with SVG-style commands M, L, C, Q.
GRASS_PATH = [
    ("M", (NOTCH_X, PAD_H)),
    ("L", (NOTCH_X, 228)),
    ("C", (126.5, 258), (96.5, 275), (61.5, 277.5)),
    ("L", (SIDEWALK_W, NOTCH_BOTTOM)),
    ("L", (SIDEWALK_W, GRASS_BOTTOM - 8)),
    ("Q", (SIDEWALK_W, GRASS_BOTTOM), (SIDEWALK_W + 8, GRASS_BOTTOM)),
    ("L", (GRASS_RIGHT, GRASS_BOTTOM)),
]
CONCRETE_PATH = [
    ("M", (GRASS_RIGHT, GRASS_BOTTOM)),
    ("C", (276, 624.5), (280, 628), (281, 635)),
    ("L", (CONCRETE_X, 671)),
    ("L", (CONCRETE_X, BOTTOM_LINE - 2)),
]

_sx, _sy, _sw, _sh = STEPS
BASE_LINES = [
    [(0, 0), (0, VIEW_BOTTOM)],                                  # left boundary
    [(0, 0), (PAD_W, 0)],                                        # top line
    [(PAD_W, 0), (PAD_W, PAD_H)],                                # pad right edge
    [(NOTCH_X, PAD_H), (PAD_W, PAD_H)],                          # pad bottom / grass top
    [(GRASS_RIGHT, PAD_H), (GRASS_RIGHT, GRASS_BOTTOM)],         # mulch line
    [(0, HOUSE_FRONT), (HOUSE_L - 2.5, HOUSE_FRONT)],            # alley line
    [(HOUSE_L, HOUSE_FRONT), (HOUSE_R, HOUSE_FRONT)],            # house front
    [(HOUSE_L, HOUSE_FRONT), (HOUSE_L, VIEW_BOTTOM)],            # house left wall
    [(HOUSE_R, HOUSE_FRONT), (HOUSE_R, BOTTOM_LINE - 4)],        # house right wall
    [(HOUSE_R - 1, BOTTOM_LINE), (PAD_W, BOTTOM_LINE)],          # bottom line
    [(_sx, HOUSE_FRONT), (_sx, _sy), (_sx + _sw, _sy), (_sx + _sw, HOUSE_FRONT)],  # steps
]
BASE_RECTS = [HALF_WALL, AC, SHED]
BASE_CIRCLES = [POST, TABLE]

# ---- Design additions ----
PLANTERS = [(44, y, 24, 72) for y in (300, 390, 480)]
TREE = (215, 329, 30)
TREE_CANOPY = (TREE[0], TREE[1], 150)          # 25' mature canopy, for scale
SHRUBS = [(289, y, 13) for y in (290, 335, 380, 425)]
# Maze 65-gal two-stage geared tumbler (41.3" W x 30" D) at the top of the mulch strip, by the parking pad
COMPOSTER = (271, PAD_H + 4, 30, 41.3)
PERGOLA = (57, 577, 240, 144)
# Royal Shade 6' x 12' x 13.4' right triangle (72" x 144" x 160.8")
SAIL = [(282.0, 487.2), (280.4, 559.2), (136.4, 555.6)]
_px, _py, _pw, _ph = PERGOLA
SAIL_MOUNTS = [(POST[0], POST[1]), (_px + _pw, _py), (_px, _py)]  # one per SAIL corner, same order

# Zen 20' x 12' free-standing 2-block kit, 6x6 frame trimmed to exactly PERGOLA.
TIMBER = 5.5                                   # actual 6x6 size
_cols = (_px, _px + (_pw - TIMBER) / 2, _px + _pw - TIMBER)
_rows = (_py, _py + _ph - TIMBER)
PERGOLA_POSTS = [(x, y, TIMBER, TIMBER) for y in _rows for x in _cols]
PERGOLA_BEAMS = ([(_px, y, _pw, TIMBER) for y in _rows]
                 + [(x, _py, TIMBER, _ph) for x in _cols])
SLATS_PER_OPENING = 11
SLAT_PLAN = 7 / 2 ** 0.5                       # plan footprint of a 2x6 tilted 45 degrees
_in_top, _in_bot = _py + TIMBER, _py + _ph - TIMBER
SLAT_SPACING = (_in_bot - _in_top) / (SLATS_PER_OPENING + 1)   # Zen: span / (slats + 1)
PERGOLA_OPENINGS = [(a + TIMBER, b) for a, b in zip(_cols, _cols[1:])]   # (x_from, x_to)
PERGOLA_SLATS = [(x0, _in_top + k * SLAT_SPACING - SLAT_PLAN / 2, x1 - x0, SLAT_PLAN)
                 for x0, x1 in PERGOLA_OPENINGS for k in range(1, SLATS_PER_OPENING + 1)]
BRACE_LEN = 30
BRACE_PLAN = BRACE_LEN / 2 ** 0.5              # 45-degree knee brace, plan projection
PERGOLA_BRACES = []                            # (start, end) along the beam centerline, from the post face
for _x in (_cols[0], _cols[-1]):
    for _y in _rows:
        _cx, _cy = _x + TIMBER / 2, _y + TIMBER / 2
        _sx_ = 1 if _x == _cols[0] else -1
        _sy_ = 1 if _y == _rows[0] else -1
        _fx, _fy = _cx + _sx_ * TIMBER / 2, _cy + _sy_ * TIMBER / 2
        PERGOLA_BRACES.append(((_fx, _cy), (_fx + _sx_ * BRACE_PLAN, _cy)))
        PERGOLA_BRACES.append(((_cx, _fy), (_cx, _fy + _sy_ * BRACE_PLAN)))
PIER_R = 6                                     # 12" Quik-Tube piers
# Piers: three front posts plus the back-right post (right of the concrete edge); the other two
# back posts bolt to the patio slab.
PERGOLA_PIERS = [(x + TIMBER / 2, y + TIMBER / 2, PIER_R) for x, y, _, _ in PERGOLA_POSTS
                 if y == _rows[0] or x + TIMBER > CONCRETE_X]
PERGOLA_SLAB_POSTS = [p for p in PERGOLA_POSTS if p[1] == _rows[1] and p[0] + TIMBER <= CONCRETE_X]

# fill, fill opacity, stroke
COLORS = {
    "base": (None, 0, "#222222"),
    "planters": ("#2f6fd6", 0.30, "#1f4fa8"),
    "tree": ("#8e44ad", 0.35, "#6c3483"),
    "tree_canopy": ("#c39bd3", 0.15, "#a569bd"),
    "shrubs": ("#d62828", 0.40, "#a4161a"),
    "composter": ("#8b5a2b", 0.45, "#5d3a1a"),
    "pergola": ("#2e8b57", 0.25, "#1f7a3a"),
    "sail": ("#f2c200", 0.45, "#c9a000"),
    "cords": (None, 0, "#e67e22"),
}
