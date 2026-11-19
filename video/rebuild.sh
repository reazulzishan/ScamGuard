#!/bin/zsh
# Build YouTube + 3 reels, grade footage, copy voice, run checks.
cd ~/Projects/ScamGuard/video/film
python3 build_sg.py 2>&1 | grep -E "scenes|!|Trace"
python3 build_sg.py reels 2>&1 | grep -E "scenes|!|Trace"
python3 build_sg.py full 2>&1 | grep -E "scenes|!|Trace"
for P in ~/Projects/ScamGuard/video/film ~/Projects/ScamGuard/video/reels/part{1,2,3} ~/Projects/ScamGuard/video/full_vertical; do
  cp ~/Projects/ScamGuard/video/vo/*.wav $P/assets/vo/ 2>/dev/null
  for k in 1 2 3; do cp ~/Projects/ScamGuard/video/vo/F$k.wav $P/assets/vo/R$k.wav; done
  (cd $P && for f in compositions/[shxt]*.html; do for id in $(grep -o 'id="[a-z0-9_-]*v" class="clip" src="assets/footage/[a-z_]*' "$f" | grep -v run_timelapse | sed 's/id="\([^"]*\)".*/\1/'); do
     npx hyperframes media-treatment --project . --file "$f" --selector "#$id" --grading '{"preset":"warm-daylight","intensity":0.6}' --apply --json >/dev/null 2>&1; done; done
   npx hyperframes check --json 2>/dev/null | python3 -c "
import json,sys;d=json.load(sys.stdin);print('$(basename $P) ok',d.get('ok'))
for k in ('lint','runtime','layout','contrast','audio'):
  for f in d[k].get('findings',[]):
    if f.get('severity')!='info': print(' ',k,f['code'],f.get('time'),f.get('selector'),f['message'][:90])" | head -8)
done
