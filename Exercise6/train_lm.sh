#!/bin/bash

# Please change the number of threads if needed:
export OMP_NUM_THREADS=2
rwth_lm='/work/asr2/irie/adv-asr-exercise/rwthlm'
DIR="./"

modelArchitecture=${1} #default 100
batchSize=${2} #default 16
maxEpoch=${3} #default 20
learningRate=${4} #default 1e-3

modelName="name-${modelArchitecture}"

mkdir -p models
resultsFolder="results_${modelArchitecture}_${batchSize}_${maxEpoch}_${learningRate}"
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
    models/${modelName} >> models/${resultsFolder}/results.txt

python ${DIR}/plotTraining.py models/${resultsFolder}/results.txt models/${resultsFolder}

rm models/name-*

echo "Best perplexity: $(cat models/${resultsFolder}/bestPerplexity.txt )"
