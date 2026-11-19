#!/bin/zsh
O="$HOME/Movies/CS Funda/scamguard"; E="$HOME/Movies/CS Funda/commerceguard_ep2"
r() { (cd "$1" && npx hyperframes render --quality delivery --output "$2" > render.log 2>&1) && echo "done $(basename $2)" || echo "FAILED $(basename $2)"; }
r ~/Projects/ScamGuard/video/film "$O/ScamGuard_YouTube_1080p.mp4"
for n in 1 2 3; do r ~/Projects/ScamGuard/video/reels/part$n "$O/ScamGuard_Reel_Part${n}of3.mp4"; done
r ~/Projects/ScamGuard/video/full_vertical "$O/ScamGuard_Full_Vertical_Reel.mp4"
r ~/Projects/CommerceGuard/video_ep2/full_vertical "$E/CommerceGuard_Ep2_Full_Vertical_Reel.mp4"
# loudness: -14 LUFS, -1.5 dBTP, two-pass, video untouched
for f in "$O"/ScamGuard_*.mp4 "$E/CommerceGuard_Ep2_Full_Vertical_Reel.mp4"; do
  j=$(ffmpeg -nostats -i "$f" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  mi=$(echo $j | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
  ffmpeg -v error -y -i "$f" -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11:${mi}:linear=true" -c:a aac -b:a 192k -ar 48000 "${f%.mp4}._tmp.mp4" && mv "${f%.mp4}._tmp.mp4" "$f" && echo "normalised $(basename $f)"
done
