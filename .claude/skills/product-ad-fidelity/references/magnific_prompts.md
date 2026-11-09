# Prompts that worked

Model for stills: `images_generate` mode `imagen-nano-banana-2-1`, resolution `2k`, aspectRatio `9:16`,
count 1-2, always pass the project `folderReference`. ≈65 credits per image.
Video: `video_generate` slug `kling-30`, resolution `1080p`, fps 24, `withSoundEffects:false`,
keyframes.start = uploaded still id. ≈90 credits per second (3 s = 270, 4 s = 360, 5 s = 450).

## Remove the old product (clean plate) — reference: the approved start image only
Flat surface:
> Edit Image 1. Remove every loose wood piece lying on the brass tray and the three wood pieces lying on the white cloth, together with their shadows, revealing the clean engraved brass tray surface and the clean white cloth underneath, continuing the existing engraving pattern naturally. Keep the single wood piece held between the right hand's thumb and finger exactly as it is. Keep everything else exactly identical: same overhead camera and framing, both hands and sleeves in the same pose, watch, white cloth shape and position, burgundy velvet, lamp, leather on the right, carved table, warm amber light, colours and sharpness. Add nothing.

Box:
> Edit Image 1. Remove all the wood pieces from inside the open green leather box, revealing the empty box interior: a clean flat cream satin-lined tray with its inner walls, softly shaded by the warm light. Keep everything else exactly identical: same camera and framing, all three green boxes, the burgundy gift bag with ribbon handles, every gold B monogram, the word Beethoven and all Arabic lettering exactly as written, the gold mabkhara and its smoke, the lantern, black-and-gold marble, room, light, colours and sharpness. Add nothing.

Remove only the held piece (keep pinch pose):
> Edit Image 1. Remove only the wood piece held between the thumb and finger, revealing the clean cream box interior and lid lining behind it. The thumb and index finger stay in exactly the same pinching pose, fingertips nearly touching with a small gap, as if holding something thin. Keep everything else exactly identical … Add nothing.

## Make the fingers really hold a piece (refs: composite, original hold shot)
> Edit Image 1. The hand must really hold the wood piece. Adjust ONLY the thumb and index finger so they physically pinch the upper end of the wood piece exactly the way Image 2 shows: the upper end of the piece is clamped between the index fingertip (behind the piece) and the thumb pad (pressing on the front face of the piece), the thumb overlapping the front of the piece, the fingertips slightly compressed by the grip, with a soft contact shadow where the fingers touch the wood. The piece itself must stay EXACTLY as in Image 1: same size, outline, angle, position, colour and pattern — do not recolour, darken, sharpen or restyle it. Keep every other pixel of Image 1 identical … Add nothing else.
Then paste back only the finger region (feathered polygon) onto the composite.

## Kling — static product, slow camera
> Animate the supplied start frame as ONE continuous photorealistic vertical luxury oud commercial shot. The open dark green leather box filled with agarwood stays completely still on the table. The camera makes a smooth, slow, steady push-in toward the box with a very gentle lateral glide from left to right, at an even speed through the whole shot, so warm light glints travel slowly across the gold clasp, the leather texture and the wood. Every wood piece stays exactly as in the start frame: same outline, size, colour, pattern and position; nothing moves. The ivory lid lining with the gold B, the word Beethoven and the Arabic lettering stays sharp and unchanged. No hands, no people. No morphing, no recolouring, no new objects. No smoke, text, speech or music. End in a clean stable hold.
negative: `moving chips, morphing wood, recolouring, extra boxes, hands, changed lettering, text distortion, smoke, text, subtitles, warping, flicker`
Package shots: add "exactly three boxes … no fourth box", "smoke only from inside the mabkhara's bowl".

## Kling — hand holding a piece (start = end keyframe = same image)
> Natural close-up footage of a hand holding an agarwood piece above an open green box. The thumb and index finger keep the piece clamped in exactly the same grip for the whole shot; the piece never rotates, never turns, never lifts away. The hand makes only a tiny natural breathing movement, dipping the piece very slightly toward the box and back. The camera stays almost still with a barely perceptible drift. The held piece and all pieces in the box keep exactly the same shape, colour and pattern. Lettering on the lid lining stays sharp. Warm light. No ring, no jewellery, no new objects, no text, no speech or music.
negative: `lifting up, pulling away, piece rotating, piece turning sideways, piece thinning, piece edge-on, colour change, lighter piece, piece falling, ring, jewellery, morphing wood, chips moving, extra fingers, changed lettering, text, warping, flicker`

## Kling — hand moves a piece (overhead tray)
> Natural overhead footage of an oud merchant's hands selecting agarwood on an engraved brass tray. The right hand slowly lowers the wood piece it holds and places it on the white cloth next to the other three, adjusting it slightly with a fingertip before letting go. The left hand rests on the tray edge with small natural breathing movements. Smooth, slow, realistic human movement with weight and gentle easing … Every wood piece keeps exactly the same dark brown-grey colour, pattern, size and shape as in the start frame; the piece in the hand is exactly the same colour as the pieces on the tray and cloth throughout. Untouched pieces do not move … No ring, no jewellery …
Generate ONCE (5 s; client rule: no re-rolls) with start = approved still; cut the 1.9 s window of the actual move.

## Empty open box for the master heap (any new scene with the box) — refs: approved box still + scene idea
> Image 2 is the exact box to use: dark green textured leather box, gold rectangular clasp in the middle of the front, lid open upright, ivory satin lid lining with the gold B monogram, the word Beethoven and the Arabic lettering exactly as in Image 2, cream satin inner tray. The box is OPEN and EMPTY: the clean cream satin inner tray is fully visible, nothing inside it. Same box proportions, colours and details as Image 2. <scene description: table, light, other objects>. Add nothing inside the box.
Then fill it locally with `box_masters.py place` — never ask the model to draw the oud.

## Empty box = approved fitted insert (refs: Image 1 = scene's empty plate, Image 2 = approved ad-1 empty box `box/e06.png`)
Client-approved look: "exactly this, always". 65 credits each; framing stayed pixel-identical in all 4 ad-2 scenes.
> Edit Image 1. Change ONLY the inside of the open green leather box so its empty interior looks exactly like the empty box interior in Image 2: a fitted, factory-made cream satin insert, perfectly taut and smooth, no wrinkles, no folds, no draped fabric; a flat cream floor panel and straight cream inner walls meeting it at clean, crisp creases with a soft shadow line, the padded bolster at the hinge in front of the lid, soft warm light gradient across the floor exactly like Image 2. The box stays open and empty. Keep everything else in Image 1 exactly identical: same camera angle and framing, <every object in the scene>, the lettering printed on the lid lining exactly as in Image 1 (do not copy the lettering from Image 2) ... Add nothing.
