# Reel 01 oud fill (approved approach: LOW, covering the floor, every visible piece whole)
LQ=$(python ../edit/low_quad.py "<rim quad BL BR FR FL>" 0.06 0.035)        # placement quad lowered toward the floor
box_masters.py place <raw> <filled> "$LQ" --clip_quad "<rim quad>" --master beethoven_0708 [--mirror] [--hide_side l|r] \
   --quad_only --wall_px 3 --edge 2 --tol 5 --relight 1.0 --front_hide --ring 0 --finish
--hide_side = the side wall whose OUTER leather face the camera sees (the other side shows its cream inner face: pieces stay whole there).
| still | rim quad | flags | side/back cut px |
|---|---|---|---|
| s02 | 617,1683 1294,1767 1050,1967 172,1839 | --mirror --hide_side l | 0 |
| s06 | 552,1325 907,1277 1062,1487 690,1612 | --hide_side r | 0 |
| s07 | 129,1988 583,1954 783,2133 262,2204 | --hide_side r | 0 |
| s10 | 542,1608 1000,1608 1058,1808 500,1808 | (frontal) | 0 |
| s11 | 686,1814 1038,1850 931,1958 626,1928 | --mirror --hide_side l | 0 |
Then `python edit/make_finals.py` (BeetHoven wordmarks, bag Arabic).
