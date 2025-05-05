#!/usr/bin/env python3

"""
📍 logger_basic.py
作用：
- 在 network namespace 中运行
- 建立 TCP 连接后发送固定大小的数据
- 记录完成时间（用于计算吞吐量）
- 写入 CSV 结果文件
"""

import argparse
import socket
import time
import csv
import random
import os

BUFFER_SIZE = 1460  # 模拟一个 MSS（最大段大小）

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True, help="Echo server 的 IP")
    parser.add_argument("--port", type=int, required=True, help="Echo 
server 的端口")
    parser.add_argument("--size", type=int, default=100 * 1024 * 1024,  # 
默认传送 100MB
                        help="总共要发送的数据量（单位：字节）")
    parser.add_argument("--scheduler", required=True, help="当前使用的 
MPTCP scheduler 名称")
    parser.add_argument("--output", default="client_metrics_basic.csv", 
help="CSV 输出文件名")
    args = parser.parse_args()

    # 🧠 生成一个待发送的数据 buffer
    buf = bytes([random.randint(0, 255) for _ in range(BUFFER_SIZE)])

    # 🌐 创建 TCP socket，连接到目标服务器
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.ip, args.port))

    # ⏱️ 记录发送前的时间
    start = time.time()

    total_sent = 0
    while total_sent < args.size:
        s.send(buf)
        try:
            s.recv(BUFFER_SIZE)  # 接收 echo 回来的内容（可省略）
        except:
            pass
        total_sent += len(buf)

    # ⏱️ 记录完成时间
    end = time.time()
    duration = end - start  # 计算总耗时（秒）
    throughput_mbps = args.size * 8 / 1e6 / duration  # 吞吐量 Mbps

    # ✅ 打印结果到终端
    print(f"Scheduler: {args.scheduler}")
    print(f"Total sent: {args.size / 1024 / 1024:.2f} MB")
    print(f"Time: {duration:.2f} s")
    print(f"Throughput: {throughput_mbps:.2f} Mbps")

    # 🧾 追加写入结果到 CSV 文件
    file_exists = os.path.exists(args.output)
    with open(args.output, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["scheduler", "data_sent_bytes", 
"duration_sec", "throughput_mbps"])
        writer.writerow([args.scheduler, args.size, round(duration, 3), 
round(throughput_mbps, 3)])

    s.close()

if __name__ == "__main__":
    main()

