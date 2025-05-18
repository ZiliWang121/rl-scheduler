#!/bin/sh

listSce="64kb 2mb 8mb 64mb"


echo "$1"
case "$1" in
	1)
		for j in 3 4 5 6;do
			echo "${j} {.dat}"
			if [ $j -eq 6 ]
			then
				sudo python3 MPTCP_test.py --action 1 --scheduler "${j}" --train 800 --file "random"
			else
				sudo python3 MPTCP_test.py --action 1 --scheduler "${j}" --train 600
			fi
		done
		;;
	2)
		for i in $listSce; do
			echo "${i} {.dat}"
			for j in `seq 0 6`
			do
				sudo python3 MPTCP_test.py --action 1 --scheduler "${j}" --scenario static_eval"${i}" --file "${i}.dat"
			done
		done
		;;
	3)
		for j in 2 3 4 5;do
			echo "${j} {.dat}"
			if [ $j -eq 5 ]
			then
				sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --train 800 --file "random"
			else
				sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --train 600
			fi
		done
		;;
	4)
		for i in $listSce; do
			echo "${i} {.dat}"
			for j in `seq 0 5`
			do
				sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --scenario static_eval"${i}" --file "${i}.dat"
			done
		done
		;;
	5)
		for j in 2 3 4 5;do
			echo "${j} {.dat}"
			if [ $j -eq 5 ]
			then 
				sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --train 800 --scenario dynamic --file "random"
			else
				sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --train 600 --scenario dynamic
			fi
		done
		;;
	6)
		for i in $listSce; do
			echo "${i} {.dat}"
			for j in `seq 0 5`
			do
				sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --scenario dynamic_eval"${i}" --file "${i}.dat"
			done
		done
		;;
	7)	
		for j in 2 3 4 5;do
			echo "${j} {.dat}"
			if [ $j -eq 5 ]
			then 
				sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --train 800 --scenario dynamic --file "random"
			else
				sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --train 600 --scenario dynamic
			fi
		done
		
		for j in `seq 0 5`
		do
			sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --scenario dynamic_evalrandom --file "random"
		done
		
		for j in `seq 0 5`
		do
			sudo python3 mininet_wifi.py --action 1 --scheduler "${j}" --scenario dynamic_eval64mb --file 64mb.dat
		done
		
		;;
	*)
		echo "wrong input"
		;;
esac




