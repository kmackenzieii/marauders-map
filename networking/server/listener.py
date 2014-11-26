import SocketServer
import threading
import socket
import re

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

if __name__ == "__main__":
    sem = threading.Semaphore()
    people = dict([])
    HOST, PORT = "localhost", 8000
    server = ThreadedUDPServer((HOST, PORT), MyUDPHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    while(1):
	pass
