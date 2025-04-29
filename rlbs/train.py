import configparser, os, torch
from threading import Event
import agent
from replay_memory import ReplayMemory
from ounoise import OUNoise
from naf_lstm import NAF_LSTM
from reles_env import Env
import numpy as np

# 1. 读取配置
cfg = configparser.ConfigParser()
cfg.read("config.ini")

state_dim = cfg.getint("env", "k") * cfg.getint("env", "max_num_subflows") * 5
action_dim = cfg.getint("env", "max_num_subflows")

# 2. 初始化 socket 环境（连接到你 server 虚拟机）
try:
    env = Env(server_ip="192.168.56.107",
              server_port=8888,
              time_interval=cfg.getfloat("env", "time"),
              alpha=cfg.getfloat("env", "alpha"))
except Exception as e:
    print(f"[ERROR] Socket connection to Server failed: {e}")
    exit(1)

# 3. 初始化经验池和噪声
memory = ReplayMemory(cfg.getint("replaymemory", "capacity"))
noise = OUNoise(action_dim)
event = Event()
agent_file = cfg.get("nafcnn", "agent")

# 4. 如果模型文件不存在则新建（源仓库逻辑）
if not os.path.exists(agent_file):
    print(f"[INFO] No model file found. Initializing new agent at '{agent_file}'")
    model = NAF_LSTM(
        gamma=cfg.getfloat("nafcnn", "gamma"),
        tau=cfg.getfloat("nafcnn", "tau"),
        hidden_size=cfg.getint("nafcnn", "hidden_size"),
        num_inputs=state_dim,
        action_space=action_dim
    )
    torch.save(model, agent_file)
else:
    print(f"[INFO] Using existing model '{agent_file}'")

# 5. 启动强化学习线程（与 server.py 完全一致）
offline_agent = agent.Offline_Agent(cfg, agent_file, memory, event)
online_agent = agent.Online_Agent(env.fd, cfg, memory, event)

offline_agent.start()
online_agent.start()
offline_agent.join()
online_agent.join()
