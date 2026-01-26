# #!/bin/bash

# TRACE=../traces/spice.trace
# BS=4

# for exp in 13 14 15 16 17 18 19 20
# do
#     CS=$((2**exp))
#     ASSOC=$((CS / BS))

#     echo "Running cache size = $CS, assoc = $ASSOC"

#     ./sim \
#         -is $CS \
#         -ds $CS \
#         -bs $BS \
#         -a $ASSOC \
#         -wb -wa \
#         $TRACE > ws_full_${CS}.txt
# done


#!/bin/bash

#!/bin/bash

TRACE=../traces/spice.trace
BS=4
OUT=ws_full
OUTDIR=../code      # ⭐ 输出到 code 目录

mkdir -p $OUTDIR    # ⭐ 确保目录存在

for exp in 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16
do
    CACHE=$((2**exp))
    ASSOC=$((CACHE / BS))

    echo "Running spice.trace WS: cache=${CACHE} bytes"

    ./sim \
        -is $CACHE \
        -ds $CACHE \
        -bs $BS \
        -a $ASSOC \
        -wb -wa \
        $TRACE > ${OUTDIR}/${OUT}_${CACHE}.txt
done
