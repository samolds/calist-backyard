# AI "finished yard" renders: working log

Goal: edit a real photo of the yard so it shows the finished plan (pergola, shade sail, Bigtooth maple, planters
with fence trellises, shrubs, table, ground cover, stepping-stone path), realistic enough to judge the look.
Sizes and positions come from `src/geometry.py`; the plan drawings stay the reference for dimensions.

**Status (2026-10-20):** the pipeline moved from the Draw Things app (FLUX.1 Kontext [dev] 5-bit) to FLUX.2 [klein] 4B
running in-process with mflux (see "Switch to FLUX.2 [klein] 4B" below). A full render with every plan item is done
(`private/renders/k10_table.png`, steps K3–K10) and waits for the user's review; see "Current state" below.

## Setup (all local, offline)

| Piece | Detail |
|---|---|
| Machine | Apple M2 Pro, 16 GB RAM. Each edit takes ~45 s at 768 px and ~75 s at 1024 px (the default) |
| Model | **FLUX.2 [klein] 4B** (Black Forest Labs, Apache-2.0), 4-bit, 4 steps, run in-process by [mflux](https://github.com/mflux-community/mflux) (`flux_edit.py`). Pinned snapshot in the shared Hugging Face cache `~/.cache/huggingface/hub` (or `$HF_HUB_CACHE`): the same download the user's rora project uses. `./setup.sh` downloads it if missing (~16 GB) |
| Memory | Peak 5.8 GB at 768x576, 7.6 GB at 1024x768 (6.6 GB with `--tile`). `edit_region.py` checks before loading and stops if an edit wouldn't fit (`--force` overrides) |
| Python | `env/` at the repo root (git-ignored), made by `./setup.sh` from `requirements.txt` (~1.3 GB). Setup from a fresh clone: README.md |
| Inputs | User photos in `private/references/*.jpg` (no GPS; checked). Base photo: `0661d98b-0298-459b-9c9f-9e175cb9389c.jpg`, 1024 × 771, taken from the parking pad looking at the house |
| Outputs | `private/renders/` (main only; `publish.sh` never publishes `private/`). `stepN_*.png` = full photo; `*_raw.png` = the model's raw crop; `guide_*.png` = photo with placeholder shapes |

**Privacy:** never copy photos or renders outside `private/`. This log and the scripts contain no PII.

## Tools (this folder)

| File | What it does |
|---|---|
| `camera.py` | Pinhole camera fitted to six ground points in the base photo (house corners, lawn corners, utility pole base, half wall). `P(x, y, z)` maps plan inches to pixels; `scale(y)` = px per inch at depth y. Max fit error ~12 px. Run it to refit after editing `OBS` |
| `guides.py` | Draws placeholder shapes at plan positions/sizes: `pergola tree planters shrubs table sail path`. Usage: `python guides.py SRC OUT tree planters` |
| `edit_region.py` | Edits a crop with an instruction, then feathers the result back into the full photo; `--mask` (from `guides.py`) pastes back only near the placeholder footprint. Usage: `edit_region.py SRC OUT "instruction" --crop x0,y0,x1,y1 --seed N [--mask M] [--max 1024]` |
| `flux_edit.py` | The model: loads FLUX.2 [klein] 4B once (`Editor`), edits a PIL image; memory check; `--download` |
| `tone.py` | Tones down oversaturated pixels of one hue range in a box (Kontext made neon leaves and lawns). `--hues 245-25` red-orange (default), `--hues 50-110` green |

Run everything from the repo root, e.g.
`env/bin/python explorations/ai_renders/edit_region.py private/renders/a.png private/renders/b.png "..." --crop 300,180,812,564`

## Method that works

Learned with Kontext (steps 1–22); klein follows the same approach.

1. **Don't ask the model to "add X somewhere".** It misplaces things (step 1 put a shingled pavilion on the parking
   pad). Instead draw a crude placeholder at the right spot with `guides.py`, then ask it to *"make the placeholder
   shapes into a real, photorealistic X, keeping exactly the same position, size and outline"*.
2. **Edit a crop, not the whole photo.** Crops of ~400–500 px sent at 640–768 px are 2–4× faster than full 1024 px
   and change less of the scene. Keep each crop free of earlier finished elements if possible.
3. **Say what must not change** ("keep the house, fences, grass ... exactly the same") and, for a pergola, say
   **"no roof covering"** and **"the house's shingled roof stays visible"**, or it invents a roof.
