#!/bin/sh
# Contact-process seed sweep (research-rl-ai.md §2.1/§2.2, step 1).
# Regenerates contact.cfg across infection weights and sweeps seeds.
# Emits CSV on stdout: lambda,wi,wr,seed,events,score,extinct
#   events  = applied rules until quiescence or budget (extinction step)
#   score   = final population - 1 (see contact.cfg)
#   extinct = 1 iff no A remained (score == -1)
# Usage: ./sweep.sh [SEEDS=30] [BUDGET=20000] > results.csv
#        WR and WI_LIST override the swept weights, e.g.
#        WR=16 WI_LIST="5 6 7 8 9 10" ./sweep.sh 50 > fine.csv
set -e
cd "$(dirname "$0")"
SEEDS=${1:-30}
BUDGET=${2:-20000}
BIN=../../zahradnice-headless
[ -x "$BIN" ] || BIN=../../zahradnice
WR=${WR:-8}
WI_LIST=${WI_LIST:-"1 2 3 4 5 6 8"}
SCREEN=17,32
INPUT=$(printf 'T%.0s' $(seq 1 "$BUDGET"))
TMP=$(mktemp --suffix=.cfg)
trap 'rm -f "$TMP"' EXIT

echo "lambda,wi,wr,seed,events,score,extinct"
for WI in $WI_LIST; do
  sed "s/   1 4\$/   1 $WI/; s/   -1 8\$/   -1 $WR/" contact.cfg > "$TMP"
  for seed in $(seq 1 "$SEEDS"); do
    "$BIN" "$TMP" --seed "$seed" --screen "$SCREEN" \
        --input "$INPUT" --max-steps "$BUDGET" 2>&1 >/dev/null \
      | sed -n 's/^Headless run: \([0-9]*\) events, final score=\(-\{0,1\}[0-9]*\).*/\1 \2/p' \
      | awk -v wi="$WI" -v wr="$WR" -v s="$seed" \
          '{printf "%.4f,%d,%d,%d,%d,%d,%d\n", wi/wr, wi, wr, s, $1, $2, ($2==-1)}'
  done
done
