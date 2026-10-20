# Backyard plan

Planning a Denver backyard: a tree, a pergola, a new lawn or ground cover, and a compost tumbler.

**Start here: [plan/FINAL_PLAN.md](plan/FINAL_PLAN.md).** It is the action plan: what to do, in what order, what to
buy, the permits, the cost estimate and a day-by-day timeline.

- Drawings: [plan/backyard_plan_layers_preview.png](plan/backyard_plan_layers_preview.png) (with measurements) and
  the permit sheet [plan/permit/site_plan_A1.pdf](plan/permit/site_plan_A1.pdf).
- Notes for agents and how to rebuild the drawings (`plan/rebuild_images.sh`): [AGENTS.md](AGENTS.md).

## Setup from a fresh clone

Git doesn't carry everything: the Python environment (`env/`), the image model and, on the public branch, the
photos (`private/`) aren't in the repo. One command sets up everything for development:

```sh
./setup.sh             # env/ with everything in requirements.txt, plus the AI-render model if it's missing
./setup.sh --no-model  # env/ only: enough for the drawings
```

Needs macOS with Python 3.12 (`brew install python@3.12`); ~1.5 GB for `env/`. The AI-render model (FLUX.2 [klein] 4B,
~16 GB) needs a Mac with Apple silicon; on other machines `setup.sh` skips it.

Then:

| Command | What it does |
|---|---|
| `plan/rebuild_images.sh` | Rebuilds the drawings in `plan/` from `src/geometry.py` (uses `env/`; `sips` makes the PNG) |
| `env/bin/python explorations/ai_renders/edit_region.py ...` | AI "finished yard" renders; see `explorations/ai_renders/LOG.md` |
| `./publish.sh` | Exports a PII-scrubbed snapshot of `main` to the local `public` branch (see `AGENTS.md`) |

The model goes in the shared Hugging Face cache (`~/.cache/huggingface/hub`, or `$HF_HUB_CACHE`), outside the
repo, so other projects using the same pinned snapshot share one download; `setup.sh` skips it if it's already
there. To remove it: `rm -rf ~/.cache/huggingface/hub/models--black-forest-labs--FLUX.2-klein-4B`.

The renders edit the yard photos in `private/references/` and write to `private/renders/`. `private/` exists only
on `main`; the public branch (`publish.sh`) drops it, so a public clone has the tools but no photos to edit.

Not in git (see `.gitignore`), all recreated by `setup.sh`: `env/` and `__pycache__/`.
