# Backyard plan: handoff notes for agents

This file lets a fresh agent pick up the backyard-planning work. It was written at the end of the
first session (2026-10-17). Read it fully before editing anything.

## What the user is doing

The user is planning their backyard. The work so far:

1. Started from a hand sketch (`reference/sketch.png`, not to scale) and a dimensioned photo
   (`reference/sketch_dimensions.png`).
2. Built an SVG drawn to scale.
3. Tried several pergola sizes.
4. Settled on a final plan (`plan/backyard_plan.svg`).
5. Exported the plan as a layered PSD for Procreate (`plan/backyard_plan_layers.psd`).

They iterate in small requests ("move X by N inches", "regenerate the psd").

## File map

```
backyard/
├── AGENTS.md          # this file
├── README.md          # points to plan/FINAL_PLAN.md; setup from a fresh clone
├── setup.sh           # the one dev setup: env/ from requirements.txt (+ the AI-render model)
├── requirements.txt   # Python packages for the drawings and the AI renders
├── publish.sh         # PII-stripped, single-commit snapshot of main -> local `public` branch
├── private/           # main-only (never published): pii-patterns.txt
├── reference/         # user's original sketches. NEVER modify
├── src/               # geometry.py (source of truth) + renderers
├── plan/              # CURRENT design outputs (all generated, except rebuild_images.sh, which makes them)
├── explorations/      # options considered (base drawing, pergola variants); ai_renders/ = photo-edit tools + LOG.md
└── docs/              # historical notes
```

