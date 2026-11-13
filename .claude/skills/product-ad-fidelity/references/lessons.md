# Lessons (what failed → what fixed it)

Ordered roughly as they happened on the Beethoven oud ad. Each one cost credits or a round-trip
with the client — don't repeat them.

## Process
| Failure | Fix |
|---|---|
| Regenerated every scene and animated them all in one go without showing anything; client: "show me first". | Still → approval → video. One scene first. Stop when told to wait. |
| Worked from the newest Magnific images, client said those were rejected versions. | Get the real edit, align each cut to its source clip, ask which images are approved. |
| Animated a shot that wasn't in the edit (wasted 360 credits). | Map every cut before generating anything. |
| GitHub push refused (no app access). | Tell the user once with the connect link; keep committing locally; push when access is fixed. |
| Drive link unreachable / Magnific upload host blocked. | Propose environment hosts: drive.google.com, drive.usercontent.google.com, ak-data.magnific.com, pikaso.cdnpk.net. |

## Product look
| Failure | Fix |
|---|---|
| Prompt-only edits (Nano Banana) with detailed descriptions: leaf/blade shapes, leopard print, orange or purple wood, splintery bark texture. ~6 rounds, still "not the same". | Stop prompting the product. Composite real cut-outs. |
| Called the pieces "flat"; client: "the reference isn't flat, it has clear height". | Describe from the photo, not from assumption; when unsure ask. |
| AI "reference-guided fill" using a real reel screenshot: right arrangement, wrong colour (different from all other scenes). | Use the same cut-outs + same colour pipeline in every scene; use reels only as *arrangement* reference. |
| First composite: too dense, pasted look, then too sparse, then "spread flat". | Final recipe: full box, 3 layers (wood on wood), small natural gaps, gaps enclosed by wood darkened as shadow, open edges keep the floor. |
| Pieces cut at the box edge / sticking out. | Every piece must fit fully inside an eroded opening mask (`fits()`); edges slightly emptier. |
| Ad 2: the same approved heap transplanted into every box, whatever the angle → small low-angle boxes looked flat and crowded; client: "ad 1's distribution is better". | `box_masters.py`: library of approved heaps from several angles, nearest angle wins, heap footprint mapped to the new opening. |
| Ad 2 box library: heap clipped to a hand-read quad that ran a few px over the left wall top → client: "the front-left of the box looks bent inward". | `place` clips to the convex hull of the plate's own light (non-green) opening: the wood stops exactly at the wall line, walls stay untouched. |
| Still "bent" after that; a wedge-shaped gap at the left wall ("looks empty") was rejected too. Cause: dark wood touching the dark rim hides the wall's top edge near the front, while at the back the edge shows against cream. | `--wall_px 14` (default): an even, thin lining strip between wood and every wall all the way round; heap stays full, walls read exactly like the empty box. |
| Then: "the rim is wider at the front than at the back". The opening mask (non-green + convex hull) reached the golden highlight on the rim, so wood covered the inner half of the rim band at the front. | Opening = non-green after a 17 px morphological open (removes the thin rim highlight), filled + smoothed, no convex hull; heap tucked under the walls (`--left/--right -0.08 --front -0.1`) so the master's own cut edge never shows; clip feathered σ 1.6. Check with a pixel diff that no rim pixel changed. |
| Clipping the heap at the rim cut whole pieces in half at the edges ("something sticking out over the edges"). | Never clip a heap to fit: shrink-fit the whole heap inside the opening, then fill the gap with whole loose pieces (`place` ring fill). |
| "The lining doesn't crumple — it's a manufactured, fixed insert" (AI empty plates had draped satin). | `taut_lining.py` on the empty plate before placing; edges kept calm with few loose pieces. |
| Local flattening of draped satin was only a patch; client pointed at the ad-1 empty box: "this exactly, always". | Re-edit each empty plate in Magnific with the approved ad-1 empty box as Image 2 (65 cr each); framing stays identical, so quads/tracks still fit. |
| Needed a wider shot (room for a prop in front) of an approved close shot: `images_expand` returned a broken low-res page with text. | Local canvas: shrink the approved frame to ~0.78, blurred reflected border, nano-banana edit "replace the blurred border with real scene + add the prop", then paste the original box/oud back (homography) before Kling. |
| Burned-in captions in a client's clip. | Search the Magnific project for the clean Kling clip of that scene (`creations_search` by prop keyword) instead of inpainting text out. |
| Pieces climbing the back wall. | Pull the back edge of the allowed area toward the floor (`backt` 0.6-0.7). |
| One side looked empty after that. | `leftwide` + `leftfill`. |
| Pieces too small → client asked "a bit longer, small amount". | `elong` 1.12 on the long axis only. |
| Pieces "stuck together". | Contact shadow σ≈2 + 1-px dark separation line around every placed piece. |
| White crescents around pieces. | Photo cast shadows are bluish-grey; keep only dark or warm (R>B) pixels as product. |
| Colour too red under warm scene light / too purple. | Measure target on wood-only crops (fingers polluted the first measurement); map in LAB with a(L), b(L) regressions after compositing. |
| Tray pieces read cool next to gold brass after matching boxes. | Small chroma lift (DA +1.5, DB +4) on that scene only; same model otherwise. |
| Piece in the hand a different colour from the others ("cut from the old reel?"). | Never let AI draw the visible product. Replace the AI piece with a real cut-out through the same pipeline; mean-matching wasn't enough, histogram matching + target chroma was. |

