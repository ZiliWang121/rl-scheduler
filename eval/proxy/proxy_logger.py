
#!/usr/bin/env python3
"""
Script: proxy_logger_wait.py
Purpose:
    Automatically listens for MPTCP connections and logs per-subflow metrics
    for a fixed number of rounds, without requiring manual input of scheduler,
    file size, or round number.

Usage:
    python3 proxy_logger_wait.py --listen_port 8888 --rounds 3 --output proxy_metrics.csv

Requirements:
    - Python C extension `mpsched` must be installed
    - Proxy must establish real MPTCP socket connections (not redirected clones)
"""

import mpsched
import socket
import csv
import struct
import argparse

LINK_MAP = {
    "10.60.0.1": "5G",
    "10.60.0.2": "Wi-Fi"
}

def int_to_ip(ip_int):
    return socket.inet_ntoa(struct.pack("!I", ip_int))

def detect_link_type(dst_ip):
    ip_str = int_to_ip(dst_ip)
    return LINK_MAP.get(ip_str, "Unknown")

def log_metrics_for_connection(fd, round_id, csv_path):
    subs = mpsched.get_sub_info(fd)

    rows = []
    for i, sub in enumerate(subs):
        segs_out = sub[0]
        rtt_us = sub[1]
        dst_ip = sub[5]
        ooopack = sub[6]

        ip_str = int_to_ip(dst_ip)
        link_type = detect_link_type(dst_ip)

        row = {
            "round": round_id,
            "subflow_id": i,
            "link_type": link_type,
            "rtt_us": rtt_us,
            "segs_out": segs_out,
            "recv_ooopack": ooopack
        }
        rows.append(row)

    file_exists = os.path.isfile(csv_path)

    with open(csv_path, "a", newline="") as f:
        fieldnames = ["round", "subflow_id", "link_type", "rtt_us", "segs_out", "recv_ooopack"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"[✓] Logged metrics for round {round_id} with {len(subs)} subflows")

def main():
    parser = argparse.ArgumentParser(description="Proxy logger that waits for MPTCP connections and logs metrics.")
    parser.add_argument("--listen_port", type=int, required=True, help="TCP port to listen on")
    parser.add_argument("--rounds", type=int, required=True, help="Total number of rounds to wait for")
    parser.add_argument("--output", type=str, default="proxy_metrics.csv", help="CSV output file")

    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", args.listen_port))
    sock.listen(5)

    print(f"[Logger] Listening on port {args.listen_port}, expecting {args.rounds} rounds...")

    for round_id in range(1, args.rounds + 1):
        conn, addr = sock.accept()
        print(f"[Logger] Accepted connection from {addr}, round {round_id}")
        fd = conn.fileno()
        mpsched.persist_state(fd)

        # Wait for end of transmission (just read and discard data)
        try:
            while True:
                data = conn.recv(2048)
                if not data:
                    break
        finally:
            conn.close()

        # Log subflow metrics
        log_metrics_for_connection(fd, round_id, args.output)

    sock.close()
    print("[Logger] All rounds complete. Exiting.")

if __name__ == "__main__":
    main()
