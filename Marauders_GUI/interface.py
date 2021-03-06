from tkinter import *
from subprocess import Popen
# from tkFileDialog import askopenfilename
import Image
import time
import sys
import signal
import os
from PIL import ImageTk
import kirk

if __name__ == "__main__":
    root = Tk()

    width = kirk.width
    height = kirk.height
    box_size = kirk.box_size
    img = ImageTk.PhotoImage(Image.open(kirk.File))
    w = Canvas(root, width=width, height=height)
    w.pack()
    w.create_image(0, 0, image=img, anchor="nw")

    for x in range(1, width // box_size):
        w.create_line(box_size * x, 0, box_size * x, height)
    for y in range(1, height // box_size):
        w.create_line(0, box_size * y, width, box_size * y)

    def piconnect(x, y):
        f = open('data/' + str(x) + '_' + str(y), 'w+')
        p = Popen("./rssi_out.sh;'", stdout=f,
                  shell=True, preexec_fn=os.setsid)  #, stdout=stdout, stderr=f)

        time.sleep(15)

        os.killpg(p.pid, signal.SIGKILL)
        f.close()

    #function to be called when mouse is clicked
    def printcoords(event):
        #outputting x and y coords to console
        print(event.x, event.y)


    #mouseclick event
    w.bind("<Button 1>", printcoords)

    root.mainloop()
