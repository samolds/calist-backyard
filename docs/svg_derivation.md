# How backyard.svg was made

> Historical: describes the first SVG (now `explorations/base/backyard.svg`). File names below are pre-restructure (`backyard*.png` are now `reference/sketch*.png`). Current geometry is in AGENTS.md.

No script was used. The SVG was written by hand. The coordinates came from reading
`backyard_dimensions.png` and doing the arithmetic below. `backyard.png` and
`backyard_labeled.png` were used only for shapes, curves and the relative position
of anything that had no measurement.

## 1. Coordinate system

- 1 SVG unit = 1 inch.
- x = 0 is the left boundary line (the outer edge of the sidewalk and alley).
- y = 0 is the top line (the top of the parking pad).
- All lines use `vector-effect="non-scaling-stroke"`, so they stay 1.5 px wide at any zoom.

## 2. Measurements read from backyard_dimensions.png

| Item | Measurement |
|---|---|
| Parking pad width (half wall to right edge) | 144 + 101 = 245" |
| Parking pad height | 144 + 73 = 217" |
| Grass top edge (right of notch) | 140" |
| Grass notch, horizontal | 85" |
| Grass notch, vertical | 61" |
| Grass height, left side | 144 + 144 + 69 = 357" |
| Grass height, middle | 144 + 144 + 120 = 408" |
| Grass width, bottom | 144 + 84.5 = 228.5" |
| Sidewalk width | 41.5" (confirmed) |
| Left edge to half wall | 36" (confirmed, from backyard_sized.png) |
| Mulch strip width (mulch line to pad right edge) | 38" |
| Mulch: top to post / post / post to bottom | 144 + 118 = 262" / 8" / 144" |
| Grass bottom to house | 96" |
| Steps | 69" wide x 51" deep, 45" from grass |
| House wall to left of steps | 48.5" |
| Right of steps to house wall | 45" |
| Alley (left boundary to house) | 23.5" |
| House right wall to concrete right edge | 99" |
| Concrete right edge to right boundary | 16" |
| A/C | 32" x 32" |
| House front to bottom line | 85" |
| Shed | 51" wide x 30.5" deep |

## 3. Conflicts and how they were resolved

1. **Notch depth.** The direct measurement is 61". The two grass heights give
   408 - 357 = 51". I used 61": a short single measurement is more trustworthy than
   the difference of two long multi-tape measurements. Result: the grass left side
   is 347" instead of 357".
2. **Grass width.** 85 + 140 = 225", but the bottom measures 228.5". I kept 228.5"
   and 85", so the top edge is 143.5".
3. **Mulch height.** 262 + 8 + 144 = 414", but the grass is 408". I scaled the gaps
   by 408/414, so the post top is at 258.2" from the pad line.
4. **Right side.** The left side gives 41.5 + 228.5 + 38 = 308". The house side gives
   23.5 + 162.5 + 99 + 16 = 301". I kept 99", so the concrete is 23" from the right
   boundary instead of 16".

## 4. Derived coordinates (inches)

- Grass: x 41.5 to 270. Top-right edge at y = 217. Bottom at y = 217 + 408 = 625.
- Notch corner: x = 41.5 + 85 = 126.5. The grass left top is at y = 217 + 61 = 278.
- Notch curve: a straight drop from y = 217 to y = 228, then the Bezier
  `C 126.5 258, 96.5 275, 61.5 277.5`, then a line to (41.5, 278).
  Fitted to points sampled from the hand drawing.
- Grass bottom-left corner: rounded, radius 8.
- Mulch: x 270 to 308. Post centre at (289, 479.2), radius 4.
- Parking pad right edge: x = 41.5 + 228.5 + 38 = 308.
- Half wall: x 36 to 308 - 245 = 63, so it is 27" thick.
- House: front at y = 625 + 96 = 721. Walls at x = 23.5 and 23.5 + 48.5 + 69 + 45 = 186.
- Steps: x 72 to 141, y 670 to 721.
- Concrete right edge: x = 186 + 99 = 285. Top-right curve copied from the drawing.
- Bottom line: y = 721 + 85 = 806.
- A/C: y 728 to 760. Shed: y 775.5 to 806.

## 5. Estimates (no measurement; proportions taken from the hand drawing)

- Half wall height: about 157" (y 28 to 185).
- A/C: x = 191.4, about 5.4" from the house wall.
- Shed: x 214.5 to 265.5, using the drawing's left/right gap ratio inside the 99" span.
  Drawn as a rectangle, not the sketch's slight trapezoid.
- Table: about 54" across, centre (235.6, 686). Size is from comparing it with the
  A/C and shed as drawn.
- Small circle near the grass corner: about 16" across, centre (270, 652).

## 6. Preview

```sh
D=$(mktemp -d /tmp/backyard_svg_preview.XXXX)
sips -s format png backyard.svg --out "$D/full.png"
```
