import re
import os
import kirk
import numpy as n
import pickle
def trimmean(arr, percent):
    n = len(arr)
    k = int(round(n*(float(percent)/100)/2))
    return n.mean(arr[k+1:n-k])

File = kirk.File
width = kirk.width
height = kirk.height
box_size = kirk.box_size

#Dictionary data structure to hold out parsed data
#For each MAC address there is a multidimensional array of size [x][y]
#In each of those arrays is a list of RSSI values found at that location
rssi = {}
#Loop through every file in our data directory and extract data into rssi
for filename in os.listdir('./fingerprint'):
	data = re.split('_',filename)
	x = int(data[0])
	y = int(data[1])
	f = open('./fingerprint/'+filename)

	for line in f:
		read = line.split()
		if len(read)==3 and read[0] == read[1]:
			mac = read[0]
			if read[2] != '':
				strength = int(read[2].strip())
				if mac in rssi:
					rssi[mac][x][y].append(strength)
				else:
					if mac != "48:5a:3f:45:21:0f": #Filter out my cellphone
						arr = [[[] for _ in range(kirk.x)] for _ in range(kirk.y)]
						rssi.update({mac:arr})
						rssi[mac][x][y].append(strength)
#Now that we have the data, calculate averages for each location
fingerprint = {}
for mac in rssi:
	avg = [[None for _ in range(kirk.x)] for _ in range(kirk.y)]
	for x in range(len(rssi[mac])):
		for y in range(len(rssi[mac][x])):
			l = rssi[mac][x][y]
			if len(l) > 0:
				avg[x][y] = n.mean(l)
				#avg[x][y] = trimmean(l, 80)
	fingerprint.update({mac:avg})

finger_file = open(r'fingerprint.pkl', 'wb')
pickle.dump(fingerprint, finger_file)
finger_file.close()

