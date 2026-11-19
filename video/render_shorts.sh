#!/bin/zsh
while pgrep -f "render_all.sh" >/dev/null; do sleep 10; done
S="$HOME/Movies/CS Funda/scamguard/shorts"; E="$HOME/Movies/CS Funda/commerceguard_ep2/shorts"; mkdir -p "$S" "$E"
r() { (cd "$1" && npx hyperframes render --quality delivery --output "$2" > render.log 2>&1) && echo "done $(basename $2)" || echo "FAILED $(basename $2)"; }
r ~/Projects/ScamGuard/video/explain/1_tfidf "$S/ScamGuard_Short1_How_TFIDF_Decides.mp4"
r ~/Projects/ScamGuard/video/explain/2_embeddings "$S/ScamGuard_Short2_How_Embeddings_Read_Meaning.mp4"
r ~/Projects/ScamGuard/video/explain/3_transformer "$S/ScamGuard_Short3_Inside_A_Transformer.mp4"
r ~/Projects/ScamGuard/video/explain/4_llm "$S/ScamGuard_Short4_How_An_LLM_Decides.mp4"
for n in 1 2 3; do r ~/Projects/CommerceGuard/video_ep2/shorts/part$n "$E/CommerceGuard_Ep2_Short_Part${n}of3.mp4"; done
for f in "$S"/*.mp4 "$E"/*.mp4; do
  j=$(ffmpeg -nostats -i "$f" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  mi=$(echo $j | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
  ffmpeg -v error -y -i "$f" -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11:${mi}:linear=true" -c:a aac -b:a 192k -ar 48000 "${f%.mp4}._tmp.mp4" && mv "${f%.mp4}._tmp.mp4" "$f" && echo "normalised $(basename $f)"
done
