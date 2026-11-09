---
name: product-ad-fidelity
description: Fix how a real product looks inside an AI-generated ad video (Magnific / Nano Banana / Kling) so it matches the client's real product photos almost exactly, then re-cut the ad with captions and pop-up badges. Use this whenever a user says the product in an AI video/ad "doesn't look like the reference", wants the oud / agarwood / incense / coffee beans / dates / jewellery / any small loose product in a scene to match real photos, asks to redo product scenes in Magnific or Kling, to fill a box/tray with the real product, to rebuild Arabic captions on an edit, to add a pop-up like the tabby/tamara logos, or mentions "تظبيط العود", "مطابق للريفرنس", "الصينية", "العلبة", "المونتاج" — even if they don't name this skill.
---

# Product-fidelity fix for AI ads

Proven on a 26 s vertical oud ad (Beethoven / فخامة سمو للطيب). Read `references/lessons.md`
before starting: almost every rule below exists because the first attempt failed.

## Core idea

AI image/video models **redraw** the product from their own idea of it; prompts plateau at
~80-90 % likeness no matter how precise. To reach "99 %", the product pixels must be **the real
product**: cut pieces out of the client's photos and composite them into an AI plate whose old
product has been removed. Use AI only for what it is good at: removing things, adjusting hands,
and camera/hand motion.

## Golden rules (client-facing)

1. **Show before you spend.** Every paid step (Magnific edit ≈65 credits/image, Kling 3.0 ≈90
   credits/second) needs the client's OK on the *still* first. Never chain image → video → edit in one go.
   When the client says "don't start anything until I say", stop after the images.
2. **Start from what is actually in the edit.** Get the real ad (download the Drive/WeTransfer
   link; allow the host in the environment if blocked) and match each cut to its source clip with
   `scripts/align_segments.py`. Don't assume the newest Magnific images are the approved ones — ask.
3. **One scene first** (the worst one), get approval on look/size/colour, then roll out.
4. **Report honestly**: what still differs, what each step cost, what you threw away.
5. Reply in the client's language/dialect; keep technical detail out of the message.

## Repeat client: lock the product look and box arrangement (do this FIRST on ad 2, 3, ...)

A prompt alone can never keep the product identical: every AI generation redraws the pieces.
What stays fixed is the **approved pixels**. For Beethoven the four approved ad-1 boxes (4 camera
angles) are stored in `assets/box_masters/` (`python scripts/box_masters.py sheet out.jpg` to view).

1. Generate/animate the rest of the scene normally, but ask Magnific for the box **open and empty**
   (prompt "Empty open box for the master heap" in `references/magnific_prompts.md`), with the approved
   box photo as reference so the box itself (green leather, gold clasp, cream lining, B logo) stays the same.
2. Read the opening corners off a grid (back-left, back-right, front-right, front-left).
3. `python scripts/box_masters.py place empty.png filled.png "BLx,BLy BRx,BRy FRx,FRy FLx,FLy"` —
   picks the approved heap whose camera angle is closest, maps the heap's own footprint into the new
   opening (`--back 0.1` leaves the small empty band at the back, as approved), relights it to the
   new scene and clips it inside the opening. `--master NAME` forces one; `--edge` px keeps it off the rim.
   A thin even lining strip is kept between wood and every wall (`--wall_px 14`, default): wood touching a dark
   rim hid the wall edge and the client saw the box "bent" — the box edges must look exactly like the empty box.
   The angle pick is only a starting point: also render every master (`--master NAME`) into the box,
   put them in one grid and pick by eye (ad 2: `beethoven_09` gave the clearest, most ad-1-like pieces in all boxes).
   Since ad 2 `place` does it in this order, all automatic: (a) find the real opening of the empty plate (rim band
   and its highlight excluded) with a thin even lining strip at every wall; (b) shrink-fit the approved heap's
   own outline inside it, pulling in only the side that would cross a rim, until no wood is over any rim;
   (c) fill the band between heap and walls with WHOLE real pieces (`assets/box_masters/pieces`, same colour
   model), each fully inside the opening, mostly lying in the gap with only its end on the heap.
   Verify: 0 changed pixels on the green leather (rim/walls) versus the empty plate.
4. Show the still before any Kling credit. If the client approves a new box, register it:
   `box_masters.py add NAME filled.png empty.png "quad"` so the library grows with every ad.
Never use one heap for every box (ad 2: the close high-angle heap squeezed into small low-angle boxes
looked flat and crowded — "ad 1's distribution is better").

## Workflow

### 1. Inventory
- Download the ad, find cut points: `ffmpeg -i ad.mp4 -vf "select='gt(scene,0.15)',showinfo" -f null - 2>&1 | grep pts_time`
- Contact sheets of every scene + of the caption areas every 0.2 s (`scripts/qc.py sheet`) → write
  down every caption word and its appear time (needed later for the caption rebuild).
- In Magnific: `creations_search` the project, `creations_lineage` each clip → its start image.
  Download start images and source clips (pikaso.cdnpk.net must be reachable).

### 2. Real product library
- `scripts/extract_pieces.py pieces/ photo1.jpg photo2.jpg` → RGBA cut-outs + `_sheet.jpg`. Delete bad ones.
  Shadows on white paper are bluish-grey: the loader drops them (otherwise white crescents appear).
  9 pieces were enough; 15-20 spaced pieces shot in daylight as original files are better.
