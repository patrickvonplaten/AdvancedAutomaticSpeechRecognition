#!/bin/bash

# Please change the number of threads if needed:
export OMP_NUM_THREADS=2
rwth_lm='/work/asr2/irie/adv-asr-exercise/rwthlm'
#curDir=$(pwd)
#rwth_lm="${curDir}/rwthlm"
DIR="./"

mkdir -p models

$rwth_lm \
    --vocab vocab.txt \
    --unk \
    --train train.txt.gz \
    --dev validation.txt.gz \
    --batch-size 16 \
    --max-epoch 20 \
    --learning-rate 1e-3 \
    --sequence-length 500 \
    --word-wrapping verbatim \
    models/name-i100-m100