| File | Status | Notes |
|---|---|---|
| `reference/sketch.png` | **Original, do not overwrite** | Hand sketch, not to scale (was `backyard.png`) |
| `reference/sketch_dimensions.png` | **Original** | Sketch with tape measurements |
| `reference/sketch_labeled.png` | **Original** | Sketch with area names: Sidewalk, Alley, Mulch, Grass, Parking Pad, Shed, etc. |
| `reference/sketch_sized.png` | **Original (user-made)** | Later dimension sheet. Adds 36" (left edge to half wall), 38" mulch measured to the pad's right edge, and 181" on the right side |
| `explorations/base/backyard.svg` | Base drawing (older) | Base drawing only. It still has the OLD half wall (y 28–185) and OLD shed x (214.5). It is NOT kept in sync with the plan |
| `explorations/base/backyard_scaled.png` | Render of `backyard.svg` | |
| `explorations/pergola_along_house/backyard_pergola_{12x12,14x12,16x12,20x12}.svg/.png` | Exploration | Pergola along the house (width × 12' depth) |
| `explorations/pergola_rotated/backyard_pergola_rotated_12x{14,16,20}.svg/.png` | Exploration | 12' along the house, longer side into the grass |
| **`src/geometry.py`** | **SOURCE OF TRUTH** | Every coordinate, size and color for the plan |
| `src/render_svg.py` | Renderer | geometry → `plan/backyard_plan.svg` (standard library only) |
| `src/export_psd.py` | Renderer | geometry → `plan/backyard_plan_layers.psd` + preview (needs Pillow). Also holds measurement-label placement. `--preview-only` writes just the preview PNG |
| `setup.sh` | Setup | Creates `env/` from `requirements.txt` and fetches the AI-render model into the shared Hugging Face cache if missing (`--no-model` skips it) |
| `plan/rebuild_images.sh` | Build | Runs the SVG, PSD, tree-size and permit renderers with `env/`, and `sips` for the PNG |
| `src/render_permit.py` | Renderer | Writes `plan/permit/site_plan_A1.png` / `.pdf`: 11×17" permit sheet A-1 (gridded site plan at 3/16" = 1'-0", pergola elevation, pier detail, notes, title block with blank address/owner lines). Lot lines are drawn from geometry and labeled approximate; update after the survey |
| `publish.sh` | Publish | Exports committed `main`, drops `private/`, scrubs text files with the regexes in `private/pii-patterns.txt`, re-checks every file (binaries too) and fails on any match, then points local `public` at one parentless commit by samolds@gmail.com. Never pushes; the user runs `git push --force origin public` |
| `private/pii-patterns.txt` | Private | `PATTERN => REPLACEMENT` Perl regexes (address, ZIP, parcel, legal description). Committed to main only. Add new PII here, never to published files |
| `plan/backyard_plan.svg` / `.png` | Generated | Do not edit by hand; edit `src/geometry.py` and run `plan/rebuild_images.sh` |
| **`plan/backyard_plan_layers.psd`** | **CURRENT deliverable** | 17 layers, measurements in inches. Rebuilt 2026-10-18 with the composter |
| `plan/backyard_plan_layers_preview.png` | Preview | Composite of every layer |
| **`plan/FINAL_PLAN.md`** | **CURRENT action plan** | The user-facing plan, in four parts (A and B independent), preceded by a "Layout and flow (feng shui)" review and "The neighbor's white fence" (glare/heat: trellises with native vines on the planters' fence side, nothing attached to the neighbor's vinyl fence), whose suggestions (curved path, seating away from the A/C, water feature, lights, privacy) are actions under "Later". **Part A (tree, do first):** A1 sewer locate (required; it also covers the pergola piers), A2 choosing the tree (tables with a heavy-clay column, A2.4 size chart, A2.5 photos, A2.6 soil + drainage test), A3 811, A4 buying, A5 planting, A6 care, A7 checklist. **Part B (pergola):** B1 risks, B2 survey/zoning, B3 permits, B4 purchases (incl. B4.1b VEIKOUS plan B), B5 build, B6 checklist. **Part C (lawn, after A and B):** soil test, grass choice (DOG TUFF™ plugs recommended: low water, winter-hardy, tan in winter; tall fescue sod runner-up; C2b: grass not required, moss won't survive full sun/alkaline soil, so microclover + low-water fescue mix for the dog area and Turkish veronica/thyme for a moss-like look), clay prep, sod, care + core-aerator rentals. **Part D (compost tumbler):** Maze 65-gal geared tumbler, placement, use. Ends with "Later" and a "Cost estimate (whole plan)" table (31 rows, low/high, running total; ✓ marks seller-checked prices; grand total $7,296–13,317). Keep its running totals consistent when prices change. Then a "Timeline" section (from Mon 2026-10-19): Mermaid Gantt, month calendars and a day-by-day table, assuming weekday 7–9 pm (indoor tasks until mid-April) and 9–1 on Sat and Sun; "(est.)" dates depend on others. Update it whenever decisions change |
| `src/tree_sizes.py` | Renderer | Writes `plan/images/trees/size_comparison.png` (Pillow): every tree option to one scale with a 5'10" person, a typical single-story house (10' eaves, 17' peak) and a 25' bar. Its sizes are copied from FINAL_PLAN A2; keep them in sync |
| `plan/images/trees/*.jpg` | Reference photos | Wikimedia Commons, 800px; attribution is listed in FINAL_PLAN A2.5. Keep the credits if images change. Photos have no scale overlay because the photographed trees' heights are unknown |
| `docs/svg_derivation.md` | Historical | Explains how the first SVG was derived. Its half-wall and pad-edge numbers are superseded below |

**Workflow:** change numbers in `src/geometry.py`, run `plan/rebuild_images.sh`, then look at
`plan/backyard_plan.png` and `plan/backyard_plan_layers_preview.png`. Measurement values are computed
from geometry. Label *placement* (which side, how far offset) is hand-tuned in `src/export_psd.py`;
check the preview for overlaps after moving things.

## Coordinate system

- 1 unit = 1 inch.
- x = 0 is the left boundary line (the outer edge of the sidewalk and alley); x grows to the right.
- y = 0 is the top line (the top edge of the parking pad); y grows downward, toward the house.
- The SVG viewBox is `-4 -4 316 836`.
- The PSD canvas spans x −30..340 and y −30..832 in inches, at 6 px/in, giving 2220 × 5172 px.

## Current geometry (inches)

**Measured or confirmed by the user**

- Parking pad: x 0–308, y 0–217. Pad height is 217.
- Half wall: x 36–63 (27 thick), y 6–185.
  - Its top sits 6" below the top line, as the user asked. The bottom is unchanged.
  - 36" from the left edge to the wall and 245" from the wall to the pad's right edge, both confirmed.
- Sidewalk: x 0–41.5 (41.5", confirmed).
- Grass:
  - Spans x 41.5–270 (228.5 wide).
  - Its top edge (the pad's bottom line) is at y 217, from x 126.5 to 308. The bottom is at y 625.
  - Right side 408". Left side runs y 278–625 (347).
  - Curved notch at the top left: 85" wide and 61" deep. Its curve is the cubic
    `C 126.5 258, 96.5 275, 61.5 277.5`.
  - The bottom-left corner is rounded, radius 8.
- Mulch strip: x 270–308 (38").
  - Post: 8" diameter, centre (289, 479.2).
- Grass to house: 96" (the house front is at y 721).
- Steps: x 72–141, y 670–721 (69 × 51), 45" from the grass.
- House: walls at x 23.5 and 186 (162.5 wide). The alley is 23.5".
- Concrete right edge: x 285, which is 99" from the house wall.
  - Its top-right curve: `M 270 625 C 276 624.5, 280 628, 281 635 L 285 671 L 285 804`.
- Bottom line: y 806, which is 85" below the house front.
- A/C: x 191.4, y 728, 32 × 32.
- Shed: x 232.5–283.5, y 775.5–806 (51 × 30.5).
  - The user moved it 18" right of its original position.

**Estimated from the sketch (marked "~" in the PSD)**

- None left. The sketch's small circle (top right of the table) was removed at the user's request (2026-10-18).

**Patio table (user-specified, 2026-10-18):** 84" round, centre (237, 673), radius 42. x is centered under the
pergola's right 10' half (x 177–297); y is centered on the patio between the grass (y 625) and the house (y 721),
leaving 6" at the top and bottom. Its right edge (x 279) is ~6" inside the concrete edge.

## Added design elements (all in `plan/backyard_plan.svg` and the PSD)

| Element | Color | Geometry |
|---|---|---|
| Pergola, 20' × 12' | green `#2e8b57` fill / `#1f7a3a` stroke | rect x 57–297, y 577–721 (240 × 144). Against the house; the user moved it 12" right of x 45. Zen detail (all derived in `geometry.py`): six 5.5" posts at x 57 / 174.25 / 291.5 by y 577 / 715.5 (111.75" clear between posts); 6x6 beams on the perimeter and the middle; 11 angled 2x6 slats per opening at ~11.08" o.c. (drawn 4.95" deep, the plan footprint at 45°); eight 30" corner braces (21.2" plan length, dark lines on the beams); dashed 12" piers under the three front posts and the back-right post; back-left and back-middle are slab-anchored |
| Shade sail | yellow `#f2c200` / `#c9a000` | Corners (282.0, 487.2), (280.4, 559.2), (136.4, 555.6). Sides 72 × 144 × 160.8 = **Royal Shade 6' × 12' × 13.4' right triangle** (a retail size: Walmart about $64, Amazon, Wayfair) |
| Sail cords | orange `#e67e22` | Lines from each sail corner to its mount. Mounts: the post (289, 479.2), the pergola front-right corner (297, 577), the pergola top-left corner (57, 577). Lengths about 10.6", 24.3", 82.2" |
| Tree | purple `#8e44ad` | circle (215, 329), radius 30 (~60" canopy). Moved 60" right of x 155, then 24" down from y 305, at the user's request (2026-10-18). Plus `TREE_CANOPY`: a lighter purple (`#c39bd3`, dashed in the SVG) radius-150 circle showing a 25' mature canopy, in the same PSD layers; it now runs ~57" past the right boundary |
| Raised planters | blue `#2f6fd6` / `#1f4fa8` | Three 24 × 72 rects at x 44, y 300 / 390 / 480 (18" gaps). In the grass along the sidewalk |
| Shrubs | red `#d62828` / `#a4161a` | Four circles, radius 13, at x 289, y 290 / 335 / 380 / 425 (45" apart, centre to centre). In the mulch strip, below the composter |
| Composter | brown `#8b5a2b` / `#5d3a1a` | `COMPOSTER` rect x 271, y 221 (PAD_H + 4), 30 × 41.3 = Maze 65-gal two-stage geared tumbler (41.3" W × 30" D × 44.5" H). Top of the mulch strip by the parking pad (user's choice, 2026-10-18: away from the pergola). Replaced the top shrub. Right edge x 301 is ~1" past a 300" city lot line; keep it inside the surveyed line |

### How the shade sail was chosen (so it isn't redone)

The user's mount points are fixed: the post, the pergola front-right corner and the pergola top-left
corner. The triangle between them is about 98 × 240 × 252 in, long and thin.

| Option tried | Result |
|---|---|
| Common equilateral sails (10', 12', etc.) and the usual right-isosceles sizes | Do **not** fit inside that triangle |
| Largest custom fit (each corner 12" in from its mount) | 79.6 × 219.5 × 230.3 in, about 60.6 sq ft. Only available as a custom order |
| Royal Shade 6' × 12' × 13.4' right triangle (**chosen**) | The largest **retail** sail found that fits, 36 sq ft |
| Royal Shade 6' × 11' × 12.5' | Retail, fits, 33 sq ft (backup) |
| Shademart 6' × 10' × 11.7' | Retail, fits, 30 sq ft (backup) |

How the sail was placed: a random search over position and rotation. It kept the sail strictly inside
the mount triangle, cords at least 6" long, and each cord within about 10° of its sail corner's angle
bisector.

## PSD layers (bottom to top) and their rules

1. Background (white)
2. Base lines (black)
3. Base measurements
4. Planters (blue)
5. Planters - measurements
6. Tree (purple)
7. Tree - measurements
8. Shrubs (red)
9. Shrubs - measurements
10. Composter (brown)
11. Composter - measurements
12. Pergola (green)
13. Pergola - measurements
14. Shade sail (yellow)
15. Shade sail - measurements
16. Sail cords (orange)
17. Sail cords - measurements

Rules:

- Turning off every layer above "Base lines" must leave a clean black line drawing.
- **All measurement labels are in inches only**, rounded to the nearest ¼". Estimates are prefixed
  with "~".
- A real `.procreate` file is not feasible. The PSD is the deliverable; Procreate imports PSD layers.
- The PSD writer is hand-rolled: 8-bit RGB with PackBits-compressed layers, each layer cropped to its
  contents.

## How to regenerate

```sh
./setup.sh --no-model   # once: env/ (the full ./setup.sh also fetches the AI-render model)
plan/rebuild_images.sh
# Optional check: env/bin/pip install psd-tools, then PSDImage.open(...) and list the layers.
```

`setup.sh` is the single setup entry point: it creates `env/` from `requirements.txt` (drawings + AI renders).
`plan/rebuild_images.sh` only rebuilds `plan/` with `env/` and stops if `env/` is missing. The system `python3` does NOT have
Pillow; don't install packages into it.
Pillow is pinned below 13 because mflux 0.23 fails to import with Pillow 13. The drawings were rebuilt with it on
2026-10-20 (before that, Pillow 13); only text anti-aliasing changed. The permit PDF embeds its build date, so it
changes on every rebuild.

## User preferences and conventions

- Make the change, re-render, and look at the PNG before reporting back. Keep replies short.
- Never overwrite or modify anything in `reference/` (the user's original sketches).
- When the user says "top" or "left", they mean the drawing as oriented: top = the parking pad / alley
  end, bottom = the house.
- The user cares about real-world sizes and retail availability (for example the shade sail). Verify
  product sizes against real listings before recommending them.

## Known open discrepancies in the source measurements (unresolved)

- **Notch depth:** the direct measurement is 61"; the two grass heights imply 408 − 357 = 51".
  The plan uses 61, so the grass's left side is 347.
- **Right edge:** the left side gives 41.5 + 228.5 + 38 = 308; along the bottom, 23.5 + 162.5 + 99 + 16 = 301.
  The plan keeps 99", so the concrete is 23" from the right boundary instead of 16".
- **Half wall thickness:** 27" is implied by 36 + w + 245 = 308. The sketch suggests about 12".
- **Dots:** `reference/sketch_sized.png` has three small dots of unknown meaning; they are not drawn.

## City of Denver records (checked 2026-10-18)

Property: Denver Property (the user asked that the address, parcel number and legal description not be stored here).
Zoning U-RH-2.5.
It is inside the **Curtis Park - G historic district**, so Landmark Preservation must also review the pergola.
Floodplain zone X. Source: the assessor page plus the Denver open-data ArcGIS layers `ODC_PROP_PARCELS_A`,
`ODC_PROP_BUILDINGOUTLINES_A` and `ODC_UTIL_SANMAIN_L` (EPSG:2232, feet). The GIS data is approximate, not a survey.

- **Lot:** a 25.03' × 126.21' rectangle (300.3" × 1514.6"), 3,150 sq ft. The rear lot line is on the alley (SE) end.
  In the drawing, +x points SW and x = 0 is the NE side.
- **Width conflict:** the plan's 308" is about 8" wider than the city's 300". The bottom-row tape total (301") matches
  the city. If x = 0 is the true lot line, the right lot line is at about x 300, so the pergola edge (x 297) is ~3" from it.
  A survey is needed before permit submittal.
- **Depth check:** the GIS house outline's back wall is 60.1' (721") from the rear lot line, which matches
  HOUSE_FRONT = 721. So y = 0 is about the rear lot line. The stepped wall at 67' matches BOTTOM_LINE = 806.
- **Sewer:** the public main is an 8" clay (VCP) collector owned by Denver Public Works. It runs in the alley
  5.7–7.7' beyond the rear lot line; its downstream invert is 5210.3', so it is ~11' deep. The private lateral
  is not mapped. It most likely crosses the yard from the house to the alley, possibly under the pergola footings.
  Have a plumber camera-locate and mark it. Excavation within 2' of a sewer line triggers a Sewer Use and Drainage Permit (SUDP).
- **Soil (USDA Soil Data Access, queried for the neighborhood):** map unit "Urban land-Elyria-Ascalon complex, 0 to 3
  percent slopes": urban fill over sandy loam / sandy clay loam (20–30% clay), with clay-loam/clay components (Weld,
  Racas); pH 7.4–8.4. Treated as "likely heavy/compacted, partly clay" in FINAL_PLAN A2.6 and Part C.
- **Neighbors:** the NE neighbor's garage sits just off the left side of the parking pad (GIS: 1–22' NE of the side
  line, 1–28.6' from the alley).

## Tree (purple marker at (215, 329)), researched 2026-10-18

The spot (moved from x 155 to 215, then down to y 329) is about 18' from the left lot line and 7–8' from the right one,
about 27' from the alley lot line and 9' 4" into the grass from the pad edge, in full sun.
Pick a tree with a mature spread of 25–35'. Species come from The Park People's "Best Trees for Denver" list.

- Shortlist:
  - American hophornbeam (native, fits the lot, slow)
  - State Street maple (`Acer miyabei 'Morton'`, 50×30)
  - Norwegian Sunset maple (35×25)
  - Chinkapin oak (best wildlife value, but wide)
  - Kentucky coffeetree 'Espresso' (male, no pods)
  - Common hackberry (Colorado native, big)
- Smaller trees, 25' canopy or less (added 2026-10-18 at the user's request; they asked for Tatarian maple):
  - Hot Wings Tatarian maple, bigtooth maple (best native), Gambel oak
  - thornless cockspur hawthorn and 'Ivory Silk' Japanese tree lilac (both in Tagawa's stock)
- Evergreens (all Colorado natives): piñon pine (don't irrigate it), Vanderwolf's Pyramid limber pine, Rocky Mountain juniper
  ('Moonglow' / 'Medora' in Tagawa's stock). Junipers spread cedar-apple rust to hawthorns.
- The user's criteria: ecologically sound, drought resistant, available locally.
  - Tagawa's live stock is scrapeable at `shop.tagawagardens.com/collection/<id>` (31 = deciduous, 79 = evergreen).
  - CreekSide Tree Nursery (Boulder, 303-668-7647) lists the natives, but warns its site stock may be stale.
- Avoid:
  - ash (emerald ash borer)
  - honeylocust (overplanted)
  - willow, silver maple, poplar (roots seek the sewer lateral)
  - Siberian elm, Russian olive
  - Callery pear, Amur maple (invasive); blue spruce, Austrian and Scotch pine; serviceberry and redbud (too thirsty)
- Photos: FINAL_PLAN A2.5 has 14 whole-tree Commons photos. The user wants mature trees, with a caption whenever
  a photo shows a related species or variety and not the exact tree in the table.
- The user hasn't chosen yet; the drawing keeps the generic tree marker.
- Where to buy, delivered in late October:
  - City Floral, Denver: delivers within 5 miles; 30% off trees
  - Echter's, Arvada: delivery and planting
  - Tagawa, Centennial: planting service; 50% off trees
- Denver Digs Trees fall 2026 applications are closed.

## AI "finished yard" images (full render done 2026-10-20, awaiting review)

- **Read `explorations/ai_renders/LOG.md` first.** It has the setup, the tools (`camera.py`, `guides.py`,
  `edit_region.py`, `flux_edit.py`, `tone.py`), every prompt tried with its result, the current state, the user's
  outstanding requests and the next steps. Append to it as you work.
- The user's yard photos are in `private/references/*.jpg` (no GPS). Outputs go to `private/renders/` (never published).
- Edits run in-process: FLUX.2 [klein] 4B via mflux, from the shared Hugging Face cache (the same model download as
  the user's rora project). Python: `env/`, made by `./setup.sh` (see README.md). No app or server needed.
- What works: draw a placeholder at the plan position (camera-fitted), then ask the model to make it realistic.

## Finishing note

Rocky Mountain Prestain (Denver, 303-286-2874) factory-stains natural wood for lumber yards. Ask Front Range
Lumber to have the cut timbers pre-stained there, then touch up any field cuts. Slats ordered later need a second
run or DIY stain.

## Pergola build: purchasing and Denver code notes (2026-10-17)

- **Kit:** Zen Pergolas 20' × 12' free-standing 2-block, 6x6. Options: angled 2x6 roof (11 slats per opening), 6x6 corner
  supports (8), no privacy walls. Optionally two Zen "6x6 Corner Hanger" brackets for the hammock.
  Zen includes brackets and screws but **no anchors or lumber**.
- **Lumber:** FOHC Douglas fir from Front Range Lumber (cut to length, delivered), stained dark. Cedar isn't needed.
  Order the 2x6 slats only after the frame is up, cut to the measured opening.
- **Footings:** Denver frost depth is 36". Planned 12" Quik-Tube piers, with the bottom about 44" below grade, under the
  three front posts and the back-right post (x 291.5–297 is right of the concrete edge at x 285). The back-left and
  back-middle posts get Titen HD 3/8" × 4" anchors (mechanically galvanized) into the patio, if the slab is thick enough.
- **Permits:** Denver requires a zoning permit **and** a building permit for every pergola (e-permits "Building Log").
  Inspections: footing, framing, final. The 240 sq ft footprint is over the 200 sq ft small-structure exemption.
- **Unresolved code risk:** the pergola's right edge (x 297) is only 11" from the right boundary (x 308), and the left
  edge is 57" from x 0. Denver side setbacks are typically 3–5'. On a 308" (25'8") lot, 3' setbacks on both sides
  leave 236" (less than 240"). Confirm the zone district and the true lot lines before ordering. The 20' width may
  have to shrink, for example to a 16' × 12' kit.
  - City records show a 300" lot (see "City of Denver records"), which makes this tighter.
  - **User decision (2026-10-18):** keep 20' × 12' and push for the permit anyway.
  - **Plan B (2026-10-18):** VEIKOUS 12' × 20' cedar pergola (PG0202 family, 240.1" × 137.8" × 88.2", 5.5" posts,
    pre-stained cedar, ground stakes only). The user likes its classic look; Zen is sturdier. Not drawn in the plan.
    Post count unconfirmed. Details and links are in FINAL_PLAN B4.1b.
  - Landmark review (Certificate of Appropriateness) is also required because the lot is in Curtis Park.
