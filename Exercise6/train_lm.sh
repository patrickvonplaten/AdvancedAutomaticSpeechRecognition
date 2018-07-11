#!/bin/bash

# Please change the number of threads if needed:
export OMP_NUM_THREADS=2
rwth_lm='/work/asr2/irie/adv-asr-exercise/rwthlm'
DIR="./"

batchSize=16
maxEpoch=20
learningRate=1e-3

mkdir -p models
resultsFolder="results_${batchSize}_${maxEpoch}_${learningRate}"
mkdir -p models/${resultsFolder}

$rwth_lm \
    --vocab vocab.txt \
    --unk \
    --train train.txt.gz \
    --dev validation.txt.gz \
    --batch-size ${batchSize} \
    --max-epoch ${maxEpoch} \
    --learning-rate ${learningRate} \
    --sequence-length 500 \
    --word-wrapping verbatim \
    models/${resultsFolder}/name-i100-m100 >> models/${resultsFolder}/results.txt

python ${Dir}/plotTraining.py models/${resultsFolder}/results.txt models/${resultsFolder}
