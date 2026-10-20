"""Render the backyard plan from geometry.py as a layered PSD (Procreate imports PSD layers).

Units are inches. Run with a Python that has Pillow.
"""
import math
import re
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import geometry as g

OUT_DIR = Path(__file__).resolve().parent.parent / "plan"
PPI = 6           # output pixels per inch
SS = 2            # supersampling factor for smooth lines
X0, Y0, X1, Y1 = -30, -30, 340, g.VIEW_BOTTOM   # canvas extent in inches (adds margin for labels)
W, H = int((X1 - X0) * PPI), int((Y1 - Y0) * PPI)
S = PPI * SS
FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

BLACK = (34, 34, 34, 255)
DIM_GRAY = (40, 40, 40, 255)
# Label position per sail cord, relative to the cord midpoint; None = along the cord
CORD_LABEL_OFFSETS = [(13.5, 8.8), (10.3, -2.1), None]


def P(x, y):
    return ((x - X0) * S, (y - Y0) * S)


def inch_label(inches, approx=False):
    q = round(inches * 4) / 4
    whole = int(q)
    frac = {0: "", 0.25: "¼", 0.5: "½", 0.75: "¾"}[round(q - whole, 2)]
    return ("~" if approx else "") + f'{whole}{frac}"'


def cubic(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(1, n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def quad(p0, p1, p2, n=12):
    pts = []
    for i in range(1, n + 1):
        t = i / n
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t ** 2
        pts.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return pts


def flatten(cmds):
    pts = []
    for cmd, *args in cmds:
        if cmd in ("M", "L"):
            pts.append(args[0])
        elif cmd == "C":
            pts += cubic(pts[-1], *args)
        elif cmd == "Q":
            pts += quad(pts[-1], *args)
    return pts


def rgba(hex_color, opacity=1.0):
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), round(255 * opacity))


def upright(angle):
    if angle > 90:
        return angle - 180
    if angle <= -90:
        return angle + 180
    return angle


class Layer:
    def __init__(self, name):
        self.name = name
        self.img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def poly(self, pts, color, width=0.5, closed=False, fill=None):
        px = [P(*p) for p in pts]
        if fill:
            self.d.polygon(px, fill=fill)
        if closed:
            px = px + [px[0]]
        self.d.line(px, fill=color, width=max(1, round(width * S)), joint="curve")

    def rect(self, x, y, w, h, color, width=0.5, fill=None):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], color, width, True, fill)

    def circle(self, cx, cy, r, color, width=0.5, fill=None):
        (ax, ay), (bx, by) = P(cx - r, cy - r), P(cx + r, cy + r)
        self.d.ellipse([ax, ay, bx, by], fill=fill, outline=color, width=max(1, round(width * S)))

    def text(self, x, y, s, color, size=4.5, angle=0.0):
        font = ImageFont.truetype(FONT_PATH, round(size * S))
        halo = max(2, round(0.6 * S))
        l, t, r, b = font.getbbox(s, stroke_width=halo)
        tile = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((2 - l, 2 - t), s, font=font, fill=color,
                                  stroke_width=halo, stroke_fill=(255, 255, 255, 255))
        if angle:
            tile = tile.rotate(angle, resample=Image.BICUBIC, expand=True)
        cx, cy = P(x, y)
        self.img.alpha_composite(tile, (round(cx - tile.width / 2), round(cy - tile.height / 2)))

    def dim(self, p1, p2, label, color, off=0.0, size=4.5):
        """Dimension line with architectural ticks; off shifts it perpendicular with extension lines."""
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        q1 = (p1[0] + nx * off, p1[1] + ny * off)
        q2 = (p2[0] + nx * off, p2[1] + ny * off)
        if off:
            for p, q in ((p1, q1), (p2, q2)):
                self.poly([p, (q[0] + nx * 1.5 * math.copysign(1, off), q[1] + ny * 1.5 * math.copysign(1, off))], color, 0.2)
        self.poly([q1, q2], color, 0.25)
        tk = 1.6
        for q in (q1, q2):
            self.poly([(q[0] - (ux + nx) * tk, q[1] - (uy + ny) * tk),
                       (q[0] + (ux + nx) * tk, q[1] + (uy + ny) * tk)], color, 0.35)
        ang = upright(-math.degrees(math.atan2(dy, dx)))
        self.text((q1[0] + q2[0]) / 2, (q1[1] + q2[1]) / 2, label, color, size, ang)

    def finish(self):
        return self.img.resize((W, H), Image.LANCZOS)


