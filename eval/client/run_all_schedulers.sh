#!/bin/bash

SCHEDULERS=("default" "roundrobin" "redundant" "blest" "ecf")
NS_NAME="ns-mptcp"
SCRIPT_PATH="/home/vagrant/sender_logger_file.py"
ROUNDS=${1:-3}

for i in "${!SCHEDULERS[@]}"; do
    sched="${SCHEDULERS[$i]}"
    echo "==== Testing scheduler: $sched (Rounds: $ROUNDS) ===="
    sudo sysctl -w net.mptcp.mptcp_scheduler=$sched

    # ✅【新增】仅第一个 scheduler 启动时发送轮数
    if [ "$i" -eq 0 ]; then
        export SEND_ROUND_FLAG=true
    else
        export SEND_ROUND_FLAG=false
    fi

    # ✅【更改】通过环境变量传递 SEND_ROUND_FLAG
    sudo ip netns exec $NS_NAME env SEND_ROUND_FLAG=$SEND_ROUND_FLAG python3 $SCRIPT_PATH $ROUNDS
    status=$?

    if [ $status -ne 0 ]; then
        echo "[Error] Scheduler $sched failed to complete sending (exit code $status)"
    else
        echo "==== Scheduler $sched Test Done ===="
    fi
    echo
    sleep 2
done
