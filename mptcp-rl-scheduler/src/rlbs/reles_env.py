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
        state = self._build_state()
        self.last_state = state
        return state

    def step(self, action):
        # ✅ 修复：将 tensor 结构转换为 Python list 后再 int()
        action_list = [int(a) for a in action.detach().cpu().numpy().flatten()]
        mpsched.set_seg([self.fd] + action_list)

        try:
            for _ in range(100):
                import os
                os.write(self.fd, b'x' * 1400)
                time.sleep(0.005)
        except Exception as e:
            print("[ERROR] os.write failed:", e)

        time.sleep(self.time)
        next_state = self._build_state()

        if self.last_state is None:
            reward = 0
        else:
            seg_diff = (next_state[:, 0] - self.last_state[:, 0]).sum()
            rtt_term = next_state[:, 1].sum()
            reward = seg_diff + self.alpha * rtt_term

        self.last_state = next_state
        return next_state, reward, False

    def _build_state(self):
        sub_info = mpsched.get_sub_info(self.fd)
        state = np.zeros((self.k * self.max_flows, 8), dtype=np.float32)

        for i, s in enumerate(sub_info):
            if i >= self.k * self.max_flows:
                break
            state[i, :] = s  # s is assumed to be 8 fields long

        return state

    def update_fd(self, fd):
        self.fd = fd