4. **Fix color in a second, recolor-only pass** ("restain the pergola very dark espresso ... change nothing else").
5. Check every result by eye before building on it.

## Log

| Step | Input → output | Crop / seed | Prompt (short) | Time | Result |
|---|---|---|---|---|---|
| 1 | base photo → `step1_pergola.png` | full 1024 / 42 | "Add a large freestanding wooden pergola ... against the back wall of the house" | 575 s | **Bad**: shingled pavilion on the parking pad |
| 1b | base photo → `step1b_pergola.png` | 200,110,800,560 / 42 | same idea, "no solid roof, no shingles" | 259 s | **Bad**: still misplaced |
| — | base photo → `guide_pergola.png` | — | `guides.py pergola` (camera-fitted placeholder) | 1 s | Placement looks right: front corners at px 379 and 691, top ~310 |
| 2 | guide → `step2_pergola.png` | 300,180,812,564 / 7 | "Make the flat brown placeholder shapes into a real Zen Pergolas freestanding pergola ... Douglas fir stained dark walnut, black steel brackets, angled 2x6 slats" | 267 s | Right place and size; **but** it added a shingled roof over it |
| 3 | guide → `step3_pergola.png` | same / 11 | "... open-top pergola ... NO roof covering ... slats with gaps ... the house's gray shingled roof stays fully visible" | 277 s | **Good** shape; wood came out reddish cedar |
| 4 | step3 → `step4_pergola_dark.png` | same / 3 | "Restain the wooden pergola a very dark espresso brown ... matte black steel brackets. Change nothing else" | 277 s | **Good. Current pergola base** |
| 5 | step4 + orange oval guide → `step5_tree.png` | 190,100,590,500 / 21 | "young Bigtooth maple ... about 3 years after planting ... red-orange fall color" | 370 s | Bad: conifer-like, too tall, neon; crop also re-rendered part of the pergola |
| 5b | step4 + smaller oval → `step5b_tree.png` | 230,140,430,500 / 5, max 640 | "... deciduous ... not a conifer" | 153 s | Bad: crop narrower than the guide, so leftover orange blob outside the crop |
| 5c | step4 + mulch ring only → `step5c_tree.png` | 210,100,470,500 / 9, max 640 | "Plant a young maple ... out of the center of the brown mulch circle ... looks like a small sugar maple" | 152 s | Best so far: right spot, deciduous-ish, but feathery/conical and neon |
| 6 | step5c → `step6_tree.png` | — | `tone.py --box 250,110,450,360 --hue 5 --sat 0.8 --val 0.7` | 1 s | Natural rust-orange color. **Current base** (tree form still not maple-like) |
| 7 | step6 + planter guide (no pixel nudge) → `step7_planters.png` | 560,250,820,540 / 13, max 640 | "three raised beds ... dark-stained cedar ... 6' trellis on the fence side with western white clematis" | 224 s | Bed + trellis look real, **but** placed on the sidewalk (camera fit is ~35 px off there). `guides.py planters` now nudges 36 px left; not re-run yet |
| 5d | step4 + mulch ring → `step5d_tree.png` | 210,100,470,500 / 31, max 768 | "... irregular, rounded, open crown ... not conical ... broad lobed leaves" | 223 s | Bad: still conical and neon |
| 5e | step4 + maple-shaped guide (trunk, limbs, round crown of colored circles) → `step5e_tree.png` | same / 17 | "Turn the cartoon tree made of colored circles into a real young Bigtooth maple, keeping exactly the same rounded crown shape" | 274 s | Bad: became a feathery conical tree (like a bald cypress) again |
| 5f | same guide → `step5f_tree.png` | same / 23, `--guidance 3.5` | "small deciduous shade tree ... like a young sugar maple ... mostly green with orange edges ... no needles" | 221 s | Still conical; guide circles leaked through the feathered crop edge. **User: tree needn't be photoreal; keep `step6_tree.png`** |
| 8 | step6 + nudged planter guide → `step8_planters.png` | 540,250,820,540 / 13, max 640 | "three beds in a row on the grass next to the sidewalk ... trellis along the fence side ... sidewalk stays clear" | 232 s | OK: two beds side by side plus one vine trellis, at the far end of the lawn by the sidewalk. Not the plan's 3-in-a-row, but reads right. Accepted |
| 9 | step8 + `shrubs composter` guides → `step9_shrubs.png` | 0,330,400,560 / 19, max 640 | "four ... small native shrubs ... loose, natural shapes (not clipped balls) ... compost tumbler" | 157 s | Shrubs **good**. Tumbler looked like a smoker grill |
| 10 | step9 → `step10_composter.png` | 0,330,300,560 / 29, max 512 | "Replace the ... smoker-like object ... with a real compost tumbler: black barrel drum ... A-frame stand" | 140 s | Barrel tumbler, but crowded by the parked car |
| 11 | step10 + `table` guide → `step11_table.png` | 380,300,700,480 / 37, max 640 | "large round outdoor dining table, 7 feet across, dark wood top on a pedestal base, six black metal chairs" | 204 s | **Good** (it also removed the fire pit) |
| 12 | step11 → `step12_nocar.png` | 0,320,360,640 / 41, max 640 | "Remove the white car and the black barrel ... empty gray concrete parking pad" (user's idea) | 217 s | **Good** removal; left a white gravel patch on the concrete |
| 13 | step12 + `composter` guide → `step13_composter.png` | same / 43 | "Maze two-stage compost tumbler: black octagonal drum ... on a black steel stand ... Replace the white patch with plain concrete" | 227 s | **Good enough**: octagonal tumbler on a stand; gravel strip ended up along the pad edge |
| 14 | step13 + `path` guide → `step14_lawn_path.png` | 230,400,760,580 / 47, max 768 | "even, healthy ... DOG TUFF grass ... curving path of flagstone stepping stones" | 132 s | Lawn neon green; stones small and pale. Left part of lawn (x < 230) not refreshed |
| 15 | step14 → `step15_lawn_tone.png` | — | `tone.py --box 200,420,720,560 --hues 50-110 --min-sat 120 --hue -6 --sat 0.6 --val 0.82` | 1 s | Natural lawn color. Best Kontext-era image at the time |
| 16 | step15 → `step16_cleared.png` | 390,280,800,530 / 51, max 768 | "Remove the round table and all the black chairs, the two wooden raised garden beds, and the lattice trellis ... show the same lawn, patio and open space under the pergola" | 724 s | Not yet checked by eye (paused). Slow run (Mac busy?) |

Steps 1–22 used FLUX.1 Kontext [dev] 5-bit in Draw Things (20 steps, guidance 2.5). From K1 on: FLUX.2 [klein] 4B
via `edit_region.py` (4 steps, guidance 1.0).

| Step | Input → output | Crop / seed | Prompt (short) | Time | Result |
|---|---|---|---|---|---|
| K1 | `guide_pergola.png` → `klein_test_pergola_768.png`, `_1024.png`, `_1024tile.png` | step 3's crop / 11, max 768 and 1024 | step 3's idea: "... open-top pergola ... NO roof covering ... house's roof stays fully visible" | 46 s / 75 s / 72 s | **Better than Kontext's step 3**: open slatted top, brackets, same outline. 1024 is crisper; tiled looks the same. Side by side: `klein_test_compare.png` |
| K2 | `klein_test_guide_pergola.png` (refit camera) → `klein_test_masked_pergola.png` | 300,180,812,564 / 11, `--mask`, max 1024 | same, "very dark espresso brown ... gaps of sky between the slats" | 74 s | **Good**; first run of `--mask`: only the footprint changed. `klein_test_masked_compare.png` |
| K3 | K2 → `k03_nocar.png` | 0,320,360,640 / 41 | "Remove the white car completely ... plain gray concrete parking pad ... gravel strip and tan fence behind it" | 92 s | **Good**, clean removal |
| K4 | K3 + `table` guide → `k04_table.png` | 380,300,700,480 / 38, `--mask --grow 45` | "large round outdoor dining table, 7 feet across, dark wood top, black pedestal, six black metal chairs ... on the concrete patio under the pergola, next to the house" | 57 s | **Good**. Grow 28 (seed 37) cut a chair in half (see-through). The guide disc was drawn over the front-middle post, so the post pixels (x 530–541, y 394–442) were pasted back from K3 to keep it in front of the table |
| K5 | K4 + `composter shrubs` → `k05_composter_shrubs.png` | 40,340,400,560 / 43, `--mask --grow 20` | "compost tumbler ... against the tan fence ... four small native shrubs, loose natural shapes, in brown mulch" | 61 s | Shrubs **good** (small evergreens). Tumbler came out as an upright trash can on legs |
| K5b | K5 + `composter` → `k05b_composter.png` | 20,340,380,560 / 47, `--mask --grow 24` | "large black octagonal drum lying on its side, on a horizontal axle on a black steel A-frame stand ... against the fence" | 60 s | **Good**: real tumbler |
| K6 | K5b + `tree` → `k06_tree.png` | 180,160,540,540 / 53, `--mask --grow 30` | "real young deciduous shade tree, a Bigtooth maple about 3 years after planting: slim gray trunk ... open, rounded, irregular crown of broad lobed leaves in natural, muted autumn orange and red, about 11 feet ... ring of brown wood mulch" | 93 s | **Good on the first try** (Kontext never managed): broad leaves, rounded crown, natural color. Its mulch bed is wider than the 3' ring and runs into the shrub bed |
| K7 | K6 + `planters` → `k07_planters.png` | 520,280,840,560 / 59, `--mask --grow 22` | "one straight row of three raised garden beds end to end along the edge of the lawn next to the sidewalk, seen from the end ... dark-stained cedar ... 6-foot trellis with a climbing vine" | 88 s | **OK**: right place and size, but reads as one long bed (from this end-on view the 18" gaps hide behind the near bed). Seed 61 asking for "three separate beds with gaps" was worse (still one bed, plus an extra planter by the steps) |
| K8 | K7 + `sail` → `k08_sail.png` | 300,160,700,420 / 71, `--mask --grow 14` | "real tan triangular shade sail ... three pointed corners, scalloped edges ... high corner on a tall black steel post, low corners cabled to the pergola's front corners" | 60 s | **OK**: from this low camera the sail is nearly edge-on and reads like a tan awning; its high corner and post are hidden behind the tree. The guide was drawn over the tree, so the tree's pixels (where K7 differs from K5b, x < 470) were pasted back on top |
| K9 | K8 + `path` → `k09_path.png` | 420,380,740,560 / 73, `--mask --grow 8` | "natural flagstone stepping stones ... set flush into the lawn, a gently curving path from the parking pad to the pergola" | 54 s | **Good enough**: stones follow the planned curve but stay oval like the guide (read as round pavers). The guide's two nearest stones fell on the pad's concrete bump and were dropped from the guide and mask first |
| K10 | K9 → `k10_notable.png` → + `table` guide → `k10_table.png` | 360,300,680,500 / 79, `--mask k10_table_mask.png --grow 4` | "round outdoor dining table ... dark wood top, black pedestal, four black metal chairs tucked in close around its front and sides ... on the concrete patio at the back of the pergola, right against the house wall, far from the camera ... nothing on the grass" | 63 s | **Good**. User: K4's table was too big and sat on the grass. The guide was right (plan: top x 451–538, foot y ≈ 429, between the post rows); K4's model output plus `--grow 45` let the table, chairs and a new concrete patch spread to y ≈ 470. Fix: restore K3's pixels wherever K4 changed them (except pixels later steps changed), then redo with a tight mask built from the plan (table + chairs within 62", none behind it: it's 6" from the house), and paste the front-middle post back. **Current best image** |

## Second photo: from the house steps (2026-10-20)

Base photo `private/references/053a0642-d716-49ce-bec7-b354ee44c0dd.jpg` (771 x 1024), taken from the house steps
looking back toward the pad, with the phone's 0.6x ultra-wide lens. Camera `steps` in `camera.py` (use
`guides.py --camera steps ...`); its outline check is `private/renders/overlay_check_steps.png`.

**Camera.** The 0.6x lens is fisheye-like, so `steps` uses an equidistant lens model (r = f * theta, plus k1, k2)
instead of the pad photo's pinhole. Fitted to the utility pole (base + 3 points up its length), the tan fence base,
the gravel edge, and the lawn's pad, sidewalk and patio edges; the lawn edges were measured from the photo (grass vs
concrete), not read by eye. Max 15 px, mean 7 px; worst at the far left/bottom corners. The pad camera is unchanged.
**Accuracy:** placement and size are right to roughly a foot; the plan drawings stay the reference for exact sizes.

