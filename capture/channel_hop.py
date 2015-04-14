import time
import os
import sys
from subprocess import Popen, PIPE

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

def channel_hop(mon_iface):
    '''
    First time it runs through the channels it stays on each channel for 5 seconds
    in order to populate the deauth list nicely. After that it goes as fast as it can
    '''
    monchannel=''

    DN = open(os.devnull, 'w')

    channelNum = 0
    maxChan = 11
    err = None

    while 1:
            channelNum +=1
            if channelNum > maxChan:
                channelNum = 1
            monchannel = str(channelNum)

            try:
                proc = Popen(['iw', 'dev', mon_iface, 'set', 'channel', monchannel], stdout=DN, stderr=PIPE)
            except OSError:
                print '['+R+'-'+W+'] Could not execute "iw"'
                os.kill(os.getpid(),SIGINT)
                sys.exit(1)
            for line in proc.communicate()[1].split('\n'):
                if len(line) > 2: # iw dev shouldnt display output unless there's an error
                    err = '['+R+'-'+W+'] Channel hopping failed: '+R+line+W
            if err != None:
                print err, monchannel
            time.sleep(.2)
        
