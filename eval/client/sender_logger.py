#!/usr/bin/env python3
import socket
import struct
import time

# ------------------ 配置区域 ------------------
SERVER_IP = "192.168.56.107"   # Server VM 的公网IP或代理出口IP
SERVER_PORT = 8888             # 与 server 端保持一致
PAYLOAD_SIZE = 1024            # 每个包总大小
INTERVAL = 0.01                # 每个包之间间隔（秒）
TOTAL_PACKETS = 1000           # 发送多少个包
# --------------------------------------------

# 创建 socket，使用 MPTCP 的用户空间效果（默认透明支持）
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))
print(f"[Client] Connected to server {SERVER_IP}:{SERVER_PORT}")

for i in range(TOTAL_PACKETS):
    send_ts = time.time()
    payload = struct.pack("!d", send_ts) + b'x' * (PAYLOAD_SIZE - 8)
    sock.sendall(payload)
    print(f"[Client] Sent packet {i+1}")
    time.sleep(INTERVAL)

sock.close()
print("[Client] All packets sent.")
