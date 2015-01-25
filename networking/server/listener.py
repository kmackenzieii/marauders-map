import SocketServer
import threading
import socket
import re
from PIL import Image
import kirk
import ImageTk
import Tkinter
from showTk import showTk


File = kirk.File
width = kirk.width
height = kirk.height
box_size = kirk.box_size
window = []

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
	pass

class MyUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = re.split(', ',self.request[0])
        socket = self.request[1]
	name = data[0]
	x = int(data[1])
	y = int(data[2])
	sem.acquire()
	if name in people:
		people[name] = (x ,y)
	else:
		people.update({name:(x, y)})
	print people
	sem.release()
	im = Image.open(File).copy()
	im.paste("red", (x*box_size, y*box_size, x*box_size+box_size, y*box_size+box_size))
	window.update(im = im)
if __name__ == "__main__":
    sem = threading.Semaphore()
    window = showTk(im = File)
    people = dict([])
    HOST, PORT = "<broadcast>", 8000
    server = ThreadedUDPServer((HOST, PORT), MyUDPHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    window.mainloop()
    while(1):
	pass
