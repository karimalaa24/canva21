# Reel 03 — "وش هالطيب؟" — delivered 17 Nov 2026
- VO: client Lahajati take ad-paced (`audio/vo_ad_paced.wav`, 37.7 s), reel 38.7 s, -14 LUFS.
- Room: camel majlis (Magnific, `references/room_master_magnific.png`), 9 stills `images/*_final.png`.
- Oud: whole real pieces only (`edit/whole_fill.py --len 0.38`, `edit/fix_specks.py`), no heap; wordmarks `edit/make_finals.py`.
- Kling 3.0 1080p, one take each, start keyframe only: S01 4 s (smoke), S02 4 s, S07 6 s, S10 5 s, S11 6 s (`clips/`, raw in `clips/raw/`).
  S06 / S08 / S09 local still motion.
- Reviews: R3A full crop with the last line revealed at «ويسألوني», then R3B; no captions over screenshots.
- Graphics: ٣ أَوْقِيَّات / + ٣ هدية, secret-gift badge, tabby/tamara, اطلب الآن; pops on all (`audio/pop_times.json`).
- Music: approved heritage track (Reel 01), -20/-28 dB. Build: `python edit/build_reel.py out.mp4 --clips [--clean] [--audio wav]`.
- Exports: `exports/reel03_FINAL_MUSIC.mp4`, `reel03_FINAL_NO_MUSIC.mp4`, `reel03_CLEAN_no_captions.mp4` (music mix).
- Credits: stills 715 + Kling 2,250 = 2,965.
- Client review: scenes 5 (P03) and 6 (P04/S07) oud too busy / near the rims -> refilled (whole_fill len 0.38, cov 0.10, lower kf/kb, l2 0-0.1; P03 hide l seed 4, P04 hide l seed 2 l2 0.1); S07 Kling clip keeps its motion, new oud tracked in with KLT on the box body (edit/track_oud.py). Free.
- Scene 5 v2: right wall shows its INNER face at this angle -> fill quad right edge moved to the floor line (872,1290 / 1030,1505), seed 2.
- Scene 5 v3: right side + gaps filled (quad right edge 878,1288 / 1040,1505, cov 0.015, l2 0, seed 2) — flat, no climb on the inner wall.
- Scene 6 (S07): tracked oud slid against the box (client) -> re-animated in Kling from the new P04 still (6 s, straight push-in only, 540 cr). Reel 03 total: 3,505.
