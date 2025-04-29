import configparser
import agent
from replay_memory import ReplayMemory
from ounoise import OUNoise
from naf_lstm import NAF_LSTM
from reles_env import Env
import numpy as np

cfg = configparser.ConfigParser()
cfg.read("config.ini")

state_dim = 2 * 5  # 两个子流，每条5个指标
action_dim = 2     # 两条路径，分别的段数

env = Env(server_ip="192.168.56.107",
          server_port=8888,
          time_interval=cfg.getfloat("env", "time"),
          alpha=cfg.getfloat("env", "alpha"))

memory = ReplayMemory(cfg.getint("replaymemory", "capacity"))
noise = OUNoise(action_dim)

offline_agent = agent.Offline_Agent(cfg, memory)
online_agent = agent.Online_Agent(env.fd, cfg, memory)

offline_agent.start()
online_agent.start()

offline_agent.join()
online_agent.join()
