import socket
import json


class Network:
    def __init__(self):
        """creates network object"""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "localhost"
        self.port = 5555
        self.addr = (self.server, self.port)
        self.client.connect(self.addr)

    def send(self, data):
        """send data to server"""
        self.client.send(str.encode(json.dumps(data)))

    def recv(self):
        """recieve data from server"""
        return json.loads(self.client.recv(2048).decode())
