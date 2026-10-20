"""Tone down oversaturated pixels of one hue range inside a box (FLUX.1 Kontext made neon leaves and lawns).

    python explorations/ai_renders/tone.py SRC OUT --box x0,y0,x1,y1 [--hues 245-25] [--hue 5 --sat 0.8 --val 0.7]

Hues are PIL HSV units (0-255): red-orange 245-25 (wraps), green 55-110.
"""
import argparse

import numpy as np
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument("src")
p.add_argument("out")
p.add_argument("--box", required=True)
p.add_argument("--hues", default="245-25", help="hue range lo-hi; wraps if lo > hi")
p.add_argument("--min-sat", type=float, default=150)
p.add_argument("--hue", type=float, default=5, help="hue shift")
p.add_argument("--sat", type=float, default=0.8)
p.add_argument("--val", type=float, default=0.7)
a = p.parse_args()

x0, y0, x1, y1 = (int(v) for v in a.box.split(","))
lo, hi = (float(v) for v in a.hues.split("-"))
hsv = np.array(Image.open(a.src).convert("RGB").convert("HSV")).astype(float)
reg = hsv[y0:y1, x0:x1]
hue = reg[..., 0]
in_range = (hue >= lo) & (hue <= hi) if lo <= hi else (hue >= lo) | (hue <= hi)
m = (reg[..., 1] > a.min_sat) & in_range
reg[..., 0][m] = (reg[..., 0][m] + a.hue) % 256
reg[..., 1][m] *= a.sat
reg[..., 2][m] *= a.val
Image.fromarray(hsv.astype("uint8"), "HSV").convert("RGB").save(a.out)
print(f"wrote {a.out}; adjusted {int(m.sum())} px")
