import re
import os
import kirk
import numpy as n
import time
import pickle
import broadcast
import sys
import signal
import os

def trimmean(arr, percent):
    n = len(arr)
    k = int(round(n*(float(percent)/100)/2))
    return n.mean(arr[k+1:n-k])

sock = broadcast.BroadcastSocket(8000)

File = kirk.File
width = kirk.width
height = kirk.height
box_size = kirk.box_size

fingerprint_file = open(r'fingerprint.pkl', 'rb')
fingerprint = pickle.load(fingerprint_file)
fingerprint_file.close()


while 1:
		
	f = open('output, 'w+')
	#p = Popen("./rssi_out.sh", stdout=f, shell=True, preexec_fn=os.setsid)#, stdout=stdout, stderr=f)
	#Popen(['cd', '~/Desktop/RSSI'])
	p = Popen(['./rssi_log.sh'], stdout=f)
	time.sleep(1)
	os.killpg(p.pid, signal.SIGKILL)
	f.close()
	
        f = open("output")
        compare = {}
        for line in f:
	        read = line.split()
	        if len(read)==3 and read[0] == read[1]:
		        mac = read[0]
                        if read[2] != '':
			        strength = int(read[2].strip())
                                if mac in compare:
				        compare[mac].append(strength)
                                else:
                                        arr = []
                                        compare.update({mac:arr})
                                        compare[mac].append(strength)	

        compare_avg = {}
        for mac in compare:
	        l = compare[mac]
	        avg = n.mean(l)
	        #avg = trimmean(l, 80)
	        compare_avg.update({mac:avg})

	guess = []
	weight = []
        for mac in compare_avg:
	        least = None
	        location = []
	        if mac in fingerprint:
		        for x in range(len(fingerprint[mac])):
			        for y in range(len(fingerprint[mac][x])):
				        if fingerprint[mac][x][y] != None:
					        c = abs(fingerprint[mac][x][y] - compare_avg[mac])
					        if least == None or c == least:
						        least = c
							location.append([(x, y), c])
						elif c < least:
							least = c
							location = [[(x, y), c]]	
		#print mac, location
		for pot in location:
                        guess.append(pot[0])
                        weight.append(pot[1])



	normalized_weight = [1-((weight[i] - min(weight)) / (max(weight) - min(weight))) for i in range(len(weight))]
	for i in range(len(normalized_weight)):
		if n.isnan(normalized_weight[i]):
			normalized_weight[i] = 1
	if len(normalized_weight) != 0:
		answer = tuple(n.round(n.average(guess,axis=0, weights=normalized_weight)))
	sock.send("kyle, "+str(int(answer[0]))+", "+str(int(answer[1])))
	f.close()
