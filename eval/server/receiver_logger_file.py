#!/usr/bin/env python3
"""
Server 接收端脚本（支持断点续测追加 log）：
- 接收 N_ROUNDS（轮数）
- 接收 Scheduler × File × Round 数据
- 追加写入 recv_log.csv，不覆盖旧记录
- 自动偏移 round 编号继续记录
"""

import socket
import struct
import time
import csv
from collections import defaultdict

# 配置区域
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 8888
CHUNK_SIZE = 1024
SCHEDULER_LIST = ["default", "roundrobin", "redundant", "blest", "ecf"]
FILE_LIST = ["8MB.file", "256MB.file"]
CSV_LOG = "recv_log.csv"
CSV_SUMMARY = "summary.csv"

# 用于接收完整固定长度数据
def recv_exact(sock, size):
    buf = b''
    while len(buf) < size:
        try:
            chunk = sock.recv(size - len(buf))
            if not chunk:
                return None
            buf += chunk
        except socket.timeout:
            raise TimeoutError("Receive timeout")
    return buf

# 初始化 socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((LISTEN_IP, LISTEN_PORT))
sock.listen(5)
print(f"[Server] Listening on {LISTEN_IP}:{LISTEN_PORT}")

# 第一次连接：接收本次轮数
print("[Server] Waiting for round count...")
conn, addr = sock.accept()
n_rounds_bytes = recv_exact(conn, 4)
N_ROUNDS = struct.unpack("!I", n_rounds_bytes)[0]
conn.close()
print(f"[Server] Received N_ROUNDS = {N_ROUNDS}")

# ✅ 新增：读取已有 recv_log.csv，自动计算已有最大轮号
try:
    with open(CSV_LOG, "r") as f:
        reader = csv.DictReader(f)
        max_existing_round = max((int(row["Round"]) for row in reader if row["Round"].isdigit()), default=0)
except FileNotFoundError:
    max_existing_round = 0
print(f"[Server] Detected max existing round = {max_existing_round}")

# 构建任务列表
expected_tasks = [(s, f, r) for s in SCHEDULER_LIST for f in FILE_LIST for r in range(1, N_ROUNDS + 1)]
file_metrics = defaultdict(list)

# ✅ 改为追加写入，不清空旧日志
file_exists = False
try:
    with open(CSV_LOG, "r"):
        file_exists = True
except FileNotFoundError:
    pass

csvfile = open(CSV_LOG, "a", newline='')
csvwriter = csv.writer(csvfile)
if not file_exists:
    csvwriter.writerow(["Scheduler", "File", "Round", "NumChunks", "AvgDelay(ms)", "Goodput(KB/s)", "DownloadTime(s)"])

# 遍历任务
for task_index, (sched, fname, round_id) in enumerate(expected_tasks, 1):
    actual_round = max_existing_round + task_index  # ✅ 自动编号偏移
    print(f"\n[Server] Waiting for: Scheduler={sched}, File={fname}, Round={actual_round}")
    conn, addr = sock.accept()
    print(f"[Server] Connection from {addr}")
    conn.settimeout(10)

    recv_bytes = 0
    delay_sum = 0
    chunk_count = 0
    start_time = time.time()

    try:
        while True:
            try:
                data = recv_exact(conn, CHUNK_SIZE)
                if data is None:
                    print("[Info] Connection closed by client.")
                    break
            except TimeoutError as e:
                print(f"[Warning] Receive timeout: {e}")
                break
            recv_time = time.time()
            try:
                send_ts = struct.unpack("!d", data[:8])[0]
            except Exception as e:
                print(f"[Error] Failed to parse timestamp: {e}")
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

    if chunk_count == 0:
        print(f"[Error] No data received: {sched}-{fname} Round {actual_round}")

    csvwriter.writerow([sched, fname, actual_round, chunk_count, avg_delay, goodput, duration])
    file_metrics[(sched, fname)].append({
        "chunks": chunk_count,
        "delay": avg_delay,
        "goodput": goodput,
        "time": duration,
    })

    print(f"[Result] {sched} | {fname} (Round {actual_round}): Delay = {avg_delay:.2f} ms | "
          f"Goodput = {goodput:.2f} KB/s | Time = {duration:.2f} s")

csvfile.close()
sock.close()

# Summary 仍然覆盖生成
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
