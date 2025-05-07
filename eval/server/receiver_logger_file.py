#!/usr/bin/env python3
"""
Server 接收端脚本（文件分组统计）：
- 每次连接接收完整一个文件（chunk流）
- 按文件名分组，记录每轮指标（delay / goodput / time）
- 所有轮次结束后输出每个文件的平均性能指标到 summary.csv
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
N_ROUNDS_PER_FILE = 3
FILE_LIST = ["64KB.file", "256KB.file", "8MB.file", "64MB.file"]
CSV_LOG = "recv_log.csv"
CSV_SUMMARY = "summary.csv"
# ------------------------------------------------

# 每个连接都按顺序推断属于哪个文件第几轮
expected_files = [(fname, i + 1) for fname in FILE_LIST for i in range(N_ROUNDS_PER_FILE)]
file_metrics = defaultdict(list)  # fname -> list of dicts with keys: delay, goodput, time

def recv_exact(sock, size):
    buf = b''
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("连接断开，提前结束")
        buf += chunk
    return buf

# 监听 socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((LISTEN_IP, LISTEN_PORT))
sock.listen(5)

print(f"[Server] Listening on {LISTEN_IP}:{LISTEN_PORT}")
csvfile = open(CSV_LOG, "w", newline='')
csvwriter = csv.writer(csvfile)
csvwriter.writerow(["File", "Round", "NumChunks", "AvgDelay(ms)", "Goodput(KB/s)", "DownloadTime(s)"])

# 主循环
for file_index, (fname, round_id) in enumerate(expected_files, 1):
    print(f"\n[Server] Waiting for: {fname}, round {round_id}")
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

    # 写入逐轮日志
    csvwriter.writerow([fname, round_id, chunk_count, avg_delay, goodput, duration])
    file_metrics[fname].append({
        "chunks": chunk_count,
        "delay": avg_delay,
        "goodput": goodput,
        "time": duration,
    })

    print(f"[Result] {fname} (Round {round_id}): Delay = {avg_delay:.2f} ms | "
          f"Goodput = {goodput:.2f} KB/s | Time = {duration:.2f} s")

csvfile.close()
sock.close()

# 写入 summary.csv：每个文件一行
with open(CSV_SUMMARY, "w", newline='') as summary:
    writer = csv.writer(summary)
    writer.writerow(["File", "AvgChunks", "AvgDelay(ms)", "AvgGoodput(KB/s)", "AvgDownloadTime(s)"])
    for fname in FILE_LIST:
        metrics = file_metrics[fname]
        avg_chunks = sum(m["chunks"] for m in metrics) / len(metrics)
        avg_delay = sum(m["delay"] for m in metrics) / len(metrics)
        avg_goodput = sum(m["goodput"] for m in metrics) / len(metrics)
        avg_time = sum(m["time"] for m in metrics) / len(metrics)
        writer.writerow([fname, avg_chunks, avg_delay, avg_goodput, avg_time])

print("\n=== Summary written to summary.csv ===")
