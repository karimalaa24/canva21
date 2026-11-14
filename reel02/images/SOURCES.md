# Reel 02 stills — Magnific project "Beethoven Reel 02 Confidence", Nano Banana 2.1, 9:16, 2k (1536×2752), 65 cr each
| still | creation | references used | local work |
|---|---|---|---|
| room master (`references/room_master_magnific.png`) | s7oWMool8e | style: Reel 01 majlis (If6gJw6tvE) | — |
| P01 closed box | nVju5LrYQD | room, three boxes, lid artwork | none needed (BeetHoven + Arabic correct) |
| P02 mabkhara + smoke | ksD2Wev16B | room, gold mabkhara | — |
| P03 open box | VXU5jO1MMU | room, approved empty box, lid artwork | oud fill: beethoven_0708 --mirror, hide r |
| P04 three boxes 45° | jUXnVmgLD0 | room, three boxes, empty box | oud fill beethoven_09 hide l; 3 wordmarks Beethoven→BeetHoven |
| P05 quantity low | 6AHIfrEiJO | room, three boxes, empty box | oud fill beethoven_09 --mirror hide r; 3 wordmarks |
| P06 gifts flat-lay | LwBYMfgswO | room, burner+Moroki | — |
| P07 bag | LwBYMEUswO | room, bag, boxes, mabkhara | — (bag artwork correct; box lids at grazing angle) |
| P08 full offer | huRw4VnvqL | room, full offer, empty box | oud fill beethoven_09 hide l — OPEN: bag (ribbon handles, two-line Arabic, Beethoven), lid wordmarks |
| P09 closing | s7oWDH6l8e | room, full offer, empty box | oud fill beethoven_09 hide l — OPEN: same as P08 + too close to P08's angle |
| PLATE | YMLQK6wWeC | room, gold mabkhara | — (centred, unlit) |
Rim quads (BL BR FR FL), lowered with `edit/low_quad.py Q 0.06 0.035`, then `box_masters.py place --clip_quad Q --quad_only --wall_px 3 --edge 2 --tol 5 --relight 1.0 --front_hide --ring 0 --finish`:
P03 614,1703 1302,1764 1021,1969 177,1841 · P04 248,1826 644,1694 831,1914 446,2074 · P05 1000,1888 1395,1900 1250,1983 868,1928 ·
P08 362,2076 662,2062 722,2162 456,2206 · P09 284,2132 606,2087 676,2205 394,2254 — side/back cut px: 0 on all.
Wordmarks: `edit/wordmarks.py` + `edit/wordmarks.json` (source = BeetHoven on P03 lid lining).

## v2 (14 Nov) — client: one niche and one table in every still
Locked room = PLATE composition: walnut slat niche centred behind the table (one carved Sadu band, hidden glow), navy seating with ivory piping,
cream rug with Sadu border, square dark-walnut table with four straight legs. Every new still used the PLATE as Image 1.
Re-generated (v1 kept in images/v1/): P01 O6fXahIynm · P03 gOIV8o9SXO · P04 cplblVi0eP (first retake s7o0BX1l8e had a slab table -> rejected) ·
P07 YMLHjjuWeC · P08 tCiw6iFmZJ · P09 ov9g9k7829 (first retake 4Ru8EQ39Aa had two boxes, a goblet burner and a green lid lining -> rejected).
New rim quads: P03 649,1692 1240,1746 966,1888 273,1792 (beethoven_09 --mirror, hide r) · P04 236,1800 533,1726 668,1846 352,1940 (09, hide l) ·
P08 302,1914 550,1880 630,1956 400,2002 (09, hide l) · P09 290,1925 534,1891 650,1959 398,1999 (09, hide l). side/back cut px 0.
Lettering fixed locally (edit/wordmarks.json): P04 3 lids, P08 4 lids + bag word + bag line «فخامة سمو», P09 4 lids + bag word + bag two-line Arabic -> one small «فخامة سمو».
Credits: v1 715 + v2 520 = 1,235 on stills.
## P03 v3 (14 Nov) — client: box too big for the table
P03 re-generated at real scale (box ≈ 1/4 of the table width, table edges out of frame): gOIV5q4SXO, refs PLATE + P03 v2 + empty box + P04 (scale).
Rim quad 698,1710 1244,1736 999,1876 326,1789, beethoven_09 --mirror, hide r, side/back cut px 0. Lid BeetHoven correct (no fix needed).
Previous oversized version kept in images/v2/. Credits on stills: 1,235 + 65 = 1,300.
