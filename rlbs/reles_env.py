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
        subflows = mpsched.get_sub_info(self.fd)
        state = self._build_state(subflows)
        self.last_state = state
        return state

    def step(self, action):
        mpsched.set_seg([self.fd] + [int(a) for a in action])

        # 发一些实际数据，确保 MPTCP 传输激活
        try:
            for _ in range(100):
                import os
                os.write(self.fd, b'x' * 1400)
                time.sleep(0.005)
        except Exception as e:
            print("[ERROR] os.write failed:", e)

        time.sleep(self.time)
        subflows = mpsched.get_sub_info(self.fd)
        next_state = self._build_state(subflows)

        # 计算 reward
        if self.last_state is None:
            reward = 0
        else:
            seg_diff = (next_state[:, 0] - self.last_state[:, 0]).sum()
            rtt_term = next_state[:, 1].sum()
            reward = seg_diff + self.alpha * rtt_term

        self.last_state = next_state
        return next_state, reward, False

    def _build_state(self, subflows):
        state = []
        for s in subflows:
            # 保留所有 8 个指标，确保与 agent.py 中访问位置一致
            state.append([float(x) for x in s])
        return np.array(state, dtype=np.float32)

    def update_fd(self, fd):
        self.fd = fd
