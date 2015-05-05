# -*- coding: utf-8 -*-

from math import sqrt, floor, ceil
import os, time, sys, yaml, kirk
import  Tkconstants as C
#import tkinter.constants as C
from Tkinter import Tk, Frame, LEFT,  Button, Label, PhotoImage, TOP, \
    FLAT, BOTH, Image
from PIL import Image, ImageTk, ImageDraw
import threading
import thread
import sys
import signal
import scapy.all as sca
import scapy_ex
import channel_hop
import pickle
import numpy as n
import signal
from subprocess import Popen, PIPE

iface = None
realt = False
fingerprint = {}
box_size = 15
map_size = 240//box_size
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

class FlatButton(Button):
    def __init__(self, master=None, cnf={}, **kw):
        Button.__init__(self, master, cnf, **kw)
        self.config(
            compound=TOP,
            relief=FLAT,
            bd=0,
            bg="#b91d47",  # dark-red
            fg="white",
            activebackground="#b91d47",  # dark-red
            activeforeground="white",
            highlightthickness=0
        )

    def set_color(self, color):
        self.configure(
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white"
        )


class Marauders(Frame):
    doc = None
    framestack = []
    icons = {}
    path = ''

    def __init__(self, parent):
        Frame.__init__(self, parent, background="white")
        self.parent = parent
        self.pack(fill=BOTH, expand=1)

        self.path = os.path.dirname(os.path.realpath(sys.argv[0]))
        with open(self.path + '/Marauders.yaml', 'r') as f:
            self.doc = yaml.load(f)
        self.show_items(self.doc)

    def show_items(self, items, upper=[]):
        """
        Creates a new page on the stack, automatically adds a back button when there are
        pages on the stack already

        :param items: list the items to display
        :param upper: list previous levels' ids
        :return: None
        """
        num = 0

        # create a new frame
        wrap = Frame(self, bg="black")
        # when there were previous frames, hide the top one and add a back button for the new one
        if len(self.framestack):
            self.hide_top()

            back = FlatButton(
                wrap,
                text='Back…',
                image=self.get_icon("arrow.left"),
                command=self.go_back,
            )

            exitbtn = FlatButton(
                wrap,
                text='Exit…',
                image=self.get_icon("exit"),
                command=self.app_exit,
            )

            back.set_color("#00a300")  # green
            exitbtn.set_color("#00a300")  # green

            back.grid(row=0, column=0, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            num +=1
            exitbtn.grid(row=0, column=1, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            num += 1

        # add the new frame to the stack and display it
        self.framestack.append(wrap)
        self.show_top()


        # calculate tile distribution
        all = len(items) + num
        rows = floor(sqrt(all))
        cols = ceil(all / rows)

        # make cells autoscale
        for x in range(int(cols)):
            wrap.columnconfigure(x, weight=1)

        for y in range(int(rows)):
            wrap.rowconfigure(y, weight=1)

        # display all given buttons
        for item in items:
            act = upper + [item['name']]

            if 'icon' in item:
                image = self.get_icon(item['icon'])
            else:
                image = self.get_icon('scrabble.' + item['label'][1:1].lower())

            btn = FlatButton(
                wrap,
                text=item['label'],
                image=image
            )

            if 'items' in item:
                # this is a deeper level
                btn.configure(command=lambda act=act, item=item:
                self.show_items(item['items'], act), text=item['label'] + '…')
                btn.set_color("#2b5797")  # dark-blue
            elif item['name'] == 'Locator':
                # this is an action
                btn.configure(command=lambda act=act: self.realtime(), )
            else:
                # this is an action
		print act
                btn.configure(command=lambda act=item['name']: self.capture(act), )

            if 'color' in item:
                btn.set_color(item['color'])

            # add button to the grid
            btn.grid(
                row=int(floor(num / cols)),
                column=int(num % cols),
                padx=1,
                pady=1,
                sticky=C.W + C.E + C.N + C.S
            )
            num += 1

    def get_icon(self, name):
        """
        Loads the given icon and keeps a reference

        :param name: string
        :return:
        """
        if name in self.icons:
            return self.icons[name]

        ico = self.path + '/ico/' + name + '.gif'

        # In case icon cannot be found display the cancel icon
        if not os.path.isfile(ico):
            ico = self.path + '/ico/cancel.gif'

        self.icons[name] = PhotoImage(file=ico)
        return self.icons[name]

    def hide_top(self):
        """
        hide the top page
        :return:
        """
        self.framestack[len(self.framestack) - 1].pack_forget()

    def show_top(self):
        """
        show the top page
        :return:
        """
        self.framestack[len(self.framestack) - 1].pack(fill=BOTH, expand=1)

    def record(self, x, y, z, iface):
        global fingerprint
        now = time.time()
        rssi={}
        future = now + 10
        while time.time() < future:
	    #os.system("sudo hciconfig hci0 reset")
            #p = Popen([self.path+"/ibeacon_scan","-b"], stdout=PIPE, stderr=PIPE, preexec_fn=os.setsid)
            packets = sca.sniff(iface=iface, timeout = 10)
            #os.killpg(p.pid, signal.SIGTERM)
            #bl_packets = p.stdout.read().split('\n')
            bl_packets = [] #Empty bluetooth until it works properly
	    for pkt in packets:
                mac, strength = parsePacket(pkt)
                if mac is not None and strength is not None and strength < 0:
                    if mac in rssi:
                        if z in rssi[mac]:
                            rssi[mac][z][x][y].append(strength)
                        else:
                            arr = [[[] for _ in range(map_size)] for _ in range(map_size)]
                            rssi[mac].update({z:arr})
                            rssi[mac][z][x][y].append(strength)
                    else:
                        if mac != "48:5a:3f:45:21:0f": #Filter out my cellphone
                            arr = [[[] for _ in range(map_size)] for _ in range(map_size)]
                            new_map = {}
                            new_map.update({z:arr})
                            rssi.update({mac:new_map})
                            rssi[mac][z][x][y].append(strength)
	    for pkt in bl_packets:
                content = pkt.split()
                if len(content) == 2:
                    mac = content[0]
                    strength = content[1]
                    if mac is not None and strength is not None and strength < 0:
                        if mac in rssi:
		            if z in rssi[mac]:
                                rssi[mac][z][x][y].append(strength)
                            else:
                                arr = [[[] for _ in range(map_size)] for _ in range(map_size)]
                                rssi[mac].update({z:arr})
                                rssi[mac][z][x][y].append(strength)
                        else:
                            arr = [[[] for _ in range(map_size)] for _ in range(map_size)]
                            new_map = {}
                            new_map.update({z:arr})
                            rssi.update({mac:new_map})
                            rssi[mac][z][x][y].append(strength)
        #Now that we have the data, calculate averages for each location
        for mac in rssi:
            if mac in fingerprint:
		if z in fingerprint[mac]:
                    avg = fingerprint[mac][z]
		else:
		    avg = [[None for _ in range(map_size)] for _ in range(map_size)]
            else:
                avg = [[None for _ in range(map_size)] for _ in range(map_size)]
                fingerprint.update({mac:{}})
            for x in range(len(rssi[mac][z])):
                        for y in range(len(rssi[mac][z][x])):
                                l = rssi[mac][z][x][y]
                                if len(l) > 0:
                                        avg[x][y] = n.mean(l)
                                        #avg[x][y] = trimmean(l, 80)
            fingerprint[mac].update({z:avg})
        finger_file = open(self.path + '/fingerprint.pkl', 'wb')
        pickle.dump(fingerprint, finger_file)
        finger_file.close()



    def capture(self, map):
	self.map = map
        box_size = 15
	print map
        # create a new frame
        wrap = Frame(self, bg="black")

        self.hide_top()
        # label showing the image
        self.image = Image.open(self.path + "/" + map + ".gif")
        draw = ImageDraw.Draw(self.image) 
        
        for x in range(1, 240//box_size):
	        draw.line((box_size*x, 0, box_size*x, 240), fill=128, width=1)
        for y in range(1, 240//box_size):
	        draw.line((0, box_size*y, 240, box_size*y), fill=128, width=1)
        
        
        self.image = ImageTk.PhotoImage(self.image)
        imagelabel = Label(wrap, image=self.image)
        imagelabel.grid(row=0, column=0, columnspan=2, sticky=C.W + C.E + C.N + C.S)


        imagelabel.bind('<Button-1>', self.printcoords)

   
        # when there were previous frames, hide the top one and add a back button for the new one
        if len(self.framestack):
            self.hide_top()

            back = FlatButton(
                wrap,
                text='Back…',
                image=self.get_icon("arrow.left"),
                command= self.go_back,
            )

            exitbtn = FlatButton(
                wrap,
                text='Exit…',
                image=self.get_icon("exit"),
                command=self.app_exit,
            )

            back.set_color("#00a300")  # green
            exitbtn.set_color("#00a300")  # green

            back.grid(row=1, column=0, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            exitbtn.grid(row=1, column=1, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            #num += 1

        # add the new frame to the stack and display it
            self.framestack.append(wrap)
        self.show_top()
        self.parent.update()
    
    def blink(self):
	wrap = Frame(self, bg="green")
	self.hide_top()
        if len(self.framestack):
	    self.hide_top()
	    self.framestack.append(wrap)
	self.show_top()
	self.parent.update()
    #function to be called when mouse is clicked
    def printcoords(self, event):
        #outputting x and y coords to console
        print (event.x//box_size, event.y//box_size)
	self.blink()
        self.record(event.x//box_size, event.y//box_size, self.map, iface)
        self.go_back()
	print "DONE"


    def realtime(self):
        global realt
        box_size = 15

        # create a new frame
        wrap = Frame(self, bg="black")

        self.hide_top()
        # label showing the image
        self.image = Image.open(self.path + "/kirk-auditorium2.gif")
        draw = ImageDraw.Draw(self.image)
        self.image = ImageTk.PhotoImage(self.image)
        imagelabel = Label(wrap, image=self.image)
        imagelabel.grid(row=0, column=0, columnspan=2, sticky=C.W + C.E + C.N + C.S)

        num = 0
        # when there were previous frames, hide the top one and add a back button for the new one
        if len(self.framestack):
            self.hide_top()

            back = FlatButton(
                wrap,
                text='Back…',
                image=self.get_icon("arrow.left"),
                command= self.go_back,
            )

            exitbtn = FlatButton(
                wrap,
                text='Exit…',
                image=self.get_icon("exit"),
                command=self.app_exit,
            )

            back.set_color("#00a300")  # green
            exitbtn.set_color("#00a300")  # green

            back.grid(row=1, column=0, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            exitbtn.grid(row=1, column=1, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            num += 1

        realt = True
        

        # add the new frame to the stack and display it
        self.framestack.append(wrap)
        self.show_top()
        self.parent.update()
        self.after(1,self.realtime_calculation, imagelabel)
        
        
    def realtime_calculation(self, imagelabel):
        global realt
        global box_size
        fingerprint_file = open(self.path+'/fingerprint.pkl', 'rb')
        fingerprint = pickle.load(fingerprint_file)
        fingerprint_file.close()
 
        max_x = 0
        max_y = 0

	difference = {}
	num_macs = {}
        for mac in fingerprint:
            for z in fingerprint[mac]:
		difference.update({z:[]})
		num_macs.update({z:[]})
                if len(fingerprint[mac][z]) > max_x:
                    max_x = len(fingerprint[mac][z])
                    for x in range(len(fingerprint[mac][z])):
                            if len(fingerprint[mac][z][x]) > max_y:
                                    max_y = len(fingerprint[mac][z][x])
        while realt:
            compare = {}
	    bl_count = 0
	    wifi_count = 0
	    #os.system("sudo hciconfig hci0 reset")
	    #p = Popen([self.path+"/ibeacon_scan","-b"], stdout=PIPE, stderr=PIPE, preexec_fn=os.setsid)
            packets = sca.sniff(iface=iface, timeout=1)
	    #sys.stdout.flush()
	    #os.killpg(p.pid, signal.SIGTERM)
            #bl_packets = p.stdout.read().split('\n')
	    bl_packets = [] # empty until bluetooth works
            for pkt in packets:
                mac, strength = parsePacket(pkt)
                if mac is not None and strength is not None and strength < 0:
                    if mac in compare:
                        compare[mac].append(strength)
                    else:
			wifi_count = wifi_count + 1
                        arr = []
                        compare.update({mac:arr})
                        compare[mac].append(strength)	
	    for pkt in bl_packets:
                content = pkt.split()
                if len(content) == 2:
                    mac = str(content[0])
                    strength = int(content[1])
		    print mac, strength
		    if mac is not None and strength is not None and strength < 0:
                        if mac in compare:
                            compare[mac].append(strength)
                        else:
			    bl_count = bl_count + 1
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
	    for z in difference:
                difference[z] = [[None]*max_y for _ in range(max_x)]
		num_macs[z] = [[0]*max_y for _ in range(max_x)]
            for mac in compare_avg:
                least = None
                location = []
                if mac in fingerprint:
		    for z in fingerprint[mac]:
                        for x in range(len(fingerprint[mac][z])):
                            for y in range(len(fingerprint[mac][z][x])):
	                            if fingerprint[mac][z][x][y] != None:
		                        c = abs(fingerprint[mac][z][x][y] - compare_avg[mac])
		                        num_macs[z][x][y] = num_macs[z][x][y] + 1
		                        if difference[z][x][y] != None:
		                                difference[z][x][y] += c
		                        else:
		                                difference[z][x][y] = c	
            final_z = ''
	    final_x = 0
            final_y = 0
	    print difference
	    for z in difference:
                for x in range(len(difference[z])):
                    for y in range(len(difference[z][x])):
			if(final_z == ''):
			    final_z = z
                        if(difference[final_z][final_x][final_y] is None and difference[z][x][y] is not None):
                            final_z = z
			    final_x = x
                            final_y = y
                        if(difference[z][x][y] != None and difference[final_z][final_x][final_y]/num_macs[final_z][final_x][final_y] > difference[z][x][y]/num_macs[z][x][y]):
                            final_z = z
			    final_x = x
                            final_y = y  
            print(final_z, final_x, final_y)
            im = Image.open(self.path + "/"+ final_z +".gif").copy()
            draw = ImageDraw.Draw(im) 
            draw.line((box_size*x, 0, box_size*x, 240), fill=128, width=1)
            draw.rectangle([final_x*box_size, final_y*box_size, final_x*box_size+box_size, final_y*box_size+box_size], fill=100)
	    draw.text([5,5], str(wifi_count))
	    draw.text([5,15], str(bl_count))
            self.image = ImageTk.PhotoImage(im)            

            imagelabel.configure(image = self.image)
            self.parent.update()
            self.after(50, self.realtime_calculation, imagelabel)
       
    def back_btn(self):
        num = 0
         # create a new frame
        wrap = Frame(self, bg="black")
        # when there were previous frames, hide the top one and add a back button for the new one
        if len(self.framestack):
            self.hide_top()

            back = FlatButton(
                wrap,
                text='Back…',
                image=self.get_icon("arrow.left"),
                command= self.go_back,
            )


    def destroy_top(self):
        """
        destroy the top page
        :return:
        """
        self.framestack[len(self.framestack) - 1].destroy()
        self.framestack.pop()

    def destroy_all(self):
        """
        destroy all pages except the first aka. go back to start
        :return:
        """
        while len(self.framestack) > 1:
            self.destroy_top()


    def go_back(self):
        """
        destroy the current frame and reshow the one below
        :return:
        """
        global realt
        realt = False
        print "go_back:", realt
        self.destroy_top()

        self.show_top()




    def app_exit(self):

        # Kills application
        self.quit()


def main():
    global fingerprint
    root = Tk()
    root.geometry("240x320")
    root.wm_title('Marauders Map')

    if len(sys.argv) > 1 and sys.argv[1] == 'fs':
        root.wm_attributes('- fullscreen', True)
    app = Marauders(root)


    channel_hop.start_mon_mode('wlan0')

    # Start channel hopping
    iface = channel_hop.get_mon_iface()
    #iface = 'wlan2'
    hop = threading.Thread(target=channel_hop.channel_hop, args=[iface])
    hop.daemon = True
    hop.start()
    

    os.system("sudo hciconfig hci0 reset")
    #p = Popen(["hciconfig", "hci0", "down"], stdout=PIPE, stderr=PIPE, preexec_fn=os.setsid)
    #p = Popen(["hciconfig", "hci0","up"], stdout=PIPE, stderr=PIPE, preexec_fn=os.setsid)

    #p = Popen([app.path+"/ibeacon_scan","-b"], stdout=PIPE, preexec_fn=os.setsid)


    if(os.path.isfile(app.path + '/fingerprint.pkl')):
        fingerprint_file = open(app.path + '/fingerprint.pkl', 'rb')
        fingerprint = pickle.load(fingerprint_file)
        fingerprint_file.close()

    root.mainloop()


if __name__ == '__main__':
    main()
