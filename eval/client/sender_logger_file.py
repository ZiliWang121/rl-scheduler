#!/usr/bin/env python3
import socket
import struct
import time
import os
import sys

SERVER_IP = "192.168.56.107"
SERVER_PORT = 8888
CHUNK_SIZE = 1024
INTERVAL = 0
N_ROUNDS = 3

FILE_LIST = [
    "testfiles/64KB.file",
    "testfiles/256KB.file",
    "testfiles/8MB.file",
    "testfiles/64MB.file"
]

if len(sys.argv) >= 2:
    try:
        N_ROUNDS = int(sys.argv[1])
        print(f"[Config] Using N_ROUNDS = {N_ROUNDS} from argument")
    except ValueError:
        print("[Warning] Invalid round number argument. Using default.")

def connect_retry():
    for attempt in range(3):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_IP, SERVER_PORT))
            return s
        except Exception as e:
            print(f"[Retry] 连接失败 (attempt {attempt + 1}): {e}")
            time.sleep(2)
    raise RuntimeError("连接失败超过最大重试次数")

def send_file(file_path, sock):
    with open(file_path, "rb") as f:
        chunk_num = 0
        while True:
            payload = f.read(CHUNK_SIZE - 8)
            if not payload:
                break
            ts = struct.pack("!d", time.time())
            if len(payload) < CHUNK_SIZE - 8:
                payload += b'x' * (CHUNK_SIZE - 8 - len(payload))
            try:
                sock.sendall(ts + payload)
            except Exception as e:
                print(f"[Error] 发送失败: {e}")
                return -1
            chunk_num += 1
            if INTERVAL > 0:
                time.sleep(INTERVAL)
    return chunk_num

first_conn = connect_retry()
first_conn.sendall(struct.pack("!I", N_ROUNDS))
first_conn.close()
time.sleep(20)

for file_path in FILE_LIST:
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        continue

    for round_id in range(1, N_ROUNDS + 1):
        print(f"\n=== Sending file: {file_path}, Round {round_id} ===")
        sock = connect_retry()
        num_chunks = send_file(file_path, sock)
        sock.close()

        if num_chunks == -1:
            print(f"[Error] 发送失败: {file_path} (Round {round_id})")
        else:
            print(f"[Client] Sent {num_chunks} chunks.")
        time.sleep(20)
