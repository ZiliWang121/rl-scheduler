#!/usr/bin/env python3
"""
UE 发送端脚本（多文件、多轮发送）：
- 每个文件发送 N_ROUNDS 次
- 每块 1024 字节，前 8 字节为发送时间戳（float64）
- 每轮之间 sleep 控制节奏
"""

import socket
import struct
import time
import os

# ------------------- 配置区域 -------------------
SERVER_IP = "192.168.56.107"     # Server 的 IP 地址
SERVER_PORT = 8888               # Server 监听端口
CHUNK_SIZE = 1024                # 每块大小，前8字节为时间戳
INTERVAL = 0                     # 每块间隔发送时间（秒）
N_ROUNDS = 3                     # 每个文件测试轮数
FILE_LIST = [                    # 要发送的文件列表
    "testfiles/64KB.file",
    "testfiles/256KB.file",
    "testfiles/8MB.file",
    "testfiles/64MB.file"
]
# ------------------------------------------------

def send_file(file_path):
    with open(file_path, "rb") as f:
        chunk_num = 0
        while True:
            payload = f.read(CHUNK_SIZE - 8)
            if not payload:
                break
            ts = struct.pack("!d", time.time())
            if len(payload) < CHUNK_SIZE - 8:
                payload += b'x' * (CHUNK_SIZE - 8 - len(payload))
            sock.sendall(ts + payload)
            chunk_num += 1
            if INTERVAL > 0:
                time.sleep(INTERVAL)
    return chunk_num

for file_path in FILE_LIST:
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        continue

    for round_id in range(1, N_ROUNDS + 1):
        print(f"\n=== Sending file: {file_path}, Round {round_id} ===")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, SERVER_PORT))
        num_chunks = send_file(file_path)
        sock.close()
        print(f"[Client] Sent {num_chunks} chunks.")
        time.sleep(1)  # 每轮间隔 1 秒
