"""Draw rough, correctly placed guide shapes for plan elements into a yard photo.

    python explorations/ai_renders/guides.py [--camera pad|steps] SRC OUT pergola tree planters ...

The image model places objects far better when it "makes the placeholder realistic" than when told where to add them.
Positions and sizes come from src/geometry.py through the camera models in camera.py (--camera picks the photo's;
default pad). Shapes are clipped to what the camera sees, so they also work when it stands among them.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
sys.path.insert(0, HERE)
import camera  # noqa: E402
import geometry as g  # noqa: E402
from camera import P, depth, poly, scale  # noqa: E402


def fill(d, pts, col):
    p = poly(pts)
    if p:
        d.polygon(p, fill=col)


def line3d(d, a, b, col, width):
    p = poly([a, b, b])  # degenerate polygon: clips the segment like a polygon
    if p:
        d.line(p[:len(p) // 3 + 1], fill=col, width=width)


def box(d, x0, x1, y0, y1, z0, z1, col, side=None, top=None):
    """Axis-aligned box; only the faces turned toward the camera are drawn."""
    xc, yc, h = camera.CAM[:3]
    side, top = side or col, top or col
    if xc < x0:
        fill(d, [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], side)
    if xc > x1:
        fill(d, [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], side)
    if yc < y0:
        fill(d, [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], col)
    if yc > y1:
        fill(d, [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], col)
    if h > z1:
        fill(d, [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top)
    if h < z0:
        fill(d, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], top)


def draw_far_first(d, items):
    """items: [((x, y, z) center, callable(d)), ...]; painter's order by distance from the camera."""
    for _, fn in sorted(items, key=lambda it: -depth(*it[0])):
        fn(d)


