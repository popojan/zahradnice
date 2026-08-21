#!/bin/bash
# forest-ladder regime sweep (route-3 heritable trait ladder).
# Conditions: none/calm/mid/fiery lightning periods + mid-run switches
# (c2f, f2c at half budget). Per run: trace -> ladder_stats.py series
# CSV in ladder/, exact reconciliation vs the final screen dump.
# Emits summary CSV on stdout:
#   cond,seed,events,score,pop1..pop5,fire,meanrung,recon
# Usage: ./laddersweep.sh [SEEDS=8] [BUDGET=150000] > ladder/summary.csv
#        PAR=N concurrent runs (default 8)
#        CONDS overrides the condition list; a cond of form pN is a
#        plain regime with lightning period N (e.g. "p12000 p32000")
#        CFG=variant.cfg TAG=prefix- run a cfg variant, prefixing the
#        per-run series filenames
set -e
cd "$(dirname "$0")"
SEEDS=${1:-8}
BUDGET=${2:-150000}
PAR=${PAR:-8}
BIN=../../zahradnice-headless
[ -x "$BIN" ] || BIN=../../zahradnice
SCREEN=33,64
CFG=${CFG:-forest-ladder.cfg}
TAG=${TAG:-}
CONDS=${CONDS:-"none calm mid fiery c2f f2c"}
OUT=ladder
mkdir -p "$OUT"
JOBD=$(mktemp -d)
trap 'rm -rf "$JOBD"' EXIT

mkinput() { # P N -> at least N chars of ((P-1) T's + l) blocks
  python3 -c "import sys; p,n=int(sys.argv[1]),int(sys.argv[2]); \
sys.stdout.write(('T'*(p-1)+'l')*(n//p+1))" "$1" "$2"
}

HALF=$((BUDGET / 2))
for cond in $CONDS; do
  case $cond in
    none) python3 -c "print('T' * $BUDGET, end='')" ;;
    calm) mkinput 4000 "$BUDGET" ;;
    mid) mkinput 1000 "$BUDGET" ;;
    fiery) mkinput 200 "$BUDGET" ;;
    c2f) mkinput 4000 "$HALF" | head -c "$HALF"; mkinput 200 "$HALF" ;;
    f2c) mkinput 200 "$HALF" | head -c "$HALF"; mkinput 4000 "$HALF" ;;
    p*) mkinput "${cond#p}" "$BUDGET" ;;
    ret*) B=${cond#ret}
      python3 -c "print('T' * 40000, end='')"
      mkinput 200 "$B" | head -c "$B"
      python3 -c "print('T' * 120000, end='')" ;;
    *) echo "unknown cond $cond" >&2; exit 1 ;;
  esac > "$JOBD/in.$cond"
done

run_one() {
  local cond=$1 seed=$2
  local tr="$JOBD/$cond.$seed.trace" sc="$JOBD/$cond.$seed.screen"
  local ev
  ev=$("$BIN" "$CFG" --seed "$seed" --screen "$SCREEN" \
      --input "@$JOBD/in.$cond" --max-steps "$BUDGET" \
      --trace "$tr" --dump-screen "$sc" 2>&1 >/dev/null \
    | sed -n 's/^Headless run: \([0-9]*\) events, final score=\(-\{0,1\}[0-9]*\).*/\1,\2/p')
  python3 ladder_stats.py "$CFG" "$tr" --sample 1000 \
    > "$OUT/series-$TAG$cond-s$seed.csv" 2>/dev/null
  python3 - "$OUT/series-$TAG$cond-s$seed.csv" "$sc" "$cond" "$seed" "$ev" \
    <<'EOF' > "$JOBD/r.$cond.$seed"
import csv
import sys
series, screen, cond, seed, ev = sys.argv[1:6]
last = list(csv.DictReader(open(series)))[-1]
body = "\n".join(open(screen, encoding="utf-8").read().splitlines()[1:])
ok = all(body.count(k) == int(last[f"pop{k}"]) for k in "12345") \
    and body.count("A") == int(last["fire"]) \
    and all(body.count(chr(0x2800 + 2 ** int(k) - 1))
            == int(last.get(f"bank{k}", 0)) for k in "12345")
recon = "ok" if ok else "MISMATCH"
print(",".join([cond, seed, ev]
               + [last[f"pop{k}"] for k in "12345"]
               + [last["fire"], last["meanrung"],
                  last.get("banktot", "0"), recon]))
EOF
  rm -f "$tr"
}

echo "cond,seed,events,score,pop1,pop2,pop3,pop4,pop5,fire,meanrung,banktot,recon"
for cond in $CONDS; do
  for seed in $(seq 1 "$SEEDS"); do
    run_one "$cond" "$seed" &
    while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do wait -n; done
  done
done
wait
for cond in $CONDS; do
  for seed in $(seq 1 "$SEEDS"); do
    cat "$JOBD/r.$cond.$seed"
  done
done
