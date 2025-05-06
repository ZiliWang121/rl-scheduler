#!/usr/bin/env python3
"""
UE 发送端脚本（配合文件下载场景）：
- 将一个文件读取为多个 1024 字节块
- 每块前 8 字节为发送时的时间戳（float64）
- 后续填充为文件内容（不足填 x）
- 每发一块 sleep INTERVAL 控制速率（可设为 0）
"""

import socket
import struct
import time
import os

# ------------------- 配置区域 -------------------
SERVER_IP = "192.168.56.107"     # 接收端 Server 的 IP 地址（你的 server VM）
SERVER_PORT = 8888               # Server 的监听端口
FILE_PATH = "testfiles/64MB.file"  # 要发送的文件路径（可修改）
CHUNK_SIZE = 1024                # 每块大小
INTERVAL = 0                     # 两块之间等待时间（单位：秒）
# ------------------------------------------------

def main():
    # 检查文件是否存在
    if not os.path.exists(FILE_PATH):
        print(f"[Error] File not found: {FILE_PATH}")
        return

    # 创建 TCP socket 并连接 Server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    print(f"[Client] Connected to {SERVER_IP}:{SERVER_PORT}")

    with open(FILE_PATH, "rb") as f:
        chunk_num = 0
        while True:
            payload = f.read(CHUNK_SIZE - 8)  # 留出8字节存时间戳
            if not payload:
                break  # 文件读取完毕

            # 获取当前时间戳（float64，单位秒）
            send_ts = time.time()
            ts_bytes = struct.pack("!d", send_ts)

            # 如果 payload 不足，补充 x 填满
            if len(payload) < CHUNK_SIZE - 8:
                payload += b'x' * (CHUNK_SIZE - 8 - len(payload))

            # 构造完整的数据块（时间戳 + 文件块）
            data_block = ts_bytes + payload
            sock.sendall(data_block)

            chunk_num += 1
            print(f"[Send] Chunk #{chunk_num}")

            if INTERVAL > 0:
                time.sleep(INTERVAL)

    sock.close()
    print("[Client] All chunks sent.")

if __name__ == "__main__":
    main()
