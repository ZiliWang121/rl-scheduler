#!/usr/bin/python3

import sys
import os
import time
import threading
import pickle
from threading import Event
import socket
import torch
from configparser import ConfigParser
from replay_memory import ReplayMemory
from agent import Online_Agent, Offline_Agent
from naf_lstm import NAF_LSTM
from datetime import datetime
import shutil

def main(argv):
    cfg = ConfigParser()
    cfg.read('config.ini')

    IP = "192.168.56.107"
    PORT = 8888

    MEMORY_FILE = cfg.get('replaymemory','memory')
    AGENT_FILE = cfg.get('nafcnn','agent')
    BATCH_SIZE = cfg.getint('train','batch_size')
    MAX_NUM_FLOWS = cfg.getint("env",'max_num_subflows')
    transfer_event = Event()
    CONTINUE_TRAIN = 1

    if os.path.exists(MEMORY_FILE) and CONTINUE_TRAIN:
        with open(MEMORY_FILE,'rb') as f:
            try:
                memory = pickle.load(f)
            except EOFError:
                print("memory EOF error not saved properly")
                memory = ReplayMemory(cfg.getint('replaymemory','capacity'))
    else:
        memory = ReplayMemory(cfg.getint('replaymemory','capacity'))

    if not os.path.exists(AGENT_FILE) or CONTINUE_TRAIN != 1:
        agent = NAF_LSTM(
            gamma=cfg.getfloat('nafcnn','gamma'),
            tau=cfg.getfloat('nafcnn','tau'),
            hidden_size=cfg.getint('nafcnn','hidden_size'),
            num_inputs=cfg.getint('env','k') * MAX_NUM_FLOWS * 5,
            action_space=MAX_NUM_FLOWS
        )
        torch.save(agent, AGENT_FILE)

    # ✅ 自动连接 socat server，并直接触发 episode
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, PORT))
    fd = sock.fileno()
    transfer_event.set()  # 🚨 自动触发，不依赖 HTTP 服务

    off_agent = Offline_Agent(cfg=cfg, model=AGENT_FILE, memory=memory, event=transfer_event)
    off_agent.daemon = True
    on_agent = Online_Agent(fd=fd, cfg=cfg, memory=memory, event=transfer_event)

    off_agent.start()
    on_agent.start()

    try:
        while on_agent.is_alive():
            if len(memory) > BATCH_SIZE and not off_agent.is_alive():
                off_agent = Offline_Agent(cfg=cfg, model=AGENT_FILE, memory=memory, event=transfer_event)
                off_agent.start()
            time.sleep(2)
    except KeyboardInterrupt:
        print("Training interrupted.")
    finally:
        with open(MEMORY_FILE,'wb') as f:
            pickle.dump(memory, f)

if __name__ == '__main__':
    main(sys.argv[1:])
