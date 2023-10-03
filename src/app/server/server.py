import socket
import threading
import os
import sys
import json

from src.environment.env import environment as env
from src.app.server.connection import Connection

class Server():

    def __init__(self):
        self._ip = env.HOST_IP
        self._port = env.HOST_PORT
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connections: list[Connection] = []

    def getIp(self):
        return self._ip
    
    def getPort(self):
        return self._port
    
    def getSocket(self):
        return self._socket

    def start(self):
        socket = self.getSocket()
        socket.bind((self.getIp(), self.getPort()))
        socket.listen()

        while True:
            print(f"Server running. Listening on port: {self.getPort()}")
            connection, address = socket.accept()
            data = connection.recv(env.MSG_MAX_SIZE).decode("utf-8").split("/")
            operation = data[1]

            if operation == "CONNECT":
                clientAdress = data[2]
                thread = threading.Thread(target=self.clientConnection, args=(clientAdress))
                thread.start()
                msg = "R/Connection successful"
                connection.send(bytes(msg, "utf-8"))

            connection.close()
    

    def clientConnection(self, clientAddress):
        pass


    def registerClient(self):
        pass