## Hands
| Failure | Fix |
|---|---|
| Pieces scattered over the fingers ("floating on his hand"). | Hand-drawn hand polygons, min distance from hands, hands pasted back on top. |
| Skin detection for hand masks grabbed brass and cream lining. | Draw polygons from a gridded zoom. |
| Pasted piece "behind the thumb" — not actually held; client predicted motion would fail. | Magnific edit that adjusts only the thumb/index to clamp the piece; keep only the AI fingers. |
| Kling lifted the piece away, rotated it edge-on, changed its colour. | Start = end keyframe (same image), "tiny breathing movement", negative prompt on rotation/lift. |
| Kling added a ring; auto inpainting ruined the cloth edge. | Accept or regenerate; tell the client. |

## Motion & edit
| Failure | Fix |
|---|---|
| Local ffmpeg zoom-in on the still: "not nice at all". | Kling 3.0 for every animated shot. |
| Kling hand shot with a big move (piece placed on cloth) — chosen version had piece size stable; the other grew. | (ad 1 only) Generated 2 and picked. Client rule since ad 2: every scene is generated ONCE — make the still and prompt right first, fix small flaws locally. |
| Captions lifted from the old render by differencing: ghost box edges/reflections ("mirror"), flickering dark band, specks when text faded, missing words at cross-fades. | Build a caption-free edit, re-type all captions (`build_titles.py`). |
| Kling clips have slight luminance flicker. | `deflicker=size=9:mode=pm` per clip before assembly. |
| Arabic subset font has no `!`/`…` → boxes. | Draw punctuation with the latin subset of the same font. |
| Long caption line ran off the frame (also in the original). | Auto-shrink lines wider than 950 px. |

