#!/usr/bin/env bash
numWords=$(./getWordGraphDensity.sh)
lmScale=50
pruningThreshold=500
./decodeWordGraphs.py ${pruningThreshold} ${lmScale} ${numWords}
./getWer.sh
echo "Done..."
