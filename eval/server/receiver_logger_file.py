#!/usr/bin/env python3
"""
Server 接收端脚本（支持断点续测 + 每调度器单独续轮）：
- 从 client 接收 N_ROUNDS
- 每次测量数据追加写入 recv_log.csv（而非覆盖）
- 每个 Scheduler × File 对分别从已有最大轮次开始继续编号
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
SCHEDULER_LIST = ["default", "roundrobin", "redundant", "blest", "ecf"]
FILE_LIST = ["8MB.file", "256MB.file"]
CSV_LOG = "recv_log.csv"
CSV_SUMMARY = "summary.csv"
# ------------------------------------------------

def recv_exact(sock, size):
    """接收固定长度数据，如果连接正常关闭则返回 None"""
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

# 第一次连接用于接收 N_ROUNDS
print("[Server] Waiting for round count...")
conn, addr = sock.accept()
n_rounds_bytes = recv_exact(conn, 4)
N_ROUNDS = struct.unpack("!I", n_rounds_bytes)[0]
conn.close()
print(f"[Server] Received N_ROUNDS = {N_ROUNDS}")

# ✅ 读取已有 CSV_LOG 中的最大轮次数（每调度器 × 文件对分开记录）
round_offset = defaultdict(int)
try:
    with open(CSV_LOG, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["Scheduler"], row["File"])
            if row["Round"].isdigit():
                round_offset[key] = max(round_offset[key], int(row["Round"]))
    print(f"[Server] Detected round offset per key: {dict(round_offset)}")
except FileNotFoundError:
    print("[Server] No previous log found, starting fresh.")

# ✅ 构建任务清单（每个 scheduler × file × round）
expected_tasks = []
for sched in SCHEDULER_LIST:
    for fname in FILE_LIST:
        base = round_offset.get((sched, fname), 0)
        for i in range(N_ROUNDS):
            round_id = base + i + 1  # 每个组合单独编号
            expected_tasks.append((sched, fname, round_id))

# 初始化 file_metrics 存储每轮结果
file_metrics = defaultdict(list)

# ✅ 打开 CSV_LOG 并追加写入，保留旧内容
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

# 主循环接收每组测试数据
for task_index, (sched, fname, round_id) in enumerate(expected_tasks, 1):
    print(f"\n[Server] Waiting for: Scheduler={sched}, File={fname}, Round={round_id}")
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
        print(f"[Error] No data received: {sched}-{fname} Round {round_id}")

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

# ✅ Summary.csv 总结本轮（仍然是覆盖）
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
