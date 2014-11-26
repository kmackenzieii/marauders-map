from socket import *
class BroadcastSocket:
	def __init__(self, port):
		self.s = socket(AF_INET, SOCK_DGRAM)
		self.port = port

		self.s.bind(('', 0))
		self.s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

	def send(self, data):
		self.s.sendto(data, ('', self.port))

	def change_port(self, port):
		self.port = port

	def destroy(self):
		self.s.close()
if __name__ == "__main__":
	sock = BroadcastSocket(8000)
	for x in range(0, 10):
		sock.send("kyle, "+str(x)+", "+str(x))
		sock.send("victor, "+str(x)+", "+str(x))

