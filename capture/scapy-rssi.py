import scapy.all as sca
import scapy_ex
import time
import thread
import threading
import signal
import sys
import matplotlib
matplotlib.use('pdf')
from matplotlib import pyplot as plt
from matplotlib import rcParams
import struct
import channel_hop
from subprocess import Popen, PIPE
import os
import re
DN = open(os.devnull, 'w')

# Console colors
W  = '\033[0m'  # white (normal)
R  = '\033[31m' # red
G  = '\033[32m' # green
O  = '\033[33m' # orange
B  = '\033[34m' # blue
P  = '\033[35m' # purple
C  = '\033[36m' # cyan
GR = '\033[37m' # gray
T  = '\033[93m' # tan

# needed to gracefully exit all threads
stopEvent = threading.Event() 
def signal_handler(signal, frame):
  global stopEvent
  print("Ctrl+C captured, exiting program!")
  stopEvent.set()
  time.sleep(1.0)
  sys.exit()
signal.signal(signal.SIGINT, signal_handler)

class ScapyRssi:
  def __init__(self, interface):
    # Radiotap field specification
    self.radiotap_formats = {"TSFT":"Q", "Flags":"B", "Rate":"B",
      "Channel":"HH", "FHSS":"BB", "dBm_AntSignal":"b", "dBm_AntNoise":"b",
      "Lock_Quality":"H", "TX_Attenuation":"H", "dB_TX_Attenuation":"H",
      "dBm_TX_Power":"b", "Antenna":"B",  "dB_AntSignal":"B",
      "dB_AntNoise":"B", "b14":"H", "b15":"B", "b16":"B", "b17":"B", "b18":"B",
      "b19":"BBB", "b20":"LHBB", "b21":"HBBBBBH", "b22":"B", "b23":"B",
      "b24":"B", "b25":"B", "b26":"B", "b27":"B", "b28":"B", "b29":"B",
      "b30":"B", "Ext":"B"}
    # data
    self.data = {}
    self.interface = interface
    self.dataMutex = thread.allocate_lock()
    self.time0 = time.time()
    thread.start_new_thread(self.sniff, (stopEvent,))
  def sniff(self, stopEvent):
    while not stopEvent.is_set():
      t0 = time.time()
      packets = sca.sniff(iface=self.interface, count = 100)
      dt = time.time() - t0
      print "current rate " + "{0:.2f}".format(100/dt) + " packets/sec"
      for pkt in packets:
        addr, rssi = self.parsePacket(pkt)
        if addr is not None:
          with self.dataMutex:
            if addr in self.data.keys():
              self.data[addr].append(rssi)
            else:
              self.data[addr] = [rssi]
  def parsePacket(self, pkt):
    if pkt.haslayer(sca.Dot11):
      if pkt.addr2 is not None:
        # check available Radiotap fields
        #field, val = pkt.getfield_and_val("present")
        #names = [field.names[i][0] for i in range(len(field.names)) if (1 << i) & val != 0]
        # check if we measured signal strength
        #if "dBm_AntSignal" in names:
          # decode radiotap header
          #fmt = "<"
          #rssipos = 0
          #channel_pos = 0
          #for name in names:
            # some fields consist of more than one value
            #if name == "dBm_AntSignal":
              # correct for little endian format sign
              #rssipos = len(fmt)-1
            #if name == "Channel":
              #channel_pos = len(fmt)-1
            #fmt = fmt + self.radiotap_formats[name]
          # unfortunately not all platforms work equally well and on my arm
          # platform notdecoded was padded with a ton of zeros without
          # indicating more fields in pkt.len and/or padding in pkt.pad
          #decoded = struct.unpack(fmt, pkt.notdecoded[:struct.calcsize(fmt)])
          #print len(fmt)
          #print decoded, channel_pos, decoded[len(fmt)-1]#decoded[len(fmt)-channel_pos]
          return pkt.addr2, pkt.dBm_AntSignal#decoded[rssipos]
    return None, None
  def plot(self, num):
    plt.clf()
    rcParams["font.family"] = "serif"
    rcParams["xtick.labelsize"] = 8
    rcParams["ytick.labelsize"] = 8
    rcParams["axes.labelsize"] = 8
    rcParams["axes.titlesize"] = 8
    data = {}
    time1 = time.time()
    with self.dataMutex:
      data = dict(self.data)
    nodes = [x[0] for x in sorted([(addr, len(data[addr])) for addr in data.keys()], key=lambda x:x[1], reverse=True)]
    nplots = min(len(nodes), num)
    for i in range(nplots):
      plt.subplot(nplots, 1, i+1)
      plt.title(str(nodes[i]) + ": " 
        + str(len(data[nodes[i]])) + " packets @ " +
        "{0:.2f}".format(len(data[nodes[i]])/(time1-self.time0)) 
        + " packets/sec")
      plt.hist(data[nodes[i]], range=(-100, -20), bins=80)
      plt.gca().set_xlim((-100, -20))
    plt.gcf().set_size_inches((6, 4*nplots))
    plt.savefig("hists.pdf")

