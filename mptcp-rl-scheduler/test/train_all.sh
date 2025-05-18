#!/bin/sh

#sudo python3 MPTCP_test.py --scheduler 3 --action 1 --train 800 --file random --scenario static_random_cubic_train
#sudo python3 MPTCP_test.py --scheduler 4 --action 1 --train 800 --file random --scenario static_random_cubic_train

# sudo python3 MPTCP_test.py --scheduler 3 --action 1 --train 800 --file random --scenario dynamic_random_cubic_train
# sudo python3 MPTCP_test.py --scheduler 4 --action 1 --train 800 --file random --scenario dynamic_random_cubic_train

listSce="64kb 2mb 8mb 64mb"
#train on 2mb and evaluated for above file sizes
for j in 3 4 5 6;do
	echo "${j} {.dat}"
	if [ $j -eq 6 ]
	then
		sudo python3 MPTCP_test.py --action 1 --scheduler "${j}" --train 800 --file "random"
	else
		sudo python3 MPTCP_test.py --action 1 --scheduler "${j}" --train 600
	fi
done

for i in $listSce; do
	echo "${i} {.dat}"
	for j in `seq 0 6`
	do
		sudo python3 MPTCP_test.py --action 1 --scheduler "${j}" --scenario static_eval"${i}" --file "${i}.dat"
	done
done
