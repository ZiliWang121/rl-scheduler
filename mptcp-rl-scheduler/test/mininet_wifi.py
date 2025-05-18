#!/usr/bin/env/python



from mn_wifi.cli import CLI
from mininet.log import setLogLevel,info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mininet.node import Controller
from mn_wifi.wmediumdConnector import interference


import numpy as np
import matplotlib.pyplot as plt
import threading
import random
import pickle
from matplotlib import pyplot as plt
from threading import Event
from multiprocessing.pool import ThreadPool
import os
import time
from MPTCP_test import start_server
from datetime import datetime
import pandas as pd
import subprocess
import re

def start_client(host,event,scheduler,scenario,client_arguments):
	
	mininet_rssi = []
	mininet_pos = []
	mininet_asso = []
	host.cmd("cd ..")
	host.cmd("cd src")
	host.cmd("cd client")
	now = datetime.now().replace(microsecond=0)
	start_putil = now.strftime("%Y-%m-%d %H:%M:%S") 
	host.cmd("sudo python3 client.py "+str(client_arguments[0])+" "+str(client_arguments[1])+
	" & > ../results/client_results"+scheduler[0]+scenario+"") # &> redirects stderr and stdout to file
	
	while True:
		if event.is_set():
			break
		else:
			mininet_rssi.append((float(host.wintfs[0].rssi),float(host.wintfs[1].rssi)))
			mininet_asso.append((str(host.wintfs[0].associatedTo),str(host.wintfs[1].associatedTo)))
			time.sleep(0.5)
	return mininet_rssi,mininet_asso,start_putil

def mininet_wifi(scheduler,scenario):
	os.system('sudo mn -c')
	os.system('sysctl -w net.mptcp.mptcp_enabled=1')
	os.system("sysctl -w net.mptcp.mptcp_debug=1")
	os.system('sysctl -w net.mptcp.mptcp_path_manager=fullmesh')
	print(scheduler)
	os.system('sysctl -w net.mptcp.mptcp_scheduler=%s'%(scheduler))
	os.system("sudo modprobe mptcp_olia")
	os.system("sudo sysctl -w net.ipv4.tcp_congestion_control=cubic")
	
	setLogLevel('info')
	net = Mininet_wifi(controller=Controller,link=wmediumd,wmediumd_mode=interference,cleanup=True) #handover mechanismn SSF
	
	if scenario.find("dynamic") != -1:
		net.setMobilityModel(time=0,model='RandomDirection',seed=20,min_v=25,max_v=28)
		sta1 = net.addStation('sta1',wlans=2,ip='10.0.1.1',min_x=50,max_x=350,min_y=50,max_y=350,txpower=10)
	elif scenario.find("static") != -1:
		sta1 = net.addStation('sta1',wlans=2,ip='10.0.1.1',position='75,50,0')
	h1 = net.addHost('h1',ip='10.0.2.10') #server
	
	#net.associationControl('ssf') #signla strength first association
	
	c0 = net.addController('c0')
	ap1 = net.addAccessPoint('ap1',ssid='ap1-ssid',mode='a',channel=36,position='55,55,0',txpower=13) # default 1 Lifi AP 
	ap2 = net.addAccessPoint('ap2',ssid='ap2-ssid',mode='a',channel=36,position='355,55,0',txpower=13) #4G accespoint
	ap3 = net.addAccessPoint('ap3',ssid='ap3-ssid',mode='a',channel=36,position='355,355,0',txpower=13) 
	ap4 = net.addAccessPoint('ap4',ssid='ap4-ssid',mode='a',channel=36,position='45,355,0',txpower=13) #4G accespoint
	ap5 = net.addAccessPoint('ap5',ssid='ap5-ssid',mode='g',position='1000,1000,0',txpower=40) #4G accespoint
	s1 = net.addSwitch('s1')
	
	
	sta1.set_circle_color('b')
	
	net.setPropagationModel(model="logDistance",exp=3)
	
	net.configureNodes()
	
	
	sta1.setIP('10.0.1.1',intf='sta1-wlan0')
	sta1.setIP('10.0.2.2',intf='sta1-wlan1')
	
	net.addLink(sta1,ap5,0,1)
	net.addLink(ap1,s1)
	net.addLink(ap2,s1)
	net.addLink(ap3,s1)
	net.addLink(ap4,s1)
	net.addLink(ap5,s1)
	net.addLink(s1,h1)
	
	net.plotGraph(max_x = 500,max_y=500)

	sta1.cmd('ip rule add from 10.0.1.1 table 1')
	sta1.cmd('ip rule add from 10.0.2.2 table 2')
	
	sta1.cmd('ip route add 10.0.1.0/8 dev sta1-wlan0 scope link table 1')
	sta1.cmd('ip route add default via 10.0.2.10 dev sta1-wlan0 table 1')
	
	sta1.cmd('ip route add 10.0.2.0/8 dev sta1-wlan1 scope link table 2')
	sta1.cmd('ip route add default via 10.0.2.10 dev sta1-wlan1 table 2') 
	
	
	net.build()
	c0.start()
	ap1.start([c0])
	ap2.start([c0])
	ap3.start([c0])
	ap4.start([c0])
	ap5.start([c0])
	s1.start([c0])
	time.sleep(5)
	net.pingAll()

	
	return sta1,h1,net
	
	
		
