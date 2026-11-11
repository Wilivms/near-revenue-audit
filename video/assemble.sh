#!/usr/bin/env bash
# Encodes one file per scene from the frames, joins them without re-encoding, adds the voice.
set -euo pipefail
F=${1:?frames dir}; OUT=${2:-video/demo.mp4}
list=$F/list.txt; : > "$list"
for d in "$F"/s[0-7]; do
  n=$(basename "$d")
  ffmpeg -v error -y -framerate 30 -i "$d/%05d.jpg" -c:v libx264 -crf 18 -preset veryfast -pix_fmt yuv420p -r 30 "$F/$n.tmp.mp4"
  mv "$F/$n.tmp.mp4" "$F/$n.mp4"; echo "file '$F/$n.mp4'" >> "$list"
done
ffmpeg -v error -y -f concat -safe 0 -i "$list" -c copy "$F/video.mp4"
ffmpeg -v error -y -i "$F/video.mp4" -i video/voice.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -af apad -shortest "$F/demo.tmp.mp4"
mv "$F/demo.tmp.mp4" "$OUT"; ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
