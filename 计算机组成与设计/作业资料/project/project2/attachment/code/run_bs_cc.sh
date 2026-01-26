#!/bin/bash

TRACE=../ext_traces/cc.trace
CACHE=8192
ASSOC=2

for exp in 4 5 6 7 8 9 10 11
do
    BS=$((2**exp))

    if [ $((ASSOC * BS)) -gt $CACHE ]; then
        echo "Skipping bs=$BS (assoc*bs > cache)"
        continue
    fi

    echo "Running cc.trace BS: cache=${CACHE}, bs=${BS}, assoc=${ASSOC}"

    ./sim \
        -is $CACHE \
        -ds $CACHE \
        -bs $BS \
        -a $ASSOC \
        -wb -wa \
        $TRACE > bs_cc_${BS}.txt
done
