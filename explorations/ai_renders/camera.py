"""Camera models for the yard photos: map plan coordinates (inches; x from the left/NE lot line, y from the alley,
z up) to photo pixels.

Pinhole camera with position, yaw, pitch, roll, focal length and radial lens distortion, fitted by least squares to
ground points, to points somewhere along known plan lines (fence bases, lawn edges) and to points along vertical
lines (the utility pole). One entry per photo in CAMERAS; pick one with use(name) or the BACKYARD_CAMERA environment
variable (default "pad"). Run this file to refit:  python camera.py [name]
"""
import math
import os
import sys

import numpy as np

CAMERAS = {
    # parking pad, looking toward the house (1024 x 771)
    "pad": dict(
        photo="private/references/0661d98b-0298-459b-9c9f-9e175cb9389c.jpg",
        size=(1024, 771),
        # (plan x, plan y, z) -> (u, v), read off the photo by eye
        points=[
            ((23.5, 721, 0), (726, 430)),   # house wall, fence-side corner
            ((186, 721, 0), (545, 431)),    # house wall, A/C-side corner
            ((0, 721, 0), (752, 430)),      # white fence base at the house wall line
            ((289, 479.2, 0), (345, 440)),  # base of the utility pole (the plan's "post")
            ((270, 217, 0), (140, 521)),    # lawn corner by the gravel strip, pad end
            ((41.5, 625, 0), (707, 445)),   # lawn's far corner at the sidewalk
            ((270, 625, 0), (452, 431)),    # lawn's far corner by the patio, gravel side
            ((72, 670, 0), (667, 432)),     # front edge of the steps, fence-side end
            ((141, 670, 0), (600, 428)),    # front edge of the steps, other end
        ],
        # (plan line, [(u, v), ...]): points somewhere on a z = 0 line; ("x", x0) is x = x0, ("y", y0) is y = y0
        lines=[
            (("x", 0), [(755, 435), (775, 475), (805, 520), (840, 575)]),    # white fence base
            (("x", 41.5), [(710, 475), (706, 495)]),                         # lawn / sidewalk edge
            (("x", 308), [(150, 468), (300, 449), (440, 431)]),              # tan fence base (top of the gravel)
            (("x", 270), [(150, 477), (300, 455)]),                          # gravel / lawn edge
            (("y", 217), [(200, 529), (350, 537)]),                          # pad / lawn edge
        ],
        verticals=[],
        # xc, yc, h (in), yaw, pitch, roll (rad), f (px), k1 (radial lens distortion)
        cam=(46.7976, -18.3811, 62.3838, 0.2457, -0.0299, 0.011, 771.6877, -0.3666),  # fit: max 13 px, mean 5 px
        start=dict(xc=(40, 80, 120), yc=(-200, -120, -40), h=55.0, yaw=0.0),
    ),
    # house steps, looking back toward the parking pad and alley (771 x 1024, wide-angle phone lens)
    "steps": dict(
        photo="private/references/053a0642-d716-49ce-bec7-b354ee44c0dd.jpg",
        size=(771, 1024),
        points=[
            ((289, 479.2, 0), (495, 487)),  # base of the utility pole
        ],
        lines=[
            (("x", 308), [(345, 437), (520, 491), (545, 500), (575, 497), (640, 519)]),  # tan fence base
            (("x", 270), [(370, 447), (600, 520), (675, 550)]),              # gravel / lawn edge
            (("y", 217), [(170, 444), (200, 442), (250, 439), (290, 437)]),  # lawn / pad edge (measured)
            # lawn / patio edge (measured where grass meets concrete)
            (("y", 625), [(10, 837), (50, 831), (90, 813), (130, 801), (170, 778), (210, 761), (250, 747), (290, 742),
                           (330, 730), (370, 715), (410, 700), (430, 695)]),
            (("x", 41.5), [(43, 485), (38, 495), (33, 505), (31, 515), (19, 525), (9, 535)]),  # lawn / sidewalk edge (measured)
        ],
        # (plan x, plan y): points somewhere along the vertical line through it
        verticals=[((289, 479.2), [(503, 400), (517, 200), (527, 5)])],      # utility pole
        cam=(140.7611, 678.2179, 59.0335, 2.7942, -0.3271, -0.0176, 316.6778, 1.4138, -0.7127),  # fisheye fit: max 15 px, mean 7 px
        # the phone's 0.6x ultra-wide is a fisheye-like lens: equidistant model (r = f * theta) + k1, k2
        lens="fisheye",
        start=dict(xc=(80, 110, 140), yc=(680, 710, 740), h=75.0, yaw=math.pi, k2=True),
    ),
}

NAME = PHOTO = W = H = POINTS = LINES = VERTICALS = CAM = None
LENS = "pinhole"


def use(name: str):
    """Make CAMERAS[name] the active camera (P, scale and project use it)."""
    global NAME, PHOTO, W, H, POINTS, LINES, VERTICALS, CAM, LENS
    c = CAMERAS[name]
    LENS = c.get("lens", "pinhole")
    NAME, PHOTO, (W, H) = name, c["photo"], c["size"]
    POINTS, LINES, VERTICALS, CAM = c["points"], c["lines"], c["verticals"], c["cam"]


