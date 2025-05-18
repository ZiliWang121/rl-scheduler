#!/bin/sh


listSce="64kb 2mb 8mb 64mb"

for j in 2 3 4 5;do
	echo "${j} {.dat}"
	if [ $j -eq 5 ]
	then
		sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --train 800 --file "random" --scenario dynamic
	else
		sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --train 600 --scenario dynamic
	fi
done

for i in $listSce; do
	echo "${i} {.dat}"
	for j in `seq 0 5`
	do
		sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --scenario dynamic_eval"${i}" --file "${i}.dat"
	done
done


