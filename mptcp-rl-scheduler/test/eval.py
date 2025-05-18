#!/usr/bin/env/python

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import pyplot as plt
import time
import os
from datetime import datetime
import seaborn as sns
from statannotations.Annotator import Annotator
import pandas as pd
import statistics 
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import seaborn as sns
import itertools
import matplotlib
from scipy.stats import mannwhitneyu


def clean_cell_list(list_):
	list_ = list_.replace("'",'')
	list_ = list_.replace("(",'')
	list_ = list_.replace(')', '')
	list_ = list_.replace('ms','')
	list_ = list_.replace('ap','')
	list_ = list_.replace('wlan','')
	list_ = list_.replace('None','0-0')
	return list_


if __name__ == '__main__':
	
	import argparse
	parser = argparse.ArgumentParser(description='Give scheduler name for debug,test or training')
	parser.add_argument('--schedulers',type=int,default=126,help='Name of the schedulers combination to evaluate')
	parser.add_argument("--scenario",type=str,default="static",help="choose static(0) or dynamic(1) links")
	parser.add_argument("--files",action="store_true",help="continue training with current memory ?")
	args = parser.parse_args()
	plot_fsize=13
	TCP_only = (("TCP","4G"),)
	base_schedulers = (("default","default"),("blest","blest"))
	RL_schedulers = (("reles","reles"),("falcon","falcon"),('reles_ext','reles_e'),("falcon_ext","falcon_e"))
	links = ["4G","5G"] #,"WLAN"]
	
	schedulers = np.concatenate((TCP_only,base_schedulers,RL_schedulers))
	all_combinations = []
	
	for L in range(len(schedulers)+1):
		for subset in itertools.combinations(schedulers,L):
			all_combinations.append(subset)
	print(all_combinations[64])
	schedulers = all_combinations[args.schedulers] 
	print(np.array(schedulers)[:,0]) 
	congestion = (("olia","cubic"))
	scenario = args.scenario
	results_path = "test_results/"
	os.makedirs("old_plots/",exist_ok=True)
	xticklabel1 = []
	xticklabel2 = []
	if scenario.find("wifi") != -1:
		links = ["WiFi","LiFi"]
	fig = plt.figure(1,figsize=(6,9))
	gs = GridSpec(3,3,figure=fig)
	fig2 = plt.figure(2,figsize=(6,9))
	gs2 = GridSpec(3,3,figure=fig2)
	
	ax1 = fig.add_subplot(gs[0,:])
	ax2 = fig2.add_subplot(gs[2,:])
	ax3 = fig.add_subplot(gs[1,:])
	ax4 = fig.add_subplot(gs[2,:])
	
	#make new fig for dynamic subplot
	
	all_data = pd.DataFrame()
	for i in range(len(schedulers)):
		print("test_results/"+schedulers[i][0]+scenario+".csv")
		csv = pd.read_csv("test_results/"+schedulers[i][0]+scenario+".csv")
		all_data = pd.concat([all_data,csv["completion time"].dropna().rename("comp"+str(i))],axis=1)
		print(csv["completion time"].dropna().mean())
		ax2.plot(csv["throughput"].dropna())
		
		xticklabel1.append(schedulers[i][1])
		if not schedulers[i][0] == TCP_only[0][0]:
			ax3.bar(i-0.0625,csv['out-of-order 4G'].mean(),width=0.125,color="tab:blue",yerr=np.std(csv['out-of-order 4G']))
			ax3.bar(i+0.0625,csv['out-of-order 5G'].mean(),width=0.125,color="tab:red",yerr=np.std(csv['out-of-order 5G']))
			ax4.bar(i-0.0625,csv["Usage"][0]/sum(csv["Usage"].dropna()),color="tab:blue",width=0.125)
			ax4.bar(i+0.0625,csv["Usage"][1]/sum(csv["Usage"].dropna()),color="tab:red",width=0.125)
			xticklabel2.append(schedulers[i][1])	
		
	
	print(xticklabel1)
	if scenario.find("wifi") != -1:
		ax5 = fig2.add_subplot(gs2[0,:])
		ax6 = fig2.add_subplot(gs2[1,:])
		rssi = ((pd.Series(csv["rssi"].dropna()).apply(clean_cell_list)))
		rssi = [i.split(',') for i in rssi]
		rssi_1 = list(map(float,np.array(rssi)[:,0]))
		rssi_2 = list(map(float,np.array(rssi)[:,1]))
		ax5.plot(rssi_1,color="blue")
		ax5.plot(rssi_2,color="red")
		ax5.legend(["WiFi","LiFi"])
		ax5.grid()
		ax5.set_ylabel("Rssi in dBm",fontsize=plot_fsize)
		ap = pd.Series(csv["pos"].apply(clean_cell_list))
		ax6.plot(ap)
		ax6.grid()
		ax6.set_ylabel("Associated AP-WiFi",fontsize=plot_fsize)
		
	else:
		ax5 = fig2.add_subplot(gs2[0,:])
		ax6 = fig2.add_subplot(gs2[1,:])
		bw = ((pd.Series(csv["bandwidth"].dropna()).apply(clean_cell_list)))
		bw = [i.split(',') for i in bw]
		bw_1 = list(map(float,np.array(bw)[:,0]))
		bw_2 = list(map(float,np.array(bw)[:,1]))
		ax6.plot(bw_1,color="blue")
		ax6.plot(bw_2,color="red")
		ax6.set_ylabel("Bandwidth in MB/s",fontsize=plot_fsize)
		ax6.grid()
		ax6.legend(links)
		delay = ((pd.Series(csv["delay"].dropna()).apply(clean_cell_list)))
		delay = [i.split(',') for i in delay]
		delay_1 = list(map(float,np.array(delay)[:,0]))
		delay_2 = list(map(float,np.array(delay)[:,1]))
		ax5.plot(delay_1,color="blue")
		ax5.plot(delay_2,color="red")
		ax5.grid()
		ax5.set_ylabel("Delay in ms",fontsize=plot_fsize)
		ax5.legend(links)
	idx = np.arange(start=(len(xticklabel1)-len(xticklabel2)),stop=len(xticklabel2)+(len(xticklabel1)-len(xticklabel2)))
	#print(all_data.columns.values.tolist())
	columns = []
	axa = sns.boxplot(data=all_data,ax=ax1,showfliers=False,width=0.35)
	pairs = []
	for k in range(1,len(schedulers)):
		pairs.append(("comp0",all_data.columns[k]))
		
	pairs.append(("comp2","comp4"))
	pairs.append(("comp3","comp5"))
	
	annotator = Annotator(axa,pairs,data=all_data)
	annotator.configure(test="Mann-Whitney-gt",comparisons_correction=None,text_format="full",
	line_width=0.85,text_offset=0.85,fontsize="x-small")
	annotator.apply_and_annotate()
	
	ax1.set_ylabel("Completion Time in s",fontsize=plot_fsize)
	ax1.set_xticklabels(xticklabel1,fontsize=plot_fsize-1)
	ax1.set_axisbelow(True)
	ax1.grid()
	ax2.set_ylabel("Throughput in MB/s",fontsize=plot_fsize)
	ax2.legend(xticklabel1,loc="lower right")
	ax2.set_xlabel("File Transfer",fontsize=plot_fsize)
	ax2.set_axisbelow(True)
	ax2.grid()
	
	ax3.set_ylabel("Average ooq in packets",fontsize=plot_fsize)
	ax3.set_xticks(idx)
	ax3.set_ylim(0)
	ax3.set_xticklabels(xticklabel2,fontsize=plot_fsize) 
	ax3.legend(links,fontsize=plot_fsize) 
	ax3.set_axisbelow(True)
	ax3.grid()
	
	ax4.set_xticks(idx)
	ax4.set_xticklabels(xticklabel2,fontsize=plot_fsize) 
	ax4.legend(links,loc="lower center") 
	ax4.set_axisbelow(True)
	ax4.grid()
	ax4.set_ylabel("Path usage in %",fontsize=plot_fsize)
	
	fig.savefig("old_plots/evaluation1"+scenario+(time.ctime()),dpi=300,bbox_inches="tight")
	#fig.savefig("old_plots/evaluation1"+scenario+(time.ctime())+".pdf",dpi=100,bbox_inches="tight")
	fig2.savefig("old_plots/evaluation2"+scenario+(time.ctime()),dpi=300)
	#fig2.savefig("old_plots/evaluation2"+scenario+(time.ctime())+".pdf",dpi=100,bbox_inches="tight")
	manager = plt.get_current_fig_manager()
	manager.resize(*manager.window.maxsize())
	plt.show()
	
	
	if args.files:
		fig = plt.figure(figsize=(6,4.5))
		file_sizes = ["64kb","2mb","8mb","64mb"]
		colors = ["green","blue","red","orange","black","purple"]
		for j in range(len(file_sizes)):
			if scenario.find("wifi") != -1:
				if scenario.find("dynamic") != -1:
					scenario_ = "dynamic_eval" + file_sizes[j] + "wifi"
				else:
					scenario_ =  "static_eval" + file_sizes[j] + "wifi"
			else:
				scenario_ = "static_eval" + file_sizes[j] 
			csvv = pd.read_csv("test_results/"+schedulers[0][0]+scenario_+".csv")
			normstd = np.std(csvv["completion time"].dropna())
			normalizationv = csvv["completion time"].dropna().mean()
			for i in range(len(schedulers)):
				print("test_results/"+schedulers[i][0]+scenario_+".csv")
				csv = pd.read_csv("test_results/"+schedulers[i][0]+scenario_+".csv")
				#normalize completion time to first scheduler of combination
				norm_ct = csv["completion time"].dropna().mean()/normalizationv
				plt.bar([j+(0.075*(i-2))],norm_ct,width=0.075,edgecolor=colors[i],hatch='/',alpha=0.8,fill=False,zorder=3)
		
		idx = np.arange(start=0,stop=len(file_sizes))
		
		plt.legend(xticklabel1,loc="lower center")
		plt.ylabel("Normalized Completion Time",fontsize=plot_fsize+2)
		plt.xlabel("Download sizes",fontsize=plot_fsize+2)
		plt.xticks(idx,file_sizes,fontsize=plot_fsize)
		ax4.set_axisbelow(True)
		plt.grid(zorder=0)
		plt.savefig("old_plots/evaluation_files"+scenario+(time.ctime()),dpi=300)
		#plt.savefig("old_plots/evaluation_files"+scenario+(time.ctime())+".pdf")
		manager = plt.get_current_fig_manager()
		manager.resize(*manager.window.maxsize())
		plt.show()
	
