#!/usr/bin/env bash
# Uji otomatis headless: menjalankan simulasi selama DURASI detik dan menyimpan log.
# Pemakaian: tools/run_test.sh [durasi_detik] [folder_log] [mode: fast|realtime]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEBOTS="${WEBOTS:-$(command -v webots || echo "$HOME/opt/webots/webots")}"
export EVAL_DURATION="${1:-180}"
export EVAL_LOG_DIR="$(realpath -m "${2:-$ROOT/logs}")"
MODE="${3:-fast}"
EXTRA="--no-rendering"
[ -n "${EVAL_SNAPSHOTS:-}" ] && EXTRA=""
MIN="--minimize"; [ -n "${EVAL_SNAPSHOTS:-}" ] && MIN=""
"$WEBOTS" --batch --mode="$MODE" $MIN $EXTRA --stdout --stderr \
  "$ROOT/worlds/obstacle_avoidance.wbt"
echo "Log tersimpan di $EVAL_LOG_DIR"
cat "$EVAL_LOG_DIR/summary.json"
