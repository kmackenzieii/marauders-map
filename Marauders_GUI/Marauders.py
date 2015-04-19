
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

iface = None
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
                        arr = [[[] for _ in range(map_size)] for _ in range(map_size)]
                        rssi.update({mac:arr})
                        rssi[mac][x][y].append(strength)

    #Now that we have the data, calculate averages for each location
    for mac in rssi:
        if mac in fingerprint:
            avg = fingerprint[mac]
        else:
	        avg = [[None for _ in range(map_size)] for _ in range(map_size)]
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
    print (event.x//box_size,event.y//box_size)
    record(event.x//box_size, event.y//box_size, iface)
    print "DONE"


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


            else:
                # this is an action
                if 'Auditorium' in item['name']:
                    btn.configure(command=lambda act=act: self.capture('kirk'), )
                else:
                    if 'hall' in item['name']:
                        btn.configure(command=lambda act=act: self.capture('Gil_first'), )
                    else:
                        if 'Locator' in item['name']:
                            btn.configure(command=lambda act=act: self.Live('kirk'), )
                        else:
                            btn.configure(command=lambda act=act: self.Live('underCons'), )

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

    def capture(self, map):
        box_size = 15

        # create a new frame
        wrap = Frame(self, bg="black")

        self.hide_top()
        # label showing the image
        self.image = Image.open(map + ".gif")
        draw = ImageDraw.Draw(self.image) 
        
        for x in range(1, 240//box_size):
	        draw.line((box_size*x, 0, box_size*x, 240), fill=128, width=1)
        for y in range(1, 240//box_size):
	        draw.line((0, box_size*y, 240, box_size*y), fill=128, width=1)
        
        
        self.image = ImageTk.PhotoImage(self.image)
        imagelabel = Label(wrap, image=self.image)
        imagelabel.grid(row=0, column=0, columnspan=2, sticky=C.W + C.E + C.N + C.S)


        imagelabel.bind('<Button-1>', printcoords)

   
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

        # add the new frame to the stack and display it
            self.framestack.append(wrap)
        self.show_top()
        self.parent.update()


    def Live(self, map):
        box_size = 15

        # create a new frame
        wrap = Frame(self, bg="black")

        self.hide_top()
        # label showing the image
        self.image = Image.open(map + ".gif")
        draw = ImageDraw.Draw(self.image)

        for x in range(1, 240//box_size):
            draw.line((box_size*x, 0, box_size*x, 240), fill=128, width=1)
        for y in range(1, 240//box_size):
            draw.line((0, box_size*y, 240, box_size*y), fill=128, width=1)


        self.image = ImageTk.PhotoImage(self.image)
        imagelabel = Label(wrap, image=self.image)
        imagelabel.grid(row=0, column=0, columnspan=2, sticky=C.W + C.E + C.N + C.S)

        def coordinates(event):
            print(event.x, event.y)

        imagelabel.bind('<Button-1>', coordinates)

        # when there were previous frames, hide the top one and add a back button for the new one

        if len(self.framestack):
            self.hide_top()

            back = FlatButton(
                wrap,
                text = 'Back…',
                image = self.get_icon("arrow.left"),
                command = self.go_back,
            )

            exitbtn = FlatButton(
                wrap,
                text = 'Exit…',
                image = self.get_icon("exit"),
                command = self.app_exit,
            )

            back.set_color("#00a300")  # green
            exitbtn.set_color("#00a300")  # green

            back.grid(row=1, column=0, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            exitbtn.grid(row=1, column=1, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            self.framestack.append(wrap)
        self.show_top()
        self.parent.update()


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

        self.destroy_top()

        self.show_top()




    def app_exit(self):

        # Kills application
        self.quit()


def main():
    root = Tk()
    root.geometry("240x320")
    root.wm_title('Marauders Map')

    if len(sys.argv) > 1 and sys.argv[1] == 'fs':
        root.wm_attributes('- fullscreen', True)
    app = Marauders(root)

    # Start channel hopping
    iface = channel_hop.get_mon_iface()
    hop = threading.Thread(target=channel_hop.channel_hop, args=[iface])
    hop.daemon = True
    hop.start()
    
    if(os.path.isfile('./fingerprint.pkl')):
        fingerprint_file = open(r'fingerprint.pkl', 'rb')
        fingerprint = pickle.load(fingerprint_file)
        fingerprint_file.close()

    root.mainloop()


if __name__ == '__main__':
    main()