`guides.py` now clips every shape to what the camera sees (it stands under the pergola's back edge) and draws the
pergola from the plan's real posts, beams, 22 slats and braces. New item `lawn` = the plan's grass outline.

| Step | Input → output | Crop / seed | Prompt (short) | Time | Result |
|---|---|---|---|---|---|
| S1 | photo + `lawn` → `s01_lawn.png` | 0,420,771,860 / 103, `--grow 4` | "real, ordinary residential lawn ... short, freshly mowed fine-bladed grass ... no edging" | 57 s | Good. Seed 101 ("DOG TUFF ... crisp edges") looked like artificial turf |
| S2–S3 | planters, path | — | as in K7/K9 | ~90 s each | Superseded by S9/S10 (planters merged into one bed; first, pinhole camera) |
| S4 | + `shrubs composter` → `s04_composter_shrubs.png` | 250,360,570,520 / 127 | "Maze two-stage compost tumbler ... four small native shrubs ... along the tan fence" | 50 s | Good, but (user) the tumbler was too close to the tree: replaced in S8 |
| S5 | + `tree` → `s05_tree.png` | 200,250,420,480 / 131 | "young Bigtooth maple ... in spring ... fresh green leaves ... small ring of mulch" | 97 s | Good; the tumbler pasted back in front |
| S6 | + `sail` → `s06_sail.png` | 250,170,650,340 / 137 | "real tan triangular shade sail ... seen from below ... high corner on the utility pole" | 44 s | Good; reads well from here |
| S7 | + `pergola` → `s07_pergola.png` | whole photo / 139 | "open-top pergola seen from just under its back edge ... gaps of blue sky" | 73 s | Good, but (user) the left rafters stopped short of the photo's edge: fixed in S11 |
| S8 | S7 minus S2/S3 → remove tumbler (`s08_clear.png`, seed 151) → place at the plan's spot (`s08_tumbler.png`, seed 157) | 240,330,500,500 | remove: "Remove the black compost tumbler and its stand completely ..."; place: "... against the tan fence in the far corner, well behind the young tree" | 61 + 62 s | **Good**: tumbler now at plan `COMPOSTER` (9' from the tree). One combined remove+place pass (seed 149) only enlarged the old tumbler: do removal and placement as separate passes |
| S9 | + `planters` (fisheye camera) → `s09_planters.png` | 0,300,260,660 / 167, `--grow 10 --feather 8` | "three separate solid, opaque raised garden beds ... nearest bed big and close, cut off by the left edge" | 77 s | OK: beds now follow the lens's curve; the near bed is solid. Seeds 109/163 with a bigger crop came out faded/translucent |
| S10 | + `path` → `s10_path.png` | 0,400,360,780 / 113 | as S3 | 97 s | Good |
| S11 | S10 + S7's pergola pasted back → boards extended → `s11_pergola.png` | 0,0,320,260 / 179, mask = extended pixels | "clean up the dark wooden pergola beams and roof slats at the top left ... continuing straight off the left edge" | 84 s | **Good**: the two slats and the side beam now run off the left edge. Extended by sliding each board's own pixels along its measured slope, then one blend pass. A full regeneration with the fisheye guide (seeds 139, 173) drew a faded, partial pergola |

