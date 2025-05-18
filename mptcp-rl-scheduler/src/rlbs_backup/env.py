import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import os

class Env:
    def __init__(self, state_file, perf_file, gamma=0.99):
        self.state_data = pd.read_csv(state_file)
        self.perf_data = pd.read_csv(perf_file)
        self.gamma = gamma

        self.num_subflows = self._get_num_subflows()
        self.current_step = 0

        self.state_dim = 8 * self.num_subflows  # ⚡注意⚡ 这里改成了8，因为每个子流8个指标
        self.action_dim = self.num_subflows

        self.states = self._build_states()
        self.rewards = self._build_rewards()

    def _get_num_subflows(self):
        # 从 state.csv 第一行推断子流数量
        columns = list(self.state_data.columns)
        # state默认每个子流有8项，且都是子流编号为0,1,2...
        subflow_indices = set()
        for col in columns:
            if '_' in col:
                idx = int(col.split('_')[0])
                subflow_indices.add(idx)
        return len(subflow_indices)

    def _build_states(self):
        # ⚡构建状态矩阵，每一行是一个时刻的所有子流的8项指标拼接
        states = []
        for _, row in self.state_data.iterrows():
            state = []
            for i in range(self.num_subflows):
                for metric in ['cwnd', 'rtt', 'unacked', 'loss', 'data_segs_out', 'srtt', 'rcv_ooopack', 'snd_wnd']:
                    state.append(row.get(f'{i}_{metric}', 0))
            states.append(state)
        return torch.FloatTensor(states)

    def _build_rewards(self):
        # ⚡从perf_data.csv直接拿reward：throughput - α * rtt - β * loss
        rewards = []
        alpha = 1.0
        beta = 1.0
        for _, row in self.perf_data.iterrows():
            reward = row['throughput_mbps'] - alpha * row['latency_max'] - beta * row['segment_loss_rate_weighted']
            rewards.append(reward)
        return torch.FloatTensor(rewards)

    def reset(self):
        self.current_step = 0
        return self.states[self.current_step]

    def step(self, action):
        # 目前是offline训练，所以只是顺序走
        reward = self.rewards[self.current_step]
        self.current_step += 1
        done = self.current_step >= len(self.states)
        next_state = None if done else self.states[self.current_step]
        return next_state, reward, done, {}

