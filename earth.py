#!/usr/bin/env python
# Implementation of algorithm from https://stackoverflow.com/a/22640362/6029703
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from datetime import datetime
import urllib.request
import pandas as pd
import os
import json
from multiprocessing import Process,Queue,Value
import os.path
import shutil

my_list=[]

def cls():
	os.system('cls' if os.name=='nt' else 'clear')

def days_of_month(year,month):
	if(month==2):
		if (year % 4) == 0:
			if (year % 100) == 0:
				if (year % 400) == 0:
					return 29
				else:
					return 28
			else:
				return 29
		else:
			return 28
	elif(month==1 or month==3 or month==5 or month==7 or month==8 or month==10 or month==12):
		return 31
	else:
		return 30

def my_time(x):
	time = x*5*60
	day = time // (24 * 3600)
	time = time % (24 * 3600)
	hour = time // 3600
	time %= 3600
	minutes = time // 60
	time %= 60
	seconds = time
	#print("d:h:m-> %d:%d:%d" % (day+1, hour, minutes))
	print("EQ AT d:h:m-> %d:%d:%d" % (day+4, hour, minutes))

def thresholding_algo(y, lag, threshold, influence):
    signals = np.zeros(len(y))
    filteredY = np.array(y)
    avgFilter = [0]*len(y)
    stdFilter = [0]*len(y)
    avgFilter[lag - 1] = np.mean(y[0:lag])
    stdFilter[lag - 1] = np.std(y[0:lag])
    for i in range(lag, len(y)):
        if abs(y[i] - avgFilter[i-1]) > threshold * stdFilter [i-1]:
            if y[i] > avgFilter[i-1]:
                signals[i] = 1
            else:
                signals[i] = -1

            filteredY[i] = influence * y[i] + (1 - influence) * filteredY[i-1]
            avgFilter[i] = np.mean(filteredY[(i-lag+1):i+1])
            stdFilter[i] = np.std(filteredY[(i-lag+1):i+1])
        else:
            signals[i] = 0
            filteredY[i] = y[i]
            avgFilter[i] = np.mean(filteredY[(i-lag+1):i+1])
            stdFilter[i] = np.std(filteredY[(i-lag+1):i+1])

    return dict(signals = np.asarray(signals),
                avgFilter = np.asarray(avgFilter),
                stdFilter = np.asarray(stdFilter))

def day_2_string(x):
	if x<10:
		return "0"+str(x)
	return str(x)

def current_day():
	now = datetime.now()
	year=now.strftime("%Y")
	month=now.strftime("%m")
	day=now.strftime("%d")
	get_data(year,int(month),int(day))

def other_day(year,month):
	get_data(year,month,days_of_month(year,month))

def get_data(year,month,day):
	filename=str(year)+day_2_string(month)+"_H8_sedae_5min/"
	try:
		shutil.rmtree(filename)
		os.mkdir(filename)
	except:
		os.mkdir(filename)
	processes=[]
	# result_queue = Queue()
	# iterations = Value('i', 0)
	for i in range(1,int(day)):
		p = Process(target=get_data_mult, args=(year,day_2_string(month),day_2_string(i),))
		p.start()
		processes.append(p)
	#result = result_queue.get()
	for process in processes:
		process.join()


	files_2_data(year,month,day)
	cls()
	print("Do you want to viualize data 'v' or just print them 'p'?")
	while(True):
		choise=input()
		if(choise.lower()=='v'):
			data_visualize()
			break
		elif(choise.lower()=='p'):
			print("only print")
			break
		else:
			print("I don't undertand. Try again. (v or p)")
			continue

def get_data_mult(year,month,day):
	#with iterations.get_lock()
	#iterations.value += 1
	filename=str(year)+str(month)+day+"_H8_sedae_5min.txt"
	noext=str(year)+str(month)+day+"_H8_sedae_5min"
	filedest=str(year)+str(month)+"_H8_sedae_5min/"
	print(filename)
	url="https://aer-nc-web.nict.go.jp/radi/data/Himawari/realtime/5min/ascii/electron/{}/{}".format(year,filename)
	while(True):
		try:
			completeName = os.path.join(filedest, filename)
			print(completeName)
			urllib.request.urlretrieve(url,completeName)
			break
		except:
			continue
		break
	noextcompleteName = os.path.join(filedest, filename)
	with open(completeName) as f, open(noextcompleteName+"_thread.txt","w") as out:
		for x in range(24):
			next(f)
		i=1
		for line in f:
			if i==1:
				newrow=line[1:]
				newrow=" ".join(newrow.split())
				i+=1
				out.write(newrow+"\n")
			else:
				newrow=" ".join(line.split())
				out.write(newrow+"\n")
	os.remove(completeName)
	os.rename(noextcompleteName+"_thread.txt", completeName)

