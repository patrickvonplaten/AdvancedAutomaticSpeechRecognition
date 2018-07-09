#!/usr/bin/env bash
numWords=$(./getWordGraphDensity.sh)
lmScale=50
lmScaleOptStep=64
lmScaleOpt=${lmScale}
pruningThreshold=500

./decodeWordGraphs.py ${pruningThreshold} ${lmScale} ${numWords}
./getWer.sh
corpScl=$( realpath ./results/results.ctm.sys)
bestWer=$(python -c "print(int($(cat ${corpScl} | grep "Sum/Avg" | awk '{print $11}')*10))")

for i in {1..8}
do
	lmScaleOptStep=$(python -c "print(${lmScaleOptStep}/2.0)")

	#tryLMScaleUp
	./decodeWordGraphs.py ${pruningThreshold} $(python -c "print(${lmScaleOpt} + ${lmScaleOptStep})") ${numWords} 
	./getWer.sh
	werUp=$(python -c "print(int($(cat ${corpScl} | grep "Sum/Avg" | awk '{print $11}')*10))")
	
	#tryLMScaleDown
	./decodeWordGraphs.py ${pruningThreshold} $(python -c "print(${lmScaleOpt} - ${lmScaleOptStep})") ${numWords} 
	./getWer.sh
	werDown=$(python -c "print(int($(cat ${corpScl} | grep "Sum/Avg" | awk '{print $11}')*10))")
	echo "${werDown} ${werUp} ${bestWer}"

	if [ "$werDown" -gt "$werUp" -a "$bestWer" -gt "$werUp" ]; then
		bestWer=${werUp}
		lmScaleOpt=$(python -c "print(${lmScaleOpt} + ${lmScaleOptStep})")
		echo "Best WER = ${bestWer} with lmScale = ${lmScaleOpt}"
	elif [ "$werUp" -gt "$werDown" -a "$bestWer" -gt "$werDown" ]; then
		bestWer=${werDown}
		lmScaleOpt=$(python -c "print(${lmScaleOpt} - ${lmScaleOptStep})")
		echo "Best WER = ${bestWer} with lmScale = ${lmScaleOpt}"
	else
		echo "Best WER = ${bestWer} with lmScale = ${lmScaleOpt}"
	fi 
done

./decodeWordGraphs.py ${pruningThreshold} ${lmScaleOpt} ${numWords}
./getWer.sh
bestWer=$(cat ${corpScl} | grep "Sum/Avg" | awk '{print $11}')

echo "LmScale optimization done..."
echo "================================"
echo "Best final WER is = ${bestWer}"