def disc(cx, cy, z, r, n=40):
    return [(cx + r * math.cos(t), cy + r * math.sin(t), z) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def pergola(d):
    T, POST_H = g.TIMBER, 96
    wood, wood_dk, steel = (74, 50, 34), (52, 34, 24), (20, 20, 20)
    px, py, pw, ph = g.PERGOLA
    top0, top1 = POST_H, POST_H + T
    items = []
    for x, y, _, _ in g.PERGOLA_POSTS:
        items.append(((x + T / 2, y + T / 2, 48), lambda d, x=x, y=y: box(d, x, x + T, y, y + T, 0, POST_H, wood, wood_dk)))
        items.append(((x + T / 2, y + T / 2, 3), lambda d, x=x, y=y: box(d, x - .5, x + T + .5, y - .5, y + T + .5, 0, 6, steel)))
    for x, y, w, ln in g.PERGOLA_BEAMS:
        items.append(((x + w / 2, y + ln / 2, top0), lambda d, x=x, y=y, w=w, ln=ln: box(d, x, x + w, y, y + ln, top0, top1, wood, wood_dk, wood_dk)))
    for x, y, w, ln in g.PERGOLA_SLATS:
        # 2x6 tilted 45 degrees, resting on the beams
        items.append(((x + w / 2, y + 2, top1 + 2), lambda d, x=x, y=y, w=w: fill(
            d, [(x, y, top1), (x + w, y, top1), (x + w, y + 4, top1 + 4), (x, y + 4, top1 + 4)], wood)))
    for (ax, ay), (bx, by) in g.PERGOLA_BRACES:
        items.append((((ax + bx) / 2, (ay + by) / 2, POST_H - 10), lambda d, ax=ax, ay=ay, bx=bx, by=by: line3d(
            d, (ax, ay, POST_H - g.BRACE_PLAN), (bx, by, POST_H), wood, 4)))
    draw_far_first(d, items)


def tree(d):
    """Young Bigtooth maple: trunk to 4', a few limbs, irregular rounded crown ~7' wide from 4' to 11'."""
    tx, ty, _ = g.TREE
    s = scale(ty)
    bx, by = P(tx, ty)
    d.ellipse([bx - 18 * s, by - 5 * s, bx + 18 * s, by + 5 * s], fill=(92, 64, 44))  # mulch ring
    rng = np.random.default_rng(4)
    trunk_top = P(tx, ty, 50)
    d.line([(bx, by), trunk_top], fill=(96, 92, 86), width=max(3, round(2.2 * s)))
    for lx, lz in [(-30, 112), (-14, 124), (4, 128), (20, 120), (32, 106)]:
        d.line([trunk_top, P(tx + lx, ty, lz)], fill=(90, 84, 78), width=max(2, round(1.2 * s)))
    cols = [(166, 74, 38), (186, 96, 44), (150, 58, 36), (196, 128, 52), (128, 52, 34)]
    for _ in range(140):
        ox, oz = rng.normal(0, 17), 88 + rng.normal(0, 13)
        if (ox / 40) ** 2 + ((oz - 88) / 36) ** 2 > 1:
            continue
        u, v = P(tx + ox, ty, oz)
        r = rng.uniform(4, 9) * s
        d.ellipse([u - r, v - r, u + r, v + r], fill=cols[rng.integers(len(cols))])


def planters(d):
    """Three beds (20" tall) along the lawn's sidewalk edge, each with a 6' trellis + vine on the sidewalk side."""
    items = []
    for x, y, w, ln in g.PLANTERS:
        def bed(d, x=x, y=y, w=w, ln=ln):
            box(d, x, x + w, y, y + ln, 0, 20, (140, 98, 60), (120, 84, 52), (70, 60, 40))
            fill(d, [(x + 2, y + 4, 20), (x + 2, y + ln - 4, 20), (x + 2, y + ln - 4, 72), (x + 2, y + 4, 72)],
                 (60, 110, 50))
        items.append(((x + w / 2, y + ln / 2, 10), bed))
    draw_far_first(d, items)


def planters_fence(d):
    """Single row of the three beds on the sidewalk, against the white fence, each with a trellis on the fence."""
    items = []
    for _, y, w, ln in g.PLANTERS:
        def bed(d, y=y, w=w, ln=ln):
            box(d, 1, 1 + w, y, y + ln, 0, 20, (140, 98, 60), (120, 84, 52), (70, 60, 40))
            fill(d, [(1, y + 4, 20), (1, y + ln - 4, 20), (1, y + ln - 4, 72), (1, y + 4, 72)], (60, 110, 50))
        items.append(((1 + w / 2, y + ln / 2, 10), bed))
    draw_far_first(d, items)


def shrubs(d):
    for x, y, r in sorted(g.SHRUBS, key=lambda s: -depth(s[0], s[1])):
        bx, by = P(x, y)
        s = scale(y, x)
        d.ellipse([bx - r * s, by - 2 * r * s, bx + r * s, by + 2], fill=(62, 96, 52))


def table(d):
    """84" round top at 30" on a pedestal."""
    x, y, r = g.TABLE
    box(d, x - 3, x + 3, y - 3, y + 3, 0, 30, (40, 30, 24))
    fill(d, disc(x, y, 30, r), (50, 36, 28))


def sail(d, z_post=150):
    # the post corner is raised (sails are pitched) so the sail reads from a low camera
    (ax, ay), (bx, by), (cx, cy) = g.SAIL
    fill(d, [(ax, ay, z_post), (bx, by, 98), (cx, cy, 98)], (214, 196, 160))
    for (sx, sy, sz), mount in zip([(ax, ay, z_post), (bx, by, 98), (cx, cy, 98)],
                                   [(*g.SAIL_MOUNTS[0], z_post + 8), (*g.SAIL_MOUNTS[1], 101), (*g.SAIL_MOUNTS[2], 101)]):
        line3d(d, (sx, sy, sz), mount, (40, 40, 40), 2)


def path(d):
    """Curving stepping stones (22" across) from the pad edge past the planters to the pergola's front-left."""
    stones = []
    for k in range(9):
        t = k / 8
        stones.append((110 + 20 * math.sin(t * math.pi) - 30 * t, 240 + t * 320))
    for x, y in sorted(stones, key=lambda s: -depth(s[0], s[1])):
        fill(d, disc(x, y, 0, 11, 24), (150, 146, 140))


def _flatten(path, n=12):
    """Plan path [(cmd, points...)] (M, L, C, Q as in SVG) -> list of (x, y)."""
    pts = []
    for cmd, *ps in path:
        if cmd in ("M", "L"):
            pts.append(ps[0])
            continue
        p0 = np.array(pts[-1], float)
        cs = [np.array(q, float) for q in ps]
        for t in np.linspace(1 / n, 1, n):
            if cmd == "Q":
                q = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * cs[0] + t ** 2 * cs[1]
            else:
                q = ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * cs[0] + 3 * (1 - t) * t ** 2 * cs[1]
                     + t ** 3 * cs[2])
            pts.append(tuple(q))
    return pts


