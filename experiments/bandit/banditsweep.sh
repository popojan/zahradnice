#!/bin/bash
# Summit-experiment sweep: 6 season blocks (a b a b a b) x 30k events.
# Emits summary CSV on stdout; per-run series in series-<cfg>-s<seed>.csv
# Usage: ./banditsweep.sh [SEEDS=6] > summary.csv   (PAR=N, default 8)
set -e
cd "$(dirname "$0")"
SEEDS=${1:-6}
PAR=${PAR:-8}
TAG=${TAG:-}
CFGS=${CFGS:-"bandit bandit-nolearn"}
BIN=../../zahradnice-headless
BUDGET=180000
BLOCK=${BLOCK:-30000}
JOBD=$(mktemp -d)
trap 'rm -rf "$JOBD"' EXIT
python3 -c "import sys; b=int(sys.argv[1]); n=180000//(2*b); \
sys.stdout.write(('a'*b+'b'*b)*max(1,n))" "$BLOCK" > "$JOBD/in"

run_one() {
  local cfg=$1 seed=$2
  local tr="$JOBD/$cfg.$seed.trace" sc="$JOBD/$cfg.$seed.screen"
  local ev
  ev=$("$BIN" "$cfg.cfg" --seed "$seed" --screen 33,64 \
      --input "@$JOBD/in" --max-steps "$BUDGET" \
      --trace "$tr" --dump-screen "$sc" 2>&1 >/dev/null \
    | sed -n 's/^Headless run: \([0-9]*\) events, final score=\(-\{0,1\}[0-9]*\).*/\1,\2/p')
  python3 bandit_stats.py "$cfg.cfg" "$tr" --sample 1000 \
    > "series-$TAG$cfg-s$seed.csv" 2>/dev/null
  python3 - "series-$TAG$cfg-s$seed.csv" "$sc" "$cfg" "$seed" "$ev" \
    <<'PYEOF' > "$JOBD/r.$cfg.$seed"
import csv, sys
series, screen, cfg, seed, ev = sys.argv[1:6]
last = list(csv.DictReader(open(series)))[-1]
body = "\n".join(open(screen, encoding="utf-8").read().splitlines()[1:])
ok = (body.count("x") == int(last["flx"]) and body.count("y") == int(last["fly"])
      and body.count("⠋") == int(last["tokx"])
      and body.count("⠙") == int(last["toky"]))
print(",".join([cfg, seed, ev, last["score"], last["tokx"], last["toky"],
                "ok" if ok else "MISMATCH"]))
PYEOF
  rm -f "$tr"
}

echo "cfg,seed,events,scoretail,score,tokx,toky,recon"
for cfg in $CFGS; do
  for seed in $(seq 1 "$SEEDS"); do
    run_one "$cfg" "$seed" &
    while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do wait -n; done
  done
done
wait
for cfg in $CFGS; do
  for seed in $(seq 1 "$SEEDS"); do cat "$JOBD/r.$cfg.$seed"; done
done
