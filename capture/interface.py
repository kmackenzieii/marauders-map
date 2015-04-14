from Tkinter import *
from subprocess import Popen
from tkFileDialog import askopenfilename
import threading
import thread
import Image, ImageTk
import time
import sys
import signal
import os
import kirk
import scapy.all as sca
import scapy_ex
import channel_hop
import pickle
import numpy as n
fingerprint = {}

radiotap_formats = {"TSFT":"Q", "Flags":"B", "Rate":"B",
      "Channel":"HH", "FHSS":"BB", "dBm_AntSignal":"b", "dBm_AntNoise":"b",
      "Lock_Quality":"H", "TX_Attenuation":"H", "dB_TX_Attenuation":"H",
      "dBm_TX_Power":"b", "Antenna":"B",  "dB_AntSignal":"B",
      "dB_AntNoise":"B", "b14":"H", "b15":"B", "b16":"B", "b17":"B", "b18":"B",
      "b19":"BBB", "b20":"LHBB", "b21":"HBBBBBH", "b22":"B", "b23":"B",
      "b24":"B", "b25":"B", "b26":"B", "b27":"B", "b28":"B", "b29":"B",
      "b30":"B", "Ext":"B"}

def parsePacket(pkt):
    if pkt.haslayer(sca.Dot11):
        if pkt.addr2 is not None:
          return pkt.addr2, pkt.dBm_AntSignal
    return None, None

def piconnect(x, y):
	    f = open('data/' + str(x) + '_' + str(y), 'w+')
	    p = Popen("sshpass -p raspberry ssh pi@192.168.43.170 'cd ~/Desktop/RSSI; ./rssi_out.sh;'", stdout=f, shell=True, preexec_fn=os.setsid)#, stdout=stdout, stderr=f)
	    #Popen(['cd', '~/Desktop/RSSI'])
	    #p = Popen(['./rssi_log.sh'], stdout=f)
	    time.sleep(15)
	    os.killpg(p.pid, signal.SIGKILL)
	    f.close()
	    
def record(x, y, iface):
    now = time.time()
    rssi={}
    future = now + 10
    while time.time() < future:
        packets = sca.sniff(iface=iface, timeout = 10)
        for pkt in packets:
            mac, strength = parsePacket(pkt)
            if mac is not None and strength is not None and strength < 0:
                if mac in rssi:
                    rssi[mac][x][y].append(strength)
                else:
                    if mac != "48:5a:3f:45:21:0f": #Filter out my cellphone
                        arr = [[[] for _ in range(kirk.x)] for _ in range(kirk.y)]
                        rssi.update({mac:arr})
                        rssi[mac][x][y].append(strength)
                      
    #Now that we have the data, calculate averages for each location
    for mac in rssi:
        if mac in fingerprint:
            avg = fingerprint[mac]
        else:
	        avg = [[None for _ in range(kirk.x)] for _ in range(kirk.y)]
        for x in range(len(rssi[mac])):
		    for y in range(len(rssi[mac][x])):
			    l = rssi[mac][x][y]
			    if len(l) > 0:
				    avg[x][y] = n.mean(l)
				    #avg[x][y] = trimmean(l, 80)
        fingerprint.update({mac:avg})
    print fingerprint
    finger_file = open(r'fingerprint.pkl', 'wb')
    pickle.dump(fingerprint, finger_file)
    finger_file.close()

#function to be called when mouse is clicked    
def printcoords(event):
    #outputting x and y coords to console
    print (event.x,event.y)
    record(event.x//box_size, event.y//box_size, iface)
    print "DONE"
    
if __name__ == "__main__":
    root = Tk()
    
    # Start channel hopping
    iface = channel_hop.get_mon_iface()
    hop = threading.Thread(target=channel_hop.channel_hop, args=[iface])
    hop.daemon = True
    hop.start()
    
    if(os.path.isfile('./fingerprint.pkl')):
        fingerprint_file = open(r'fingerprint.pkl', 'rb')
        fingerprint = pickle.load(fingerprint_file)
        fingerprint_file.close()
    
    width = kirk.width
    height = kirk.height
    box_size = kirk.box_size
    img = ImageTk.PhotoImage(Image.open(kirk.File))
    w = Canvas(root, width=width, height=height)
    w.pack()
    w.create_image(0,0,image=img,anchor="nw")
    
    for x in range(1, width//box_size):
	    w.create_line(box_size*x, 0, box_size*x, height)
    for y in range(1, height//box_size):
	    w.create_line(0, box_size*y, width, box_size*y)
    
    
    
    #mouseclick event
    w.bind("<Button 1>",printcoords)

    root.mainloop()
