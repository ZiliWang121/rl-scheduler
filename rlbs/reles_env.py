import time
import os
import numpy as np
import mpsched

class Env:
    def __init__(self, fd, time, k, alpha, b, c, max_flows):
        self.fd = fd
        self.time = time
        self.k = k
        self.alpha = alpha
        self.b = b
        self.c = c
        self.max_flows = max_flows
        self.last_state = None

    def get_state(self):
        print("[DEBUG] Getting current subflow state")
        subflows = mpsched.get_sub_info(self.fd)
        state = []
        for s in subflows:
            segs_out, rtt, cwnd, unacked, retrans, *_ = s
            if rtt == 0:
                rtt = 1
            state.append([segs_out, 1e6 / rtt, cwnd, unacked, retrans])
        state = np.array(state, dtype=np.float32)
        self.last_state = state
        print("[DEBUG] Current state:", state)
        return state

    def step(self, action):
        print("[DEBUG] Step with action:", action)
        # 设置调度器动作
        mpsched.set_seg([self.fd] + list(map(int, action)))

        # ✅ 实际发送数据（触发 TCP/MPTCP 路径）
        try:
            os.write(self.fd, b'x' * 1400)  # 立即发送数据
            print("[DEBUG] Sent 1400 bytes to server")
        except Exception as e:
            print("[ERROR] os.write failed:", e)

        time.sleep(self.time)

        subflows = mpsched.get_sub_info(self.fd)
        next_state = []
        for s in subflows:
            segs_out, rtt, cwnd, unacked, retrans, *_ = s
            if rtt == 0:
                rtt = 1
            next_state.append([segs_out, 1e6 / rtt, cwnd, unacked, retrans])
        next_state = np.array(next_state, dtype=np.float32)
        print("[DEBUG] Next state:", next_state)

        if self.last_state is None:
            reward = 0
        else:
            seg_diff = (next_state[:, 0] - self.last_state[:, 0]).sum()
            rtt_term = next_state[:, 1].sum()
            reward = seg_diff + self.alpha * rtt_term

        print("[DEBUG] Reward:", reward)
        self.last_state = next_state
        return next_state, reward
