#!/bin/bash

# ==========================================
# Project 2.4 — Full parameter sweep
# Split I/D, WT/WB × WA/WNA
# ==========================================

SIM=../code/sim
OUTDIR=mb_all_results

mkdir -p $OUTDIR
rm -f $OUTDIR/*.txt

wa_nw=("-wa" "-nw")
wt_wb=("-wt" "-wb")

# 所有 trace（按你项目里的位置）
TRACES=(
  "../ext_traces/cc.trace"
  "../ext_traces/tex.trace"
  "../traces/spice.trace"
)

for f in "${TRACES[@]}"; do
  tname=$(basename "$f" .trace)

  for ((cs = 8192; cs <= 16384 ; cs *= 2)); do       # cache size
    for ((bs = 64; bs <= 128 ; bs *= 2)); do         # block size
      for ((as = 2; as <= 4 ; as *= 2)); do          # associativity
        for an in "${wa_nw[@]}"; do                   # write miss policy
          for bt in "${wt_wb[@]}"; do                 # write hit policy

            echo "Running $tname | CS=$cs BS=$bs A=$as $bt $an"

            $SIM \
              -is $cs -ds $cs \
              -bs $bs -a $as \
              $bt $an \
              $f \
              > $OUTDIR/mb_${tname}_${cs}_${bs}_${as}_${bt#-}_${an#-}.txt

          done
        done
      done
    done
  done
done

echo "All simulations finished. Results in $OUTDIR/"