def build_layers():
    layers = []

    bg = Layer("Background")
    bg.img.paste((255, 255, 255, 255), (0, 0, bg.img.width, bg.img.height))
    layers.append(bg)

    # ---- Base black line drawing ----
    base = Layer("Base lines")
    lw = 0.5
    for seg in g.BASE_LINES:
        base.poly(seg, BLACK, lw)
    for path in (g.GRASS_PATH, g.CONCRETE_PATH):
        base.poly(flatten(path), BLACK, lw)
    for r in g.BASE_RECTS:
        base.rect(*r, BLACK, lw)
    for cc in g.BASE_CIRCLES:
        base.circle(*cc, BLACK, lw)
    layers.append(base)

    # ---- Base measurements (placement offsets are hand-tuned to avoid overlaps) ----
    m = Layer("Base measurements")
    c = DIM_GRAY
    sm = 3.2
    hx, hy, hw, hh = g.HALF_WALL
    sx, sy, sw, sh_ = g.STEPS
    ax_, ay_, aw, ah = g.AC
    shx, shy, shw, shh = g.SHED
    px, py, pr = g.POST
    ptop, pbot = py - pr, py + pr
    PW, PH, GB, GR, HF, BL = g.PAD_W, g.PAD_H, g.GRASS_BOTTOM, g.GRASS_RIGHT, g.HOUSE_FRONT, g.BOTTOM_LINE
    for p1, p2, kw in [
        ((0, -14), (PW, -14), {}),
        ((0, 20), (hx, 20), {}),
        ((hx + hw, 20), (PW, 20), {}),
        ((hx, hy + hh + 7), (hx + hw, hy + hh + 7), {"size": sm}),
        ((g.SIDEWALK_W, PH + 19), (g.NOTCH_X, PH + 19), {}),
        ((g.NOTCH_X, PH + 9), (GR, PH + 9), {}),
        ((g.SIDEWALK_W, GB - 13), (GR, GB - 13), {}),
        ((GR, py - 23), (PW, py - 23), {"size": sm}),
        ((sx, sy - 8), (sx + sw, sy - 8), {}),
        ((g.HOUSE_L, HF + 11), (sx, HF + 11), {"size": sm}),
        ((sx + sw, HF + 11), (g.HOUSE_R, HF + 11), {"size": sm}),
        ((g.HOUSE_L, HF + 31), (g.HOUSE_R, HF + 31), {}),
        ((0, HF + 23), (g.HOUSE_L, HF + 23), {"size": sm}),
        ((g.HOUSE_R, (ay_ + ah + shy) / 2), (g.CONCRETE_X, (ay_ + ah + shy) / 2), {}),
        ((g.CONCRETE_X, BL - 11), (PW, BL - 11), {"size": sm}),
        ((-14, 0), (-14, PH), {}),
        ((20, g.NOTCH_BOTTOM), (20, GB), {}),
        ((50, PH), (50, g.NOTCH_BOTTOM), {"size": sm}),
        ((260, PH), (260, GB), {}),
        ((318, PH), (318, ptop), {"size": sm}),
        ((318, pbot), (318, GB), {"size": sm}),
        ((33, GB), (33, HF), {"size": sm}),
        ((150, GB), (150, sy), {"size": sm}),
        ((150, sy), (150, HF), {"size": sm}),
        ((300, HF), (300, BL), {"size": sm}),
        ((hx + hw + 7, hy), (hx + hw + 7, hy + hh), {"size": sm}),
        ((hx + hw + 7, 0), (hx + hw + 7, hy), {"size": 2.4}),
    ]:
        m.dim(p1, p2, inch_label(math.dist(p1, p2)), c, **kw)
    for y, x0 in ((PH, PW), (ptop, px + 4), (pbot, px + 4), (GB, PW)):
        m.poly([(x0, y), (321, y)], c, 0.2)
    m.text(px + 11, py - 11.2, f'{2 * pr:g}" dia.', c, 2.8)
    tx, ty, tr_ = g.TABLE
    m.text(tx, ty, inch_label(2 * tr_) + " dia.", c, sm)
    m.text(ax_ + aw / 2, ay_ + 11, "A/C", c, sm)
    m.text(ax_ + aw / 2, ay_ + 21, f"{inch_label(aw)} × {inch_label(ah)}", c, 2.6)
    m.text(shx + shw / 2, shy + 9.5, "Shed", c, sm)
    m.text(shx + shw / 2, shy + 20.5, f"{inch_label(shw)} × {inch_label(shh)}", c, 2.8)
    layers.append(m)

    # ---- Planters (blue) ----
    fill, op, stroke = g.COLORS["planters"]
    blue_d = rgba(stroke)
    pl = Layer("Planters (blue)")
    for r in g.PLANTERS:
        pl.rect(*r, blue_d, 0.35, fill=rgba(fill, op))
    layers.append(pl)
    pm = Layer("Planters - measurements")
    for x, y, w, h in g.PLANTERS:
        pm.text(x + w / 2, y + h / 2, f"{inch_label(w)} × {inch_label(h)}", blue_d, 3.0, 90)
    for (x, y1, w, h1), (_, y2, _, _) in zip(g.PLANTERS, g.PLANTERS[1:]):
        pm.dim((x + w + 6, y1 + h1), (x + w + 6, y2), inch_label(y2 - y1 - h1), blue_d, size=2.8)
    layers.append(pm)

    # ---- Tree (purple) ----
    fill, op, stroke = g.COLORS["tree"]
    tx, ty, tr_ = g.TREE
    tr = Layer("Tree (purple)")
    cfill, cop, cstroke = g.COLORS["tree_canopy"]
    tr.circle(*g.TREE_CANOPY, rgba(cstroke), 0.3, fill=rgba(cfill, cop))
    tr.circle(tx, ty, tr_, rgba(stroke), 0.35, fill=rgba(fill, op))
    layers.append(tr)
    tm = Layer("Tree - measurements")
    _, _, cr = g.TREE_CANOPY
    tm.dim((tx, ty - cr), (tx, ty + cr), "", rgba(cstroke), size=3.5)
    tm.text(tx, ty + cr * 0.55, f"{inch_label(2 * cr)} (25') mature canopy", (125, 60, 152, 255), 3.5)
    tm.dim((tx - tr_, ty), (tx + tr_, ty), inch_label(2 * tr_, True) + " canopy", (88, 40, 110, 255), size=3.5)
    layers.append(tm)

    # ---- Shrubs (red) ----
    fill, op, stroke = g.COLORS["shrubs"]
    red_d = rgba(stroke)
    sh = Layer("Shrubs (red)")
    for s in g.SHRUBS:
        sh.circle(*s, red_d, 0.35, fill=rgba(fill, op))
    layers.append(sh)
    smm = Layer("Shrubs - measurements")
    for x, y, r in g.SHRUBS:
        smm.text(x, y, inch_label(2 * r, True), red_d, 2.8)
    (x1, y1, r1), (_, y2, _) = g.SHRUBS[:2]
    smm.dim((x1 + 15, y1), (x1 + 15, y2), f"{inch_label(y2 - y1)} o.c.", red_d, size=2.6)
    layers.append(smm)

    # ---- Composter (brown) ----
    fill, op, stroke = g.COLORS["composter"]
    brown_d = rgba(stroke)
    cx0, cy0, cw, ch = g.COMPOSTER
    co = Layer("Composter (brown)")
    co.rect(cx0, cy0, cw, ch, brown_d, 0.35, fill=rgba(fill, op))
    layers.append(co)
    cm = Layer("Composter - measurements")
    cm.text(cx0 + cw / 2, cy0 + ch / 2 - 4, "Compost", brown_d, 2.6)
    cm.text(cx0 + cw / 2, cy0 + ch / 2 + 2, f"{inch_label(cw)} × {inch_label(ch)}", brown_d, 2.4)
    cm.dim((cx0 + cw + 6, cy0), (cx0 + cw + 6, cy0 + ch), inch_label(ch), brown_d, size=2.6)
    layers.append(cm)

    # ---- Pergola (green) ----
    fill, op, stroke = g.COLORS["pergola"]
    green_d = rgba(stroke)
    gx, gy, gw, gh = g.PERGOLA
    brace_c = (11, 77, 35, 255)
    pg = Layer("Pergola (green)")
    pg.rect(gx, gy, gw, gh, green_d, 0.3, fill=rgba(fill, 0.08))
    for cx_, cy_, r_ in g.PERGOLA_PIERS:
        pg.circle(cx_, cy_, r_, green_d, 0.25)
    for r in g.PERGOLA_SLATS:
        pg.rect(*r, green_d, 0.15, fill=rgba(fill, 0.15))
    for r in g.PERGOLA_BEAMS:
        pg.rect(*r, green_d, 0.3, fill=rgba(fill, 0.45))
    for r in g.PERGOLA_POSTS:
        pg.rect(*r, green_d, 0.3, fill=rgba(stroke, 0.9))
    for a, b in g.PERGOLA_BRACES:
        pg.poly([a, b], brace_c, 0.9)
    layers.append(pg)
    pgm = Layer("Pergola - measurements")
    t = g.TIMBER
    xs = sorted({x for x, _, _, _ in g.PERGOLA_POSTS})
    pgm.dim((gx, gy - 6), (gx + gw, gy - 6), inch_label(gw) + " overall", green_d, size=3.2)
    pgm.dim((gx - 6, gy), (gx - 6, gy + gh), inch_label(gh), green_d, size=3.2)
    pgm.dim((0, gy + 40), (gx, gy + 40), inch_label(gx), green_d, size=3.0)
    pgm.dim((gx + gw, gy + 40), (g.PAD_W, gy + 40), inch_label(g.PAD_W - gx - gw), green_d, size=2.4)
    for a, b in zip(xs, xs[1:]):
        pgm.dim((a + t, gy + gh - 16), (b, gy + gh - 16), inch_label(b - a - t) + " clear", green_d, size=2.8)
    ox0, ox1 = g.PERGOLA_OPENINGS[0]
    s0, s1 = g.PERGOLA_SLATS[0], g.PERGOLA_SLATS[1]
    pgm.dim((ox0 + 40, s0[1] + s0[3] / 2), (ox0 + 40, s1[1] + s1[3] / 2),
            inch_label(g.SLAT_SPACING) + " o.c.", green_d, size=2.4)
    pgm.text((ox0 + ox1) / 2, gy + gh / 2 - 2, f"{g.SLATS_PER_OPENING} angled 2x6 slats", green_d, 3.0)
    pgm.text((ox0 + ox1) / 2, gy + gh / 2 + 3, "per opening (45°)", green_d, 2.6)
    pgm.text(xs[1] - 10, gy + t + 4.3, '6x6 post', green_d, 2.4)
    fx, fy, fr = g.PERGOLA_PIERS[1]
    pgm.text(fx + 14, fy + 10, '12" pier', green_d, 2.4)
    sx_, sy_, _, _ = g.PERGOLA_SLAB_POSTS[1]
    pgm.text(sx_ + t / 2, sy_ - 3.5, "slab anchors", green_d, 2.4)
    (bx0, by0), (bx1, by1) = g.PERGOLA_BRACES[0]
    pgm.text((bx0 + bx1) / 2 + 3, (by0 + t / 2 + g.PERGOLA_SLATS[0][1]) / 2, f'{inch_label(g.BRACE_LEN)} brace', brace_c, 2.4)
    layers.append(pgm)

    # ---- Shade sail (yellow) ----
    fill, op, stroke = g.COLORS["sail"]
    sail = g.SAIL
    ys = Layer("Shade sail (yellow)")
    ys.poly(sail, rgba(stroke), 0.35, closed=True, fill=rgba(fill, op))
    layers.append(ys)
    ysm = Layer("Shade sail - measurements")
    yd = (138, 109, 0, 255)
    sides = []
    for a, b in zip(sail, sail[1:] + sail[:1]):
        sides.append(math.dist(a, b))
        ysm.dim(a, b, inch_label(sides[-1]), yd, off=-6, size=3.5)
    cxs = sum(p[0] for p in sail) / 3 + 7
    cys = sum(p[1] for p in sail) / 3
    ysm.text(cxs, cys + 2, "Royal Shade right triangle", yd, 2.8)
    ysm.text(cxs, cys + 8, " × ".join(f'{round(s, 1):g}"' for s in sorted(sides)), yd, 2.8)
    layers.append(ysm)

    # ---- Cords (orange) ----
    _, _, stroke = g.COLORS["cords"]
    od = (192, 86, 26, 255)
    cords = list(zip(g.SAIL, g.SAIL_MOUNTS))
    cd = Layer("Sail cords (orange)")
    for a, b in cords:
        cd.poly([a, b], rgba(stroke), 0.35)
    layers.append(cd)
    cdm = Layer("Sail cords - measurements")
    for (a, b), off in zip(cords, CORD_LABEL_OFFSETS):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if off:
            cdm.text(mx + off[0], my + off[1], inch_label(math.dist(a, b)), od, 2.8)
        else:
            ang = upright(-math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
            cdm.text(mx, my - 3.5, inch_label(math.dist(a, b)), od, 3.0, ang)
    layers.append(cdm)

    return [(lyr.name, lyr.finish()) for lyr in layers]


# ---------------- PSD writer (8-bit RGB, PackBits) ----------------
_RUN = re.compile(rb"(.)\1{2,}", re.DOTALL)


def _packbits(row: bytes) -> bytes:
    out = bytearray()

    def literal(chunk):
        for i in range(0, len(chunk), 128):
            part = chunk[i:i + 128]
            out.append(len(part) - 1)
            out.extend(part)

    pos = 0
    for mt in _RUN.finditer(row):
        s, e = mt.span()
        literal(row[pos:s])
        n, val = e - s, row[s]
        while n >= 2:
            k = min(128, n)
            out.append((257 - k) & 0xFF)
            out.append(val)
            n -= k
        if n == 1:
            literal(bytes([val]))
        pos = e
    literal(row[pos:])
    return bytes(out)


def _rle_channel(plane: bytes, w: int, h: int):
    rows = [_packbits(plane[i * w:(i + 1) * w]) for i in range(h)]
    return b"".join(struct.pack(">H", len(r)) for r in rows), b"".join(rows)


def _pascal(name: str) -> bytes:
    raw = name.encode("mac_roman", "replace")[:255]
    b = bytes([len(raw)]) + raw
    return b + b"\0" * ((4 - len(b) % 4) % 4)


def _unicode_name_block(name: str) -> bytes:
    data = struct.pack(">I", len(name)) + name.encode("utf-16-be")
    if len(data) % 2:
        data += b"\0"
    return b"8BIMluni" + struct.pack(">I", len(data)) + data


def composite(layers):
    comp = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    for _, img in layers:
        comp.alpha_composite(img)
    return comp.convert("RGB")


def write_psd(path: Path, layers):
    records, channel_data = bytearray(), bytearray()
    for name, img in layers:
        bbox = img.getchannel("A").getbbox() or (0, 0, 1, 1)
        crop = img.crop(bbox)
        cw, ch = crop.size
        left, top, right, bottom = bbox
        chans = []
        for cid, band in ((-1, "A"), (0, "R"), (1, "G"), (2, "B")):
            counts, data = _rle_channel(crop.getchannel(band).tobytes(), cw, ch)
            blob = struct.pack(">H", 1) + counts + data
            chans.append((cid, blob))
        rec = struct.pack(">iiiiH", top, left, bottom, right, len(chans))
        for cid, blob in chans:
            rec += struct.pack(">hI", cid, len(blob))
        extra = struct.pack(">I", 0) + struct.pack(">I", 0) + _pascal(name) + _unicode_name_block(name)
        rec += b"8BIMnorm" + bytes([255, 0, 0, 0]) + struct.pack(">I", len(extra)) + extra
        records += rec
        for _, blob in chans:
            channel_data += blob

    layer_info = struct.pack(">h", len(layers)) + records + channel_data
    if len(layer_info) % 2:
        layer_info += b"\0"
    layer_and_mask = struct.pack(">I", len(layer_info)) + layer_info + struct.pack(">I", 0)

    comp = composite(layers)
    all_counts, all_data = bytearray(), bytearray()
    for band in "RGB":
        cts, dat = _rle_channel(comp.getchannel(band).tobytes(), W, H)
        all_counts += cts
        all_data += dat

    with open(path, "wb") as f:
        f.write(b"8BPS" + struct.pack(">H", 1) + b"\0" * 6 + struct.pack(">HIIHH", 3, H, W, 8, 3))
        f.write(struct.pack(">I", 0))   # color mode data
        f.write(struct.pack(">I", 0))   # image resources
        f.write(struct.pack(">I", len(layer_and_mask)) + layer_and_mask)
        f.write(struct.pack(">H", 1) + all_counts + all_data)
    return comp


if __name__ == "__main__":
    import sys
    lyrs = build_layers()
    if "--preview-only" in sys.argv:
        preview = composite(lyrs)
    else:
        preview = write_psd(OUT_DIR / "backyard_plan_layers.psd", lyrs)
    preview.save(OUT_DIR / "backyard_plan_layers_preview.png")
    print(f"{W}x{H}px, {len(lyrs)} layers:", ", ".join(n for n, _ in lyrs))
