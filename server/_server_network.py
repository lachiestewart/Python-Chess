import socket
import json


class Network:
    def __init__(self):
        """creates network object"""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "localhost"
        self.port = 5555
        self.client.bind((self.server, self.port))
        self.client.listen()

    def send(self, conn, data):
        """send data to client"""
        conn.send(str.encode(json.dumps(data)))

    def recv(self, conn):
        """recieve data from client"""
        try:
            return json.loads(conn.recv(2048).decode())
        except:
            return "disconnected"

    def acpt(self):
        """accept new client"""
        return self.client.accept()
