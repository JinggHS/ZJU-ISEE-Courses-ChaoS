#!/bin/bash

TRACE=../ext_traces/cc.trace
CACHE=8192
BS=128

for exp in 0 1 2 3 4 5 6
do
    ASSOC=$((2**exp))

    if [ $((ASSOC * BS)) -gt $CACHE ]; then
        echo "Skipping assoc = $ASSOC (too large)"
        continue
    fi

    echo "Running cc.trace with associativity = $ASSOC"

    ./sim \
        -is $CACHE \
        -ds $CACHE \
        -bs $BS \
        -a $ASSOC \
        -wb -wa \
        $TRACE > assoc_cc_${ASSOC}.txt
done