**Latest image: `private/renders/s11_pergola.png`.** Not shown: the table (it stands beside/behind the
photographer). Left as is: the car, the dog and its mat, the covered grill. Known flaws: faint joins where the
extended pergola boards meet the originals; the near planter is cut by the frame edge.

## Switch to FLUX.2 [klein] 4B (2026-10-20)

- Why: one model shared with the rora project (one download in the shared Hugging Face cache), no app or HTTP
  server to keep open, and Draw Things' model format can't be shared. FLUX.1 Kontext [dev] via mflux would need a
  34 GB download and doesn't fit comfortably in 16 GB alongside other apps.
- klein is ~4–6× faster per edit and followed "no roof covering" on the first try (K1).
- Kontext-era lessons below (neon colors, conical tree) may not apply to klein; recheck before relying on them.

## Lessons about the tree

klein (K6) produced a convincing young maple on the first try with the prompt in the K6 row. The notes below are
from the Kontext era.

Kontext (5-bit) keeps turning "young maple in fall color" into a feathery, conical, neon tree, even with a rounded
placeholder. Ideas not yet tried:
- Describe it without the word "maple" or "autumn": "a small deciduous shade tree with a rounded crown of broad
  flat leaves, like a young sugar maple, leaves turning orange".
- Show it in **summer green** (shape is easier to read), then recolor in a separate pass.
- Raise `--guidance` to ~3.5 for stronger prompt adherence, or try several seeds.
- Composite a real photo cut-out (e.g. `plan/images/trees/bigtooth_maple.jpg`, CC BY-SA, keep credit) and ask
  Kontext only to blend lighting and shadows.

