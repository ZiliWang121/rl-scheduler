#!/usr/bin/env python3

import numpy as np
import pandas as pd
import os

class MPTCPEnv:
    """
    适配你Testbed环境的 MPTCP 环境封装。
    读取 state_{scheduler}.csv 文件，用于训练。
    """

    def __init__(self, scheduler="default"):
        """
        初始化
        :param scheduler: 测试的 scheduler 名字
        """
        self.scheduler = scheduler
        self.state_file = f"state_{scheduler}.csv"
        self.metrics_file = f"metrics_{scheduler}.csv"

        if not os.path.exists(self.state_file):
            raise FileNotFoundError(f"{self.state_file} 不存在，请先运行数据采集脚本！")
        if not os.path.exists(self.metrics_file):
            raise FileNotFoundError(f"{self.metrics_file} 不存在，请先运行数据采集脚本！")

        # 读取state和reward数据
        self.states = pd.read_csv(self.state_file).values
        self.metrics = pd.read_csv(self.metrics_file)

        self.max_step = len(self.states)
        self.current_step = 0

    def reset(self):
        """
        重置环境，回到初始状态
        """
        self.current_step = 0
        return self.states[self.current_step]

    def step(self, action):
        """
        执行动作，移动到下一个state
        :param action: agent输出的动作（在这个简单离线训练里，其实不会影响state变化）
        :return: next_state, reward, done
        """
        self.current_step += 1
        done = self.current_step >= self.max_step

        if done:
            next_state = np.zeros_like(self.states[0])
            reward = 0
        else:
            next_state = self.states[self.current_step]
            # 根据 proposal 和 ReLeS 文章，reward = throughput - alpha * RTT - beta * loss
            throughput = self.metrics.loc[self.current_step, 'throughput_mbps']
            rtt = self.metrics.loc[self.current_step, 'latency_max']
            loss = self.metrics.loc[self.current_step, 'segment_loss_rate_weighted']
            # 这里 alpha=0.01, beta=0.1 可根据你 proposal 或实验需要调
            reward = throughput - 0.01 * rtt - 0.1 * loss

        return next_state, reward, done

    def get_state_dim(self):
        """
        返回state的维度（用于初始化神经网络输入）
        """
        return self.states.shape[1]

    def get_action_dim(self):
        """
        返回action维度（用于初始化神经网络输出）
        假设一个动作对应每条子流一个比例
        """
        n_subflows = (self.states.shape[1] - 1) // 8
        return n_subflows

