import time
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

    def reset(self):
        # 与原 env.py 完全一致，返回初始状态
        subflows = mpsched.get_sub_info(self.fd)
        return self._build_state(subflows)

    def step(self, action):
        mpsched.set_seg([self.fd] + [int(a) for a in action])

        for _ in range(100):  # 向 server 发数据触发路径
            try:
                import os
                os.write(self.fd, b'x' * 1400)
            except Exception as e:
                print("[ERROR] os.write failed:", e)
                break
            time.sleep(0.005)

        time.sleep(self.time)
        subflows = mpsched.get_sub_info(self.fd)
        next_state = self._build_state(subflows)

        if self.last_state is None:
            reward = 0
        else:
            seg_diff = (next_state[:, 0] - self.last_state[:, 0]).sum()
            rtt_term = next_state[:, 1].sum()
            reward = seg_diff + self.alpha * rtt_term

        self.last_state = next_state
        return next_state, reward, False  # False 表示未结束

    def update_fd(self, fd):
        self.fd = fd

    def _build_state(self, subflows):
        state = []
        for s in subflows:
            segs_out, rtt, cwnd, unacked, retrans, *_ = s
            if rtt == 0: rtt = 1
            state.append([segs_out, 1e6/rtt, cwnd, unacked, retrans])
        state = np.array(state, dtype=np.float32)
        self.last_state = state
        return state
