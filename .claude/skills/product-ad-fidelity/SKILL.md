---
name: product-ad-fidelity
description: Build or fix a vertical AI product ad (Magnific / Nano Banana / Kling) so the real product looks exactly like the client's photos and approved boxes, then cut the full video (voiceover, captions, effects, pop-ups) to match a reference edit. Use whenever a user says the product in an AI video/ad "doesn't look like the reference", wants oud / agarwood / incense / coffee / dates / jewellery or any small loose product placed in a box or tray, wants scenes generated or redone in Magnific/Kling, wants a new voiceover laid on an existing ad, wants props (burner, sticks, card) added or removed, wants Arabic captions rebuilt, tabby/tamara pop-ups, or mentions "تظبيط العود", "مطابق للريفرنس", "العلبة", "المبخرة", "الفويس", "الكابشن", "المونتاج" — even if they don't name this skill.
---

# Product-fidelity AI ads (Beethoven / فخامة سمو للطيب method)

Proven on two Beethoven oud ads (26-33 s, 1080×1920, 30 fps). Read `references/lessons.md` first:
almost every rule here exists because a first attempt was rejected. The client's brief format and the
still-design guide are in `references/client_brief_template.md`.

## Core idea
AI models **redraw** the product every time; prompts plateau at ~80-90 % likeness. For 99 % the product
pixels must be the **real/approved product**: real cut-outs or an approved heap composited into an AI plate
whose product area is empty. AI is used for what it is good at: empty plates, scene stills, hands, motion.

## Golden rules
1. **Show before you spend.** Stills (free or ≈65 cr) are approved before any Kling credit (≈90 cr/s).
2. **Every scene is generated ONCE.** No re-rolls, no "generate 2 and pick". Get the still, duration and the
   proven prompt right first; fix small flaws locally (retime, re-track, mask, paste back).
3. **Start from the real edit.** Download the reference ad, find every cut (frame numbers) and caption timing.
4. **Search before generating.** The client's Magnific project often already has the clean clip/still
   (`creations_search` by prop/scene keyword, `creations_lineage` for start images).
5. **Box edges are sacred**: wood never touches or covers a rim; 0 changed px on the leather vs the empty box.
6. Reply in the client's dialect, no jargon; report credits spent and anything that still differs.

## Locked assets (repeat client)
- `assets/box_masters/` — 4 approved filled boxes (angles 04, 06, 0708, 09), real piece cut-outs (`pieces/`),
  colour target (`target.json`), approved empty box (`empty_ref/`). `box_masters.py sheet out.jpg` to view.
  `beethoven_09` gave the most ad-1-like result in every ad-2 box.
- Fonts: Almarai 800 (two-line gold style), Alexandria 900 (karaoke style). Logos: tabby / tamara.

## Full-video pipeline
### 1. Inventory (free)
- Cuts: `qc.py sheet` + frame-difference cut list; captions: per-frame yellow/white pixel boxes → word start
  times and y (see `references/edit_recipes.md`). Write a scene table: frames, source, what must change.
- Voice: `pace_voice.py gaps` lists silences (for pauses or cuts).
### 2. Stills per scene (≈65 cr each, approve before motion)
- Box scenes: Magnific edit → box **open and EMPTY** with the approved fitted insert (prompt "Empty box =
  approved fitted insert", Image 2 = `empty_ref`). If an AI floor came out draped: `taut_lining.py`.
- Fill: `box_masters.py place empty.png filled.png "BL BR FR FL"` (opening corners from a grid) — real opening
  mask, shrink-fit heap, whole-piece ring fill, `--wall_px` lining strip. Render all 4 masters, pick by eye.
- Loose product on tray/cloth: `scatter_on_surface.py`; box from scratch: `fill_container.py`; hand holding a
  piece: hand-pinch edit + real cut-out (`match_piece_color.py`).
- Props (burner, sticks, card): add them in the still with a nano-banana edit using a reference frame of the
  prop; wide shot needed? build a 0.78× canvas with a blurred border and let nano-banana "replace the blurred
  border" + add the prop, then paste the approved box/oud back by homography (`images_expand` failed).
### 3. Motion (Kling 3.0, 1080p, 24 fps, no sound, ONE take)
- Prompts in `references/magnific_prompts.md`. Duration = scene length + 0.5 s (round up).
- Long scene: lock the camera in Kling ("locked-off tripod"), add hold + zoom locally (`fx/hold_zoom.py`).
- Verify 6 frames of the product area (oud, rims, lettering) before using a clip.
### 4. Free fixes on existing clips
- Add a static prop / card to a clip without regenerating: `track_insert.py` (still mode or quad mode).
- Burned-in captions on a needed clip: find its clean Kling original in the project instead of inpainting.
### 5. Edit
- `assemble.sh voice.m4a clean.mp4 clip:FRAMES[:start[:speed[:deflicker]]] ...` on the reference's frame counts.
- New voiceover on an existing ad: re-cut each scene to the new voice's cut frames (`edit_recipes.md`).
- Voice tools: `pace_voice.py cut` (remove a phrase) / `insert` (pauses + time map; stretch scenes with
  minterpolate, ≤ 1.2×).
### 6. Effects & captions
- Effects template `fx/fx_template.py`: card glow outside the card only, laser box outlines on per-box tracks,
  `fx/sun_ray.py` soft sun shaft (client rejected bloom/sweeps/glints).
- Captions: two approved styles — **two-line gold** `build_titles.py` (ad 1) or **karaoke** white+outline with
  yellow current word `karaoke_captions.py` (ad 2). Never lift old captions by differencing.
- Pop-ups: `make_badges.py`; tabby/tamara pop with their word; the gift card works best **inside the lid, upper
  right, leaning on the right wall** (`track_insert.py` quad mode + `--glow` on "هدية سرية").
- Keep captions off props (move the group up if a prop sits in the caption zone).
### 7. QC & deliver
- Cut frames identical to the reference; caption on/off match ≥ 98 %; 0 changed rim px; `qc.py flicker`.
- Side-by-side sheets (reference vs new) at the same moments; commit + push; send video + sheet; list credits.

## Files
- scripts: `common.py`, `extract_pieces.py`, `measure_target_color.py`, `scatter_on_surface.py`, `fill_container.py`,
  `transplant_heap.py`, `box_masters.py`, `taut_lining.py`, `match_piece_color.py`, `align_segments.py`, `assemble.sh`,
  `build_titles.py`, `karaoke_captions.py`, `make_badges.py`, `track_insert.py`, `pace_voice.py`, `qc.py`,
  `fx/fx_template.py`, `fx/sun_ray.py`, `fx/hold_zoom.py`
- references: `lessons.md` (read first), `magnific_prompts.md`, `edit_recipes.md`, `client_brief_template.md`,
  `beethoven_case.md`, `titles_example.json`
