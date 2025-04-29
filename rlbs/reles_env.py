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

    def get_state(self):
        subflows = mpsched.get_sub_info(self.fd)
        state = []
        for s in subflows:
            segs_out, rtt, cwnd, unacked, retrans, *_ = s
            if rtt == 0:
                rtt = 1
            state.append([segs_out, 1e6 / rtt, cwnd, unacked, retrans])
        state = np.array(state, dtype=np.float32)
        self.last_state = state
        return state

    def step(self, action):
        mpsched.set_seg([self.fd] + list(map(int, action)))
        time.sleep(self.time)

        subflows = mpsched.get_sub_info(self.fd)
        next_state = []
        for s in subflows:
            segs_out, rtt, cwnd, unacked, retrans, *_ = s
            if rtt == 0:
                rtt = 1
            next_state.append([segs_out, 1e6 / rtt, cwnd, unacked, retrans])
        next_state = np.array(next_state, dtype=np.float32)

        if self.last_state is None:
            reward = 0
        else:
            seg_diff = (next_state[:, 0] - self.last_state[:, 0]).sum()
            rtt_term = next_state[:, 1].sum()
            reward = seg_diff + self.alpha * rtt_term

        self.last_state = next_state
        return next_state, reward
