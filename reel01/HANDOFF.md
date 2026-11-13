# Reel 01 — handoff (state on 13 Nov 2026)

Continue this campaign from here. Read in this order:
1. `.claude/skills/product-ad-fidelity/SKILL.md` + `references/lessons.md` (all rules, incl. ad-4/ad-5 lessons)
2. this file
3. `reel01/references/SOURCE_AUDIT.md`, `reel01/audio/vo_script_locked_2026-11-13.txt`,
   `reel01/edit/subtitle_phrases.txt`, `reel01/edit/provisional_timeline.json`
The full production spec is the client's "BEETHOVEN — REEL 01: EXPECTATION → EXPERIENCE → OFFER v1.1"
(expectation → product ID → same customer's result + packaging → 2 more reviews → offer → order).

## Client decisions (locked)
- Reply to the client in short Egyptian Arabic, no jargon; show stills before any Kling credit; one Kling take per scene; report credits.
- Brand wordmark everywhere = **BeetHoven** (script). Arabic = فخامة سمو للطيب (lids), فخامة سمو (small line on the bag).
- NEW majlis = client photo `references/room_master_new_majlis.jpg` (Magnific upload "reel01_room_master_new_majlis").
- New camera angles approved (batch in `qa/stills_final_v1.jpg`).
- Full-offer / bag / closing scenes KEEP the gold mabkhara with smoke (client OK'd, overrides the spec's no-smoke).
- Oud: approved heap only via `box_masters.py place ... --master beethoven_04 --relight 1.0 --front_hide --ring 0 --finish --edge 4`;
  no extra loose pieces, every visible piece whole, filled to the front rim (S02 used `--mirror`).
- Reviews in THIS reel: one at a time, phrase-led, narrator audible (spec) — not the ad-5 pile.
- Carry over from ad 5: product light lift, big readable review cards, pop SFX on card entrances and on tabby/tamara,
  -14 LUFS; music only if wanted and very low (-22 dB gaps / -30 dB under voice).

## Done
- Reviews (`reviews/`): R01A 521×63, R01B 521×220 (re-cut from `R01_full_conversation_source.jpg`, both messages; packaging
  message starts ≈ y 108 → reveal mask), R02 611×236, R03 496×114. Never retype/redraw them.
- Stills (`images/*_final.png`, 1536×2752, Nano Banana 2.1 2k in the Magnific project):
  S02 close open box · S06 three boxes high angle · S07 three boxes low · S08 burner + Moroki top-down flat-lay ·
  S09 bag · S10 full offer · S11 closing hero. `_raw` = Magnific output (empty boxes), `_filled` = heap added,
  `_final` = heap + wordmark fixes (`edit/fix_wordmark.py`, free local fix: inpaint old word, paste the correct
  BeetHoven cut from S02's lid, render Arabic with Almarai-ExtraBold `oud-fix5/fonts/`).
- Credits spent on this reel: 585 (9 stills × 65). Account ≈ 20,750 left after that.

## Next
1. WAITING: the Lahjati VO of the 13-Nov script (revised bridge "وَالْحِين، التَّايْقَر يِجِيك بِهَالْعَرْض" + closing).
   Measure markers from the real waveform; never speed up / cut words.
2. Upload the `_final` stills to Magnific (request_upload → PUT → finalize), then Kling 3.0, 1080p, START keyframe only,
   duration = measured scene length + 0.5 s, camera moves / products still, smoke only from the mabkhara bowl.
   Estimate 2,900–3,300 cr (90 cr/s). Show the exact per-scene cost to the client first.
   S06 can be a free local pull-back on the still (no smoke there).
3. Edit: real Kling frames at 30 fps (no minterpolate), captions = Section-3 words (white/gold two-line, Almarai),
   review crops large in clear negative space, R01B reveal at "والتغليف", offer graphics by phrase
   (٣ أَوْقِيَّات / + ٣ هدية / مبخرة خشبية / أعواد موروكي / وهدية سرّية / الشحن مجّانًا / tabby+tamara / اطلب الآن).
   Reusable code: `oud-fix5/titles5.py` (captions, pills, logos, pops), `oud-fix5/base5.py` (scene builder + lift).
4. Deliver: captioned MP4 1080×1920 30 fps + clean version, commit to `reel01/exports/`.
