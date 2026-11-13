# Reel 01 oud fill (approved approach: LOW, covering the floor, every visible piece whole)
python ../edit/low_quad.py "<rim quad BL BR FR FL>" 0.10 0.06   -> lowered placement quad (s11: 0.08 0.05)
box_masters.py place <raw> <filled> "<lowered quad>" --clip_quad "<rim quad>" --master <m> [--mirror] [--hide_side l|r]
   --quad_only --wall_px 3 --edge 2 --tol 5 --relight 1.0 --front_hide --ring 0 --finish
| still | rim quad | master | flags |
|---|---|---|---|
| s02 | 617,1683 1294,1767 1050,1967 172,1839 | beethoven_04 | --mirror --hide_side r |
| s06 | 552,1325 907,1277 1062,1487 690,1612 | beethoven_04 | --hide_side l |
| s07 | 129,1988 583,1954 783,2133 262,2204 | beethoven_04 | --hide_side l |
| s10 | 542,1608 1000,1608 1058,1808 500,1808 | beethoven_04 | (frontal) |
| s11 | 686,1814 1038,1850 931,1958 626,1928 | beethoven_0708 | --hide_side r, lowered 0.08/0.05 |
All: "side/back cut px: 0" (no piece cut where the viewer can see a rim). Then edit/make_finals.py for the names.
