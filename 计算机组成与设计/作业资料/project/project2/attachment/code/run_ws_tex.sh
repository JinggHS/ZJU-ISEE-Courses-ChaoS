# #!/bin/bash

# TRACE=../ext_traces/tex.trace
# BS=4    # small block size to reduce spatial locality effects

# for exp in 13 14 15 16 17 18 19 20
# do
#     CACHE=$((2**exp))
#     ASSOC=$((CACHE / BS))   # approximate fully associative

#     echo "Running tex.trace WS: cache=${CACHE}, bs=${BS}, assoc=${ASSOC}"

#     ./sim \
#         -is $CACHE \
#         -ds $CACHE \
#         -bs $BS \
#         -a $ASSOC \
#         -wb -wa \
#         $TRACE > ws_tex_${CACHE}.txt
# done

#!/bin/bash

#!/bin/bash

TRACE=../ext_traces/tex.trace
BS=4
OUT=ws_tex
OUTDIR=../code       # ⭐ 输出到 code 目录

mkdir -p $OUTDIR

for exp in 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16
do
    CACHE=$((2**exp))
    ASSOC=$((CACHE / BS))

    echo "Running tex.trace WS: cache=${CACHE} bytes"

    ./sim \
        -is $CACHE \
        -ds $CACHE \
        -bs $BS \
        -a $ASSOC \
        -wb -wa \
        $TRACE > ${OUTDIR}/${OUT}_${CACHE}.txt
done