def files_2_data(year,month,day):
	global my_list
	filedest=str(year)+day_2_string(month)+"_H8_sedae_5min/"
	for i in range(1,int(day)):
		filename=str(year)+day_2_string(int(month))+day_2_string(i)+"_H8_sedae_5min.txt"
		print(filename)
		completeName = os.path.join(filedest, filename)
		with open(completeName) as f:
			lines = f.readlines() # list containing lines of file
			columns = [] # To store column names
			i = 1
			for line in lines:
				line = line.strip() # remove leading/trailing white spaces
				if line:
					if i == 1:
						columns = [item.strip() for item in line.split(' ')]
						i+=1
					else:
						d = {} # dictionary to store file data (each line)
						data = [item.strip() for item in line.split(' ')]
						for index, elem in enumerate(data):
							d[columns[index]] = data[index]
						my_list.append(d) # append dictionary to list

def data_visualize():
	def update(val):
		days_array=[]
		magnitute_array=[]
		lag=int(s_ax_lag.val)	#less than len(y)
		#lag=200
		threshold=(s_ax_threshold.val)
		#threshold=3
		influence=(s_ax_influence.val)
		#influence=1
		a=thresholding_algo(y,lag,threshold,influence)
		k.set_ydata(a['signals'])
		a_new=a['signals']
		last=0
		counter=0
		pos=100
		for index in range(len(a_new)):
			if(a_new[index]==1 or a_new[index]==-1):
				pos=100
				last=index
				counter+=1
			else:
				if index==len(a_new)-1:
					days_array.append(last)
					magnitute_array.append(counter)	
				if pos==0:
					days_array.append(last)
					magnitute_array.append(counter)
					counter=0
				pos-=1
		cls()
		for j in range(len(days_array)):
			my_time(int(days_array[j]))
			print("score="+str(magnitute_array[j])+"\n")

		fig.canvas.draw_idle()
	y=[]
	x=[]
	i=0
	for l in my_list:
		x.append(i)
		i+=1
		temp=float(l["E_CH0"][:-4])
		maybe=(-temp)+2*temp
		y.append(temp)
	#newplot=plt.plot(y)

	fig, ax = plt.subplots()
	plt.subplots_adjust(left=0.25, bottom=0.25)
	plt.ylim(-1.5, 1.5) 
	k, = plt.step(x,y)

	ax.margins(x=0)

	ax_lag = plt.axes([0.25, 0.05, 0.65, 0.03])
	ax_threshold = plt.axes([0.25, 0.10, 0.65, 0.03])
	ax_influence = plt.axes([0.25, 0.15, 0.65, 0.03])

	s_ax_lag = Slider(ax_lag, 'lag', 1, len(y), valinit=1100, valstep=1.0)
	s_ax_threshold = Slider(ax_threshold, 'threshold', 0.0, 10.0, valinit=1.5, valstep=0.1)
	s_ax_influence = Slider(ax_influence, 'influence', 0.0, 2.0, valinit=1, valstep=0.1)

	s_ax_lag.on_changed(update)
	s_ax_threshold.on_changed(update)
	s_ax_influence.on_changed(update)

	plt.show()


if __name__ == '__main__':
	print("!!Welcome to EQ_Greece!!\nDo you want to download data? (Y or n)\n(press 'q' to quit)")
	while(True):
		choise=input()
		cls()
		if(choise.lower()=='y' or choise.lower()=='yes'):
			print("Do you want data about today 't' or other day 'o'?")
			while(True):
				choise=input()
				cls()
				if(choise.lower()=='t'):
					current_day()
					break
				elif(choise.lower()=='o'):
					print("Please give year and month and day...(Year 2014..2020)(Month 1..12)")
					while(True):
						year=int(input("Year:"))
						month=int(input("Month:"))
						cls()
						if(year<2014 or year>2020 or month<1 or month>12):
							print("Wrong values. Try again. (Year 2014..2020)(Month 1..12)")
							continue
						else:
							other_day(year,month)
							break
					break
				else:
					print("I don't undertand. Try again. (t or o)")
					continue
			break
		elif(choise.lower()=='n' or choise.lower()=='no'):
			files_2_data(2019,3,31)
			data_visualize()
			break
		elif(choise.lower()=='q'):
			print("Goodbye")
			break
		else:
			print("I don't undertand. Try again. (Y or n)")
			continue