## Current state (2026-10-20; was CHECKPOINT.md)

**Camera (`camera.py`).** Refit on 2026-10-19 with yaw, pitch, roll and radial lens distortion, using 9 ground points
plus points along 5 known plan lines (fence bases, lawn edges). Max error 13 px, mean 5 px.
`CAM = (46.7976, -18.3811, 62.3838, 0.2457, -0.0299, 0.011, 771.6877, -0.3666)`
(camera x, y, height in inches; yaw, pitch, roll in radians; focal px; k1). `private/renders/overlay_check.png` shows
the plan outlines on the photo. Lines that start behind the camera (y < -18) draw wildly; ignore them.
**All renders up to step 16 used the older, less accurate camera** (no yaw/roll; planters ~35 px off).

**Latest image: `private/renders/k10_table.png`** (2026-10-20). Rebuilt from the original photo with klein and the
refit camera (K2–K10) instead of continuing `step22_notable.png`, whose items were placed with the old camera. Every
plan item is at its plan position: open-top pergola; table + chairs at the back of its left half (in the photo), on
the patio against the house (K10); tumbler and four shrubs along the tan fence; young maple in the lawn; one row of
raised beds with a trellis along the sidewalk edge; shade sail; stepping-stone path. The car is removed (as in step 12).
Known flaws: the sail reads like an awning (edge-on from this camera); the tree's mulch bed is too wide and joins the
shrub bed; the beds read as one long bed; the stones are oval; the existing fire pit (not in the plan) is visible
again in front of the table since K10 (K4 had covered it). Lawn left as is: the plan's DOG TUFF grass is tan from
mid-fall, like the photo.

