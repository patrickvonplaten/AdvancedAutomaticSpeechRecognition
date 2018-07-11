#!/usr/bin/env bash

vocabFile='vocab.txt'
numberOfWordsInVocabTxt=$(cat ${vocabFile} | wc -l)
smallestWordClassIdx=$(cat vocab.txt | awk '{ print $2 }' | sort -n | head -1) 
biggestWordClassIdx=$(cat vocab.txt | awk '{ print $2 }' | sort -n | tail -1) 
numberOfWordClasses=$(( biggestWordClassIdx - smallestWordClassIdx + 1 ))

echo "Size of vocabulary: ${numberOfWordsInVocabTxt}"
echo "Number of word classes: ${numberOfWordClasses}"

