#!/bin/bash

TRACE=../ext_traces/cc.trace
CACHE=8192
BS=16
ASSOC=1

echo "WT + NWA"
./sim -us $CACHE -bs $BS -a $ASSOC -wt -nw $TRACE > bw_cc_wt_nwa.txt

echo "WB + NWA"
./sim -us $CACHE -bs $BS -a $ASSOC -wb -nw $TRACE > bw_cc_wb_nwa.txt

echo "WB + WA"
./sim -us $CACHE -bs $BS -a $ASSOC -wb -wa $TRACE > bw_cc_wb_wa.txt
