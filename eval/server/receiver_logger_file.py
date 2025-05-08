#!/usr/bin/env python3
import socket
import struct
import time
import csv
from collections import defaultdict

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 8888
CHUNK_SIZE = 1024

#SCHEDULER_LIST = ["default", "roundrobin", "redundant", "blest", "ecf", "reles", "falcon"]
SCHEDULER_LIST = ["default", "roundrobin", "redundant", "blest", "ecf"]
FILE_LIST = ["64KB.file", "256KB.file", "8MB.file", "64MB.file"]

CSV_LOG = "recv_log.csv"
CSV_SUMMARY = "summary.csv"

def recv_exact(sock, size):
    buf = b''
    while len(buf) < size:
        try:
            chunk = sock.recv(size - len(buf))
            if not chunk:
                raise ConnectionError("连接断开，提前结束")
            buf += chunk
        except socket.timeout:
            raise TimeoutError("接收超时")
    return buf

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((LISTEN_IP, LISTEN_PORT))
sock.listen(5)
print(f"[Server] Listening on {LISTEN_IP}:{LISTEN_PORT}")

print("[Server] Waiting for round count...")
conn, addr = sock.accept()
n_rounds_bytes = recv_exact(conn, 4)
N_ROUNDS = struct.unpack("!I", n_rounds_bytes)[0]
conn.close()
print(f"[Server] Received N_ROUNDS = {N_ROUNDS}")

expected_tasks = [(s, f, r) for s in SCHEDULER_LIST for f in FILE_LIST for r in range(1, N_ROUNDS + 1)]
file_metrics = defaultdict(list)

csvfile = open(CSV_LOG, "w", newline='')
csvwriter = csv.writer(csvfile)
csvwriter.writerow(["Scheduler", "File", "Round", "NumChunks", "AvgDelay(ms)", "Goodput(KB/s)", "DownloadTime(s)"])

for task_index, (sched, fname, round_id) in enumerate(expected_tasks, 1):
    print(f"\n[Server] Waiting for: Scheduler={sched}, File={fname}, Round={round_id}")
    conn, addr = sock.accept()
    print(f"[Server] Connection from {addr}")
    conn.settimeout(10)  # ✅ 新增：防止阻塞在某个阶段卡死

    recv_bytes = 0
    delay_sum = 0
    chunk_count = 0
    start_time = time.time()

    try:
        while True:
            try:
                data = recv_exact(conn, CHUNK_SIZE)
            except (ConnectionError, TimeoutError) as e:
                print(f"[Warning] 连接结束: {e}")
                break
            recv_time = time.time()
            try:
                send_ts = struct.unpack("!d", data[:8])[0]
            except Exception as e:
                print(f"[Error] 无法解析时间戳: {e}")
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
        print(f"[Error] 未收到数据: {sched}-{fname} Round {round_id}")

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
