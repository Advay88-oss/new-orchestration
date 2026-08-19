#!/bin/bash
CH=31098616-3d0b-4202-86b4-96bfd36680cd
SCOUT=66c2fe9d97ee7ae0af92a1a9c2c8ac64a8716966cf25495706d85f418757ddd6
for i in $(seq 1 30); do
  out=$(buzz messages get --channel $CH --limit 15 2>/dev/null | python -c "
import sys,json
try: d=json.load(sys.stdin)
except Exception: raise SystemExit(0)
for m in d:
    if m['pubkey']=='$SCOUT' and m['created_at']>1786679547:
        print('SCOUT_POSTED', m['created_at'], m['id'])
        break
")
  if [ -n "$out" ]; then echo "$out"; exit 0; fi
  sleep 20
done
echo "SCOUT_TIMEOUT"