## Edit, voice, captions (ads 2-3)
| Failure | Fix |
|---|---|
| Long scene: two clips / Kling camera move didn't match. | Locked Kling clip + local hold-and-zoom (`fx/hold_zoom.py`), zoom made stronger for free. |
| Long-scene "light" as bloom, sweeps, star glints: "not this at all". | One soft sun shaft that drifts over part of the scene and fades (`fx/sun_ray.py`). |
| Laser outline drifted (global affine, parallax) and missed box edges. | Hand-traced box polygons + per-box optical-flow tracks; occluded box masked. |
| Card glow covered the logo. | Halo only outside the card polygon. |
| "Sentences too fast". | `pace_voice.py insert` 0.3-0.4 s at sentence ends, scenes stretched to match, captions stay through pauses. |
| Gift badge floating mid-frame. | Card glued in the lid, upper right, leaning on the right wall, tracked; glow on "هدية سرية". |
| Captions landed on the burner. | Move that caption group to the top zone. |
| Ad 4: white band of lining in front of the heap ("fill to the front rim; pieces may hide behind the front wall"). | `box_masters.py place --front_hide`: heap extends under the front wall (front margin -0.14), fit loop never pulls the front in, front clip = real opening (no lining strip), sides keep the strip; then restore every leather pixel from the empty plate. |
| Ad 4: stills cut from the delivered video were soft/pixelated (compressed + digital zoom + burned captions). | Find the ORIGINAL stills in the client's Magnific project (match each scene by ORB inliers; the folder also holds rejected versions — pick the one that matches the video) and use the higher-res approved heap (beethoven_04) with a light sharpen + warm daylight lift. |
| Ad 4: start = end keyframe on hand shots made scenes look like still photos ("looks like images, not good"). | Start keyframe only; the CAMERA moves (push-in / lateral glide / small arc), hand calm. For detail shots a very subtle hand tilt + light gliding over the grain. If Kling flips the piece mid-clip, keep only the clean part and slow it (minterpolate) — no re-roll. |
| Ad 4: Kling bag-lift take — the ribbon handle doubled/twisted and mabkhara smoke drifted across the bag. | Generation artefact, not fixable by masking. Used the calm (locked) take and added a free local move: zoom toward the right ×1.14 with a ~2° roll (`fx/hold_zoom.py`-style warpAffine). |
| Ad 4: brand name wrong on bag/box lids ("Best Haven") after all scenes were animated. | No re-animation: nano-banana edit of each still (only the script word → "Beethoven"), align edit to still, cut a padded rect per word, track each word's surface with LK in the existing Kling clip and paste (`v4/rename.py` pattern). For clips that got a local zoom/roll, paste on the un-rolled clip, then re-apply the roll. 65 cr per still. Run trackers one or two at a time (memory). |
| Ad 4: bag handle "flashes" / looks wrong for single frames. Cause: 24→30 fps conversion with `minterpolate` (motion-compensated invented frames warp thin bright details). | Never minterpolate Kling clips for frame-rate: play the real frames at 30 fps (`setpts=N/30/TB`, i.e. 1.25× slower — fine for slow camera moves; generate +25 % duration if the scene needs it). |
| Ad 4: tracked name patch on a bag that the hand LIFTS looked wrong (the bag moves/tilts independently). | Tracked text patches only on surfaces that move with the camera. If the object itself moves, re-animate from the corrected still (one take). |
| Ad 5: small Arabic line on the bag came out garbled from the AI ("فختية شمو" instead of "فخامة سمو"). | Free fix, no Magnific edit: inpaint the old line on the ORIGINAL still, render the correct text yourself (full Almarai TTF, size/gold sampled from the old text), then track it into the clip (`rename.py` pattern, camera-only motion). AI image models garble small Arabic text — always zoom-check every Arabic line on bags/boxes before motion. |
| Ad 5: reviews section = 6-7 real screenshot cards piling up (looked busy). Tried 3 big cards one at a time — client PREFERRED the original pile. | Keep the pile (social-proof wall): all REAL screenshot cards (never invent reviews), each taken sharp from the frame where it is newest; pop every 0.5 s, zigzag right/left, older cards blur + grey, background dims 42 % + softens. Make cards ×1.2, space them by 0.765 × card height so the whole pile stays inside 1920 px, and ORDER them so the first, the middle and the last card are the strongest reviews (a 4-star card goes 2nd). Keep the original pop SFX. |
| Ad 5: oud looked "not the approved one" in review — it WAS the approved heap, only dark under evening light. | Compare side-by-side with the master before calling it wrong. Fix = product lift grade (luminance gamma 0.78 weighted to the lower frame + 6 % saturation), not a new heap. |
| Ad 5: "+" rendered as an empty box in the "٣ + ٣ هدية" badge. | The fontsource Almarai woff is an Arabic subset (no "+"). Use the full `Almarai-ExtraBold.ttf` for captions and badges. |
| Ad 5: dead air (silence) before a product scene made it feel long. | Cut the silence from the voice (0.55 s) and shift every later caption/scene; spend the saved time on an end hold after the last word. |
| Ad 5: weak static hook. | Free: open 1.5× close on the oud and ease out to the full box over 1.3 s (warpAffine zoom on the clean clip). |
| Ad 5: no music bed (voice only). | Lyria 3 (80 cr, 30 s) soft oud/qanun/daf bed, atempo-stretched to the video length, first mix (-10 dB gaps / -18 dB under voice) was "much too loud" → use -22 dB in gaps / -30 dB under the voice (music ≈24 dB below the voice) (own envelope, 60 ms attack / 450 ms release), fade-in 0.6 s, fade-out 1.6 s, then loudnorm -14 LUFS. |
| Ad 5: tabby / tamara logos popped in silently. | Same pop SFX as the review cards at each logo pop. Deliver 3 audio versions on the same picture: full, no music, no voice (music + pops). |
| Reel 01: cream gap left on one side of the box ("فراغ عالشمال / عاليمين") in new-angle stills. Cause: the opening mask is cut down to the detected cream colour, and the inner wall facing the camera is in shade, so it is dropped and the fit keeps the heap away from that whole side. | `box_masters.py place ... --quad_only --wall_px 3 --edge 2 --tol 60` (opening = the hand-measured rim quad). Margins went from 0.13-0.23 to 0.02 on both sides, no cut pieces, leather untouched. Check every box side by side on one sheet before sending. |
| Reel 01: client — when a WhatsApp screenshot is on screen and the VO reads it, do NOT caption the same words again. | Captions only for narrator lines that are not in the screenshot. |
| Reel 01: VO wording check. | Upload the VO as a black-frame MP4 and use Magnific `video_analyze` (free) per 15 s range for an Arabic transcript with times; caption the words actually spoken and flag any line that differs from the script. |
| Reel 01: client — "I don't want the box full and high; pieces LOW, not many, just covering the box floor (like the approved videos)". | Place the approved heap on a LOWERED quad (rim quad shifted down: front corners 0.10 × front-edge length, back corners 0.06; `reel01/edit/low_quad.py`) and clip the wood to the real rim with `box_masters.py --clip_quad "<rim quad>"` so the front wall/clasp hide it: `--quad_only --wall_px 3 --edge 2 --tol 60 --front_hide --ring 0 --finish`. Lining shows above the oud at the back; no stretch to the rim, no extra pieces. |
| Reel 01: "no piece may look cut — every piece whole". With a lowered heap the side rims clipped pieces against the visible inner wall. | `--clip_quad` now also drives the fit: sides/back must stay inside the real rim (only the front hides). The remaining side gap is always on the wall whose OUTER face the camera sees -> `--hide_side l|r` lets pieces tuck behind that wall (natural occlusion). Script prints "side/back cut px" — must be 0. Try all 4 masters (+mirror) and pick by eye; beethoven_0708 lowered 0.06/0.035 gave the most even floor cover. Recipe: `reel01/edit/FILL_RECIPE.md`. |
| Reel 01: client — a small cream gap in a box corner "looks strange: fill it, even with one piece". | `box_masters.py ... --ring 1 --max_ring 2 --seed N` (try seeds 1-6) adds 1-2 WHOLE real pieces in the band between heap and wall; pick the seed where the piece lies flat in the corner (with `--relight 1.0 --finish` the colour matched). |
| Reel 01: review background — empty majlis looked bare; client wanted a gold mabkhara on the table, CENTRED. | Generated the plate with the mabkhara (65 cr); it came out off-centre -> moved it locally: GrabCut mask, row-copy the background from 300 px left, per-row lighting match of the wood to both sides of the patch, carry the base reflection with the object (`reel01/images/review_plate_mabkhara_centered.png`). Ask for "exactly in the centre of the table" in the prompt next time. |
