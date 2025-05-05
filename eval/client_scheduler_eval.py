#!/usr/bin/env python3

"""
client_scheduler_eval.py

📍作用：
- 依次设置每种调度器
- 在 namespace 中执行 logger_basic.py 测试脚本
"""

import argparse
import subprocess

NAMESPACE = "ns-mptcp"

def set_scheduler(sched):
    subprocess.run(["sudo", "sysctl", 
f"net.mptcp.mptcp_scheduler={sched}"], check=True)
    print(f"✅ Scheduler set to {sched}")

def run_test_in_namespace(ip, port, sched, output):
    subprocess.run([
        "sudo", "ip", "netns", "exec", NAMESPACE,
        "python3", "logger_basic.py",
        "--ip", ip,
        "--port", str(port),
        "--scheduler", sched,
        "--output", output
    ], check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--schedulers", nargs="+", required=True,
                        help="Schedulers to test, e.g., minrtt rr reles")
    parser.add_argument("--output", default="client_metrics_basic.csv")
    args = parser.parse_args()

    for sched in args.schedulers:
        print(f"\n🧪 Testing scheduler: {sched}")
        set_scheduler(sched)
        run_test_in_namespace(args.ip, args.port, sched, args.output)

if __name__ == "__main__":
    main()

