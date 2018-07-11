#!/bin/bash

declare -a arr1=("m100" "m200" "m50-m50") #architecture
declare -a arr2=("4" "16") #batch size
declare -a arr3=("20") #epochs 
declare -a arr4=("5e-2" "1e-2" "5e-3") #learning rate

echo "Start tuning" > tuning.txt
echo "============" >> tuning.txt

for a in "${arr1[@]}"
do
	for b in "${arr2[@]}"
	do
		for c in "${arr3[@]}"
		do
			for d in "${arr4[@]}"
			do
			echo "./train_lm.sh i100-${a} ${b} ${c} ${d}"
			echo "------------------" >> tuning.txt
			echo "./train_lm.sh i100-${a} ${b} ${c} ${d}" >> tuning.txt 
			./train_lm.sh i100-${a} ${b} ${c} ${d} >> tuning.txt
			echo "done..."
			done
		done
	done
done
