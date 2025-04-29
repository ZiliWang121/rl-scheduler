import configparser
import agent
from replay_memory import ReplayMemory
from ounoise import OUNoise
from naf_lstm import NAF_LSTM
from reles_env import Env
import numpy as np
from threading import Event

cfg = configparser.ConfigParser()
cfg.read("config.ini")

state_dim = 2 * 5
action_dim = 2

# 初始化环境
env = Env(server_ip="192.168.56.107",
          server_port=8888,
          time_interval=cfg.getfloat("env", "time"),
          alpha=cfg.getfloat("env", "alpha"))

# 初始化组件
memory = ReplayMemory(cfg.getint("replaymemory", "capacity"))
noise = OUNoise(action_dim)
event = Event()
model_path = cfg.get("nafcnn", "agent")  # e.g., "agent.pkl"

# 初始化 agent（保持原始结构）
offline_agent = agent.Offline_Agent(cfg, model_path, memory, event)
online_agent = agent.Online_Agent(env.fd, cfg, memory, event)

# 启动训练线程
offline_agent.start()
online_agent.start()
offline_agent.join()
online_agent.join()
