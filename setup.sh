#!/usr/bin/env bash
# One-time development setup, the single entry point after cloning:
#   - env/: a Python virtual env with everything in requirements.txt (plan drawings + AI renders)
#   - FLUX.2 [klein] 4B, the AI-render model, in the shared Hugging Face cache (~/.cache/huggingface/hub,
#     or $HF_HUB_CACHE); skipped if it's already there (e.g. from the rora project)
# Then: plan/rebuild_images.sh rebuilds the drawings in plan/; explorations/ai_renders/LOG.md explains the renders.
#   ./setup.sh             env + model (~1.5 GB + ~16 GB the first time)
#   ./setup.sh --no-model  env only (enough for plan/rebuild_images.sh)
set -euo pipefail
cd "$(dirname "$0")"

MODEL=1
for arg in "$@"; do
  case "$arg" in
    --no-model) MODEL=0 ;;
    *) echo "usage: ./setup.sh [--no-model]" >&2; exit 2 ;;
  esac
done

PY="${PYTHON:-$(command -v python3.12 || command -v python3 || true)}"
if [ -z "$PY" ]; then
  echo "Python 3 not found; install Python 3.12 (e.g. brew install python@3.12) or set PYTHON=..." >&2
  exit 1
fi

[ -d env ] || "$PY" -m venv env
env/bin/pip install -q --upgrade pip
env/bin/pip install -q -r requirements.txt
echo "env/ is ready ($(env/bin/python --version))"

APPLE_SILICON=0
[ "$(uname -s)/$(uname -m)" = "Darwin/arm64" ] && APPLE_SILICON=1
if [ "$MODEL" = 1 ] && [ "$APPLE_SILICON" = 0 ]; then
  echo "Skipping the AI-render model: it runs with mflux, which needs a Mac with Apple silicon."
elif [ "$MODEL" = 1 ]; then
  env/bin/python - <<'PY'
import sys
sys.path.insert(0, "explorations/ai_renders")
import flux_edit

missing = [f for f in flux_edit.REQUIRED if not (flux_edit.model_dir() / f).exists()]
if not missing:
    print(f"{flux_edit.NAME} is already in {flux_edit.model_dir()}")
else:
    print(f"Downloading {flux_edit.NAME} (~16 GB, first time only) into {flux_edit.HUB} ...")
    flux_edit.download()
    print("done")
PY
fi

echo
echo "Next: plan/rebuild_images.sh rebuilds the drawings in plan/. AI renders: explorations/ai_renders/LOG.md"
echo "(the yard photos they edit live in private/, which only the main branch has)."
