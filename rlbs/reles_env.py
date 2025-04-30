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
        self.tp = [[] for _ in range(self.max_flows)]
        self.rtt = [[] for _ in range(self.max_flows)]
        self.cwnd = [[] for _ in range(self.max_flows)]
        self.rr = [[] for _ in range(self.max_flows)]
        self.in_flight = [[] for _ in range(self.max_flows)]
        self.last = None

    def reset(self):
        self.last = mpsched.get_sub_info(self.fd)
        for _ in range(self.k):
            subs = mpsched.get_sub_info(self.fd)

            for j in range(self.max_flows):
                if len(self.tp[j]) == self.k:
                    self.tp[j].pop(0)
                    self.rtt[j].pop(0)
                    self.cwnd[j].pop(0)
                    self.rr[j].pop(0)
                    self.in_flight[j].pop(0)

                if len(self.last) < self.max_flows:
                    for _ in range(self.max_flows - len(self.last)):
                        self.last.append([0, 0, 0, 0, 0])
                if len(subs) < self.max_flows:
                    for _ in range(self.max_flows - len(subs)):
                        subs.append([0, 0, 0, 0, 0])

                self.tp[j].append(np.abs(subs[j][0] - self.last[j][0]) * 1.44)
                self.rtt[j].append(subs[j][1] / 1000)
                self.cwnd[j].append((subs[j][2] + self.last[j][2]) / 2)
                self.rr[j].append(np.abs(subs[j][3] - self.last[j][3]))
                self.in_flight[j].append(np.abs(subs[j][4] - self.last[j][4]))

            self.last = subs
            time.sleep(self.time / 10)

        return [self.tp[0], self.tp[1], self.rtt[0], self.rtt[1],
                self.cwnd[0], self.cwnd[1], self.rr[0], self.rr[1],
                self.in_flight[0], self.in_flight[1]]

    def step(self, action):
        mpsched.set_seg([self.fd] + list(map(int, action)))
        try:
            for _ in range(100):
                os.write(self.fd, b'x' * 1400)
                time.sleep(0.01)
        except Exception as e:
            print("[ERROR] os.write failed:", e)

        time.sleep(self.time)

        subs = mpsched.get_sub_info(self.fd)
        for j in range(self.max_flows):
            if len(self.tp[j]) == self.k:
                self.tp[j].pop(0)
                self.rtt[j].pop(0)
                self.cwnd[j].pop(0)
                self.rr[j].pop(0)
                self.in_flight[j].pop(0)

            if len(self.last) < self.max_flows:
                for _ in range(self.max_flows - len(self.last)):
                    self.last.append([0, 0, 0, 0, 0])
            if len(subs) < self.max_flows:
                for _ in range(self.max_flows - len(subs)):
                    subs.append([0, 0, 0, 0, 0])

            self.tp[j].append(np.abs(subs[j][0] - self.last[j][0]) * 1.44)
            self.rtt[j].append(subs[j][1] / 1000)
            self.cwnd[j].append((subs[j][2] + self.last[j][2]) / 2)
            self.rr[j].append(np.abs(subs[j][3] - self.last[j][3]))
            self.in_flight[j].append(np.abs(subs[j][4] - self.last[j][4]))

        self.last = subs

        reward = (self.tp[0][-1] + self.tp[1][-1])
        if reward != 0:
            reward -= (1 / reward) * self.alpha * (
                self.rtt[0][-1] * self.tp[0][-1] + self.rtt[1][-1] * self.tp[1][-1])
        reward -= self.b * (self.in_flight[0][-1] + self.in_flight[1][-1])

        return [self.tp[0], self.tp[1], self.rtt[0], self.rtt[1],
                self.cwnd[0], self.cwnd[1], self.rr[0], self.rr[1],
                self.in_flight[0], self.in_flight[1]], reward, False

    def update_fd(self, fd):
        self.fd = fd
