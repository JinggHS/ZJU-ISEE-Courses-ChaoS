#!/bin/bash

TRACE=../traces/spice.trace
CACHE=8192
BS=32
ASSOC=2

echo "=== Write Through vs Write Back (No Write Allocate) ==="

# Write Through + No Write Allocate
./sim \
    -is $CACHE \
    -ds $CACHE \
    -bs $BS \
    -a $ASSOC \
    -wt -nw \
    $TRACE > bw_wt_nwa.txt

# Write Back + No Write Allocate
./sim \
    -is $CACHE \
    -ds $CACHE \
    -bs $BS \
    -a $ASSOC \
    -wb -nw \
    $TRACE > bw_wb_nwa.txt


echo "=== Write Allocate vs No Write Allocate (Write Back) ==="

# Write Back + Write Allocate
./sim \
    -is $CACHE \
    -ds $CACHE \
    -bs $BS \
    -a $ASSOC \
    -wb -wa \
    $TRACE > bw_wb_wa.txt

# Write Back + No Write Allocate
./sim \
    -is $CACHE \
    -ds $CACHE \
    -bs $BS \
    -a $ASSOC \
    -wb -nw \
    $TRACE > bw_wb_nwa2.txt
