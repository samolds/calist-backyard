#!/bin/sh
# Rebuild every generated image in plan/ from src/geometry.py (run ./setup.sh once first).
#   plan/rebuild_images.sh   (from anywhere)
set -eu
cd "$(dirname "$0")/.."   # repo root

PY=env/bin/python
if [ ! -x "$PY" ]; then
  echo "env/ is missing; run ./setup.sh first (./setup.sh --no-model is enough for the drawings)." >&2
  exit 1
fi

"$PY" src/render_svg.py
sips -s format png plan/backyard_plan.svg --out plan/backyard_plan.png >/dev/null
echo "wrote plan/backyard_plan.png"
"$PY" src/export_psd.py
"$PY" src/tree_sizes.py
"$PY" src/render_permit.py
