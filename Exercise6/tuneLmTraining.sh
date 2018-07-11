#!/bin/bash

declare -a arr1=("m100")
declare -a arr2=("16")
declare -a arr3=("20")
declare -a arr4=("3e-3" "2.5e-3")

echo "Start tuning" > tuning.txt
ecoh "============" >> tuning.txt

for a in "${arr1[@]}"
do
	for b in "${arr2[@]}"
	do
		for c in "${arr3[@]}"
		do
			for d in "${arr4[@]}"
			do
			echo "------------------" >> tuning.txt
			echo "./train_lm.sh i100-m100 4 20 1e-3" >> tuning.txt 
			./train_lm.sh i100-${a} ${b} ${c} ${d} >> tuning.txt
			done
		done
	done
done
