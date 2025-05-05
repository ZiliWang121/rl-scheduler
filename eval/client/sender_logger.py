#!/usr/bin/env python3
"""
UE 端发送脚本，在 network namespace 中运行，连接到 server 并发送数据。
每个包包含当前时间戳（用于 delay 测量）。
"""

import socket
import struct
import time

# --- 配置部分 ---
SERVER_IP = "192.168.56.107"   # Server 的公网出口 IP
SERVER_PORT = 8888
PAYLOAD_SIZE = 1024            # 每个包大小（前8字节是时间戳）
TOTAL_PACKETS = 1000
INTERVAL = 0.01                # 两包之间的间隔（秒），控制发送速率
# ----------------

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))
print(f"[Client] Connected to server {SERVER_IP}:{SERVER_PORT}")

for i in range(TOTAL_PACKETS):
    send_ts = time.time()
    # 前8字节是发送时间戳，其余填充任意内容
    payload = struct.pack("!d", send_ts) + b'x' * (PAYLOAD_SIZE - 8)
    sock.sendall(payload)
    print(f"[Send] Packet {i+1}")
    time.sleep(INTERVAL)

sock.close()
print("[Client] All packets sent.")