def record_mobility(sta,event):
	test = 0
	rssi = []
	sta_pos = []
	while(True):
		rssi.append((float(sta.wintfs[0].rssi),float(sta.wintfs[1].rssi)))
		sta_pos.append(sta.position)
		time.sleep(0.5) 
		if event.is_set():
			break
	
	return rssi,sta_pos

def debug(scheduler,scenario):
	
	sta1,h1,net = mininet_wifi(scheduler[0],scenario)
	
	h1.cmd("cd ..")
	h1.cmd("cd src")
	h1.cmd("cd "+scheduler[1]+"")
	
	sta1.cmd("cd ..")
	sta1.cmd("cd src")
	sta1.cmd("cd client")
	sta1.cmd("xterm &")
	h1.cmd("xterm &")
	time.sleep(5)
	#h1.cmd("sudo python3 client.py &> ../results/client_results"+scheduler+scenario+"")
	CLI(net)
	net.stop()
	
	
def test(scheduler,scenario,client_arguments,server_arguments):
	
	event = Event() 
	sta1,h1,net = mininet_wifi(scheduler[0],scenario)
	
	pool = ThreadPool(processes=1)
	
	t1 = threading.Thread(target=start_server,args=(h1,scheduler,scenario,server_arguments))
	t1.daemon = True
	
	t1.start()
	time.sleep(40) #start client and start process of randomizing data
	
	async_result = pool.apply_async(start_client,args=(sta1,event,scheduler,scenario,client_arguments))
	print(client_arguments[1])
	if client_arguments[1] == "random":
		file_size = 4
	elif client_arguments[1].find("kb") != -1:
		file_size = 1
	else:
		file_size = int(re.findall(r'\d+',client_arguments[1])[0]) 
	timeout_ = 550*(client_arguments[0]/150)*(file_size/2)
	print(timeout_)
	t1.join(timeout=timeout_)
	if t1.is_alive():
		#os.execv(sys.executable, ['python'] + sys.argv) #sys.argv[0],sys.argv)
		print("test")
	event.set()
	
	mininet_rssi,mininet_pos,start_putil = async_result.get()
	
	return mininet_rssi,mininet_pos,start_putil
	
if __name__ == "__main__":

	import argparse
	parser = argparse.ArgumentParser(description='Give scheduler name for debug,test or training')
	parser.add_argument('--scheduler',type=int,default=0,help='Name of the scheduler')
	parser.add_argument('--action',type=int,default=0,help='choose whether to debug(0),test_scheduler(1) or test_all(2) with scheduler')
	parser.add_argument("--scenario",type=str,default="static",help="choose static(0) or dynamic(1) links")
	parser.add_argument("--train",type=int,default=150,help="number of file transfers to train learning models")
	parser.add_argument("--continued",action="store_true",help="continue training with current memory ?")
	parser.add_argument("--file",type=str,default="2mb.dat",help="File name for file transfer used for different file sizes or random")
	args = parser.parse_args()
	
	np.random.seed(42)
	
	base_schedulers = (("default","base","default"),("blest","base","blest"))
	RL_schedulers = (("reles","reles","reles"),("falcon","falcon","falcon"),("reles","reles_ext","reles_ext"),("falcon","falcon_ext","falcon_ext"))
	schedulers = np.concatenate((base_schedulers,RL_schedulers))
	scenario = args.scenario + "wifi"
	results_path = "test_results/"
	os.makedirs(results_path,exist_ok=True)
	mininet_data = []
	under_testing = args.scheduler
	client_arguments = (args.train,args.file)
	server_arguments = (0,scenario)
	if args.continued or args.train == 150:
		server_arguments = (1,scenario)
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
			mininet_rssi,mininet_pos,start_putil = test(scheduler,scenario,client_arguments,server_arguments)
			client_metrics = pd.read_csv("../src/client/client_metrics.csv")
			mininet_metrics = pd.DataFrame({"rssi":mininet_rssi,
							"pos":mininet_pos}) 
			
			path_metrics = pd.DataFrame()
			if args.train == 150:
				cmd = ['journalctl', '--since='+start_putil , '--dmesg', '-p7', '--output', 'cat']
				output = subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]
				output = str(output)
				output = re.findall(r'\d+',output)
				i=0
				while True:
					if output[i] == "1":
						output.pop(i-1)
					i+= 1
					if i>= len(output):
						break
				path_usage1 = output.count("16842762") #defined as subflow 1
				path_usage2 = output.count("33685514") #defined as subflow 2
				path_usage = [path_usage1,path_usage2]
				print(path_usage)
				path_metrics = pd.DataFrame({"Usage":path_usage})
				print(path_metrics)
				
			performance_metrics = pd.concat([client_metrics,mininet_metrics,path_metrics],axis=1)
			performance_metrics.to_csv("test_results/"+scheduler[2]+scenario+".csv")
			if args.action ==1:
				break
	
	

