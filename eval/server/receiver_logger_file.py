#!/usr/bin/env python3
"""
Server 接收端脚本（调度器 + 文件 + 多轮统计）：
- 第一次连接接收 N_ROUNDS（4 字节）
- 后续按 [调度器 × 文件 × 轮次] 顺序接收 chunk 流
- 每轮记录 delay / goodput / time，最终输出 summary.csv
"""

import socket
import struct
import time
import csv
from collections import defaultdict

# ------------------- 配置区域 -------------------
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 8888
CHUNK_SIZE = 1024

# 与 client 保持一致顺序
SCHEDULER_LIST = ["default", "roundrobin", "redundant", "blest", "ecf", "reles", "falcon"]
FILE_LIST = ["64KB.file", "256KB.file", "8MB.file", "64MB.file"]

CSV_LOG = "recv_log.csv"
CSV_SUMMARY = "summary.csv"
# ------------------------------------------------

def recv_exact(sock, size):
    buf = b''
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("连接断开，提前结束")
        buf += chunk
    return buf

# 初始化 socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((LISTEN_IP, LISTEN_PORT))
sock.listen(5)
print(f"[Server] Listening on {LISTEN_IP}:{LISTEN_PORT}")

# ⚠️ 第一次连接用于接收 N_ROUNDS（4 字节）
print("[Server] Waiting for round count...")
conn, addr = sock.accept()
n_rounds_bytes = recv_exact(conn, 4)
N_ROUNDS = struct.unpack("!I", n_rounds_bytes)[0]
conn.close()
print(f"[Server] Received N_ROUNDS = {N_ROUNDS}")

# 构建任务顺序：Scheduler × File × Round
expected_tasks = []
for sched in SCHEDULER_LIST:
    for fname in FILE_LIST:
        for round_id in range(1, N_ROUNDS + 1):
            expected_tasks.append((sched, fname, round_id))

# 初始化数据结构
file_metrics = defaultdict(list)  # key = (sched, fname)

# 初始化日志
csvfile = open(CSV_LOG, "w", newline='')
csvwriter = csv.writer(csvfile)
csvwriter.writerow(["Scheduler", "File", "Round", "NumChunks", "AvgDelay(ms)", "Goodput(KB/s)", "DownloadTime(s)"])

# 接收循环
for task_index, (sched, fname, round_id) in enumerate(expected_tasks, 1):
    print(f"\n[Server] Waiting for: Scheduler={sched}, File={fname}, Round={round_id}")
    conn, addr = sock.accept()
    print(f"[Server] Connection from {addr}")

    recv_bytes = 0
    delay_sum = 0
    chunk_count = 0
    start_time = time.time()

    try:
        while True:
            try:
                data = recv_exact(conn, CHUNK_SIZE)
            except ConnectionError:
                break

            recv_time = time.time()
            try:
                send_ts = struct.unpack("!d", data[:8])[0]
            except:
                continue
            delay_ms = (recv_time - send_ts) * 1000
            delay_sum += delay_ms
            recv_bytes += len(data)
            chunk_count += 1
    finally:
        conn.close()

    end_time = time.time()
    duration = end_time - start_time
    avg_delay = delay_sum / chunk_count if chunk_count > 0 else 0
    goodput = (recv_bytes / 1024) / duration if duration > 0 else 0

    csvwriter.writerow([sched, fname, round_id, chunk_count, avg_delay, goodput, duration])
    file_metrics[(sched, fname)].append({
        "chunks": chunk_count,
        "delay": avg_delay,
        "goodput": goodput,
        "time": duration,
    })

    print(f"[Result] {sched} | {fname} (Round {round_id}): Delay = {avg_delay:.2f} ms | "
          f"Goodput = {goodput:.2f} KB/s | Time = {duration:.2f} s")

csvfile.close()
sock.close()

# 写入 summary.csv（调度器 × 文件）
with open(CSV_SUMMARY, "w", newline='') as summary:
    writer = csv.writer(summary)
    writer.writerow(["Scheduler", "File", "AvgChunks", "AvgDelay(ms)", "AvgGoodput(KB/s)", "AvgDownloadTime(s)"])
    for sched in SCHEDULER_LIST:
        for fname in FILE_LIST:
            metrics = file_metrics[(sched, fname)]
            if not metrics:
                continue
            avg_chunks = sum(m["chunks"] for m in metrics) / len(metrics)
            avg_delay = sum(m["delay"] for m in metrics) / len(metrics)
            avg_goodput = sum(m["goodput"] for m in metrics) / len(metrics)
            avg_time = sum(m["time"] for m in metrics) / len(metrics)
            writer.writerow([sched, fname, avg_chunks, avg_delay, avg_goodput, avg_time])

print("\n=== Summary written to summary.csv ===")
