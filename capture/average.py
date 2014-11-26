import re
import os
from PIL import Image
import kirk

File = kirk.File
width = kirk.width
height = kirk.height
box_size = kirk.box_size

#Dictionary data structure to hold out parsed data
#For each MAC address there is a multidimensional array of size [x][y]
#In each of those arrays is a list of RSSI values found at that location
rssi = {}
#Loop through every file in our data directory and extract data into rssi
for filename in os.listdir('./data'):
	data = re.split('_',filename)
	x = int(data[0])
	y = int(data[1])
	f = open('./data/'+filename)

	for line in f:
		read = line.split()
		if len(read)==3 and read[0] == read[1]:
			mac = read[0]
			if read[2] != '':
				strength = int(read[2].strip())
				if mac in rssi:
					rssi[mac][x][y].append(strength)
				else:
					arr = [[[] for _ in range(kirk.x)] for _ in range(kirk.y)]
					rssi.update({mac:arr})
					rssi[mac][x][y].append(strength)
#Now that we have the data, calculate averages for each location and plot it
for mac in rssi:
        #This is for graphing the signal strength
	im = Image.open(File).copy()
	mask = Image.new("RGBA", (width, height), (127, 127, 127))
	
	#Like it says the true average with negative sign in tact
	true_avg = [[None for _ in range(kirk.x)] for _ in range(kirk.y)]
	#The average with sign flipped to be used for plotting
	avg = [_[:] for _ in true_avg]
	print mac
	for x in range(len(rssi[mac])):
		for y in range(len(rssi[mac][x])):
			l = rssi[mac][x][y]
			if len(l) > 0:
				true_avg[x][y] = sum(l)/float(len(l))
				avg[x][y] = 100+true_avg[x][y]
				print x, y, true_avg[x][y] 
	#Maximum average RSSI for this MAC Address
	high = max(map(max, avg))
	l=[j for i in avg for j in i if j != None]	
	#Minimum RSSI for this MAC Address
	low = min(l)
	
	#Plot the averages onto the image of Kirk auditorium
	for x in range(len(rssi[mac])):
                for y in range(len(rssi[mac][x])):
                        l = rssi[mac][x][y]
			if len(l) > 0:
                        	norm = (avg[x][y] - low) / ((high - low) if (high - low)>0 else 1)
				color = (int(255*(1-norm)), int(255*norm), int(0))
				im.paste(color, (x*box_size, y*box_size, x*box_size+box_size, y*box_size+box_size))
	im.show()
	im.save(mac, "PNG")
	
