class BroadcastSocket:
	def __init__(self, port):
		self.s = socket(AF_INET, SOCK_DGRAM)
		self.port = port

		self.s.bind(('', 0))
		self.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

	def send(self, data):
		self.s.sendto(data, ('<broadcast>', self.port))

	def change_port(self, port):
		self.port = port

	def destroy(self):
		self.s.close()
