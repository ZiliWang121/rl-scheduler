#!/usr/bin/env/python


import time
import os
import sys
import torch
import pandas as pd
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
import numpy as np
import matplotlib.pyplot as plt
import threading
import random
from matplotlib import pyplot as plt
from threading import Event
from multiprocessing.pool import ThreadPool
import shutil
from datetime import datetime
import subprocess
import re


def start_server(host,scheduler,scenario,server_arguments):
	print("starting server")
	host.cmd("cd ..")
	host.cmd("cd src")
	host.cmd("cd "+scheduler[1]+"")
	host.cmd("sudo python3 server.py " +str(server_arguments[0]) + " " + str(server_arguments[1])+ " &> ../results/server_results"+scheduler[0]+scenario+"")
	if scheduler[0] == "blest" or scheduler[0] == "default":
		host.cmd("sudo dmesg -t &> ../results/server_results"+scheduler[0]+scenario+"")
		
	
def start_client(net,l1,l2,host,event,scheduler,scenario,client_arguments):
	host.cmd("cd ..")
	host.cmd("cd src")
	host.cmd("cd client")
	now = datetime.now().replace(microsecond=0)
	start_putil = now.strftime("%Y-%m-%d %H:%M:%S")
	
	host.cmd("sudo python3 client.py "+str(client_arguments[0])+" "+str(client_arguments[1])+
	" & > ../results/client_results"+scheduler[0]+scenario+"") # &> redirects stderr and stdout to file
	delay_data = []
	bw_data = []
	while True:
		if event.is_set():
			break
		if scenario.find("static") != -1:
			if scheduler[0] == "none":
				delay_data.append((host.intfs[0].params["delay"],0))
				bw_data.append((host.intfs[0].params["bw"],0))
			else:
				delay_data.append((host.intfs[0].params["delay"],host.intfs[1].params["delay"]))
				bw_data.append((host.intfs[0].params["bw"],host.intfs[1].params["bw"]))

		elif scenario.find("dynamic") != -1:
			
			delay_1 = max(np.random.normal(loc=20,scale=70),15)
			bw_1 = max(np.random.normal(loc=900,scale=200),850)
		
			
			delay_2 = max(np.random.normal(loc=20,scale=70),15)
			bw_2 = max(np.random.normal(loc=150,scale=100),140)
			
			delay_data.append((delay_1,delay_2))
			bw_data.append((bw_1,bw_2))
			
			delay_1 = str(round(delay_1)) + "ms"
			delay_2 = str(round(delay_2)) + "ms"
			
			host.intfs[0].config(delay=delay_2,bw=bw_2)
			if scheduler[0] != "none":
				host.intfs[1].config(delay=delay_1,bw=bw_1)
				print(host.intfs[0].params["delay"],host.intfs[1].params["delay"],
				host.intfs[0].params["bw"],host.intfs[1].params["bw"])
		
		time.sleep(5)
	return delay_data,bw_data,start_putil
	
			
def mininet_setup(scheduler):
	os.system('sudo mn -c')
	if scheduler != "none":
		os.system('sysctl -w net.mptcp.mptcp_enabled=1')
		os.system('sysctl -w net.mptcp.mptcp_path_manager=fullmesh')
		os.system('sysctl -w net.mptcp.mptcp_scheduler=%s'%(scheduler))
		os.system("sudo modprobe mptcp_olia")
		os.system("sudo sysctl -w net.ipv4.tcp_congestion_control=cubic")
	else:
		os.system("sysctl -w net.mptcp.mptcp_enabled=0")
		os.system("sudo sysctl -w net.ipv4.tcp_congestion_control=cubic")
		
	
	setLogLevel('info')

	net = Mininet( cleanup=True)
	
	h1 = net.addHost ( 'h1',ip='10.0.1.1')
	h2 = net.addHost('h2',ip="10.0.2.10")

	s3= net.addSwitch('s3')
		
	c0 = net.addController('c0')

	l2 = net.addLink(h1,s3,cls=TCLink,bw=140,delay='14.6ms',jitter='2.4ms',loss=0.1)#4G with routing l2 is 2nd index
	
	if scheduler != "none":
		l1 = net.addLink(h1,s3,cls=TCLink,bw=1000,delay='13.7ms',jitter='3.2ms',loss=0.1)#5G
		h1.setIP('10.0.2.2',intf='h1-eth1')
	else:
		l1 = 0	
	
	net.addLink(h2,s3,cls=TCLink,bw=1000)
	
	h1.setIP('10.0.1.1',intf='h1-eth0') 
	h2.setIP('10.0.2.10',intf='h2-eth0')
	
	
	h1.cmd('ip rule add from 10.0.1.1 table 1')
	h1.cmd('ip rule add from 10.0.2.2 table 2')
	
	h1.cmd('ip route add 10.0.1.0/8 dev h1-eth0 scope link table 1')
	h1.cmd('ip route add default via 10.0.2.10 dev h1-eth0 table 1')
	
	h1.cmd('ip route add 10.0.2.0/8 dev h1-eth1 scope link table 2')
	h1.cmd('ip route add default via 10.0.2.10 dev h1-eth1 table 2') 
	
	
	net.start() 
	time.sleep(5)
	net.pingAll()
	
	return h1,h2,net,l1,l2
	
