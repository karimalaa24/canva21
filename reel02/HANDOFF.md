# Reel 02 — handoff (14 Nov 2026)

Spec: `reel02/PROMPT_REEL02_v2.md` (luxury → first incense → product → confidence → genuine repeat requests → offer → order).
Magnific project: **Beethoven Reel 02 Confidence**.

## Client decisions (this session)
- VO = client upload `audio/voice_over.mp3` (48.01 s). «من عود التايقر الفيتنامي درجة أولى» removed on purpose — not captioned.
  Caption «والحين، خذه بهالعرض» (client: خذه).
- Room: ONE niche (centred walnut slat niche, single Sadu band, hidden glow) and ONE square walnut table with four legs in every shot
  (client rejected v1 where niche/table changed). Locked from the review PLATE.
- P03: box at real scale on the table (client: v2 box too big).
- Oud: whole real pieces only, no cut heap (client). `edit/whole_fill.py`, pieces from the skill's `box_masters/pieces`.
- Customer photo + «رائحة جميلة» (crop of `references/reviews/source_1000395799.jpg`, no phone number) shown between R2A and R2B4;
  0.8 s silence added there (`audio/vo_pauses.json`, silence only, no stretch).

## Files
- Stills: `images/*_final.png` (sources, quads, seeds: `images/SOURCES.md`); older versions in `images/v1`, `v2`, `v3_heap`.
- Lettering fixes: `edit/wordmarks.py` + `edit/wordmarks.json` (BeetHoven from the first P03 lid; Arabic with Almarai-ExtraBold TTF).
- Kling: `clips/JOBS.md` (job ids, review). Raw takes `clips/raw/`; used clips `clips/S02,S08,S11,S12.mp4`
  (S08/S11 = products tracked back from the stills with `edit/track_products.py` + `edit/track_S08.json`, `track_S11.json`).
- Edit: `edit/build_reel.py out.mp4 --clips [--clean] [--audio wav]`; QA frames `--frames t1,t2,...`; pop times `--pops`.
- Audio: `edit/make_mixes.py END` → `audio/mix_music.wav`, `audio/mix_no_music.wav` (-14 LUFS, -1.5 dBTP, two-pass);
  music = Reel 01 approved heritage track (read-only), window in `audio/music_window.json`, -20 dB gaps / -28 dB under VO.
- Timing: `audio/vo_phrases.json` (19 phrases), `audio/pop_times.json`.

## Exports
- `exports/reel02_FINAL_MUSIC.mp4` — captions + graphics, VO + pops + music.
- `exports/reel02_FINAL_NO_MUSIC.mp4` — same picture, VO + pops.
- `exports/reel02_CLEAN_no_captions.mp4` — screenshots + physical branding kept, captions/pills/badge/logos/CTA off; music mix.

## Credits (Magnific, measured)
Room + stills: 1,300 (20 × 65). Kling 3.0 1080p: 2,340 (S02 4 s, S03 5 s — rejected, S08 5 s, S11 6 s, S12 6 s).
Music: 0 (reused). **Total Reel 02: 3,640.** Balance after: 13,831.

## Known limits
- Small background lids: BeetHoven repaired but soft at high zoom; Arabic correct but low detail.
- S03 is local still motion (Kling take turned the box). S12 uses a local counter-zoom to hide an invented ceiling/marble floor.
