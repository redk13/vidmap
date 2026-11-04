#!/bin/bash
set -euo pipefail

# Concatenate the 16 GitHub Actions video chunks (all 30fps, H.264, muted).
rm -f list.txt video.mp4 mix.wav tokyo-v9-full.mp4
for i in $(seq 0 15); do
  test -s "parts/part-$i.mp4"
  printf "file 'parts/part-%s.mp4'\n" "$i" >> list.txt
done
ffmpeg -y -v error -f concat -safe 0 -i list.txt -c copy video.mp4

# Generate VO + exact audio_mg.py whispered pad; no pre-made music beds.
python scripts/mix_full_audio.py --output mix.wav

# Deliverable encode is performed on GitHub Actions; CRF 23 preserves map/text clarity
# while keeping the downloaded artifact manageable. Audio remains AAC 192 kb/s.
ffmpeg -y -v error -i video.mp4 -i mix.wav \
  -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart -t 422.833333 \
  tokyo-v9-full.mp4

ffprobe -v error \
  -show_entries format=duration,size,bit_rate \
  -show_entries stream=codec_name,width,height,nb_frames,r_frame_rate \
  -of default=noprint_wrappers=1 tokyo-v9-full.mp4
ls -lh tokyo-v9-full.mp4
