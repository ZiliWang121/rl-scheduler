#!/usr/bin/env python3
"""
Server 接收端脚本（支持多轮每文件测试）：
- 每次连接对应一个完整文件
- 统计每轮 avg delay, goodput, download time
- 最后输出各文件总体平均值
"""

import socket
import struct
import time
import csv

# ------------------- 配置区域 -------------------
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 8888
CHUNK_SIZE = 1024
CSV_FILE = "recv_log.csv"     # 输出日志 CSV
N_EXPECTED_FILES = 12         # 例如 4 个文件 * 每个 3 轮
# ------------------------------------------------

def recv_exact(sock, size):
    buf = b''
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("连接断开，提前结束")
        buf += chunk
    return buf

# 准备监听
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((LISTEN_IP, LISTEN_PORT))
sock.listen(5)

print(f"[Server] Listening on {LISTEN_IP}:{LISTEN_PORT}")
csvfile = open(CSV_FILE, "w", newline='')
csvwriter = csv.writer(csvfile)
csvwriter.writerow(["Round#", "NumChunks", "AvgDelay(ms)", "Goodput(KB/s)", "DownloadTime(s)"])

# 总统计
total_chunks = 0
total_delay = 0
total_bytes = 0
total_time = 0
rounds_completed = 0

while rounds_completed < N_EXPECTED_FILES:
    print(f"\n[Server] Waiting for file #{rounds_completed + 1}...")
    conn, addr = sock.accept()
    print(f"[Server] Connection from {addr}")

    start_time = time.time()
    recv_bytes = 0
    delay_sum = 0
    chunk_count = 0

    try:
        while True:
            try:
                data = recv_exact(conn, CHUNK_SIZE)
            except ConnectionError:
                print("[Server] Client closed connection.")
                break

            recv_time = time.time()
            try:
                send_ts = struct.unpack("!d", data[:8])[0]
            except:
                continue
            delay_ms = (recv_time - send_ts) * 1000
            recv_bytes += len(data)
            delay_sum += delay_ms
            chunk_count += 1
    finally:
        conn.close()

    end_time = time.time()
    download_time = end_time - start_time
    avg_delay = delay_sum / chunk_count if chunk_count > 0 else 0
    goodput = (recv_bytes / 1024) / download_time if download_time > 0 else 0

    print(f"[Result] Round {rounds_completed + 1}: {chunk_count} chunks | "
          f"Delay = {avg_delay:.2f} ms | Goodput = {goodput:.2f} KB/s | Time = {download_time:.2f} s")

    csvwriter.writerow([rounds_completed + 1, chunk_count, avg_delay, goodput, download_time])

    # 累计总计数
    total_chunks += chunk_count
    total_delay += delay_sum
    total_bytes += recv_bytes
    total_time += download_time
    rounds_completed += 1

# 输出总结
csvfile.close()
sock.close()

print("\n========= Final Summary =========")
print(f"Total rounds: {rounds_completed}")
print(f"Avg chunks per round: {total_chunks / rounds_completed:.2f}")
print(f"Avg delay: {total_delay / total_chunks:.2f} ms")
print(f"Avg goodput: {(total_bytes / 1024) / total_time:.2f} KB/s")
print(f"Avg download time: {total_time / rounds_completed:.2f} s")
