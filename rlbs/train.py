import configparser
from agent import Agent
from replay_memory import ReplayMemory
from ounoise import OUNoise
from naf_lstm import NAF_LSTM
from reles_env import Env
import numpy as np

cfg = configparser.ConfigParser()
cfg.read("config.ini")

state_dim = 2 * 5  # 两个子流，每个5个指标
action_dim = 2     # 每条路径一个segment数

env = Env(server_ip="192.168.56.107",
          server_port=8888,
          time_interval=cfg.getfloat("env", "time"),
          alpha=cfg.getfloat("env", "alpha"))

memory = ReplayMemory(cfg.getint("replaymemory", "capacity"),
                      cfg.get("replaymemory", "memory"))
noise = OUNoise(action_dim)
agent = Agent(state_dim, action_dim, memory, noise,
              gamma=cfg.getfloat("nafcnn", "gamma"),
              tau=cfg.getfloat("nafcnn", "tau"))

for episode in range(cfg.getint("train", "episode")):
    state = env.get_state().flatten()
    agent.model.reset_hidden()
    for _ in range(cfg.getint("train", "interval")):
        action = agent.select_action(state)
        next_state, reward = env.step(action)
        memory.push(state, action, reward, next_state.flatten())
        state = next_state.flatten()
        agent.train(cfg.getint("train", "batch_size"))
    print(f"[Episode {episode}] finished.")
