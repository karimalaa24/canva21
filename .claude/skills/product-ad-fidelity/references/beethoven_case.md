# Reference project: Beethoven oud ad (26.2 s, 1080×1920, 30 fps)

Magnific project folder (Anwar Saeed account): oud ad project; final files in repo `oud-fix/final/`.

## Timeline of the final edit
| Frames @30 | Time (s) | Scene | Source |
|---|---|---|---|
| 0-131 | 0.00-4.40 | hand holding piece (untouched) | Kling clip, 24 fps laid at 30 fps → setpts ×1.25 |
| 132-188 | 4.40-6.30 | tray, hand places piece on cloth | Kling 5 s, window 1.15-3.05 s |
| 189-332 | 6.30-11.10 | open box, one continuous shot (merged two scenes) | Kling 5 s |
| 333-380 | 11.10-12.70 | closed box (untouched) | source clip from 0.025 s |
| 381-527 | 12.70-17.60 | full offer | Kling 5 s |
| 528-624 | 17.60-20.83 | package push-in | Kling 4 s |
| 625-682 | 20.83-22.77 | package glide | Kling 3 s |
| 683-785 | 22.77-26.20 | final hero | Kling 4 s |

## Approved parameters
- Pieces: 9 cut-outs from 2 WhatsApp photos (960×1280). Piece length = 1/3 of box front edge, elong 1.12.
- Target colour: L 53.3 ± 26.5, a(L)=0.06L+129.8, b(L)=0.14L+130.2 (OpenCV LAB); LM −4, CK 0.25;
  tray extra DA +1.5, DB +4; scatter light falloff clipped to 0.8-1.0.
- Box fills: cov 0.05-0.07, l2 0.30, l3 0.10, backt 0.6 (scene 6/9), 0.65-0.7 (scene 7/8), leftfill 3-6.
- Captions: Almarai 800, line1 80 px white gradient, line2 84 px gold gradient, layouts top (335/447),
  bottom (1490/1608), final (205/313); word fade 0.22 s, rise 16 px; group fade-out 0.18 s.
- Gift badge 470×165, burgundy (128,26,42)→(66,10,20), gold border, gift icon + Beethoven logo lifted
  from the lid lining; pops at 19.62 s with the word "سرية" (scene 7). tabby 24.6 s, tamara 24.8 s.

## Costs (credits, approx.)
Stills/edits ≈65 each; Kling ≈90/s. Whole job ≈ 9-10k credits including ~2k of rejected
prompt-only attempts — the real-cut-out method would have saved most of those.
