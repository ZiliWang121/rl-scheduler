#!/usr/bin/env python3
"""
UE 发送端脚本（多文件、多轮发送）：
- 每个文件发送 N_ROUNDS 次（可通过命令行参数指定）
- 每块 1024 字节，前 8 字节为发送时间戳（float64）
- 每轮之间 sleep 控制节奏
"""

import socket
import struct
import time
import os
import sys  # ← 新增：用于接收命令行参数

# ------------------- 配置区域 -------------------
SERVER_IP = "192.168.56.107"
SERVER_PORT = 8888
CHUNK_SIZE = 1024
INTERVAL = 0

# 默认轮数（可被命令行参数覆盖）
N_ROUNDS = 3

FILE_LIST = [
    "testfiles/64KB.file",
    "testfiles/256KB.file",
    "testfiles/8MB.file",
    "testfiles/64MB.file"
]
# ------------------------------------------------

# 新增：通过命令行参数修改 N_ROUNDS
if len(sys.argv) >= 2:
    try:
        N_ROUNDS = int(sys.argv[1])
        print(f"[Config] Using N_ROUNDS = {N_ROUNDS} from argument")
    except ValueError:
        print("[Warning] Invalid round number argument. Using default.")

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

# ⚠️ 新增：首次连接，发送 4 字节的 N_ROUNDS 给 server
first_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
first_conn.connect((SERVER_IP, SERVER_PORT))
first_conn.sendall(struct.pack("!I", N_ROUNDS))  # 网络字节序整数
first_conn.close()
time.sleep(20)

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
        time.sleep(20)
