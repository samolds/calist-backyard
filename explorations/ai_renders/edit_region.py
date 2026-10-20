"""Edit a region of a photo with FLUX.2 [klein] 4B (in-process, see flux_edit.py), then blend it back into the photo.

    env/bin/python explorations/ai_renders/edit_region.py SRC OUT "instruction" [--crop x0,y0,x1,y1] [--seed N] [--max 1024]

Writes OUT (the full photo with the edited region feathered in) and OUT_raw.png (the model's raw output).
"""
import argparse
import time

import numpy as np
from PIL import Image, ImageFilter

import flux_edit

p = argparse.ArgumentParser()
p.add_argument("src")
p.add_argument("out")
p.add_argument("prompt")
p.add_argument("--crop", help="x0,y0,x1,y1 in source pixels; whole image if omitted")
p.add_argument("--seed", type=int, default=42)
p.add_argument("--steps", type=int, default=flux_edit.STEPS)
p.add_argument("--guidance", type=float, default=flux_edit.GUIDANCE)
p.add_argument("--max", type=int, default=1024, help="longest side sent to the model (multiple of 64)")
p.add_argument("--quantize", type=int, choices=(4, 8), default=4, help="model weight precision in bits")
p.add_argument("--tile", action="store_true",
               help="encode/decode in tiles: less memory for big --max, may leave faint seams")
p.add_argument("--force", action="store_true", help="run even if the memory check says it won't fit")
p.add_argument("--feather", type=int, default=24)
p.add_argument("--mask", help="footprint mask (from guides.py); only pixels near it are pasted back")
p.add_argument("--grow", type=int, default=12, help="px to grow the mask by (shadows, chairs, leaves)")
a = p.parse_args()

full = Image.open(a.src).convert("RGB")
box = tuple(int(v) for v in a.crop.split(",")) if a.crop else (0, 0, *full.size)
region = full.crop(box)
s = a.max / max(region.size)
w, h = round(region.width * s / 64) * 64, round(region.height * s / 64) * 64
flux_edit.check_memory(w, h, a.quantize, a.tile, a.force)
t = time.time()
editor = flux_edit.Editor(quantize=a.quantize, tile=a.tile)
edited = editor.edit(region.resize((w, h), Image.LANCZOS), a.prompt, a.seed, a.steps, a.guidance)
edited.save(a.out.rsplit(".", 1)[0] + "_raw.png")

edited = edited.resize(region.size, Image.LANCZOS)
f = a.feather
# linear fade over f px on each side, except sides that touch the photo's border
ys, xs = np.mgrid[0:region.height, 0:region.width].astype(float)
ramps = [np.ones_like(xs)]
if box[0] > 0:
    ramps.append(xs / f)
if box[1] > 0:
    ramps.append(ys / f)
if box[2] < full.width:
    ramps.append((region.width - 1 - xs) / f)
if box[3] < full.height:
    ramps.append((region.height - 1 - ys) / f)
alpha = np.clip(np.minimum.reduce(ramps), 0, 1)
if a.mask:
    m = Image.open(a.mask).convert("L").crop(box)
    m = m.filter(ImageFilter.MaxFilter(2 * a.grow + 1)).filter(ImageFilter.GaussianBlur(a.grow / 3))
    alpha = np.minimum(alpha, np.array(m, dtype=float) / 255)
mask = Image.fromarray((alpha * 255).astype("uint8"), "L")
full.paste(Image.composite(edited, region, mask), box[:2])
full.save(a.out)
print(f"wrote {a.out} {full.size} (edited {w}x{h}) in {time.time() - t:.0f}s")
