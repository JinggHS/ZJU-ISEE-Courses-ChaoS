#!/bin/bash

TRACE=../ext_traces/tex.trace
CACHE=8192
BS=128

for exp in 0 1 2 3 4 5 6
do
    ASSOC=$((2**exp))

    if [ $((ASSOC * BS)) -gt $CACHE ]; then
        echo "Skipping assoc=$ASSOC (assoc*bs > cache)"
        continue
    fi

    echo "Running tex.trace ASSOC: assoc=${ASSOC}"

    ./sim \
        -is $CACHE \
        -ds $CACHE \
        -bs $BS \
        -a $ASSOC \
        -wb -wa \
        $TRACE > assoc_tex_${ASSOC}.txt
done
