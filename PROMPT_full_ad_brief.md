# Full-ad brief — copy, fill the [brackets], send

```
Use the product-ad-fidelity skill to produce the complete vertical ad, end to end.

PROJECT
- Brand / product: [Beethoven – فخامة سمو للطيب – Vietnamese Tiger oud]
- Magnific project: [project name or link]   (search it first; reuse any clean clip or still already there)
- Reference / edit to match: [Drive link of the video whose edit, timing and captions I want]
- Voiceover: [use the voice from: Drive link | keep the reference voice | remove the phrase "..."]
- Pauses: [none | add natural pauses between sentences]

PRODUCT LOCK (non-negotiable)
- The oud pieces and the box arrangement must be the approved ones from the skill library
  (assets/box_masters, ad-1 look). Box = open, empty, fitted cream insert, then fill with box_masters.py.
- Box rims/walls/clasp/lid lettering stay untouched (0 changed pixels on the leather). No piece cut by a rim,
  no wood over a rim, a thin calm lining strip at the edges is fine.
- Lid lettering must read exactly: [Beethoven / فخامة سمو للطيب].

SCENES (one line each — use the reference's cut points)
1. [0.0–4.9 s] [hook: hand holding one piece]          -> [reuse approved clip | new still attached]
2. [4.9–6.7 s] [tray, hands sorting]                    -> [...]
3. [...]                                                -> [...]
Props: [wooden carved burner + navy tube with incense sticks in scenes N, M | none]
Gift card: [inside the lid, upper right, leaning on the right wall | badge pop-up | none]

LOOK & EDIT
- Captions style: [two-line gold (ad 1) | karaoke white + black outline, yellow current word (ad 2)]
- Caption text = the voiceover words, timed word by word; keep captions off products and props.
- Effects: [laser outline on the final boxes | glow around the card | soft sun ray in the long scene | none]
- Long scene: [hold 2 s then slow zoom-in, locked Kling camera]
- Pop-ups: tabby + tamara with their words at the end.

BUDGET & APPROVALS
- Show me every still first (free/65 credits) and wait for my OK before any Kling credit.
- Each scene is generated ONCE in Kling — no second takes; fix small things locally.
- Max credits for this job: [e.g. 3000]. Tell me the cost before each paid step.

DELIVERY
- Final MP4 1080x1920 30 fps + a no-captions version + side-by-side check vs the reference.
- Commit and push to the working branch; tell me the credits spent.
```

---

# How to design scene stills so they plug straight into the pipeline

Generate in Magnific with **Nano Banana 2.1 (imagen-nano-banana-2-1), 2k, 9:16**, inside the same project.
One still per scene, named `sceneNN_<what>.png`. Send the still names/links in the brief.

## Product scenes (box with oud)
1. **Leave the box OPEN and EMPTY.** Never let the model draw the oud — it is filled later from the approved
   library, so it always matches. Prompt: "the box is open and empty: a fitted, factory-made cream satin insert,
   perfectly taut, flat floor, straight inner walls, crisp creases, padded bolster at the hinge, nothing inside".
2. **Attach the approved empty box** (`assets/box_masters/empty_ref/ad1_approved_empty_box.png`) as Image 2:
   "the box interior looks exactly like Image 2".
3. **Camera angles that already exist in the library** (fill looks best when the angle is close):
   - close, slightly high, box filling the lower half (like beethoven_04)
   - medium, three-quarter from the front-left, box in the lower-left (like beethoven_06 / 09)
   - low, wide, box small in the lower third next to other boxes (like beethoven_0708)
4. The whole opening visible: no hand, card, or prop covering the inner floor; the four inner corners visible.
5. Lid lettering written in the prompt exactly ("Beethoven", "فخامة سمو للطيب"); check it before approving.
6. Lighting: warm, from upper left; avoid a hard highlight on the inner floor (it changes the oud colour).

## Props and composition
- Leave **empty foreground** (marble/table) in front of the box if a burner or sticks will be added; it is
  easier to add a prop into free space than to widen a tight shot.
- Keep the **caption zones free**: about y 180–330 px (top) and 1450–1650 px (bottom) on a 1080×1920 frame —
  no logos or faces there.
- The gold mabkhara: smoke only from its bowl; the wooden burner is unlit.
- Same room, table, lanterns and colour across scenes of one ad.

## Hands
- Hand holding a piece: generate the hand in a pinch pose **with a piece**, then the real piece is swapped in;
  fingertips must clearly clamp the upper end. No rings/jewellery unless wanted.
- Hands sorting on a tray: tray visible, pieces are replaced with real cut-outs later.

## Motion notes (tell me per scene)
- Static product + slow push-in / glide (default), or **locked camera** (I add the zoom for free).
- Say the scene length you need; I generate length + 0.5 s once.

## Checklist before sending a still
- [ ] 9:16, 2k, same project   - [ ] box open & empty, taut insert, 4 inner corners visible
- [ ] lettering correct          - [ ] caption zones free   - [ ] space left for props if needed
- [ ] matches one library angle  - [ ] lighting warm, no blown highlight inside the box
