#!/bin/bash

SCHEDULERS=("default" "roundrobin" "redundant" "blest" "ecf" "reles" "falcon")
NS_NAME="ns-mptcp"
SCRIPT_PATH="/home/vagrant/sender_logger_file.py"

# 默认轮数为 3，允许通过第一个参数传入新值
ROUNDS=${1:-3}

for sched in "${SCHEDULERS[@]}"; do
    echo "==== Testing scheduler: $sched (Rounds: $ROUNDS) ===="
    sudo sysctl -w net.mptcp.mptcp_scheduler=$sched

#    LOGFILE="result_${sched}_$(date +%Y%m%d_%H%M%S).log"
    sudo ip netns exec $NS_NAME python3 $SCRIPT_PATH $ROUNDS

    echo "==== Scheduler $sched Test Done ===="
    echo
    sleep 2
done