def get_mon_iface():
    global monitor_on
    monitors, interfaces = iwconfig()
    if len(monitors) > 0:
        monitor_on = True
        return monitors[0]
    else:
        # Start monitor mode on a wireless interface
        print '['+G+'*'+W+'] Finding the most powerful interface...'
        #interface = get_iface(interfaces)
        interface = 'wlan1'
	monmode = start_mon_mode(interface)
        return monmode

def iwconfig():
    monitors = []
    interfaces = {}
    try:
        proc = Popen(['iwconfig'], stdout=PIPE, stderr=DN)
    except OSError:
        sys.exit('['+R+'-'+W+'] Could not execute "iwconfig"')
    for line in proc.communicate()[0].split('\n'):
        if len(line) == 0: continue # Isn't an empty string
        if line[0] != ' ': # Doesn't start with space
            wired_search = re.search('eth[0-9]|em[0-9]|p[1-9]p[1-9]', line)
            if not wired_search: # Isn't wired
                iface = line[:line.find(' ')] # is the interface
                if 'Mode:Monitor' in line:
                    monitors.append(iface)
                elif 'IEEE 802.11' in line:
                    if "ESSID:\"" in line:
                        interfaces[iface] = 1
                    else:
                        interfaces[iface] = 0
    return monitors, interfaces

def get_iface(interfaces):
    scanned_aps = []

    if len(interfaces) < 1:
        sys.exit('['+R+'-'+W+'] No wireless interfaces found, bring one up and try again')
    if len(interfaces) == 1:
        for interface in interfaces:
            return interface

    # Find most powerful interface
    for iface in interfaces:
        count = 0
        proc = Popen(['iwlist', iface, 'scan'], stdout=PIPE, stderr=DN)
        for line in proc.communicate()[0].split('\n'):
            if ' - Address:' in line: # first line in iwlist scan for a new AP
               count += 1
        scanned_aps.append((count, iface))
        print '['+G+'+'+W+'] Networks discovered by '+G+iface+W+': '+T+str(count)+W
    try:
        interface = max(scanned_aps)[1]
        return interface
    except Exception as e:
        for iface in interfaces:
            interface = iface
            print '['+R+'-'+W+'] Minor error:',e
            print '    Starting monitor mode on '+G+interface+W
            return interface

def start_mon_mode(interface):
    print '['+G+'+'+W+'] Starting monitor mode off '+G+interface+W
    try:
        os.system('ifconfig %s down' % interface)
        os.system('iwconfig %s mode monitor' % interface)
        os.system('ifconfig %s up' % interface)
        return interface
    except Exception:
        sys.exit('['+R+'-'+W+'] Could not start monitor mode')

def remove_mon_iface(mon_iface):
    os.system('ifconfig %s down' % mon_iface)
    os.system('iwconfig %s mode managed' % mon_iface)
    os.system('ifconfig %s up' % mon_iface)  

if __name__ == "__main__":
  # Start channel hopping
  args = get_mon_iface()
  hop = threading.Thread(target=channel_hop.channel_hop, args=[args])
  hop.daemon = True
  hop.start()
  sniffer = ScapyRssi(args)
  time.sleep(30)
  sniffer.plot(20)
  print "plotted"