def debug(scheduler,scenario):
	
	h1,h2,net,l1,l2 = mininet_setup(scheduler[0])
	event= Event()

	h2.cmd("cd ..")
	h2.cmd("cd src")
	h2.cmd("cd "+scheduler[1]+"")
	
	h1.cmd("cd ..")
	h1.cmd("cd src")
	h1.cmd("cd client")
	h1.cmd("xterm &")
	h2.cmd("xterm &")
	time.sleep(5)
	
	
	CLI(net)
	
def test(scheduler,scenario,client_arguments,server_arguments):
	
	timeout = True
	
	event = Event()
	h1,h2,net,l1,l2 = mininet_setup(scheduler[0])
	print(scenario)
	print(client_arguments[1])	
	pool = ThreadPool(processes=1)
		
	t1 = threading.Thread(target=start_server,args=(h2,scheduler,scenario,server_arguments))
	t1.daemon = True

	t1.start()
	time.sleep(40) #start client and start process of randomizing data
	async_result = pool.apply_async(start_client,args=(net,l1,l2,h1,event,scheduler,scenario,client_arguments))
	if client_arguments[1] == "random":
		file_size = 2
	elif client_arguments[1].find("kb") != -1:
		file_size = 1
	else:
		file_size = int(re.findall(r'\d+',client_arguments[1])[0]) 
	timeout_ = 300*(client_arguments[0]/150)*(file_size/2)
	print(timeout_)
	t1.join(timeout=timeout_)
	if t1.is_alive():
		#os.execv(sys.executable, ['python'] + sys.argv) #sys.argv[0],sys.argv)
		print("test")
	event.set()
	delay_data,bw_data,start_putil = async_result.get()	
	
	return delay_data,bw_data,start_putil
	

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Give scheduler name for debug,test or training')
	parser.add_argument('--scheduler',type=int,default=0,help='Name of the scheduler')
	parser.add_argument('--action',type=int,default=0,help='choose whether to debug(0),test_scheduler(1) or test_all(2) with scheduler')
	parser.add_argument("--scenario",type=str,default="static",help="choose static(0) or dynamic(1) links")
	parser.add_argument("--train",type=int,default=150,help="number of file transfers to train learning models")
	parser.add_argument("--continued",action="store_true",help="continue training with current memory ?")
	parser.add_argument("--file",type=str,default="2mb.dat",help="File name for file transfer used for different file sizes or random")
	#make scheduer under testing 0-5 and action 0-2
	args = parser.parse_args()
	
	np.random.seed(42)
	
	base_schedulers = (("none","base","TCP"),("default","base","default"),("blest","base","blest"))
	RL_schedulers = (("reles","reles","reles"),("falcon","falcon","falcon"),("reles","reles_ext","reles_ext"),("falcon","falcon_ext","falcon_ext"))
	schedulers = np.concatenate((base_schedulers,RL_schedulers))
	scenario = args.scenario
	results_path = "test_results/"
	os.makedirs(results_path,exist_ok=True)
	mininet_data = []
	under_testing = args.scheduler
	client_arguments = (args.train,args.file)
	server_arguments = (0,scenario)
	if args.continued or args.train == 150:
		server_arguments = (1,scenario) #add train and amount to server arguments to test if timeout ?
	print(server_arguments[0])
	if args.action == 0:
		debug(scheduler=schedulers[under_testing],scenario=scenario)
		
		quit()
	elif args.action ==2 or args.action == 1:
		for i in range(len(schedulers)):
			if args.action ==1:
				scheduler = schedulers[under_testing]
			else:
				scheduler = schedulers[i]
			print(scheduler[0])
			print(server_arguments)
			mininet_delay,mininet_bw,start_putil = test(scheduler,scenario,client_arguments,server_arguments)
			client_metrics = pd.read_csv("../src/client/client_metrics.csv")
			mininet_metrics = pd.DataFrame({"delay":mininet_delay,
							"bandwidth":mininet_bw}) 
			
			path_metrics = pd.DataFrame()
			if scheduler[0] != "none" and args.train == 150:
				cmd = ['journalctl', '--since='+start_putil , '--dmesg', '-p7', '--output', 'cat']
				output = subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]
				output = str(output)
				#if len output != 0
				output = re.findall(r'\d+',output)
				i=0
				while True:
					if output[i] == "1":
						output.pop(i-1)
					i+= 1
					if i>= len(output):
						break
					
				path_usage1 = output.count("16842762") #16777226 defined as subflow 1
				path_usage2 = output.count("33685514") #33554442defined as subflow 2
				path_usage3 = output.count("50528266")
				path_usage = [path_usage1,path_usage2] 
				print(path_usage)
				path_metrics = pd.DataFrame({"Usage":path_usage})
				print(path_metrics)
	
			mininet_data.append((mininet_delay,mininet_bw))
			performance_metrics = pd.concat([client_metrics,mininet_metrics,path_metrics],axis=1)
			performance_metrics.to_csv("test_results/"+scheduler[2]+scenario+".csv")
			if args.action ==1:
				break
	

