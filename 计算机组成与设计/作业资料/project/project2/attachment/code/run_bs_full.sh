#!/bin/bash

TRACE=../traces/spice.trace
CACHE=8192
ASSOC=2

for exp in 4 5 6 7 8 9 10 11
do
    BS=$((2**exp))

    # block 太大时，cache 容量必须 >= block * assoc
    if [ $((BS * ASSOC)) -gt $CACHE ]; then
        echo "Skipping block size $BS (too large)"
        continue
    fi

    echo "Running block size = $BS"

    ./sim \
        -is $CACHE \
        -ds $CACHE \
        -bs $BS \
        -a $ASSOC \
        -wb -wa \
        $TRACE > bs_full_${BS}.txt
done
