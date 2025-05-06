#!/usr/bin/env python3
"""
UE 端脚本：将文件分块上传至 Server，并在每块数据前附加发送时间戳。
适用于 MPTCP 测试。
"""

import socket
import struct
import time
import argparse
import os

# ---------------- 参数配置 ----------------
parser = argparse.ArgumentParser()
parser.add_argument('--file', type=str, required=True, help='要发送的文件路径')
parser.add_argument('--server-ip', type=str, required=True, help='服务器 IP')
parser.add_argument('--port', type=int, default=8888, help='服务器端口')
parser.add_argument('--chunk-size', type=int, default=1024, help='每块数据大小（字节）')
args = parser.parse_args()

file_path = args.file
server_ip = args.server_ip
port = args.port
chunk_size = args.chunk_size
assert chunk_size > 8, "块大小必须大于 8 字节（用于时间戳）"

# ---------------------------------------

# 打开文件并连接 Server
file_size = os.path.getsize(file_path)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((server_ip, port))
print(f"[Client] Connected to {server_ip}:{port}, sending {file_path} ({file_size} bytes)...")

with open(file_path, "rb") as f:
    sent_bytes = 0
    while True:
        data = f.read(chunk_size - 8)  # 每块前面预留8字节时间戳
        if not data:
            break
        ts = time.time()
        chunk = struct.pack("!d", ts) + data  # 加入时间戳（float64, 8字节）
        sock.sendall(chunk)
        sent_bytes += len(data)
        print(f"[Client] Sent {sent_bytes}/{file_size} bytes", end="\r")

sock.close()
print(f"\n[Client] Upload complete.")
