import socket
import time
import numpy as np
import mpsched

class Env:
    def __init__(self, server_ip, server_port, time_interval, alpha):
        self.time = time_interval
        self.alpha = alpha
        self.sock = None
        self.fd = None
        self.last_state = None
        self.server_ip = server_ip
        self.server_port = server_port

        self.connect_socket()

    def connect_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server_ip, self.server_port))
        self.fd = self.sock.fileno()

    def get_state(self):
        subflows = mpsched.get_sub_info(self.fd)
        state = []
        for s in subflows:
            segs_out, rtt, cwnd, unacked, retrans, *_ = s
            if rtt == 0: rtt = 1  # 防除0
            state.append([segs_out, 1e6/rtt, cwnd, unacked, retrans])
        state = np.array(state, dtype=np.float32)
        self.last_state = state
        return state

    def step(self, action):
        # 设置动作（段数分配）
        mpsched.set_seg([self.fd] + list(map(int, action)))

        # 等待调度起效
        time.sleep(self.time)

        # 获取新状态
        subflows = mpsched.get_sub_info(self.fd)
        next_state = []
        for s in subflows:
            segs_out, rtt, cwnd, unacked, retrans, *_ = s
            if rtt == 0: rtt = 1
            next_state.append([segs_out, 1e6/rtt, cwnd, unacked, retrans])
        next_state = np.array(next_state, dtype=np.float32)

        # 计算奖励（吞吐增量 + RTT逆）
        if self.last_state is None:
            reward = 0
        else:
            seg_diff = (next_state[:, 0] - self.last_state[:, 0]).sum()
            rtt_term = next_state[:, 1].sum()
            reward = seg_diff + self.alpha * rtt_term

        self.last_state = next_state
        return next_state, reward
