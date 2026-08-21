#!/bin/bash
# SIR outbreak sweep: p in P_LIST, THREADS, SEEDS runs each.
# CSV: p,threads,seed,events,size   (size = final score = burned trees)
set -e
cd "$(dirname "$0")"
SEEDS=${1:-200}
P_LIST=${P_LIST:-"0.40 0.45 0.50 0.55 0.60"}
THREADS=${THREADS:-1}
PAR=${PAR:-8}
BIN=../../zahradnice-headless
INPUT=$(printf 'T%.0s' $(seq 1 30000))
JOBD=$(mktemp -d)
trap 'rm -rf "$JOBD"' EXIT
run_one() {
  local p=$1 seed=$2 q
  q=$(python3 -c "print(1-$p)")
  "$BIN" "$JOBD/p$p.cfg" --seed "$seed" --screen 33,64 \
      --input "$INPUT" --max-steps 30000 2>&1 >/dev/null \
    | sed -n 's/^Headless run: \([0-9]*\) events, final score=\(-\{0,1\}[0-9]*\).*/\1 \2/p' \
    | awk -v p="$p" -v t="$THREADS" -v s="$seed" \
        '{printf "%s,%d,%d,%d,%d\n", p, t, s, $1, $2}' > "$JOBD/r.$p.$seed"
}
for p in $P_LIST; do
  q=$(python3 -c "print(1-$p)")
  sed "s/   1 0.5\$/   1 $p/; s/   0 0.5\$/   0 $q/; s/^#threads 1\$/#threads $THREADS/" \
      sir.cfg > "$JOBD/p$p.cfg"
done
echo "p,threads,seed,events,size"
for p in $P_LIST; do
  for seed in $(seq 1 "$SEEDS"); do
    run_one "$p" "$seed" &
    while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do wait -n; done
  done
done
wait
for p in $P_LIST; do for seed in $(seq 1 "$SEEDS"); do cat "$JOBD/r.$p.$seed"; done; done