The Kontext series ended at `step22_notable.png` (pergola top a solid band, neon tree and lawn, oversized tumbler
off the fence, two beds side by side).

**User's requests from 2026-10-19/20** (all addressed in K3–K10; waiting for the user's review):
1. **Every colored plan item at its accurate plan location** (pergola, table, tumbler, planters, shrubs, tree, sail).
2. **Table** under the pergola, **up against the house** (plan `TABLE` = 84" round at (237, 673): under the pergola's
   right 10' half, 6" from the house; in the photo that's the left half of the pergola).
3. **Compost tumbler** against the tan fence with some bushes (plan `COMPOSTER` x 271–301, y 221–262).
4. **Shade sail** (`guides.py ... sail`; post corner raised to 150" so it reads from this low camera).
5. **One row of planters**; against the white fence is fine (`planters` = plan positions in the lawn edge;
   `planters_fence` = on the sidewalk against the fence).

**Possible next passes:** shrink the tree's mulch to a ~3' ring; remove the fire pit (in front of the table, on the
grass; mask it tightly so the table stays); irregular flagstones (draw irregular polygons in `guides.py path`); a second camera (e.g. from the patio)
would show the sail and the beds' gaps far better than this low, end-on view.

**Techniques added in K4–K9:** when a guide is drawn over something that stands in front of the new object (a post,
the tree), paste the occluder's pixels back from the previous step after the edit. When `--grow` is too small, the
mask edge cuts objects (see-through chairs); grow it to cover chairs/branches. Same seed + prompt reproduces a result.

## Next steps (polish, all optional)

1. Shade sail (`guides.py ... sail`): nearly edge-on from this camera; expect a thin tan wedge between the utility
   pole and the pergola's front-left (photo) corner.
2. Pergola: from this low camera its slatted top reads as a solid flat roof. A pass asking for "visible gaps of sky
   between the roof slats" might help (crop 300,180,812,564).
3. Lawn left of x 230 is still the old, dull grass; edit crop ~0,420,300,560 to match.
4. Stepping stones: larger, darker natural flagstone.
5. Tree: neon and conical (accepted by the user); `tone.py` can calm it further.
6. Try the same pipeline on a second photo (e.g. one from the patio) by refitting `camera.py` with new `OBS`.

### Notes added during steps 8–15
- `edit_region.py` (then `dt_region.py`) feathers only crop sides that are inside the photo, so crops touching the border blend cleanly.
- A placeholder must lie fully inside the crop and away from its feathered edge, or bits of it show through.
- Removing the parked car first (step 12) made the compost tumbler much easier to place.
