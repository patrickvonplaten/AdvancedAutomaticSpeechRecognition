#!/usr/bin/env bash

transcriptionTxtFilePath='./transcriptions.txt'


plainText=$(sed '/;;/d' ${transcriptionTxtFilePath} | sed 's/^.*<o,unk>//')
numberOfWords=$(echo ${plainText} | wc -w)

sumArcs=0
for fileName in ./lattice*; do
	arcs=$(cat ${fileName} | zgrep "LINKS" | sed 's/^.*=//')
	sumArcs=$((sumArcs + arcs))
done

echo "The word graph density is $(expr $((sumArcs/numberOfWords)))"
