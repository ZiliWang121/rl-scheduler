#!/bin/bash

#SCHEDULERS=("default" "reles" "falcon")
SCHEDULERS=("default" "roundrobin" "redundant" "blest" "ecf" "reles" "falcon")
NS_NAME="ns-mptcp"
SCRIPT_PATH="/home/vagrant/sender_logger_file.py"

for sched in "${SCHEDULERS[@]}"; do
    echo "==== Testing scheduler: $sched ===="
    sudo sysctl -w net.mptcp.mptcp_scheduler=$sched

    LOGFILE="result_${sched}_$(date +%Y%m%d_%H%M%S).log"
    sudo ip netns exec $NS_NAME python3 $SCRIPT_PATH | tee $LOGFILE

    echo "==== Scheduler $sched Test Done ===="
    echo
    sleep 2
done