- Target colour: crop **wood-only** patches (no fingers!) from the client's preferred photos →
  `scripts/measure_target_color.py target.json a.jpg:x0,y0,x1,y1 ...`. The client judges colour
  against those photos, not against what looks nice.

### 3. Clean plates (Magnific, `images_generate`, model `imagen-nano-banana-2-1`, 2k, 9:16)
Edit the approved start image with the "remove the product" prompt in `references/magnific_prompts.md`
(reference = the start image only). Keep hands/held pieces when they matter. Check the empty plate
against the original (logos, lettering, box shape must be unchanged).

### 4. Composite (free, local)
- Find coordinates: draw a labelled grid on a zoom of the plate (OpenCV lines + `putText`) and read
  the rim / floor / hand corners off it. Hands: hand-draw polygons from the grid — skin-colour
  detection fails on brass/cream/gold.
- **Flat surface (tray, cloth, table):** `scripts/scatter_on_surface.py cfg.json` — loose single layer,
  brass visible between pieces, `hand_margin` keeps pieces off the fingers (client: "pieces floating on
  his hand"), `fixed` places the cloth pieces and the pinched piece.
- **Container (box):** `scripts/fill_container.py cfg.json` — what the client finally approved:
  pieces ≈ 1/3 of the box front width, elongated ×1.12, full but with natural gaps, wood on wood
  (3 layers), every piece fully inside the opening, `backt` 0.6-0.7 so nothing climbs the back wall,
  `leftfill` if one side looks empty. Try 2 seeds, show the better one.
- All new product in a video must share **one colour pipeline** (`apply_target_colour`); a piece
  graded differently (e.g. the one in the hand) is noticed immediately.
- Compare against the reference with `scripts/qc.py compare` before sending.

### 5. Hands holding a piece
Placing a cut-out "behind the thumb" looks pasted and breaks in motion. What worked:
1. composite the box without the held piece;
2. Magnific edit with the hand-pinch prompt → AI draws fingers that truly clamp a piece;
3. replace the AI piece with a real cut-out (`fill_container.py` `held`, or
   `scripts/match_piece_color.py` histogram-match), keep only the AI **fingers** on top;
4. if the fingers still don't close on the piece, one more Magnific edit "adjust only thumb and index
   finger so they physically pinch the upper end" — then paste back only the finger region.
Validate the grip on a still: "if the grip isn't right, the motion won't be either" (client).

### 6. Motion (Kling 3.0 via `video_generate`, 1080p, 24 fps, no sound)
- Upload the approved still (`creations_request_upload` → PUT → `creations_finalize_upload`).
- Prompts in `references/magnific_prompts.md`: product static, slow push-in/glide, "keep exactly the
  same shape, colour, pattern", strong negative prompt. Duration ≥ scene length + 0.5 s.
- Hand shots: lock **start and end keyframe to the same image** + "tiny breathing movement" — otherwise
  Kling lifts/rotates the piece and recolours it.
- Kling may add rings/jewellery; automatic removal damaged nearby edges — tell the client, offer a regen.
- A slow zoom made locally (ffmpeg zoompan) was rejected as "not nice" — use Kling for motion.
- Check every clip with a 5-frame strip of the product area before using it.

### 7. Re-cut and captions
- Build a **caption-free** edit on the original frame counts with `scripts/assemble.sh` (deflicker on
  AI clips; untouched scenes from their clean source clips — check speed: 24 fps clips laid at 30 fps
  need `setpts` ×1.25). Send it to the client as a check.
- Rebuild captions from scratch with `scripts/build_titles.py titles.json clean.mp4 original_ad.mp4 out.mp4`
  (example config: `references/titles_example.json`). Do **not** lift old burned-in captions
  by differencing against sources — it leaked old-scene ghosts ("mirror" patches) and flickered.
- Pop-ups: `scripts/make_badges.py` — lift a logo from the product (gold-on-cream), build a gift badge,
  lift existing tabby/tamara badges from the original. Badges pop with the word they belong to.
- Final QC: `scripts/qc.py flicker` (mean ≤ ~0.3 per band, spikes only at cuts) + contact sheet.

### 8. Deliver
Commit everything (final mp4, clean mp4, per-scene clips with/without captions, stills, configs) to
the working branch, push, send the final video, list the timeline and the credits spent.

## Files
- `scripts/common.py` – piece loading, grading, shadowed placement, target colour mapping
- `scripts/extract_pieces.py`, `measure_target_color.py`, `scatter_on_surface.py`, `fill_container.py`,
  `match_piece_color.py`, `align_segments.py`, `assemble.sh`, `build_titles.py`, `make_badges.py`, `qc.py`
- `scripts/box_masters.py` – approved-box library: add / place (nearest camera angle) / sheet
- `assets/box_masters/` – approved Beethoven heaps (ad 1, 4 angles) + `masters.json`
- `assets/almarai-*.woff` – caption font (Arabic 800 + Latin for ! . …)
- `references/lessons.md` – every failure and its fix (read first)
- `references/magnific_prompts.md` – the exact prompts that worked
- `references/beethoven_case.md` – full numbers of the reference project (timings, coordinates, costs)
- `references/titles_example.json` – caption/badge config of the reference ad