def lawn(d):
    """The lawn area (plan GRASS_PATH, closed along the gravel and the pad), flat green."""
    pts = _flatten(g.GRASS_PATH) + [(g.GRASS_RIGHT, g.PAD_H)]
    fill(d, [(x, y, 0) for x, y in pts], (88, 132, 58))


def composter(d):
    """Maze 65-gal geared tumbler: two black drums on a frame, ~44" tall."""
    x, y, w, ln = g.COMPOSTER
    box(d, x, x + w, y, y + ln, 0, 44.5, (25, 25, 25), (40, 40, 40), (30, 30, 30))


def overlay(d):
    """Thin outlines of the plan (base lines + colored additions) for checking the camera fit by eye."""
    def seg(pts, col, w=2):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            line3d(d, (ax, ay, 0), (bx, by, 0), col, w)

    def flat(path):
        pts = []
        for cmd, *ps in path:
            if cmd in ("M", "L"):
                pts.append(ps[0])
            else:
                pts.append(ps[-1])
        return pts

    for line in g.BASE_LINES:
        seg(line, (0, 0, 0))
    seg(flat(g.GRASS_PATH), (0, 0, 0))
    seg(flat(g.CONCRETE_PATH), (0, 0, 0))
    px, py, pw, ph = g.PERGOLA
    seg([(px, py), (px + pw, py), (px + pw, py + ph), (px, py + ph), (px, py)], (46, 139, 87), 3)
    for x, y, w, ln in g.PLANTERS:
        seg([(x, y), (x + w, y), (x + w, y + ln), (x, y + ln), (x, y)], (47, 111, 214), 3)
    x, y, w, ln = g.COMPOSTER
    seg([(x, y), (x + w, y), (x + w, y + ln), (x, y + ln), (x, y)], (139, 90, 43), 3)
    for cx_, cy_, r in [g.TREE, g.TABLE, *g.SHRUBS]:
        ring = [(cx_ + r * math.cos(t), cy_ + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40)]
        seg(ring, (142, 68, 173) if (cx_, cy_) == g.TREE[:2] else (214, 40, 40), 3)
    sail_pts = [(282.0, 487.2), (280.4, 559.2), (136.4, 555.6), (282.0, 487.2)]
    seg(sail_pts, (242, 194, 0), 3)


FUNCS = {"lawn": lawn, "pergola": pergola, "tree": tree, "planters": planters, "shrubs": shrubs, "table": table, "sail": sail,
         "path": path, "composter": composter, "planters_fence": planters_fence, "overlay": overlay}

if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--camera"]:
        camera.use(args[1])
        args = args[2:]
    src, out, *what = args
    im = Image.open(src).convert("RGB")
    before = np.array(im)
    d = ImageDraw.Draw(im)
    for w in what:
        FUNCS[w](d)
    im.save(out)
    # footprint mask of everything drawn, for edit_region.py --mask
    changed = (np.abs(np.array(im).astype(int) - before).sum(axis=2) > 0).astype("uint8") * 255
    mask_path = out.rsplit(".", 1)[0] + "_mask.png"
    Image.fromarray(changed, "L").save(mask_path)
    print("wrote", out, "and", mask_path, what)
