#!/usr/bin/env python3
import socket
import struct
import time
import csv

# ------------------ 配置区域 ------------------
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 8888
PAYLOAD_SIZE = 1024
CSV_FILE = "recv_log.csv"
# --------------------------------------------

# 确保完整接收一个包的函数
def recv_full(conn, length):
    buf = b''
    while len(buf) < length:
        part = conn.recv(length - len(buf))
        if not part:
            return None
        buf += part
    return buf

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((LISTEN_IP, LISTEN_PORT))
sock.listen(1)

print(f"[Server] Listening on {LISTEN_IP}:{LISTEN_PORT} ...")
conn, addr = sock.accept()
print(f"[Server] Connection established from {addr}")

csvfile = open(CSV_FILE, "w", newline='')
csvwriter = csv.writer(csvfile)
csvwriter.writerow(["Packet#", "Delay(ms)", "Goodput(KB/s)", "RecvTime"])

recv_count = 0
recv_bytes = 0
start_time = time.time()

try:
    while True:
        data = recv_full(conn, PAYLOAD_SIZE)
        recv_time = time.time()
        if data is None:
            print("[Info] Client closed connection.")
            break

        if len(data) != PAYLOAD_SIZE:
            print(f"[Warning] Received incorrect packet length: {len(data)}")
            continue

        try:
            send_ts = struct.unpack("!d", data[:8])[0]
            delay_ms = (recv_time - send_ts) * 1000
        except Exception as e:
            print(f"[Error] Failed to decode timestamp: {e}")
            continue

        recv_count += 1
        recv_bytes += len(data)
        duration = recv_time - start_time
        goodput_kbps = (recv_bytes / 1024) / duration if duration > 0 else 0

        print(f"[Server] Packet {recv_count} | Delay: {delay_ms:.2f} ms | Goodput: {goodput_kbps:.2f} KB/s")
        csvwriter.writerow([recv_count, delay_ms, goodput_kbps, recv_time])

finally:
    end_time = time.time()
    total_time = end_time - start_time
    print(f"[Done] Download complete. Total download time: {total_time:.3f} seconds")
    conn.close()
    sock.close()
    csvfile.close()
