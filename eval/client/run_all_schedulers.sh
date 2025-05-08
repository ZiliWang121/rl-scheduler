#!/bin/bash

#SCHEDULERS=("default" "roundrobin" "redundant" "blest" "ecf" "reles" "falcon")
SCHEDULERS=("default" "roundrobin" "redundant" "blest" "ecf")
NS_NAME="ns-mptcp"
SCRIPT_PATH="/home/vagrant/sender_logger_file.py"
ROUNDS=${1:-3}

for sched in "${SCHEDULERS[@]}"; do
    echo "==== Testing scheduler: $sched (Rounds: $ROUNDS) ===="
    sudo sysctl -w net.mptcp.mptcp_scheduler=$sched

    sudo ip netns exec $NS_NAME python3 $SCRIPT_PATH $ROUNDS
    status=$?

    if [ $status -ne 0 ]; then
        echo "[Error] Scheduler $sched failed to complete sending (exit code $status)"
    else
        echo "==== Scheduler $sched Test Done ===="
    fi
    echo
    sleep 2
done
