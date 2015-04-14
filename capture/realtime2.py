import re
import os
import kirk
import numpy as n
import time
import pickle

def trimmean(arr, percent):
    n = len(arr)
    k = int(round(n*(float(percent)/100)/2))
    return n.mean(arr[k+1:n-k])

File = kirk.File
width = kirk.width
height = kirk.height
box_size = kirk.box_size

fingerprint_file = open(r'fingerprint.pkl', 'rb')
fingerprint = pickle.load(fingerprint_file)
fingerprint_file.close()

max_x = 0
max_y = 0

for mac in fingerprint:
        if len(fingerprint[mac]) > max_x:
                max_x = len(fingerprint[mac])
        for x in range(len(fingerprint[mac]))
                if len(fingerprint[mac][x] > max_y):
                        max_y = len(fingerprint[mac][x])

while 1:
		
	time.sleep(1)
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
	difference = [[None]*max_y for _ in range(max_x)]
        for mac in compare_avg:
	        least = None
	        location = []
	        if mac in fingerprint:
		        for x in range(len(fingerprint[mac])):
			        for y in range(len(fingerprint[mac][x])):
				        if fingerprint[mac][x][y] != None:
					        c = abs(fingerprint[mac][x][y] - compare_avg[mac])
					        if difference[x][y] != None:
					                difference[x][y] += c
					        else
					                difference[x][y] = c	
        final_x = 0
        final_y = 0
	for x in range(len(difference)):
                for y in range(len(difference[x])):
	                  if(difference[final_x][final_y] > difference[x][y]):
	                        final_x = x
	                        final_y = y  
        print(final_x, final_y)       
	f.close()
