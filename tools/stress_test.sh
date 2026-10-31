#!/usr/bin/env bash
# Uji ketahanan: beberapa posisi awal & seed acak, masing-masing DURASI detik.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DUR="${1:-300}"
STARTS=("-1.2,-1.2,0.785" "1.2,1.2,-2.3" "0,0.7,0" "1.2,-0.5,3.14" "-1.2,1.2,-0.5" "0.6,-0.5,1.57" "-0.3,-1.2,0" "0.9,0.3,2.0")
i=0
for s in "${STARTS[@]}"; do
  i=$((i+1))
  ( EVAL_START="$s" OA_SEED="$((400+i))" "$ROOT/tools/run_test.sh" "$DUR" "$ROOT/logs/stress/run_$i" > "$ROOT/logs/stress/run_$i.log" 2>&1 ) &
  mkdir -p "$ROOT/logs/stress"
  if (( i % 4 == 0 )); then wait; fi
done
wait
python3 - "$ROOT/logs/stress" "${STARTS[@]}" <<'PY'
import json, sys, os
d = sys.argv[1]; starts = sys.argv[2:]
print(f"{'run':4} {'start (x,y,yaw)':20} {'jarak':>7} {'tabrakan':>8} {'clear_min':>9} {'coverage':>8}")
for i, s in enumerate(starts, 1):
    p = os.path.join(d, f"run_{i}", "summary.json")
    r = json.load(open(p))
    print(f"{i:<4} {s:20} {r['jarak_tempuh_m']:7.1f} {r['tabrakan']:8d} {r['clearance_min_m']:9.3f} {r['coverage_persen']:7.1f}%")
PY
