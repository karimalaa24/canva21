# Reel 03 — "وش هالطيب؟" — plan & cost (17 Nov 2026, prices verified live in Magnific)

Timing master: `audio/vo_ad_paced.wav` (client's Lahajati take, ad-paced on request: 43.9 s -> 37.7 s) + ~1.3 s closing hold ≈ 39 s.

| Beat | Time (s) | VO | Picture | Method |
|---|---|---|---|---|
| S01 | 0–3.3 | وش هالطيب؟ سؤال ودك تسمعه في مجلسك | P01 ready majlis + active gold mabkhara | **Kling 4 s** (live smoke) |
| S02 | 3.3–6.5 | تايجر بيتهوفن… للي يهتم بطيب ضيافته | P02 one open box, LOW real-piece oud | local slide (or Kling 4 s) |
| S03 | 6.5–10.3 | أنا رايح العزيمة… يجربونه | R3A1 on PLATE | edit |
| S04 | 10.3–12.8 | ويسألوني عن الخصم عشان يطلبون | R3A2 (same message) | edit |
| S05 | 12.8–15.0 | العود فواح بالمجلس من المغرب | R3B | edit |
| S06 | 15.0–17.5 | والحين، طيب مجلسك بهالعرض | P03 three boxes high angle | local pull-back |
| S07 | 17.5–23.0 | اطلب ثلاث… وخذ ثلاث أوقيات هدية | P04 three boxes low | local glide (or Kling 6 s) |
| S08 | 23.0–27.2 | مبخرة خشبية، أعواد موروكي، هدية سرية | P05 flat-lay + secret-gift badge | local overhead slide |
| S09 | 27.2–29.6 | كلها تجيك في كيس بيتهوفن الفاخر | P06 bag + 2 closed boxes (NO mabkhara — Reel 01 lesson) | local straight push |
| S10 | 29.6–33.7 | والشحن مجانا… تابي أو تمارا | P07 full offer + active gold mabkhara | **Kling 5 s** |
| S11 | 33.7–39.0 | اطلب عرض التايجر الحين… حديث المجلس | P08 closing hero + CTA | **Kling 6 s** |

## Credits (Nano Banana 2.1 2k = 65 / image; Kling 3.0 1080p = 90 / s)
| Item | Lean | Full |
|---|---|---|
| Room master + P01–P08 + PLATE (10 stills) | 650 | 650 |
| Kling P01 4 s + P07 5 s + P08 6 s | 1,350 | 1,350 |
| Kling P02 4 s + P04 6 s | — | 900 |
| Music (reuse approved heritage track) / pops / edit / oud fill / lettering | 0 | 0 |
| **Total** | **2,000** | **2,900** |
Balance before Reel 03: 13,681.

## Notes
- VO line 3 is recorded «أنا رايح العزيمة» (masculine); the screenshot (a woman) reads «انا رايحه لعزيمه». No caption is shown over the screenshot, so the card carries her exact words; re-record only if the client wants the feminine form.
- The client asked for the faster ad pace (per-phrase tempo, ~0.30 s gaps) — this overrides the prompt's "never change speech speed".

## Decisions
- 17 Nov: client approved the FULL plan (Kling also for P02 close box 4 s and P04 three boxes 6 s) = 2,900 credits.
- Room master generated (65): corner majlis, navy seating on two walls, tall walnut-slat niche with carved Sadu panel and hidden glow,
  small arched niche with one brass lantern, square walnut table with a deep plinth on a cream Sadu rug, greige plaster, light from upper left.
  `references/room_master_magnific.png` — waiting for client approval before the 9 dependent stills.
- Room v2 (65): client asked to change the colour to avoid repeating navy -> camel/sand seating, rust-terracotta Sadu cushions, warm cream plaster; geometry unchanged. room_master_magnific.png = v2 (v1 kept as room_master_v1_navy.png).
- 9 stills (585): P01-P08 + PLATE in the camel room; 5 boxes filled (beethoven_0708 low, side/back cut px 0); wordmarks fixed (edit/make_finals.py). Reel 03 spent so far: 715.
- P08 (client: oud too low): placement quad back corners raised 35 px (mound rising toward the back, front at the rim), clip = same, beethoven_0708 --mirror, back 0.02; side/back cut px 0.
- P08 v2 (client: 35 px too high on the right): back corners raised 20 px left / 10 px right — medium, even height.
- OUD v2 (client: heap quality poor, "use the real pieces we started with, not the heap"): all five boxes refilled with
  `edit/whole_fill.py` (only whole real cut-outs from box_masters/pieces, no heap master) + `edit/fix_specks.py`, then make_finals.
  Seeds: P02 1 (hide l) · P03 2 (r) · P04 2 (l) · P07 1 · P08 2 with back corners raised 20/10, kf 0.02 kb 0.01 (r). Visible cut px 0 on all.
  Previous heap versions kept in images/heap_v1/.
- OUD v3 (client: pieces a bit small): --len 0.38 (was 0.30) on all five boxes, same seeds; 0.45 too soft (pieces upscaled past their source resolution).
