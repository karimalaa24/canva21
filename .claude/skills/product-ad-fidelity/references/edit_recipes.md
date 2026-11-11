# Edit recipes (measured, reusable)

## Cut list of a reference ad
```python
cap=cv2.VideoCapture(f); prev=None; i=0; cuts=[]
while True:
    ok,im=cap.read();  # ...
    g=cv2.resize(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY),(108,192)).astype(float)
    if prev is not None and np.abs(g-prev).mean()>20: cuts.append(i)
    prev=g; i+=1
```
Scene frame counts = differences between cuts. Rebuild on exactly these counts; verify the new edit gives the
same cut list.

## Caption timing from a burned-in reference
Per frame: yellow = R>225 & G>180 & B<100 near dark outline pixels; white = min(RGB)>235 near outline.
Print a line whenever the yellow box changes → word start times, line y, which word is highlighted.
Read the words themselves from crops of the caption band every 0.25-0.5 s.

## New voiceover on an existing ad (ad 1 + ad-3 voice)
1. Cut list of the video that carries the new voice → new scene lengths.
2. Each scene of the approved ad is re-cut to its new length from the SAME source clip (more/less of the clip,
   never time-stretched unless the clip is too short).
3. Scenes that exist only in the new video (burner close-up) → search the Magnific project for the clean clip.
4. Props that appear in the new video's scenes → add in the still (nano-banana) or `track_insert.py`.
5. Captions: same style as the approved ad, new words/timings measured from the new video.

## Pauses between sentences (client: "sentences too fast")
`pace_voice.py gaps` → choose sentence ends inside silences; `insert` 0.3-0.4 s there, 0.2 s breaths.
Each scene grows by the pauses inside it; stretch with `minterpolate` (≤ 1.2×); shift effect times and caption
times with the time map; keep a caption on screen through the pause after it.

## Remove a phrase from the voice (ad 2: "ومبخرة خشبية هدية")
`pace_voice.py cut ad.mp4 voice.m4a 11.40 13.333`, then shorten the scenes after it and shift all later
caption/effect times by the cut length.

## Props into clips (no regeneration)
- Same framing still with the prop → `track_insert.py clip out --still prop.png --poly "..."`.
- Flat prop from another video (gift card) → quad mode with `--track` = the plane it rests on (lid lining).
- Drift check: LK on points inside vs around the prop; median < 4 px is invisible.

## Rebuild a delivered ad from its clean Kling clips (ad 5)
1. Match every scene of the delivered video to its clip: NCC of 135×240 grey frames (ignore the caption band)
   against every frame of every project clip → clip id + frame index at scene start / mid / end.
2. Re-cut from the clean clips on the same scene times (real frames only, 24→30 by frame picking).
3. Line on/off times of the old captions: per caption band, white / gold pixel columns per frame.
4. Silences in the voice (`ebur`/RMS per 50 ms) → cut dead air, keep a pop-only section's audio free to redesign.
5. Overlay (captions, cards, pills, logos) on the clean base, loudnorm two-pass to -14 LUFS / -1.5 dBTP.
Scripts: `oud-fix5/base5.py` (scenes, free zooms, product lift) + `oud-fix5/titles5.py` (captions, review cards, pills, gift badge, tabby/tamara).