def _rot(yaw, pitch, roll):
    cy, sy, cp, sp, cr, sr = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch), np.cos(roll), np.sin(roll)
    Ry = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def project(x, y, z=0.0, cam=None):
    c = CAM if cam is None else cam
    xc, yc, h, yaw, pitch, roll, f, k1 = c[:8]
    k2 = c[8] if len(c) > 8 else 0.0
    X, Y, Z = _rot(yaw, pitch, roll) @ np.array([x - xc, z - h, y - yc], dtype=float)
    return _lens(X, Y, Z, f, k1, k2)


def _lens(X, Y, Z, f, k1, k2):
    if LENS == "fisheye":
        rho = math.hypot(X, Y)
        th = math.atan2(rho, Z)  # angle from the optical axis
        rd = th * (1 + k1 * th * th + k2 * th ** 4)
        s = f * rd / rho if rho > 1e-9 else f / Z
        return (W / 2 - s * X, H / 2 - s * Y)
    a, b = X / Z, Y / Z
    r2 = a * a + b * b
    d = 1 + k1 * r2 + k2 * r2 * r2
    return (W / 2 - f * a * d, H / 2 - f * b * d)


def P(x, y, z=0.0):
    u, v = project(x, y, z)
    return (float(u), float(v))


def scale(y, x=150.0):
    """Approximate pixels per inch at plan depth y."""
    return abs(project(x + 6, y)[0] - project(x - 6, y)[0]) / 12


def to_cam(x, y, z=0.0):
    """Plan point -> camera space (X toward the image's left, Y up, Z forward), in inches."""
    xc, yc, h, yaw, pitch, roll = CAM[:6]
    return _rot(yaw, pitch, roll) @ np.array([x - xc, z - h, y - yc], dtype=float)


def depth(x, y, z=0.0):
    """Distance in front of the camera (negative = behind it); for drawing far things first."""
    return float(to_cam(x, y, z)[2])


def _image(q):
    k2 = CAM[8] if len(CAM) > 8 else 0.0
    u, v = _lens(q[0], q[1], q[2], CAM[6], CAM[7], k2)
    return (float(u), float(v))


def poly(pts, near=6.0, margin=1.1, steps=12):
    """Project a 3-D polygon [(x, y, z), ...] onto the photo, clipped to what the camera sees (in front of it and
    within the frame plus `margin`), with edges split so they bend with the lens distortion. [] if nothing shows.
    Needed when the camera stands among the objects (e.g. under the pergola)."""
    f = CAM[6]
    am, bm = margin * W / 2 / f, margin * H / 2 / f
    planes = [np.array(n) for n in ((0, 0, 1, -near), (-1, 0, am, 0), (1, 0, am, 0), (0, -1, bm, 0), (0, 1, bm, 0))]
    cp = [to_cam(*p) for p in pts]
    for n in planes:
        out = []
        for i, a in enumerate(cp):
            b = cp[(i + 1) % len(cp)]
            da, db = n[:3] @ a + n[3], n[:3] @ b + n[3]
            if da >= 0:
                out.append(a)
            if (da >= 0) != (db >= 0):
                out.append(a + (b - a) * (da / (da - db)))
        cp = out
        if len(cp) < 3:
            return []
    dense = [a + (b - a) * t for a, b in zip(cp, cp[1:] + cp[:1]) for t in np.linspace(0, 1, steps, endpoint=False)]
    return [_image(q) for q in dense]


def _residuals(p):
    r = []
    for (x, y, z), (u, v) in POINTS:
        pu, pv = project(x, y, z, p)
        r += [pu - u, pv - v]
    ts = np.linspace(-60, 900, 481)
    for (axis, c), pts in LINES:
        line = np.array([project(c, t, 0, p) if axis == "x" else project(t, c, 0, p) for t in ts])
        for u, v in pts:
            r.append(np.min(np.hypot(line[:, 0] - u, line[:, 1] - v)))
    zs = np.linspace(0, 600, 301)
    for (x, y), pts in VERTICALS:
        line = np.array([project(x, y, z, p) for z in zs])
        for u, v in pts:
            r.append(np.min(np.hypot(line[:, 0] - u, line[:, 1] - v)))
    return np.array(r)


def fit():
    st = CAMERAS[NAME]["start"]
    best = None
    for yc0 in st["yc"]:
        for xc0 in st["xc"]:
            p = np.array([xc0, yc0, st["h"], st["yaw"], 0.0, 0.0, 900.0, 0.0] + ([0.0] if st.get("k2") else []))
            lam = 1e-3
            for _ in range(150):
                r = _residuals(p)
                J = np.zeros((len(r), len(p)))
                for k in range(len(p)):
                    dp = np.zeros(len(p))
                    dp[k] = 1e-3 if k in (3, 4, 5, 7, 8) else 1e-2 * max(1, abs(p[k]))
                    J[:, k] = (_residuals(p + dp) - r) / dp[k]
                step = np.linalg.solve(J.T @ J + lam * np.diag(np.diag(J.T @ J) + 1e-9), -J.T @ r)
                if np.sum(_residuals(p + step) ** 2) < np.sum(r ** 2):
                    p, lam = p + step, lam * 0.5
                else:
                    lam *= 4
            e = np.abs(_residuals(p))
            if best is None or e.max() < best[0]:
                best = (e.max(), e.mean(), p)
    return best


use(os.environ.get("BACKYARD_CAMERA", "pad"))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        use(sys.argv[1])
    emax, emean, p = fit()
    print(f"max error {emax:.1f} px, mean {emean:.1f} px")
    print(f"{NAME}: cam=", tuple(round(float(v), 4) for v in p))
