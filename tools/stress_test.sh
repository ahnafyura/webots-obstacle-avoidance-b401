#!/usr/bin/env bash
# Uji ketahanan: 8 posisi awal x DURASI detik. Mode eksplorasi: kebaruan (default) atau acak.
# Pemakaian: tools/stress_test.sh [durasi] [mode] [folder]
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DUR="${1:-600}"
MODE="${2:-kebaruan}"
OUT="${3:-$ROOT/logs/stress_$MODE}"
STARTS=("-2.0,-2.0,0.785" "2.1,1.0,-2.3" "0.0,1.2,0.0" "2.0,-0.8,3.14" "-2.0,1.9,-0.5" "-0.6,-0.1,1.57" "-0.5,-2.1,0.0" "1.45,0.35,2.0")
# set posisi awal kedua untuk validasi: STARTS_SET=2
if [ "${STARTS_SET:-1}" = "2" ]; then
  STARTS=("-2.1,0.6,0.0" "0.0,-1.1,1.57" "1.1,-0.9,2.5" "-1.0,0.0,-1.0" "0.3,0.9,1.0" "2.15,-1.0,1.57" "-0.9,-2.1,1.0" "0.5,2.1,0.0")
fi
mkdir -p "$OUT"
i=0
for s in "${STARTS[@]}"; do
  i=$((i+1))
  ( OA_ROS=0 OA_EXPLORE="$MODE" EVAL_START="$s" OA_SEED="$((${SEED_BASE:-400}+i))" \
      "$ROOT/tools/run_test.sh" "$DUR" "$OUT/run_$i" > "$OUT/run_$i.log" 2>&1 ) &
  if (( i % 4 == 0 )); then wait; fi
done
wait
python3 - "$OUT" "$MODE" "${STARTS[@]}" <<'PY'
import json, sys, os
d, mode, starts = sys.argv[1], sys.argv[2], sys.argv[3:]
print(f"mode={mode}")
print(f"{'run':4} {'start (x,y,yaw)':18} {'jarak':>6} {'tabrakan':>8} {'jatuh':>5} {'clear_min':>9} {'coverage':>8}")
for i, s in enumerate(starts, 1):
    r = json.load(open(os.path.join(d, f"run_{i}", "summary.json")))
    print(f"{i:<4} {s:18} {r['jarak_tempuh_m']:6.1f} {r['tabrakan']:8d} {r['jatuh']:5d} {r['clearance_min_m']:9.3f} {r['coverage_persen']:7.1f}%")
PY
