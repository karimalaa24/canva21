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
| Kling hand shot with a big move (piece placed on cloth) — chosen version had piece size stable; the other grew. | Generate 2, pick by checking piece size over time. |
| Captions lifted from the old render by differencing: ghost box edges/reflections ("mirror"), flickering dark band, specks when text faded, missing words at cross-fades. | Build a caption-free edit, re-type all captions (`build_titles.py`). |
| Kling clips have slight luminance flicker. | `deflicker=size=9:mode=pm` per clip before assembly. |
| Arabic subset font has no `!`/`…` → boxes. | Draw punctuation with the latin subset of the same font. |
| Long caption line ran off the frame (also in the original). | Auto-shrink lines wider than 950 px. |
