#!/usr/bin/env bash
# Assemble a caption-free edit from scene clips, on the exact frame counts of the original ad,
# with mild deflicker on AI clips, and the ORIGINAL ad audio.
#
# usage: assemble.sh original_ad.mp4 out.mp4  clip1.mp4:FRAMES[:start_sec[:speed[:deflicker]]]  clip2 ...
#   FRAMES   = frames this scene occupies in the 30 fps ad (cut points * 30)
#   start    = where to start inside the clip (default 0)
#   speed    = setpts factor (1.25 when a 24 fps clip was laid frame-by-frame into 30 fps; default 1)
#   deflicker= 1 to apply ffmpeg deflicker (use on every Kling clip; default 1)
# example (Beethoven ad): hook.mp4:132:0:1.25:0 tray.mp4:57:1.15 box.mp4:144 closed.mp4:48:0.025:1:0 ...
set -euo pipefail
AD=$1; OUT=$2; shift 2
TMP=$(mktemp -d); i=0; : > "$TMP/list.txt"
for spec in "$@"; do
  IFS=: read -r f n ss sp df <<< "$spec"; ss=${ss:-0}; sp=${sp:-1}; df=${df:-1}; i=$((i+1))
  vf="setpts=PTS*${sp},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30"
  [ "$df" = 1 ] && vf="$vf,deflicker=size=9:mode=pm"
  ffmpeg -nostdin -v error -y -ss "$ss" -i "$f" -an -vf "$vf,format=yuv420p" -frames:v "$n" -c:v libx264 -crf 15 -preset slow "$TMP/s$i.mp4"
  got=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$TMP/s$i.mp4")
  [ "$got" = "$n" ] || echo "WARNING: $f gave $got frames, expected $n (clip too short?)" >&2
  echo "file '$TMP/s$i.mp4'" >> "$TMP/list.txt"
done
ffmpeg -nostdin -v error -y -f concat -safe 0 -i "$TMP/list.txt" -i "$AD" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
rm -rf "$TMP"
