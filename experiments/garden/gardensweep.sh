#!/bin/bash
# Garden MVP sweep: three season regimes x seeds, shares as readout.
# Usage: ./gardensweep.sh [SEEDS=6] > summary.csv
set -e
cd "$(dirname "$0")"
SEEDS=${1:-6}
PAR=${PAR:-8}
BIN=../../zahradnice-headless
CFG=${CFG:-garden.cfg}
BUDGET=180000
JOBD=$(mktemp -d)
trap 'rm -rf "$JOBD"' EXIT
CONDS=${CONDS:-"const p30 p90"}
for cond in $CONDS; do
  case $cond in
    const) python3 -c "print('a'*180000, end='')" ;;
    p*) B=${cond#p}000
      python3 -c "import sys; b=int(sys.argv[1]); n=180000//(2*b); \
sys.stdout.write(('a'*b+'b'*b)*max(1,n))" "$B" ;;
  esac > "$JOBD/in.$cond"
done

run_one() {
  local cond=$1 seed=$2
  local tr="$JOBD/$cond.$seed.trace" sc="$JOBD/$cond.$seed.screen"
  "$BIN" "$CFG" --seed "$seed" --screen 33,64 \
      --input "@$JOBD/in.$cond" --max-steps "$BUDGET" \
      --trace "$tr" --dump-screen "$sc" >/dev/null 2>&1
  python3 garden_stats.py "$CFG" "$tr" --sample 1000 \
    > "series-$cond-s$seed.csv" 2>/dev/null
  python3 - "series-$cond-s$seed.csv" "$sc" "$cond" "$seed" \
    <<'PYEOF' > "$JOBD/r.$cond.$seed"
import csv, sys
series, screen, cond, seed = sys.argv[1:5]
last = list(csv.DictReader(open(series)))[-1]
body = "\n".join(open(screen, encoding="utf-8").read().splitlines()[1:])
ok = (body.count("n") == int(last["popn"])
      and body.count("i") == int(last["popi"])
      and body.count("p") == int(last["popp"])
      and body.count("⠃") == int(last["tokix"])
      and body.count("⠘") == int(last["tokiy"])
      and body.count("⠇") == int(last["tokpx"])
      and body.count("⠸") == int(last["tokpy"]))
print(",".join([cond, seed, last["popn"], last["popi"], last["popp"],
                last["score"], "ok" if ok else "MISMATCH"]))
PYEOF
  rm -f "$tr"
}

echo "cond,seed,popn,popi,popp,births,recon"
for cond in $CONDS; do
  for seed in $(seq 1 "$SEEDS"); do
    run_one "$cond" "$seed" &
    while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do wait -n; done
  done
done
wait
for cond in $CONDS; do
  for seed in $(seq 1 "$SEEDS"); do cat "$JOBD/r.$cond.$seed"; done
done
