#!/bin/bash

TRACE=../traces/spice.trace
CACHE=8192
BS=128

for exp in 0 1 2 3 4 5 6
do
    ASSOC=$((2**exp))

    # 安全检查
    if [ $((ASSOC * BS)) -gt $CACHE ]; then
        echo "Skipping assoc = $ASSOC (too large)"
        continue
    fi

    echo "Running associativity = $ASSOC"

    ./sim \
        -is $CACHE \
        -ds $CACHE \
        -bs $BS \
        -a $ASSOC \
        -wb -wa \
        $TRACE > assoc_full_${ASSOC}_new.txt
done
