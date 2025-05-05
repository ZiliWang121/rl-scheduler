#!/usr/bin/env python3
"""
Server 脚本，用于接收 UE 发来的上行数据包，并记录以下信息：
- Application Delay：每个包从 UE 应用发出，到此接收端接收的延迟
- Application Goodput：每秒钟接收到的应用数据量（不含 TCP 重传/开销）
- Download Time：整体传输完毕的耗时
"""

import socket
import struct
import time
import csv

# --- 配置部分 ---
LISTEN_IP = "0.0.0.0"        # 监听所有网卡（适合测试）
LISTEN_PORT = 8888           # 要和 UE 一致
PAYLOAD_SIZE = 1024          # 每个包大小（固定），前8字节是发送时间戳
CSV_FILE = "recv_log.csv"    # 输出日志文件
# ----------------

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((LISTEN_IP, LISTEN_PORT))
sock.listen(1)

print(f"[Server] Waiting for UE to connect...")
conn, addr = sock.accept()
print(f"[Server] Connection from {addr}")

# 打开 CSV 日志文件，记录 Delay + Goodput
csvfile = open(CSV_FILE, "w", newline='')
csvwriter = csv.writer(csvfile)
csvwriter.writerow(["Packet#", "Delay(ms)", "Goodput(KB/s)", "RecvTime"])

recv_count = 0
recv_bytes = 0
start_time = time.time()   # 用于计算 Download Time 和 Goodput

try:
    while True:
        data = conn.recv(PAYLOAD_SIZE)
        if not data:
            break  # EOF，client 主动关闭连接
        recv_time = time.time()

        if len(data) < 8:
            print(f"[WARN] Received packet too short")
            continue

        # 从前8字节中提取发送时间戳（float64）
        send_ts = struct.unpack("!d", data[:8])[0]
        delay_ms = (recv_time - send_ts) * 1000  # 转换为毫秒

        # 更新 Goodput 统计
        recv_count += 1
        recv_bytes += len(data)
        duration = recv_time - start_time
        goodput_kbps = (recv_bytes / 1024) / duration if duration > 0 else 
0

        print(f"[Recv] #{recv_count} | Delay = {delay_ms:.2f} ms | Goodput 
= {goodput_kbps:.2f} KB/s")
        csvwriter.writerow([recv_count, delay_ms, goodput_kbps, 
recv_time])

finally:
    end_time = time.time()
    conn.close()
    sock.close()
    csvfile.close()

    total_time = end_time - start_time
    print(f"[Done] Total download time: {total_time:.2f} s")

